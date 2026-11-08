from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.codebase import CodebaseFileSummary, CodebaseSymbolSummary, CodebaseDependencySummary


class TaskContextRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the task to perform")
    repository_id: str = Field(default="default", description="Repository ID or name")
    branch: Optional[str] = Field(default="main", description="Target branch")
    current_file: Optional[str] = Field(default=None, description="Current file active in editor")
    max_tokens: Optional[int] = Field(default=3500, ge=1, le=32000, description="Max token budget")
    include: Optional[List[str]] = Field(
        default=[
            "decisions",
            "constraints",
            "files",
            "symbols",
            "dependencies",
            "unfinished_tasks",
            "conversation_memories"
        ],
        description="Categories to include"
    )
    changed_files: Optional[List[str]] = Field(default=None, description="Hints of files changed")


class TaskOutcomeRequest(BaseModel):
    repository_id: str = Field(default="default")
    branch: Optional[str] = Field(default="main")
    task: str = Field(..., min_length=1)
    outcome_summary: str = Field(..., min_length=1)
    decisions: Optional[List[str]] = Field(default=list)
    changed_files: Optional[List[str]] = Field(default=list)
    symbols_changed: Optional[List[str]] = Field(default=list)
    tests_run: Optional[List[str]] = Field(default=list)
    test_results: Optional[str] = Field(default="passed")
    unresolved_issues: Optional[List[str]] = Field(default=list)
    commit_hash: Optional[str] = Field(default=None)


class TaskContextResponse(BaseModel):
    repository_id: str
    branch: str
    task: str
    context_sections: Dict[str, List[str]]
    relevant_files: List[CodebaseFileSummary]
    symbols: List[CodebaseSymbolSummary]
    dependencies: List[CodebaseDependencySummary]
    memory_items: List[Dict[str, Any]]
    estimated_tokens: int
    token_estimation_method: str = "approximate (1.33 words/token)"
    coverage: str  # high | partial | low
    needs_more_context: bool
    omitted_items: List[str]
    sources: List[str]
