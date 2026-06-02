from __future__ import annotations

from typing import Any, Dict, Optional

# Use relative imports so this module works when `src` is a package or when
# code adjusts sys.path at runtime (the project's other modules already do
# similar manipulations). This also makes static analysis happier.
from ..utils.config import Settings
from .providers.openai_adapter import OpenAIAdapter
from .providers.anthropic_adapter import AnthropicAdapter


class CloudService:
    """
    CloudService is the front-door for all LLM interactions. It holds
    provider adapters and exposes high-level methods used by the
    orchestrator such as `plan` and `generate`.

    This implementation uses Mock adapters to return deterministic
    responses so the orchestration and integration can be tested before
    real provider SDKs are integrated.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Initialize adapters with any relevant keys (mocked adapters ignore keys)
        self.adapters = {
            "openai": OpenAIAdapter(api_key=settings.openai_api_key),
            "anthropic": AnthropicAdapter(api_key=settings.anthropic_api_key),
        }

    def _select_provider(self, role: str, preferred: Optional[str] = None) -> str:
        """
        Select a provider based on the role (e.g., 'planning', 'creative')
        and optional preference. This selection logic is intentionally
        simple for now and can be extended to include fallbacks, weights,
        and circuit-breakers later.
        """
        if preferred and preferred in self.adapters:
            return preferred

        # Default routing: prefer Anthropic for planning, OpenAI for creative
        if role == "planning":
            return "anthropic" if self.settings.anthropic_api_key else "openai"
        if role == "creative":
            return "openai" if self.settings.openai_api_key else "anthropic"
        # Generic fallback
        return "openai"

    def plan(self, context: Dict[str, Any], persona: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Produce an edit/shot plan given the context and an optional persona.

        Returns a deterministic dict such as {"edit_plan": "cut at 5s, zoom at 10s"}
        when using mock adapters.
        """
        selected = self._select_provider(role="planning", preferred=provider)
        adapter = self.adapters[selected]
        return adapter.plan(context=context, persona=persona)

    def generate(self, prompt: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate creative text (e.g., voiceover, script) for a given prompt.

        Returns a deterministic dict with a `text` field in mock mode.
        """
        selected = self._select_provider(role="creative", preferred=provider)
        adapter = self.adapters[selected]
        return adapter.generate(prompt=prompt)
