# app/config.py
import os

def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

EXECUTION_ENABLED = bool(int(os.getenv("EXECUTION_ENABLED", "0")))
APPROVER_ALLOWLIST = _csv_env("APPROVER_ALLOWLIST", "partner")
