#!/usr/bin/env python3
"""
Test script for the complete N8N webhook workflow.
This script sends a test transcript file to the webhook endpoint.
"""

import requests
import sys
from pathlib import Path

def test_webhook_with_file(file_path: str):
    """Test the webhook with a transcript file."""
    
    # Check if file exists
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
            
            print(f"🚀 Sending {file_path.name} to webhook...")
            print(f"📡 URL: {webhook_url}")
            
            # Send the request
            response = requests.post(webhook_url, files=files, data=data, timeout=60)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: Webhook triggered successfully!")
                print(f"📄 Response: {response.text}")
                return True
            else:
                print(f"❌ ERROR: Webhook failed with status {response.status_code}")
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
        print("Usage: python test_webhook_complete.py <transcript_file>")
        print("\nExample:")
        print("  python test_webhook_complete.py data/transcripts/test_sprint01.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = test_webhook_with_file(file_path)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📊 Check N8N UI at http://localhost:5678 for execution details")
        print("🗄️  Check Qdrant at http://localhost:6333/dashboard for vectors")
        print("📋 Check Baserow at http://localhost:8080 for CRM data")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
