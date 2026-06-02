from __future__ import annotations

from typing import Any, Dict, Optional


class OpenAIAdapter:
    """
    Mock OpenAI adapter. Implements a minimal interface used by CloudService.

    Replace the internals of these methods with real SDK calls when ready.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    def plan(self, context: Dict[str, Any], persona: Optional[str] = None) -> Dict[str, Any]:
        """Return a deterministic 'planning' response for testing."""
        # Deterministic mock: echo some keys from context to make tests predictable
        clip_count = len(context.get("clips", [])) if isinstance(context, dict) else 0
        return {
            "provider": "openai",
            "edit_plan": f"cut at 5s, zoom at 10s, clips={clip_count}",
            "persona_used": persona or "default",
        }

    def generate(self, prompt: str) -> Dict[str, Any]:
        """Return a deterministic creative generation response."""
        text = f"[OpenAI-Mock] Creative output for prompt: {prompt[:60]}"
        return {"provider": "openai", "text": text}

