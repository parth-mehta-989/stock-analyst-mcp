"""Abstract cache interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...


class NullCache(Cache):
    def get(self, key: str) -> Optional[Any]:
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    def exists(self, key: str) -> bool:
        return False
