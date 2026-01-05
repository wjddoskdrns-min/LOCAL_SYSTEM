# app/store.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RunRecord:
    run_id: str
    kind: str
    payload: Dict[str, Any]
    state: str  # HOLD / APPROVED / EXECUTED
    executed: int


class Store:
    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        r = self._runs.get(run_id)
        if not r:
            return None
        return {
            "run_id": r.run_id,
            "kind": r.kind,
            "payload": r.payload,
            "state": r.state,
            "executed": r.executed,
        }

    def create_run(self, run_id: str, kind: str, payload: Dict[str, Any]) -> None:
        self._runs[run_id] = RunRecord(
            run_id=run_id,
            kind=kind,
            payload=payload,
            state="HOLD",
            executed=0,
        )

    def approve(self, run_id: str) -> bool:
        r = self._runs.get(run_id)
        if not r:
            return False
        r.state = "APPROVED"
        return True

    def mark_executed(self, run_id: str) -> bool:
        r = self._runs.get(run_id)
        if not r:
            return False
        r.state = "EXECUTED"
        r.executed = 1
        return True

    # --- Advice persistence (file-based, simplest) ---
    def save_advice(self, run_id: str, advice: Dict[str, Any]) -> None:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", f"advice_{run_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(advice, f, ensure_ascii=False, indent=2)

    def get_advice(self, run_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join("data", f"advice_{run_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


store = Store()
