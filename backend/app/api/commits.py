from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.version_service import VersionService
from backend.app.schemas.commit import (
    CommitCreate,
    CommitResponse,
    CommitDiffResponse,
    SnapshotItemResponse
)

router = APIRouter(tags=["Commits & Snapshots"])


@router.post("/repositories/{repository_id}/commits", response_model=CommitResponse, status_code=status.HTTP_201_CREATED)
def create_commit(
    repository_id: str,
    commit_in: CommitCreate,
    db: Session = Depends(get_db)
):
    version_svc = VersionService(db)
    try:
        commit = version_svc.create_commit(repository_id, commit_in)
        items = version_svc.get_commit_items(commit.id)
        return CommitResponse(
            id=commit.id,
            repository_id=commit.repository_id,
            branch_id=commit.branch_id,
            parent_commit_ids=commit.parent_commit_ids,
            message=commit.message,
            snapshot_hash=commit.snapshot_hash,
            created_at=commit.created_at,
            author=commit.author,
            items=[SnapshotItemResponse.model_validate(i) for i in items]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "COMMIT_FAILED", "message": str(e)}
        )


@router.get("/repositories/{repository_id}/commits/{commit_id}", response_model=CommitResponse)
def get_repository_commit(repository_id: str, commit_id: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    commit = version_svc.get_commit(commit_id)
    if not commit or commit.repository_id != repository_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMIT_NOT_FOUND", "message": f"Commit '{commit_id}' not found."}
        )
    items = version_svc.get_commit_items(commit.id)
    return CommitResponse(
        id=commit.id,
        repository_id=commit.repository_id,
        branch_id=commit.branch_id,
        parent_commit_ids=commit.parent_commit_ids,
        message=commit.message,
        snapshot_hash=commit.snapshot_hash,
        created_at=commit.created_at,
        author=commit.author,
        items=[SnapshotItemResponse.model_validate(i) for i in items]
    )


@router.get("/commits/{commit_id}", response_model=CommitResponse)
def get_commit_by_id(commit_id: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    commit = version_svc.get_commit(commit_id)
    if not commit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMIT_NOT_FOUND", "message": f"Commit '{commit_id}' not found."}
        )
    items = version_svc.get_commit_items(commit.id)
    return CommitResponse(
        id=commit.id,
        repository_id=commit.repository_id,
        branch_id=commit.branch_id,
        parent_commit_ids=commit.parent_commit_ids,
        message=commit.message,
        snapshot_hash=commit.snapshot_hash,
        created_at=commit.created_at,
        author=commit.author,
        items=[SnapshotItemResponse.model_validate(i) for i in items]
    )


@router.get("/commits/{commit_id}/diff/{other_commit_id}", response_model=CommitDiffResponse)
def diff_commits(commit_id: str, other_commit_id: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    c1 = version_svc.get_commit(commit_id)
    c2 = version_svc.get_commit(other_commit_id)
    if not c1 or not c2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMMIT_NOT_FOUND", "message": "One or both commits not found for diff."}
        )
    diff = version_svc.diff_commits(commit_id, other_commit_id)
    return diff

