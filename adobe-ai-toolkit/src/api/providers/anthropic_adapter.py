from __future__ import annotations

from typing import Any, Dict, Optional


class AnthropicAdapter:
    """
    Mock Anthropic adapter. Implements the same minimal interface used by CloudService.

    Replace the internals with real Anthropic SDK calls when integrating.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    def plan(self, context: Dict[str, Any], persona: Optional[str] = None) -> Dict[str, Any]:
        """Return a deterministic 'planning' response for testing."""
        # Make the response slightly different to allow the orchestrator to
        # detect which provider produced the plan in integration tests.
        clip_count = len(context.get("clips", [])) if isinstance(context, dict) else 0
        return {
            "provider": "anthropic",
            "edit_plan": f"trim: start 2s end 20s; add_b_roll_every=10s; clips={clip_count}",
            "persona_used": persona or "default",
        }

    def generate(self, prompt: str) -> Dict[str, Any]:
        """Return a deterministic creative generation response."""
        text = f"[Anthropic-Mock] Script for prompt: {prompt[:60]}"
        return {"provider": "anthropic", "text": text}

