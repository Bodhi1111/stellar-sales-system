#!/usr/bin/env python3
"""
Simple file watcher for automatic transcript processing.
Monitors the transcripts folder and processes new files automatically.
"""
import time
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from orchestrator.pipeline import run_pipeline


class TranscriptHandler(FileSystemEventHandler):
    """Handler for new transcript files"""
    
    def __init__(self, watch_directory: Path):
        self.watch_directory = watch_directory
        self.processed_files = set()
    
    def on_created(self, event):
        """Called when a new file is created"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Only process .txt files
        if file_path.suffix != '.txt':
            return
        
        # Avoid processing the same file twice
        if str(file_path) in self.processed_files:
            return
            
        print(f"\n🆕 New transcript detected: {file_path.name}")
        print(f"⏳ Processing...")
        
        # Mark as processed
        self.processed_files.add(str(file_path))
        
        # Process the file
        try:
            asyncio.run(run_pipeline(file_path))
            print(f"✅ Successfully processed: {file_path.name}\n")
        except Exception as e:
            print(f"❌ Failed to process {file_path.name}: {e}\n")


def watch_folder(watch_directory: Path):
    """Watch a folder for new transcript files"""
    if not watch_directory.exists():
        print(f"❌ Directory does not exist: {watch_directory}")
        return
    
    print(f"👀 Watching for new transcripts in: {watch_directory}")
    print(f"📂 Drop .txt files here to process automatically")
    print(f"Press Ctrl+C to stop\n")
    
    event_handler = TranscriptHandler(watch_directory)
    observer = Observer()
    observer.schedule(event_handler, str(watch_directory), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("✅ File watcher stopped")


if __name__ == "__main__":
    # Watch the standard transcripts folder
    from config.settings import settings
    watch_folder(settings.WATCHER_DIRECTORY)

