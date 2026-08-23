"""Base sink interface."""
from abc import ABC, abstractmethod


class BaseSink(ABC):
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the target system."""

    @abstractmethod
    def write(self, records: list[dict], target: str) -> int:
        """Write records to target. Returns number of records written."""

    @abstractmethod
    def close(self) -> None:
        """Close connection and cleanup resources."""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
