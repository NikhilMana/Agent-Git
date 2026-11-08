import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import create_all_tables
from backend.app.api.router import api_router
from backend.app.api.health import router as health_router

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AgentGit database schema...")
    create_all_tables()
    logger.info("AgentGit backend initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AgentGit — Model-Agnostic, User-Controllable, Versioned Memory Layer for AI Agents",
    lifespan=lifespan
)

# Enable CORS for local dev & dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": detail}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail)}}
    )


# Root health endpoint as defined in API_SPEC.md
app.include_router(health_router)

# Versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static web dashboard UI
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root_ui():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "AgentGit",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "health": "/health"
    }


@app.get("/ui")
def ui_redirect():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "UI not found"}
