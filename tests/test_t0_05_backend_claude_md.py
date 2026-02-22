import os
import subprocess
import pytest

BACKEND_CLAUDE = os.path.join(os.path.dirname(__file__), '../backend/CLAUDE.md')

def test_no_taskmaster_reference():
    """Test that 'taskmaster' does not appear in backend/CLAUDE.md (case-insensitive)."""
    with open(BACKEND_CLAUDE, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    assert 'taskmaster' not in content, "Found dead TaskMaster reference in backend/CLAUDE.md"

def test_fastapi_mentioned():
    """Test that 'FastAPI' is mentioned in backend/CLAUDE.md."""
    with open(BACKEND_CLAUDE, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'FastAPI' in content, "Missing FastAPI convention in backend/CLAUDE.md"

def test_ruff_mentioned():
    """Test that 'ruff' is mentioned in backend/CLAUDE.md."""
    with open(BACKEND_CLAUDE, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'ruff' in content, "Missing ruff linting convention in backend/CLAUDE.md"
