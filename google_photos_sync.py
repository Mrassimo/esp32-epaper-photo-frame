"""
Google Photos Album Sync for ESP32 E-Paper Photo Frame
Automatically fetches photos from a shared Google Photos album
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
import json
import time

class GooglePhotosSync:
    def __init__(self):
        # These will be set as environment variables in Railway
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET') 
        self.refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
        self.album_id = os.getenv('GOOGLE_ALBUM_ID')
        self.access_token = None
        self.token_expires = None
        
    def get_access_token(self):
        """Get or refresh Google Photos API access token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
            
        if not self.refresh_token:
            print("No refresh token available. Need to complete OAuth flow.")
            return None
            
        # Refresh the access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(token_url, data=data)
            token_data = response.json()
            
            if 'access_token' in token_data:
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                return self.access_token
            else:
                print(f"Token refresh failed: {token_data}")
                return None
                
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None
    
    def get_album_photos(self, max_photos=50):
        """Fetch photos from the specified Google Photos album"""
        access_token = self.get_access_token()
        if not access_token:
            return []
        
        # First, get the album details to find the album ID
        if not self.album_id:
            print("No album ID provided")
            return []
        
        # Search for media items in the album
        search_url = "https://photoslibrary.googleapis.com/v1/mediaItems:search"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        request_body = {
            'albumId': self.album_id,
            'pageSize': min(max_photos, 100)  # Google Photos API max is 100
        }
        
        try:
            response = requests.post(search_url, headers=headers, json=request_body)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('mediaItems', [])
            else:
                print(f"Failed to fetch photos: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching photos: {e}")
            return []
    
    def download_photo(self, photo_item):
        """Download a photo and return it as base64"""
        try:
            # Get the base URL and add download parameters
            base_url = photo_item['baseUrl']
            download_url = f"{base_url}=w600-h448-c"  # Resize to our target dimensions
            
            response = requests.get(download_url)
            if response.status_code == 200:
                # Convert to base64
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                return {
                    'base64': image_base64,
                    'filename': photo_item.get('filename', 'unknown.jpg'),
                    'creation_time': photo_item.get('mediaMetadata', {}).get('creationTime', ''),
                    'id': photo_item['id']
                }
            else:
                print(f"Failed to download photo: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading photo: {e}")
            return None
    
    def sync_album_photos(self, process_image_callback, max_photos=10):
        """Sync photos from Google Photos album and process them"""
        print(f"🔄 Syncing photos from Google Photos album...")
        
        photos = self.get_album_photos(max_photos)
        if not photos:
            print("❌ No photos found or failed to fetch")
            return []
        
        print(f"📸 Found {len(photos)} photos in album")
        
        processed_photos = []
        for i, photo in enumerate(photos):
            print(f"🔄 Processing photo {i+1}/{len(photos)}: {photo.get('filename', 'unknown')}")
            
            # Download the photo
            downloaded = self.download_photo(photo)
            if downloaded:
                # Process through the same pipeline as manual uploads
                processed_data = process_image_callback(downloaded['base64'])
                if processed_data:
                    processed_photos.append({
                        'data': processed_data,
                        'timestamp': datetime.now().isoformat(),
                        'name': downloaded['filename'],
                        'google_id': downloaded['id'],
                        'creation_time': downloaded['creation_time']
                    })
                    print(f"✅ Processed {downloaded['filename']}")
                else:
                    print(f"❌ Failed to process {downloaded['filename']}")
            
            # Small delay to be nice to the API
            time.sleep(0.5)
        
        print(f"🎉 Successfully processed {len(processed_photos)} photos")
        return processed_photos

def get_album_id_from_url(share_url):
    """Extract album ID from Google Photos share URL"""
    # Example URL: https://photos.app.goo.gl/xxxxx
    # We'll need to follow redirects to get the actual album ID
    try:
        response = requests.get(share_url, allow_redirects=True)
        final_url = response.url
        
        # Look for album ID in the final URL
        if 'albums/' in final_url:
            album_id = final_url.split('albums/')[-1].split('?')[0]
            return album_id
        else:
            print(f"Could not extract album ID from URL: {final_url}")
            return None
            
    except Exception as e:
        print(f"Error extracting album ID: {e}")
        return None