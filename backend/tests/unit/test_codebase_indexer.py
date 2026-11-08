import os
import tempfile
import pytest
from sqlalchemy.orm import Session
from backend.app.services.codebase_indexer import CodebaseIndexer
from backend.app.services.version_service import VersionService


def test_path_traversal_rejection(db_session: Session):
    with tempfile.TemporaryDirectory() as tmp_dir:
        indexer = CodebaseIndexer(db_session, repository_root=tmp_dir)
        
        # Valid path within root
        valid_path = os.path.join(tmp_dir, "test.py")
        with open(valid_path, "w") as f:
            f.write("print('hello')")
        assert indexer._validate_path(valid_path) == os.path.realpath(valid_path)

        # Path traversal outside root
        outside_path = os.path.abspath(os.path.join(tmp_dir, "..", "forbidden.txt"))
        with pytest.raises(PermissionError):
            indexer._validate_path(outside_path)


def test_exclusion_rules(db_session: Session):
    indexer = CodebaseIndexer(db_session)
    assert indexer._is_excluded(".git/config", "config") is True
    assert indexer._is_excluded("node_modules/pkg/index.js", "index.js") is True
    assert indexer._is_excluded(".venv/lib/site.py", "site.py") is True
    assert indexer._is_excluded(".env", ".env") is True
    assert indexer._is_excluded(".env.production", ".env.production") is True
    assert indexer._is_excluded("certs/server.key", "server.key") is True
    assert indexer._is_excluded("compiled.pyc", "compiled.pyc") is True
    assert indexer._is_excluded("app/main.py", "main.py") is False


def test_python_ast_parsing(db_session: Session):
    with tempfile.TemporaryDirectory() as tmp_dir:
        py_file = os.path.join(tmp_dir, "service.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(
                '"""Module docstring."""\n'
                'import os\n'
                'from typing import List\n\n'
                'class UserService:\n'
                '    """Manages users."""\n'
                '    def __init__(self, db: str):\n'
                '        self.db = db\n\n'
                '    async def get_user(self, user_id: str) -> dict:\n'
                '        """Fetch user by ID."""\n'
                '        return {"id": user_id}\n'
            )

        indexer = CodebaseIndexer(db_session, repository_root=tmp_dir)
        version_svc = VersionService(db_session)
        repo = version_svc.get_or_create_repository("test-codebase-repo")

        report = indexer.index_repository(repo.id)
        assert report.indexed_count == 1
        assert report.deleted_count == 0

        status = indexer.get_index_status(repo.id)
        assert status.total_files == 1
        # Should have UserService, __init__, get_user
        assert status.total_symbols >= 2
        # Should have imports os, typing
        assert status.total_dependencies >= 1


def test_incremental_deletion_and_update(db_session: Session):
    with tempfile.TemporaryDirectory() as tmp_dir:
        indexer = CodebaseIndexer(db_session, repository_root=tmp_dir)
        version_svc = VersionService(db_session)
        repo = version_svc.get_or_create_repository("test-inc-repo")

        file1 = os.path.join(tmp_dir, "file1.py")
        file2 = os.path.join(tmp_dir, "file2.py")
        with open(file1, "w") as f:
            f.write("def func_a(): pass")
        with open(file2, "w") as f:
            f.write("def func_b(): pass")

        report1 = indexer.index_repository(repo.id)
        assert report1.indexed_count == 2

        # Delete file2
        os.remove(file2)
        report2 = indexer.index_repository(repo.id)
        assert report2.deleted_count == 1

        status = indexer.get_index_status(repo.id)
        assert status.total_files == 1

