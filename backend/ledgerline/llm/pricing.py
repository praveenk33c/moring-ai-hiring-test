"""Token pricing for the cost dashboard and the llm_calls table."""
from __future__ import annotations

# USD per million tokens: (input, output). From the providers' pricing pages.
# Last updated Oct 2026 (RK) when we moved to the 5.5 models.
USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-4-5": (5.0, 25.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.0),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.0-flash": (0.10, 0.40),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = USD_PER_MTOK.get(model, (0.0, 0.0))
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
