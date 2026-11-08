from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.models.message import Message
from backend.app.schemas.memory import MemoryCandidate


class BaseModelProvider(ABC):
    @abstractmethod
    def extract_candidates(self, messages: List[Message]) -> List[MemoryCandidate]:
        """Extract memory candidates from raw messages."""
        pass

    @abstractmethod
    def classify_candidate(self, candidate: MemoryCandidate) -> MemoryCandidate:
        """Assign retain/summarize/discard action and rationale."""
        pass

    @abstractmethod
    def summarize_text(self, text: str, preserve_entities: Optional[List[str]] = None) -> str:
        """Produce compressed summary while retaining key facts."""
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Return embedding vector or None if unsupported."""
        pass

