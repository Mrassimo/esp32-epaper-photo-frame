# ESP32 E-Paper Photo Frame Server

A Flask server for processing and serving images to an ESP32-powered E-Paper digital photo frame.

## Features

- 🖼️ Web interface for easy photo uploads
- 🎨 Automatic image processing with Floyd-Steinberg dithering
- 🎯 7-color palette optimization for E-Paper displays
- ⚡ REST API endpoints for ESP32 communication
- 💤 Smart power management scheduling
- 🌐 Cloud deployment ready (Railway, Heroku, etc.)

## Quick Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/zUcpux)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py

# Test the server
python test_local.py
```

## API Endpoints

- `GET /` - Web interface for photo uploads
- `POST /upload` - Upload and process new images
- `GET /get-img-data` - Get processed image data for ESP32
- `GET /wakeup-interval` - Get sleep interval based on time
- `GET /status` - Server and image status
- `POST /clear-images` - Clear all stored images

## Image Processing

Images are automatically:
1. Resized to 600x448 pixels (E-Paper display size)
2. Processed with Floyd-Steinberg dithering
3. Converted to 7-color palette for optimal E-Paper display
4. Formatted as hex data for ESP32 consumption

## Power Schedule

- **8 AM - 8 PM**: ESP32 requests updates hourly
- **8 PM - 8 AM**: Deep sleep mode for battery conservation

## Deployment

Ready for deployment on:
- Railway (recommended, $5/month free tier)
- Heroku
- Render
- Any Python PaaS platform

See [SETUP_GUIDE.md](../SETUP_GUIDE.md) for complete setup instructions.