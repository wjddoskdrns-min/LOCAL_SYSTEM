# app/main.py
from __future__ import annotations

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.store import store

app = FastAPI(title="LOCAL_SYSTEM Server")

AUDIT_PATH = Path(__file__).resolve().parents[1] / "audit.jsonl"
START_TS = datetime.now(timezone.utc)
RID = str(uuid.uuid4())


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def audit(event: Dict[str, Any]) -> None:
    event["ts"] = _utc_iso()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def env_bool(name: str, default: str = "0") -> bool:
    return bool(int(os.getenv(name, default)))


def get_execution_enabled() -> bool:
    return env_bool("EXECUTION_ENABLED", "0")


def get_allowlist() -> List[str]:
    raw = os.getenv("APPROVER_ALLOWLIST", "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


class RequestIn(BaseModel):
    kind: str = "demo"
    payload: Dict[str, Any] = {}


class ApproveIn(BaseModel):
    approver: str
    note: str = ""


@app.get("/status")
def status() -> Dict[str, Any]:
    uptime = (datetime.now(timezone.utc) - START_TS).total_seconds()
    return {"ok": True, "rid": RID, "uptime_sec": int(uptime), "ts": _utc_iso()}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "ts": _utc_iso()}


@app.post("/requests")
def create_request(req: RequestIn) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    store.create_run(run_id, req.kind, req.payload)
    audit({"event": "REQUEST_CREATED", "run_id": run_id, "kind": req.kind, "hold": True})
    return {"ok": True, "run_id": run_id, "state": "HOLD"}


@app.post("/approve/{run_id}")
def approve(run_id: str, body: ApproveIn) -> Dict[str, Any]:
    allow = get_allowlist()
    if allow and body.approver not in allow:
        audit(
            {
                "event": "APPROVE_FORBIDDEN",
                "run_id": run_id,
                "approver": body.approver,
                "allowlist": allow,
            }
        )
        # 403은 "정상 차단" (의도된 보안 신호)
        raise HTTPException(status_code=403, detail="approver not in allowlist")

    ok = store.approve(run_id)
    if not ok:
        audit({"event": "APPROVE_NOT_FOUND", "run_id": run_id, "approver": body.approver})
        raise HTTPException(status_code=404, detail="run_id not found")

    audit({"event": "APPROVED", "run_id": run_id, "approver": body.approver, "note": body.note})
    return {"ok": True, "run_id": run_id, "state": "APPROVED", "executed": 0}


@app.post("/execute/{run_id}")
def execute(run_id: str) -> Dict[str, Any]:
    rec = store.get_run(run_id)
    if rec is None:
        audit({"event": "EXECUTE_NOT_FOUND", "run_id": run_id})
        return {"ok": False, "run_id": run_id, "state": "RUN_NOT_FOUND", "executed": 0}

    if rec["state"] != "APPROVED":
        audit({"event": "EXECUTE_BLOCKED", "run_id": run_id, "reason": "NOT_APPROVED"})
        return {"ok": False, "run_id": run_id, "state": "BLOCKED", "executed": 0}

    if not get_execution_enabled():
        audit({"event": "EXECUTE_BLOCKED", "run_id": run_id, "reason": "EXECUTION_DISABLED"})
        return {"ok": False, "run_id": run_id, "state": "BLOCKED", "executed": 0}

    store.mark_executed(run_id)
    audit({"event": "EXECUTED", "run_id": run_id, "reason": "OK"})
    return {"ok": True, "run_id": run_id, "state": "EXECUTED", "executed": 1}


@app.post("/advice/{run_id}")
def create_advice(run_id: str) -> Dict[str, Any]:
    rec = store.get_run(run_id)
    if rec is None:
        audit({"event": "ADVICE_BLOCKED", "run_id": run_id, "reason": "RUN_NOT_FOUND"})
        return {"ok": False, "run_id": run_id, "state": "RUN_NOT_FOUND"}

    exec_enabled = get_execution_enabled()
    advice = {
        "ok": True,
        "run_id": run_id,
        "summary": f"[{rec.get('kind')}] state={rec.get('state')} exec_enabled={1 if exec_enabled else 0}",
        "risks": {
            "execution enabled (EXECUTION_ENABLED=1) — ensure approvals are strict"
            if exec_enabled
            else "execution disabled (EXECUTION_ENABLED=0)"
        },
        "counter_cases": {
            "non-allowlisted approver => 403" if get_allowlist() else "allowlist empty => no approver gating"
        },
        "confidence": 0.4 if exec_enabled else 0.3,
        "ts": _utc_iso(),
    }
    audit({"event": "ADVICE_CREATED", "run_id": run_id, "reason": "OK"})
    store.save_advice(run_id, advice)
    return advice


@app.get("/advice/{run_id}")
def get_advice(run_id: str) -> Dict[str, Any]:
    adv = store.get_advice(run_id)
    if adv is None:
        return {"ok": False, "run_id": run_id, "state": "NOT_FOUND"}
    return adv
