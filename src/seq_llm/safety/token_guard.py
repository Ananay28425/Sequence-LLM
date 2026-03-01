"""
Token safety utilities.

Prevents conversations from exceeding model context window,
which would otherwise cause crashes or OOM errors.
"""

from typing import List, Tuple


def estimate_tokens(text: str) -> int:
    """
    Rough token estimator.

    Rule of thumb:
        1 token ≈ 4 characters (safe conservative approximation)
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def conversation_tokens(messages: List[dict]) -> int:
    """Calculate approximate token count for conversation."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("content", ""))
    return total


def ensure_within_ctx(
    messages: List[dict],
    ctx_size: int,
    safety_margin: float = 0.9,
) -> Tuple[List[dict], bool]:
    """
    Trim conversation to fit within context window.

    Returns:
        (trimmed_messages, fits_flag)
    """

    if ctx_size <= 0:
        return messages, True

    safe_limit = int(ctx_size * safety_margin)

    total = 0
    trimmed = []

    # Keep most recent messages first
    for msg in reversed(messages):
        t = estimate_tokens(msg.get("content", ""))
        if total + t > safe_limit:
            break
        trimmed.insert(0, msg)
        total += t

    return trimmed, total <= safe_limit
