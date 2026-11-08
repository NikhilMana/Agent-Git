import re
import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.schemas.retrieval import RetrievedMemoryItem, RetrievalResponse
from backend.app.services.version_service import VersionService
from backend.app.models.snapshot import SnapshotItem
from backend.app.core.logging import logger


def tokenize(text: str) -> List[str]:
    raw_tokens = [w for w in re.findall(r"[A-Za-z0-9]+", text.lower()) if len(w) > 1]
    expanded = list(raw_tokens)
    for w in raw_tokens:
        if w.endswith("s") and len(w) > 3:
            expanded.append(w[:-1])
    return expanded


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.version_service = VersionService(db)

    def retrieve(
        self,
        repository_id: str,
        query: str,
        branch_name: str = "main",
        top_k: int = 5
    ) -> RetrievalResponse:
        branch = self.version_service.get_branch(repository_id, branch_name)
        if not branch or not branch.head_commit_id:
            return RetrievalResponse(
                query=query,
                branch=branch_name,
                commit_id=None,
                results=[],
                context_text=""
            )

        commit_id = branch.head_commit_id
        items: List[SnapshotItem] = self.version_service.get_commit_items(commit_id)
        if not items:
            return RetrievalResponse(
                query=query,
                branch=branch_name,
                commit_id=commit_id,
                results=[],
                context_text=""
            )

        scored_items: List[Tuple[float, SnapshotItem]] = []
        q_tokens = set(tokenize(query))
        q_lower = query.lower()

        # Compute scores for each active memory item at current commit
        for item in items:
            content_lower = item.content_at_commit.lower()
            item_tokens = tokenize(item.content_at_commit)
            if not item_tokens:
                continue

            # Exact substring match bonus
            exact_bonus = 2.0 if q_lower in content_lower else 0.0

            # Token overlap (Jaccard-like + term match)
            matching_tokens = q_tokens.intersection(set(item_tokens))
            overlap_score = len(matching_tokens) / (len(q_tokens) + 1e-6)

            # Topic / key bonus
            topic_bonus = 0.5 if item.topic_at_commit.lower() in q_lower else 0.0
            if item.logical_key and any(t in item.logical_key.lower() for t in q_tokens):
                topic_bonus += 0.5

            total_score = exact_bonus + overlap_score + topic_bonus

            # Only include if there is some relevance
            if total_score > 0.05 or len(matching_tokens) > 0:
                scored_items.append((total_score, item))

        # Sort descending by score
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_items[:top_k]

        results = [
            RetrievedMemoryItem(
                memory_item_id=item.memory_item_id,
                content=item.content_at_commit,
                score=round(score, 4),
                source_message_ids=item.source_message_ids,
                topic=item.topic_at_commit,
                commit_id=commit_id,
                logical_key=item.logical_key,
                category=item.category_at_commit
            )
            for score, item in top_results
        ]

        # Context builder for downstream agent consumption
        context_blocks = []
        for r in results:
            src_refs = ", ".join(r.source_message_ids)
            key_str = f" [{r.logical_key}]" if r.logical_key else ""
            context_blocks.append(f"- ({r.topic}){key_str} {r.content} (source: {src_refs})")

        context_text = "\n".join(context_blocks)
        logger.info(f"Retrieved {len(results)} items for query '{query}' on branch '{branch_name}' (commit {commit_id[:8]})")

        return RetrievalResponse(
            query=query,
            branch=branch_name,
            commit_id=commit_id,
            results=results,
            context_text=context_text
        )

