import sys
import unittest
from pathlib import Path


class WorkspaceTestCase(unittest.TestCase):
    """Unit test for Python version and monorepo workspace structure (DB agnostic)."""

    def test_python_version_is_3_13_or_higher(self) -> None:
        """Verify Python 3.13+ runtime version requirement."""
        self.assertGreaterEqual(
            sys.version_info[:2],
            (3, 13),
            f"Python 3.13+ required, but currently running on {sys.version}",
        )

    def test_monorepo_root_files_exist(self) -> None:
        """Verify pyproject.toml and .env.example exist at project root."""
        root_dir = Path(__file__).resolve().parent.parent.parent
        pyproject_file = root_dir / "pyproject.toml"
        env_example_file = root_dir / ".env.example"

        self.assertTrue(pyproject_file.exists(), "pyproject.toml must exist at root")
        self.assertTrue(env_example_file.exists(), ".env.example must exist at root")
