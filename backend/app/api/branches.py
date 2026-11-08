from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.version_service import VersionService
from backend.app.schemas.branch import BranchCreate, BranchResponse, BranchHistoryResponse, RestoreRequest
from backend.app.schemas.commit import CommitResponse, SnapshotItemResponse

router = APIRouter(tags=["Branches & History"])


@router.get("/repositories/{repository_id}/branches", response_model=List[BranchResponse])
def list_branches(repository_id: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    return version_svc.list_branches(repository_id)


@router.post("/repositories/{repository_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(repository_id: str, branch_in: BranchCreate, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    try:
        branch = version_svc.create_branch(
            repository_id=repository_id,
            name=branch_in.name,
            from_commit_id=branch_in.from_commit_id
        )
        return branch
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BRANCH_CREATION_FAILED", "message": str(e)}
        )


@router.get("/repositories/{repository_id}/branches/{branch_name}/history", response_model=BranchHistoryResponse)
def get_branch_history(repository_id: str, branch_name: str, db: Session = Depends(get_db)):
    version_svc = VersionService(db)
    try:
        commits = version_svc.list_branch_history(repository_id, branch_name)
        commit_responses = []
        for c in commits:
            items = version_svc.get_commit_items(c.id)
            commit_responses.append(
                CommitResponse(
                    id=c.id,
                    repository_id=c.repository_id,
                    branch_id=c.branch_id,
                    parent_commit_ids=c.parent_commit_ids,
                    message=c.message,
                    snapshot_hash=c.snapshot_hash,
                    created_at=c.created_at,
                    author=c.author,
                    items=[SnapshotItemResponse.model_validate(i) for i in items]
                )
            )
        return BranchHistoryResponse(branch=branch_name, commits=commit_responses)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BRANCH_NOT_FOUND", "message": str(e)}
        )


@router.post("/repositories/{repository_id}/branches/{branch_name}/restore", response_model=CommitResponse)
def restore_snapshot_on_repo(
    repository_id: str,
    branch_name: str,
    restore_req: RestoreRequest,
    db: Session = Depends(get_db)
):
    version_svc = VersionService(db)
    try:
        new_commit = version_svc.restore_snapshot(
            repository_id=repository_id,
            branch_name=branch_name,
            target_commit_id=restore_req.commit_id,
            message=restore_req.message
        )
        items = version_svc.get_commit_items(new_commit.id)
        return CommitResponse(
            id=new_commit.id,
            repository_id=new_commit.repository_id,
            branch_id=new_commit.branch_id,
            parent_commit_ids=new_commit.parent_commit_ids,
            message=new_commit.message,
            snapshot_hash=new_commit.snapshot_hash,
            created_at=new_commit.created_at,
            author=new_commit.author,
            items=[SnapshotItemResponse.model_validate(i) for i in items]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "RESTORE_FAILED", "message": str(e)}
        )


@router.post("/branches/{branch_name}/restore", response_model=CommitResponse)
def restore_snapshot_default_repo(
    branch_name: str,
    restore_req: RestoreRequest,
    db: Session = Depends(get_db)
):
    version_svc = VersionService(db)
    default_repo = version_svc.get_or_create_repository()
    return restore_snapshot_on_repo(
        repository_id=default_repo.id,
        branch_name=branch_name,
        restore_req=restore_req,
        db=db
    )

