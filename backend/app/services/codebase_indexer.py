import ast
import hashlib
import os
import re
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.models.codebase_index import (
    RepositoryIndexMeta,
    CodebaseFileRecord,
    CodebaseSymbolRecord,
    CodebaseDependencyRecord,
)
from backend.app.models.repository import Repository
from backend.app.schemas.codebase import IndexRefreshReport, CodebaseIndexStatus
from backend.app.core.logging import logger

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "htmlcov",
    "eggs",
    ".eggs",
}

DEFAULT_EXCLUDED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe",
    ".db", ".sqlite", ".sqlite3",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".rar",
    ".bin", ".parquet", ".pkl"
}

SENSITIVE_FILENAME_PATTERNS = [
    r"^\.env(\.|$)",
    r"id_rsa",
    r"id_ed25519",
    r".*\.pem$",
    r".*\.key$",
    r".*\.pfx$",
    r"secrets?\.(json|yaml|yml|toml)",
    r"credentials?\.(json|yaml|yml|toml)"
]

LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript-react",
    ".js": "javascript",
    ".jsx": "javascript-react",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
}


def compute_file_hash(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class CodebaseIndexer:
    def __init__(self, db: Session, repository_root: Optional[str] = None):
        self.db = db
        self.repository_root = os.path.realpath(repository_root or os.getcwd())

    def _validate_path(self, path: str) -> str:
        """Resolve path and verify it is strictly within canonical root."""
        abs_path = os.path.realpath(path)
        try:
            common = os.path.commonpath([self.repository_root, abs_path])
            if common != self.repository_root:
                raise PermissionError(f"Access denied: path '{path}' traverses outside repository root '{self.repository_root}'")
        except ValueError:
            raise PermissionError(f"Access denied: path '{path}' is on a different drive or outside root")
        return abs_path

    def _is_excluded(self, rel_path: str, filename: str) -> bool:
        # Check directory parts
        parts = os.path.normpath(rel_path).split(os.sep)
        for part in parts[:-1]:
            if part in DEFAULT_EXCLUDED_DIRS or part.startswith("."):
                return True

        # Check sensitive patterns
        for pat in SENSITIVE_FILENAME_PATTERNS:
            if re.match(pat, filename, re.IGNORECASE):
                return True

        # Check extension
        _, ext = os.path.splitext(filename)
        if ext.lower() in DEFAULT_EXCLUDED_EXTENSIONS:
            return True

        return False

    def index_repository(self, repository_id: str, git_commit: Optional[str] = None) -> IndexRefreshReport:
        t0 = time.perf_counter()
        canon_root = self.repository_root

        # Get or create index metadata
        stmt = select(RepositoryIndexMeta).where(RepositoryIndexMeta.repository_id == repository_id)
        meta = self.db.scalars(stmt).first()
        if not meta:
            meta = RepositoryIndexMeta(
                id=str(uuid.uuid4()),
                repository_id=repository_id,
                canonical_root=canon_root,
                last_indexed_commit=git_commit,
                index_version="2.0.0"
            )
            self.db.add(meta)
            self.db.flush()
        else:
            meta.canonical_root = canon_root
            meta.last_indexed_commit = git_commit

        # Existing files in DB
        existing_files_stmt = select(CodebaseFileRecord).where(CodebaseFileRecord.index_meta_id == meta.id)
        existing_files_map = {f.relative_path: f for f in self.db.scalars(existing_files_stmt).all()}

        indexed_count = 0
        skipped_count = 0
        deleted_count = 0
        stale_count = 0

        found_rel_paths: Set[str] = set()

        for root, dirs, files in os.walk(canon_root):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDED_DIRS and not d.startswith(".")]

            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, canon_root).replace("\\", "/")

                if self._is_excluded(rel_path, file):
                    skipped_count += 1
                    continue

                found_rel_paths.add(rel_path)
                try:
                    curr_hash = compute_file_hash(abs_file)
                    size = os.path.getsize(abs_file)
                    _, ext = os.path.splitext(file)
                    lang = LANGUAGE_MAP.get(ext.lower(), "text")

                    existing = existing_files_map.get(rel_path)
                    if existing and existing.content_hash == curr_hash:
                        # File unchanged
                        existing.is_stale = False
                        continue

                    # File is new or changed
                    if existing:
                        # Delete existing symbols before re-indexing
                        del_stmt = delete(CodebaseSymbolRecord).where(CodebaseSymbolRecord.file_record_id == existing.id)
                        self.db.execute(del_stmt)
                        existing.content_hash = curr_hash
                        existing.size_bytes = size
                        existing.is_stale = False
                        existing.indexed_commit = git_commit
                        file_record = existing
                    else:
                        file_record = CodebaseFileRecord(
                            id=str(uuid.uuid4()),
                            index_meta_id=meta.id,
                            relative_path=rel_path,
                            language=lang,
                            size_bytes=size,
                            content_hash=curr_hash,
                            indexed_commit=git_commit,
                            is_stale=False
                        )
                        self.db.add(file_record)
                        self.db.flush()

                    # Parse symbols and dependencies
                    symbols, dependencies = self._parse_file(abs_file, rel_path, lang, repository_id, file_record.id)
                    for s in symbols:
                        self.db.add(s)
                    for d in dependencies:
                        self.db.add(d)

                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index file {rel_path}: {e}")
                    skipped_count += 1

        # Check for deleted files
        for rel_path, existing_rec in existing_files_map.items():
            if rel_path not in found_rel_paths:
                self.db.delete(existing_rec)
                deleted_count += 1

        self.db.commit()
        duration_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            f"Codebase indexing complete for {repository_id}: "
            f"{indexed_count} indexed, {skipped_count} skipped, {deleted_count} deleted in {duration_ms:.1f}ms"
        )
        return IndexRefreshReport(
            repository_id=repository_id,
            indexed_count=indexed_count,
            skipped_count=skipped_count,
            deleted_count=deleted_count,
            stale_count=stale_count,
            duration_ms=round(duration_ms, 2)
        )

    def _parse_file(
        self,
        abs_path: str,
        rel_path: str,
        lang: str,
        repository_id: str,
        file_record_id: str
    ) -> Tuple[List[CodebaseSymbolRecord], List[CodebaseDependencyRecord]]:
        symbols: List[CodebaseSymbolRecord] = []
        dependencies: List[CodebaseDependencyRecord] = []

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if lang == "python":
                symbols, dependencies = self._parse_python(content, rel_path, repository_id, file_record_id)
            elif lang.startswith("typescript") or lang.startswith("javascript"):
                symbols, dependencies = self._parse_js_ts(content, rel_path, repository_id, file_record_id)
        except Exception as e:
            logger.debug(f"Parser error on {rel_path}: {e}")

        return symbols, dependencies

    def _parse_python(
        self,
        content: str,
        rel_path: str,
        repository_id: str,
        file_record_id: str
    ) -> Tuple[List[CodebaseSymbolRecord], List[CodebaseDependencyRecord]]:
        symbols = []
        dependencies = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return symbols, dependencies

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(
                    CodebaseSymbolRecord(
                        id=str(uuid.uuid4()),
                        file_record_id=file_record_id,
                        name=node.name,
                        kind="class",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        docstring=doc[:300] if doc else None,
                        signature=f"class {node.name}"
                    )
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                args_str = ", ".join([a.arg for a in node.args.args])
                prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                symbols.append(
                    CodebaseSymbolRecord(
                        id=str(uuid.uuid4()),
                        file_record_id=file_record_id,
                        name=node.name,
                        kind="function",
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", node.lineno),
                        docstring=doc[:300] if doc else None,
                        signature=f"{prefix}{node.name}({args_str})"
                    )
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(
                        CodebaseDependencyRecord(
                            id=str(uuid.uuid4()),
                            repository_id=repository_id,
                            source_path=rel_path,
                            target_path=alias.name,
                            relation="imports",
                            confidence=1.0
                        )
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependencies.append(
                    CodebaseDependencyRecord(
                        id=str(uuid.uuid4()),
                        repository_id=repository_id,
                        source_path=rel_path,
                        target_path=node.module,
                        relation="imports",
                        confidence=1.0
                    )
                )

        return symbols, dependencies

    def _parse_js_ts(
        self,
        content: str,
        rel_path: str,
        repository_id: str,
        file_record_id: str
    ) -> Tuple[List[CodebaseSymbolRecord], List[CodebaseDependencyRecord]]:
        symbols = []
        dependencies = []

        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            line_str = line.strip()

            # Class match
            m_class = re.search(r"\bclass\s+([A-Za-z0-9_]+)", line_str)
            if m_class:
                symbols.append(
                    CodebaseSymbolRecord(
                        id=str(uuid.uuid4()),
                        file_record_id=file_record_id,
                        name=m_class.group(1),
                        kind="class",
                        line_start=idx,
                        line_end=idx,
                        signature=line_str[:120]
                    )
                )

            # Interface / Type match
            m_interface = re.search(r"\b(interface|type)\s+([A-Za-z0-9_]+)", line_str)
            if m_interface:
                symbols.append(
                    CodebaseSymbolRecord(
                        id=str(uuid.uuid4()),
                        file_record_id=file_record_id,
                        name=m_interface.group(2),
                        kind=m_interface.group(1),
                        line_start=idx,
                        line_end=idx,
                        signature=line_str[:120]
                    )
                )

            # Function / Const match
            m_fn = re.search(r"(?:function\s+([A-Za-z0-9_]+)|(?:const|let)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\()", line_str)
            if m_fn:
                name = m_fn.group(1) or m_fn.group(2)
                symbols.append(
                    CodebaseSymbolRecord(
                        id=str(uuid.uuid4()),
                        file_record_id=file_record_id,
                        name=name,
                        kind="function",
                        line_start=idx,
                        line_end=idx,
                        signature=line_str[:120]
                    )
                )

            # Import statements
            m_imp = re.search(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", line_str)
            if m_imp:
                dependencies.append(
                    CodebaseDependencyRecord(
                        id=str(uuid.uuid4()),
                        repository_id=repository_id,
                        source_path=rel_path,
                        target_path=m_imp.group(1),
                        relation="imports",
                        confidence=0.9
                    )
                )

        return symbols, dependencies

    def get_index_status(self, repository_id: str) -> CodebaseIndexStatus:
        stmt = select(RepositoryIndexMeta).where(RepositoryIndexMeta.repository_id == repository_id)
        meta = self.db.scalars(stmt).first()
        if not meta:
            return CodebaseIndexStatus(
                repository_id=repository_id,
                canonical_root=self.repository_root,
                total_files=0,
                total_symbols=0,
                total_dependencies=0,
                last_indexed_at=None,
                last_indexed_commit=None
            )

        files_count_stmt = select(CodebaseFileRecord).where(CodebaseFileRecord.index_meta_id == meta.id)
        files = list(self.db.scalars(files_count_stmt).all())
        file_ids = [f.id for f in files]

        symbols_count = 0
        if file_ids:
            symbols_stmt = select(CodebaseSymbolRecord).where(CodebaseSymbolRecord.file_record_id.in_(file_ids))
            symbols_count = len(list(self.db.scalars(symbols_stmt).all()))

        dep_stmt = select(CodebaseDependencyRecord).where(CodebaseDependencyRecord.repository_id == repository_id)
        dep_count = len(list(self.db.scalars(dep_stmt).all()))

        return CodebaseIndexStatus(
            repository_id=repository_id,
            canonical_root=meta.canonical_root,
            total_files=len(files),
            total_symbols=symbols_count,
            total_dependencies=dep_count,
            last_indexed_at=meta.last_indexed_at,
            last_indexed_commit=meta.last_indexed_commit
        )

