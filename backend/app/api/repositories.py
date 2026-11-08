from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.version_service import VersionService
from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(repo_in: RepositoryCreate, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    try:
        repo = version_svc.get_or_create_repository(name=repo_in.name, description=repo_in.description)
        return repo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REPOSITORY_CREATE_FAILED", "message": str(e)}
        )


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    return version_svc.list_repositories()


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(repository_id: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    repo = version_svc.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPOSITORY_NOT_FOUND", "message": f"Repository '{repository_id}' not found."}
        )
    return repo

