from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.version_service import VersionService
from backend.app.schemas.merge import MergeRequest
from backend.app.schemas.commit import CommitResponse, SnapshotItemResponse

router = APIRouter(tags=["Merge"])


@router.post("/repositories/{repository_id}/merge", response_model=CommitResponse)
def merge_branches(
    repository_id: str,
    merge_in: MergeRequest,
    db: Session = Depends(get_db)
):
    version_svc = VersionService(db)

    # First check for conflicts
    try:
        conflicts, _, _ = version_svc.check_merge_conflicts(
            repository_id=repository_id,
            source_branch_name=merge_in.source_branch,
            target_branch_name=merge_in.target_branch,
            selected_memory_item_ids=merge_in.selected_memory_item_ids
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MERGE_VALIDATION_ERROR", "message": str(e)}
        )

    if conflicts:
        conflict_payload = {
            "error": {
                "code": "MERGE_CONFLICT",
                "message": f"Merge conflict detected for {len(conflicts)} items. Explicit resolution required."
            },
            "conflicts": [c.model_dump() for c in conflicts]
        }
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=conflict_payload)

    try:
        merge_commit = version_svc.merge_branches(
            repository_id=repository_id,
            source_branch_name=merge_in.source_branch,
            target_branch_name=merge_in.target_branch,
            selected_memory_item_ids=merge_in.selected_memory_item_ids,
            message=merge_in.message
        )
        items = version_svc.get_commit_items(merge_commit.id)
        return CommitResponse(
            id=merge_commit.id,
            repository_id=merge_commit.repository_id,
            branch_id=merge_commit.branch_id,
            parent_commit_ids=merge_commit.parent_commit_ids,
            message=merge_commit.message,
            snapshot_hash=merge_commit.snapshot_hash,
            created_at=merge_commit.created_at,
            author=merge_commit.author,
            items=[SnapshotItemResponse.model_validate(i) for i in items]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MERGE_FAILED", "message": str(e)}
        )

