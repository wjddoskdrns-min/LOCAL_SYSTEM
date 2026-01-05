from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Optional
import os
import uuid

# store
from app.store import store

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
EXECUTION_ENABLED = bool(int(os.getenv("EXECUTION_ENABLED", "0")))

app = FastAPI(title="LOCAL_SYSTEM Server")

START_TS = datetime.utcnow()
RID = str(uuid.uuid4())


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class RequestIn(BaseModel):
    kind: str = "generic"
    payload: Dict[str, Any] = {}


class ApproveIn(BaseModel):
    approver: str
    note: str = ""


# -----------------------------------------------------------------------------
# Core endpoints (ops_check 호환)
# -----------------------------------------------------------------------------
@app.get("/status")
def status():
    return {
        "ok": True,
        "rid": RID,
        "uptime_sec": int((datetime.utcnow() - START_TS).total_seconds()),
        "ts": datetime.utcnow().isoformat(),
    }


@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}


# -----------------------------------------------------------------------------
# Visibility endpoints (ops_check 호환)
# -----------------------------------------------------------------------------
@app.get("/rooms")
def rooms():
    # 기존 시스템과 호환만 유지하는 stub
    return {"ok": True, "rooms": ["SYSTEM", "HOLD", "APPROVED", "EXECUTED", "BLOCKED"]}


@app.get("/events/summary")
def events_summary(tail: int = 500, order: str = "desc"):
    # audit.jsonl 마지막 N줄을 요약/반환
    return store.events_summary(tail=tail, order=order)


# -----------------------------------------------------------------------------
# Workflow endpoints
# -----------------------------------------------------------------------------
@app.post("/requests")
def create_request(req: RequestIn):
    run_id = store.create_run(req.kind, req.payload)
    store.audit("REQUEST_CREATED", run_id, kind=req.kind, hold=True)
    return {"ok": True, "run_id": run_id, "state": "HOLD"}


@app.post("/approve/{run_id}")
def approve(run_id: str, body: ApproveIn):
    ok = store.approve(run_id, body.approver, body.note)
    if not ok:
        store.audit("APPROVE_BLOCKED", run_id, reason="RUN_NOT_FOUND")
        return {"ok": False, "run_id": run_id, "state": "RUN_NOT_FOUND"}

    store.audit("APPROVED", run_id, approver=body.approver, note=body.note)
    return {"ok": True, "run_id": run_id, "state": "APPROVED", "executed": 0}


@app.post("/execute/{run_id}")
def execute(run_id: str):
    rec = store.get_run(run_id)
    if rec is None:
        store.audit("EXECUTE_BLOCKED", run_id, reason="RUN_NOT_FOUND")
        return {"ok": False, "run_id": run_id, "state": "RUN_NOT_FOUND", "executed": 0}

    if rec.get("state") != "APPROVED":
        store.audit("EXECUTE_BLOCKED", run_id, reason="NOT_APPROVED")
        return {"ok": False, "run_id": run_id, "state": "BLOCKED", "executed": 0}

    if not EXECUTION_ENABLED:
        store.audit("EXECUTE_BLOCKED", run_id, reason="EXECUTION_DISABLED")
        return {"ok": False, "run_id": run_id, "state": "BLOCKED", "executed": 0}

    store.mark_executed(run_id)
    store.audit("EXECUTED", run_id, reason="OK")
    return {"ok": True, "run_id": run_id, "state": "EXECUTED", "executed": 1}


@app.post("/advice/{run_id}")
def create_advice(run_id: str):
    rec = store.get_run(run_id)
    if rec is None:
        store.audit("ADVICE_BLOCKED", run_id, reason="RUN_NOT_FOUND")
        return {"ok": False, "run_id": run_id, "state": "RUN_NOT_FOUND"}

    advice = {
        "ok": True,
        "run_id": run_id,
        "summary": f"[{rec.get('kind')}] HOLD/APPROVED/EXECUTE 판단 보조(더미)",
        "risks": ["execution disabled by default", "approval required"],
        "counter_cases": ["approved but EXECUTION_ENABLED=0 => BLOCKED"],
        "confidence": 0.3,
        "ts": datetime.utcnow().isoformat(),
    }
    store.save_advice(run_id, advice)
    store.audit("ADVICE_CREATED", run_id, reason="OK")
    return advice


@app.get("/advice/{run_id}")
def get_advice(run_id: str):
    advice = store.get_advice(run_id)
    if advice is None:
        store.audit("ADVICE_NOT_FOUND", run_id, reason="NO_FILE")
        return {"ok": False, "run_id": run_id, "state": "NOT_FOUND"}
    return advice
