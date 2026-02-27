from fastapi import APIRouter, Request, HTTPException
from Backend.LegalAPI.app.auth.api_key_manager import generate_api_key
import os

router = APIRouter(prefix="/dev", tags=["Dev"])

@router.post("/generate-api-key")
def dev_generate_api_key(request: Request):
    client_host = request.client.host if request.client else None
    allow_env = os.getenv("ALLOW_DEV_KEY_GEN", "false").lower() == "true"
    if not allow_env and client_host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Dev key generation not allowed")

    result = generate_api_key(owner="dev_console", app_name="rakshak_web")
    return {
        "api_key": result["plaintext"],
        "key_id": result["record"]["key_id"],
        "status": result["record"]["status"],
        "created_at": result["record"]["created_at"],
        "note": "This key will not be shown again"
    }

