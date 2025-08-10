#!/usr/bin/env python3
"""
Test script to verify the Flask server works locally
Run with: python test_local.py
"""

import requests
import base64
import json
from PIL import Image
import io

def create_test_image():
    """Create a simple test image"""
    # Create a 300x300 test image with some colors
    img = Image.new('RGB', (300, 300), color='white')
    
    # Add some colored rectangles
    pixels = img.load()
    for i in range(100):
        for j in range(100):
            pixels[i, j] = (255, 0, 0)  # Red square
            pixels[i + 100, j] = (0, 255, 0)  # Green square
            pixels[i + 200, j] = (0, 0, 255)  # Blue square
            pixels[i, j + 100] = (255, 255, 0)  # Yellow square
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    return img_data

def test_server():
    BASE_URL = "http://127.0.0.1:5000"
    
    print("🧪 Testing Flask server locally...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"✅ Server status: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python app.py")
        return False
    
    # Test 2: Upload test image
    test_image = create_test_image()
    upload_data = {
        "image": test_image,
        "name": "test_image.png"
    }
    
    print("📤 Uploading test image...")
    response = requests.post(f"{BASE_URL}/upload", json=upload_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result}")
    else:
        print(f"❌ Upload failed: {response.text}")
        return False
    
    # Test 3: Get image data
    print("📥 Getting image data...")
    response = requests.get(f"{BASE_URL}/get-img-data")
    
    if response.status_code == 200:
        data = response.text
        print(f"✅ Image data retrieved: {len(data)} characters")
        print(f"Sample: {data[:100]}...")
    else:
        print(f"❌ Failed to get image data: {response.text}")
        return False
    
    # Test 4: Check wakeup interval
    print("⏰ Testing wakeup interval...")
    response = requests.get(f"{BASE_URL}/wakeup-interval")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Wakeup interval: {result['interval']} seconds")
    else:
        print(f"❌ Failed to get wakeup interval: {response.text}")
        return False
    
    print("\n🎉 All tests passed! Server is working correctly.")
    return True

if __name__ == "__main__":
    test_server()