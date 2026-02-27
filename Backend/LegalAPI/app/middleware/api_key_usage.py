from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from typing import Callable
from starlette.responses import JSONResponse
from Backend.LegalAPI.app.auth.api_key import validate_api_key

class ApiKeyUsageMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        api_key = None
        if auth:
            api_key = auth.replace("Bearer ", "")
        path = request.url.path or ""

        if request.method == "OPTIONS":
            return await call_next(request)

        protected = (
            path.startswith("/v1/analyze")
            or path.startswith("/v1/draft")
        )
        dev_whitelist = path.startswith("/v1/dev/generate-api-key")

        is_valid = validate_api_key(api_key) if api_key else False
        request.state.api_key_valid = is_valid

        if protected and not dev_whitelist and not is_valid:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"}
            )

        response = await call_next(request)
        return response
