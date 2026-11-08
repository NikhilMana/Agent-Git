import os
import tempfile
from sqlalchemy.orm import Session
from backend.app.services.codebase_indexer import CodebaseIndexer
from backend.app.services.freshness_manager import FreshnessManager
from backend.app.services.version_service import VersionService


def test_file_freshness_detection(db_session: Session):
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = os.path.join(tmp_dir, "app.py")
        with open(test_file, "w") as f:
            f.write("def start(): print('v1')")

        indexer = CodebaseIndexer(db_session, repository_root=tmp_dir)
        freshness = FreshnessManager(db_session, repository_root=tmp_dir)
        version_svc = VersionService(db_session)
        repo = version_svc.get_or_create_repository("freshness-repo")

        # Initial index
        indexer.index_repository(repo.id)

        # 1. Fresh check
        is_fresh, reason = freshness.check_file_freshness(repo.id, "app.py")
        assert is_fresh is True
        assert "Fresh" in reason

        # 2. Modify file content on disk -> should detect stale
        with open(test_file, "w") as f:
            f.write("def start(): print('v2 modified')")

        is_fresh, reason = freshness.check_file_freshness(repo.id, "app.py")
        assert is_fresh is False
        assert "differs" in reason.lower()

        # 3. Delete file from disk -> should report deleted
        os.remove(test_file)
        is_fresh, reason = freshness.check_file_freshness(repo.id, "app.py")
        assert is_fresh is False
        assert "deleted" in reason.lower()

