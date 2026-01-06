from __future__ import annotations

from typing import Any, Dict, List

from .contract import AssistRequest, AssistResponse, clamp_int


def run_assist(req: AssistRequest) -> AssistResponse:
    """
    Placeholder engine (local deterministic).
    Later: swap with LLM provider(s), but keep SSOT contract stable.
    """
    # 기본: 역할별 템플릿만 제공 (결론/집행/판단 금지)
    role = req.role

    if role == "summarize":
        summary = "요약: 핵심 맥락/변수/현재 상태를 압축 정리합니다(결론 없음)."
        bullets = [
            "현재 입력(prompt)에서 주요 명사/조건/목표를 추출",
            "불확실/누락된 전제를 표시",
            "다음 행동 후보를 '제안' 형태로만 나열",
        ]
        evidence_codes = ["CTX", "VAR", "GOAL"]
        risk_floor = 10

    elif role == "risk_countercase":
        summary = "리스크/반례: 실패 시나리오와 반례를 우선 정렬합니다(결론 없음)."
        bullets = [
            "가장 치명적인 반례 3개를 먼저",
            "꼬리리스크(p95/p99) 관점에서 체크",
            "SSOT/권한/상태전이 위반 가능성 경고",
        ]
        evidence_codes = ["CC", "TAIL", "SSOT"]
        risk_floor = 35

    elif role == "evidence_priority":
        summary = "근거 압축: 필요한 근거를 우선순위로 압축합니다(결론 없음)."
        bullets = [
            "필요 근거를 '필수/권장/선택'으로 분류",
            "시간/비용 대비 정보가치(VOI) 기준 정렬",
            "검증 순서를 최소 단계로 제안",
        ]
        evidence_codes = ["EVI", "VOI", "ORDER"]
        risk_floor = 20

    else:
        summary = "알 수 없는 role 입니다."
        bullets = ["role 값을 확인하세요: summarize | risk_countercase | evidence_priority"]
        evidence_codes = ["ERR_ROLE"]
        risk_floor = 50

    return AssistResponse(
        request_id=req.request_id,
        role=req.role,
        ok=True,
        summary=summary,
        bullets=bullets,
        risk_floor_score=clamp_int(risk_floor, 0, 100),
        evidence_codes=evidence_codes,
        conflicts_with=[],
        novelty_score=0.2,
        notes={"provider": "local_stub", "timebox_ms": req.timebox_ms},
    )
