from abc import ABC, abstractmethod
from config.settings import Settings


class BaseAgent(ABC):
    """Abstract base class for agents."""

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
