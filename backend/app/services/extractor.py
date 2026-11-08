from typing import List, Optional
from backend.app.models.message import Message
from backend.app.schemas.memory import MemoryCandidate
from backend.app.providers import get_provider


class CandidateExtractor:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode

    def extract(self, messages: List[Message], mode: Optional[str] = None) -> List[MemoryCandidate]:
        provider = get_provider(mode or self.mode)
        candidates = provider.extract_candidates(messages)
        return candidates

