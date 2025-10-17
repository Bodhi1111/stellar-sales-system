#!/usr/bin/env python3
"""
Upload a transcript file to the webhook for processing.
"""

import requests
import sys
from pathlib import Path

def upload_transcript(file_path: str):
    """Upload a transcript file to the webhook."""
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ ERROR: File not found: {file_path}")
        return False
    
    # Webhook URL
    webhook_url = "http://localhost:5678/webhook/stellar-sales-webhook"
    
    try:
        # Prepare the file for upload
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/plain')
            }
            data = {
                'filename': file_path.name,
                'transcript_id': file_path.stem.replace(' ', '_')
            }
            
            print(f"🚀 Uploading {file_path.name} to webhook...")
            print(f"📡 URL: {webhook_url}")
            
            # Send the request
            response = requests.post(webhook_url, files=files, data=data, timeout=60)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: Transcript uploaded and processing started!")
                print(f"📄 Response: {response.text}")
                print("\n📊 Check N8N UI at http://localhost:5678 for execution details")
                print("📋 Check Baserow at http://localhost:8080 for CRM data")
                return True
            else:
                print(f"❌ ERROR: Upload failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python upload_transcript.py <transcript_file_path>")
        print("\nExample:")
        print("  python upload_transcript.py /path/to/Linda_Barnes_transcript.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = upload_transcript(file_path)
    
    if success:
        print("\n🎉 Upload completed successfully!")
    else:
        print("\n💥 Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
