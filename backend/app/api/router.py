from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.memory import router as memory_router
from backend.app.api.repositories import router as repositories_router
from backend.app.api.commits import router as commits_router
from backend.app.api.branches import router as branches_router
from backend.app.api.merge import router as merge_router
from backend.app.api.retrieval import router as retrieval_router
from backend.app.api.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(sessions_router)
api_router.include_router(memory_router)
api_router.include_router(repositories_router)
api_router.include_router(commits_router)
api_router.include_router(branches_router)
api_router.include_router(merge_router)
api_router.include_router(retrieval_router)
api_router.include_router(audit_router)

