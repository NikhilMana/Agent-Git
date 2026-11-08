from typing import Optional
from backend.app.core.config import settings
from backend.app.providers.base import BaseModelProvider
from backend.app.providers.deterministic import DeterministicProvider
from backend.app.providers.ollama import OllamaProvider


def get_provider(mode: Optional[str] = None) -> BaseModelProvider:
    selected_mode = (mode or settings.AGENTGIT_MODE).lower()
    if selected_mode == "ollama":
        return OllamaProvider()
    return DeterministicProvider()


__all__ = ["BaseModelProvider", "DeterministicProvider", "OllamaProvider", "get_provider"]

