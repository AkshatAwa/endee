from fastapi import FastAPI
from .routes.analyze import router as analyze_router
from fastapi.middleware.cors import CORSMiddleware
from .routes.default_draft import router as default_draft_router
from .routes.dev_console import router as dev_router
from .routes.research import router as research_router
from .middleware.api_key_usage import ApiKeyUsageMiddleware

app = FastAPI(
    title="SwaRakshak Legal Intelligence API",
    version="1.0",
    description="India-specific verified legal intelligence API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApiKeyUsageMiddleware)


app.include_router(analyze_router, prefix="/v1")
app.include_router(default_draft_router, prefix="/v1")
app.include_router(dev_router, prefix="/v1")
app.include_router(research_router, prefix="/v1")

@app.get("/")
def root():
    return {"status": "SwaRakshak LegalAPI running"}


@app.get("/health")
def health():
    return {"status": "ok"}
