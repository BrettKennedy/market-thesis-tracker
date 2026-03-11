from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def temp_repo(tmp_path: Path, repo_root: Path) -> Path:
    for directory in ["config", "themes", "templates", "reviews", "docs", "prompts"]:
        shutil.copytree(repo_root / directory, tmp_path / directory, dirs_exist_ok=True)

    shutil.copy2(repo_root / "tests" / "fixtures" / "themes.md", tmp_path / "themes" / "themes.md")
    shutil.copy2(
        repo_root / "tests" / "fixtures" / "ticker_baskets.yaml",
        tmp_path / "config" / "ticker_baskets.yaml",
    )

    for directory in [
        "data/raw/news",
        "data/raw/sec",
        "data/processed",
        "outputs",
        "outputs/weekly",
        "outputs/post_earnings",
    ]:
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)

    return tmp_path
