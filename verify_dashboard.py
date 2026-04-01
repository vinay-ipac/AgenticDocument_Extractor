#!/usr/bin/env python3
"""Verify dashboard installation and dependencies."""

import sys
from pathlib import Path


def check_backend():
    """Check backend dependencies and imports."""
    print("Checking backend dependencies...")

    missing = []

    try:
        import fastapi
        print(f"  ✓ FastAPI {fastapi.__version__}")
    except ImportError:
        missing.append("fastapi")
        print("  ✗ FastAPI not found")

    try:
        import uvicorn
        print(f"  ✓ Uvicorn {uvicorn.__version__}")
    except ImportError:
        missing.append("uvicorn")
        print("  ✗ Uvicorn not found")

    try:
        from src.api import main
        print("  ✓ API module imports successfully")
    except Exception as e:
        print(f"  ✗ API module import failed: {e}")
        missing.append("api-module")

    try:
        from src import DocumentProcessor
        print("  ✓ DocumentProcessor imports successfully")
    except Exception as e:
        print(f"  ✗ DocumentProcessor import failed: {e}")

    return missing


def check_frontend():
    """Check frontend setup."""
    print("\nChecking frontend setup...")

    frontend_dir = Path(__file__).parent / "frontend"

    if not frontend_dir.exists():
        print("  ✗ frontend/ directory not found")
        return False

    if not (frontend_dir / "package.json").exists():
        print("  ✗ package.json not found")
        return False

    print("  ✓ Frontend directory exists")

    if (frontend_dir / "node_modules").exists():
        print("  ✓ node_modules exists (dependencies installed)")
    else:
        print("  ⚠ node_modules not found - run: cd frontend && npm install")
        return False

    return True


def check_env():
    """Check environment variables."""
    print("\nChecking environment...")

    import os
    if os.getenv("OPENAI_API_KEY"):
        print("  ✓ OPENAI_API_KEY is set")
    else:
        print("  ⚠ OPENAI_API_KEY not set - VLM extraction will fail")
        print("    Set it with: export OPENAI_API_KEY=sk-...")


def main():
    print("="*60)
    print("Document Extraction Dashboard - Installation Verification")
    print("="*60 + "\n")

    missing_backend = check_backend()
    frontend_ok = check_frontend()
    check_env()

    print("\n" + "="*60)
    if missing_backend:
        print("BACKEND: Missing dependencies")
        print(f"  Install with: pip install {' '.join(missing_backend)}")
    else:
        print("BACKEND: ✓ All dependencies installed")

    if frontend_ok:
        print("FRONTEND: ✓ Setup complete")
    else:
        print("FRONTEND: ⚠ Setup incomplete")
        print("  Run: cd frontend && npm install")

    print("="*60)

    if not missing_backend and frontend_ok:
        print("\n✓ Dashboard is ready to run!")
        print("\nTo start:")
        print("  Development: python run_dashboard.py --mode dev")
        print("  Production:  python run_dashboard.py --mode prod")
        print("\nOr manually:")
        print("  Terminal 1: python -m src.api.main")
        print("  Terminal 2: cd frontend && npm run dev")
        return 0
    else:
        print("\n⚠ Some dependencies missing - see above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
