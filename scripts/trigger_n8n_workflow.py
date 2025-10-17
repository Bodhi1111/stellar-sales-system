#!/usr/bin/env python3
"""
Trigger N8N workflow via webhook with a transcript file.
Provides instant visual monitoring in N8N UI.
"""
import requests
import argparse
import json
from pathlib import Path
import sys
import time


class N8NWorkflowTrigger:
    """Trigger N8N workflow via webhook"""

    def __init__(self, webhook_url: str = "http://localhost:5678/webhook/stellar-sales-webhook"):
        self.webhook_url = webhook_url

    def trigger_workflow(self, transcript_path: Path) -> dict:
        """
        Send transcript to N8N webhook to trigger pipeline.

        Args:
            transcript_path: Path to transcript file

        Returns:
            dict: Response from webhook
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        print(f"\n{'='*70}")
        print("🚀 N8N WORKFLOW TRIGGER")
        print(f"{'='*70}")
        print(f"📄 File: {transcript_path.name}")
        print(f"📊 Size: {transcript_path.stat().st_size / 1024:.1f} KB")
        print(f"🌐 Webhook: {self.webhook_url}")
        print(f"{'='*70}\n")

        # Read file content
        with open(transcript_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Prepare multipart form data
        files = {
            'data': (transcript_path.name, file_content, 'text/plain')
        }

        # Additional metadata
        data = {
            'filename': transcript_path.name,
            'trigger_source': 'python_script',
            'timestamp': time.time()
        }

        try:
            print("📤 Sending file to webhook...")
            response = requests.post(
                self.webhook_url,
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ Workflow triggered successfully!")
                print(f"\n📊 Response Status: {response.status_code}")

                # Try to parse JSON response
                try:
                    result = response.json()
                    print(f"📋 Response Data:\n{json.dumps(result, indent=2)}")
                except:
                    print(f"📋 Response: {response.text[:500]}")

                print(f"\n{'='*70}")
                print("🎯 Next Steps:")
                print("   1. Open N8N UI: http://localhost:5678")
                print("   2. Go to 'Executions' tab")
                print("   3. Watch your workflow execute in real-time!")
                print(f"{'='*70}\n")

                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': response.text
                }
            else:
                print(f"❌ Webhook returned error: {response.status_code}")
                print(f"Response: {response.text}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }

        except requests.exceptions.ConnectionError:
            print("❌ ERROR: Could not connect to N8N webhook")
            print("   Make sure N8N is running at http://localhost:5678")
            print("   Check that the workflow is active and has a webhook trigger")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("❌ ERROR: Webhook request timed out")
            print("   The file might be too large or N8N is not responding")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            sys.exit(1)

    def check_n8n_status(self) -> bool:
        """Check if N8N is accessible"""
        try:
            response = requests.get("http://localhost:5678/healthz", timeout=5)
            return response.status_code == 200
        except:
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Trigger N8N workflow with a transcript file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trigger with test file
  %(prog)s --file data/transcripts/test_sprint01.txt

  # Use custom webhook URL
  %(prog)s --file data/transcripts/test.txt --url http://custom:5678/webhook/custom

  # Trigger and show help
  %(prog)s --help
"""
    )

    parser.add_argument(
        '--file',
        type=Path,
        required=True,
        help='Path to transcript file'
    )

    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:5678/webhook/stellar-sales-webhook',
        help='Webhook URL (default: http://localhost:5678/webhook/stellar-sales-webhook)'
    )

    args = parser.parse_args()

    # Initialize trigger
    trigger = N8NWorkflowTrigger(webhook_url=args.url)

    # Check N8N status
    print("🔍 Checking N8N status...")
    if not trigger.check_n8n_status():
        print("❌ WARNING: N8N may not be running or not accessible")
        print("   URL: http://localhost:5678")
        print("   Continuing anyway...\n")

    # Trigger workflow
    result = trigger.trigger_workflow(args.file)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
