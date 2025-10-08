import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from agents.base_agent import BaseAgent
from config.settings import settings
from orchestrator.pipeline import run_pipeline


class FileCreationHandler(FileSystemEventHandler):
    """A handler that calls the async pipeline when a file is created."""

    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        if not event.is_directory:
            print(f"📄 New file detected: {event.src_path}")
            # Safely call our async pipeline from this synchronous thread
            asyncio.run_coroutine_threadsafe(
                run_pipeline(file_path=Path(event.src_path)),
                self.loop
            )


class WatcherAgent(BaseAgent):
    """This agent watches a directory and triggers the main pipeline."""

    def __init__(self, settings):
        super().__init__(settings)
        self.path_to_watch = str(settings.WATCHER_DIRECTORY)

    async def run(self, data=None):
        loop = asyncio.get_running_loop()
        event_handler = FileCreationHandler(loop)
        observer = Observer()
        observer.schedule(event_handler, self.path_to_watch, recursive=False)
        observer.start()

        print(f"🔎 WatcherAgent is now monitoring '{self.path_to_watch}'...")
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            observer.stop()
            observer.join()


# This block allows us to test the agent
if __name__ == "__main__":
    agent = WatcherAgent(settings)
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\nWatcher agent stopped by user.")
