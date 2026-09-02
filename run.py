"""Streamlit entry point - loads .env and runs the app."""

import os
import sys
from pathlib import Path

# Try to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import main

if __name__ == "__main__":
    main()
