from abc import ABC, abstractmethod
from config.settings import Settings

class BaseAgent(ABC):
    """
    An abstract base class for all agents in the system.
    It provides a common interface and shared setup functionality.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        print(f"✅ Initialized {self.__class__.__name__}")

    @abstractmethod
    async def run(self, data=None):
        """
        The main entry point for the agent's logic.
        Must be implemented by subclasses.
        """
        pass