import os
import json
import hmac
import hashlib
import secrets
import time
from typing import Optional, Dict, Any, List

STORAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "storage", "api_keys.json")
)

def _ensure_storage_file():
    os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
    if not os.path.exists(STORAGE_PATH):
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def _load_keys() -> List[Dict[str, Any]]:
    _ensure_storage_file()
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def _save_keys(keys: List[Dict[str, Any]]) -> None:
    _ensure_storage_file()
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2)

def _sha256(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

def _new_key_id() -> str:
    return secrets.token_hex(8)

def generate_api_key(owner: Optional[str] = None, app_name: Optional[str] = None, requests_left: Optional[int] = None) -> Dict[str, Any]:
    rand_a = secrets.token_urlsafe(32)
    rand_b = secrets.token_hex(16)
    ts_ns = str(int(time.time_ns()))
    plaintext = f"rakshak_live_{rand_a}{rand_b}{ts_ns}"
    hashed = _sha256(plaintext)

    record = {
        "key_id": _new_key_id(),
        "hashed_key": hashed,
        "status": "active",
        "created_at": int(time.time()),
        "owner": owner,
        "app_name": app_name,
        "requests_left": requests_left,
    }

    keys = _load_keys()
    keys.append(record)
    _save_keys(keys)

    print(f"DEBUG: generated key_id={record['key_id']} hash={hashed}")

    return {
        "plaintext": plaintext,
        "record": record
    }

def check_api_key(plaintext: str) -> Optional[Dict[str, Any]]:
    if not plaintext:
        return None
    keys = _load_keys()
    for rec in keys:
        status = rec.get("status", "active")
        if status != "active" and rec.get("active") is False:
            continue

        hashed_key = rec.get("hashed_key")
        if hashed_key:
            candidate = _sha256(plaintext)
            if hmac.compare_digest(candidate, hashed_key):
                if rec.get("requests_left") is not None:
                    if rec["requests_left"] <= 0:
                        return None
                    rec["requests_left"] -= 1
                    _save_keys(keys)
                return rec
        else:
            legacy_plain = rec.get("api_key")
            if isinstance(legacy_plain, str) and hmac.compare_digest(legacy_plain, plaintext):
                if rec.get("requests_left") is not None:
                    if rec["requests_left"] <= 0:
                        return None
                    rec["requests_left"] -= 1
                    _save_keys(keys)
                return rec
    return None
