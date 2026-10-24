"""
Ports: what the use cases need from the outside world, without saying how it's
done. The adapters in adapters/ implement them; tests use in-memory fakes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain.history import HistoryEntry


class HistoryRepository(Protocol):
    """Where the history is kept."""

    def read(self) -> list[HistoryEntry]: ...

    def append(self, entry: HistoryEntry) -> None: ...


@dataclass(frozen=True)
class ConductFile:
    location: str  # where it was read from, for display
    text: str


class ConductSource(Protocol):
    """Where the latest conduct summary comes from."""

    def latest(self) -> ConductFile | None:
        """The most recent conduct file, or None if there isn't one."""
        ...
