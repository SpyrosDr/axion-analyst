from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.ai.client import AIProviderError
from app.config import settings
from app.database.db import init_db
from app.routes import ai, auth, cases, evidence, reports, tools
from app.search.client import SearchProviderError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Axion Analyst Investigation Workbench",
    description="MVP backend for structured fraud investigation support.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(AIProviderError)
async def ai_provider_error_handler(request: Request, exc: AIProviderError):
    return JSONResponse(
        status_code=502,
        content={
            "detail": f"AI provider ({settings.AI_PROVIDER}) request failed: {exc}"
        },
    )


@app.exception_handler(SearchProviderError)
async def search_provider_error_handler(request: Request, exc: SearchProviderError):
    return JSONResponse(
        status_code=502,
        content={
            "detail": f"Search provider ({settings.SEARCH_PROVIDER}) request failed: {exc}"
        },
    )


app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(tools.router)


@app.get("/")
def read_root():
    return {
        "message": "Fraud Investigation Workbench API is running"
    }
