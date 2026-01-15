"""Base collector interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """Abstract base class for all performance collectors."""

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Collect performance metrics.
        
        Returns:
            Dictionary containing collected metrics.
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get a description of what this collector measures.
        
        Returns:
            Human-readable description string.
        """
        pass
