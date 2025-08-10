import os
import tempfile
import base64
from datetime import datetime, time, timedelta
from flask import Flask, request, jsonify, render_template
from PIL import Image
import numpy as np
from io import BytesIO

app = Flask(__name__)

# In-memory storage for images (since we can't use local file system reliably in cloud)
processed_images = []
sent_images = []
current_image_index = 0

# Define the 7-color palette mapping
color_palette = {
    (255, 255, 255): 0xFF,  # White
    (255, 255, 0): 0xFC,    # Yellow
    (255, 165, 0): 0xEC,    # Orange
    (255, 0, 0): 0xE0,      # Red
    (0, 128, 0): 0x35,      # Green
    (0, 0, 255): 0x2B,      # Blue
    (0, 0, 0): 0x00         # Black
}

def closest_palette_color(rgb):
    """Find the closest color in the palette."""
    min_dist = float('inf')
    closest_color = (255, 255, 255)  # Default to white
    for palette_rgb in color_palette:
        dist = sum((int(rgb[i]) - int(palette_rgb[i])) ** 2 for i in range(3))
        if dist < min_dist:
            min_dist = dist
            closest_color = palette_rgb
    return closest_color

def apply_floyd_steinberg_dithering(image):
    """Apply Floyd-Steinberg dithering to the image."""
    pixels = np.array(image, dtype=np.int16)
    for y in range(image.height):
        for x in range(image.width):
            old_pixel = tuple(pixels[y, x][:3])
            new_pixel = closest_palette_color(old_pixel)
            pixels[y, x][:3] = new_pixel
            quant_error = np.array(old_pixel) - np.array(new_pixel)
            
            # Distribute the quantization error to neighboring pixels
            if x + 1 < image.width:
                pixels[y, x + 1][:3] += (quant_error * 7 / 16).astype(np.int16)
            if x - 1 >= 0 and y + 1 < image.height:
                pixels[y + 1, x - 1][:3] += (quant_error * 3 / 16).astype(np.int16)
            if y + 1 < image.height:
                pixels[y + 1, x][:3] += (quant_error * 5 / 16).astype(np.int16)
            if x + 1 < image.width and y + 1 < image.height:
                pixels[y + 1, x + 1][:3] += (quant_error * 1 / 16).astype(np.int16)
    
    pixels = np.clip(pixels, 0, 255)
    return Image.fromarray(pixels.astype(np.uint8))

def process_image(image_data):
    """Process uploaded image and convert to display format."""
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Resize and convert
        image = image.resize((600, 448))
        image = image.convert("RGB")
        
        # Apply dithering
        dithered_image = apply_floyd_steinberg_dithering(image)
        
        # Create data array
        data_array = []
        for y in range(448):
            for x in range(600):
                rgb = dithered_image.getpixel((x, y))
                color_code = color_palette.get(tuple(rgb), 0xFF)
                data_array.append(f"0x{color_code:02X}")
        
        return ", ".join(data_array)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload and process a new image."""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        processed_data = process_image(data['image'])
        if processed_data:
            processed_images.append({
                'data': processed_data,
                'timestamp': datetime.now().isoformat(),
                'name': data.get('name', f'image_{len(processed_images) + 1}')
            })
            
            return jsonify({
                "message": "Image uploaded and processed successfully",
                "total_images": len(processed_images)
            })
        else:
            return jsonify({"error": "Failed to process image"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/get-img-data', methods=['GET'])
def get_img_data():
    """Get the next image data in the format expected by ESP32."""
    global current_image_index
    
    if not processed_images:
        return jsonify({"error": "No images available"}), 404
    
    # Get next image (cycle through available images)
    image = processed_images[current_image_index % len(processed_images)]
    current_image_index = (current_image_index + 1) % len(processed_images)
    
    # Track sent images
    if image not in sent_images:
        sent_images.append(image)
    
    # Return the data in the format expected by ESP32
    return image['data'], 200, {'Content-Type': 'text/plain'}

@app.route('/status', methods=['GET'])
def status():
    """Get server status."""
    return jsonify({
        "total_images": len(processed_images),
        "sent_images": len(sent_images),
        "current_index": current_image_index,
        "uptime": "running"
    })

@app.route('/wakeup-interval', methods=['GET'])
def wakeup_interval():
    """Return the interval until next wakeup based on time schedule."""
    now = datetime.now()
    current_time = now.time()

    # Define time boundaries
    morning_time = time(8, 0)  # 8 AM
    evening_time = time(20, 0)  # 8 PM

    if morning_time <= current_time < evening_time:
        interval = 3600  # 1 hour in seconds during day
    else:
        # Calculate seconds until the next 8 AM
        next_morning = datetime.combine(now.date() + timedelta(days=1), morning_time)
        interval = int((next_morning - now).total_seconds())

    return jsonify(interval=interval)

@app.route('/clear-images', methods=['POST'])
def clear_images():
    """Clear all stored images (for testing)."""
    global processed_images, sent_images, current_image_index
    processed_images = []
    sent_images = []
    current_image_index = 0
    
    return jsonify({"message": "All images cleared"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)