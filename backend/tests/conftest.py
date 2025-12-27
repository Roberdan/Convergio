"""
Backend Tests Configuration
Sets up Python path for backend test imports.
"""

import sys
from pathlib import Path

# Setup Python paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_SRC_DIR = BACKEND_DIR / "src"

# Add backend and backend/src to Python path
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_SRC_DIR))
