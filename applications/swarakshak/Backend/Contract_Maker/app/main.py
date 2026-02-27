from fastapi import FastAPI
from Backend.LegalAPI.app.routes.default_draft import router as default_draft_router
from Backend.Contract_Maker.app.engine.Custom_Clause.output.custom_draft import router as custom_draft_router

app = FastAPI()

app.include_router(default_draft_router)
app.include_router(custom_draft_router)
