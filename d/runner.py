import os, json, time

print(json.dumps({
    "ts": time.time(),
    "scope": os.getenv("SCOPE", "unknown"),
    "mode": os.getenv("MODE", "noop"),
    "note": "D_LAYER_OK_NO_EXECUTION"
}, ensure_ascii=False))
