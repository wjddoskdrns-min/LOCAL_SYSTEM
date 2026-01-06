from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


AssistantRole = Literal["summarize", "risk_countercase", "evidence_priority"]


@dataclass(frozen=True)
class AssistRequest:
    """
    Judgment Assist is READ/PROPOSE only.
    It must never decide/execute. It only returns structured notes for the human/main-core.
    """
    request_id: str
    role: AssistantRole
    prompt: str
    context: Optional[dict[str, Any]] = None
    timebox_ms: int = 2500  # hard timebox for assist (rule-level)
    max_tokens_hint: int = 800


@dataclass(frozen=True)
class AssistResponse:
    request_id: str
    role: AssistantRole
    ok: bool
    summary: str
    bullets: list[str]
    risk_floor_score: int  # 0~100 (lower bound risk emphasis)
    evidence_codes: list[str]
    conflicts_with: list[str]
    novelty_score: float  # 0~1
    notes: Optional[dict[str, Any]] = None


def clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(x)))
