#!/usr/bin/env python3
"""
Simple script to run the Document Extraction Dashboard.

Development mode: Starts backend only (frontend should run separately with npm run dev)
Production mode: Builds frontend and serves via backend
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_backend():
    """Run the FastAPI backend."""
    print("Starting FastAPI backend...")
    os.chdir(Path(__file__).parent)
    subprocess.run([sys.executable, "-m", "src.api.main"])


def build_frontend():
    """Build the frontend for production."""
    frontend_dir = Path(__file__).parent / "frontend"
    print(f"Building frontend in {frontend_dir}...")

    if not frontend_dir.exists():
        print("ERROR: frontend/ directory not found")
        sys.exit(1)

    os.chdir(frontend_dir)
    subprocess.run(["npm", "run", "build"], check=True)
    print("Frontend build complete!")


def main():
    parser = argparse.ArgumentParser(description="Run Document Extraction Dashboard")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Development mode (backend only) or production mode (build + serve)",
    )
    args = parser.parse_args()

    if args.mode == "prod":
        build_frontend()
        print("\n" + "="*60)
        print("Production build complete!")
        print("Starting backend (will serve frontend at http://localhost:8000)")
        print("="*60 + "\n")
        run_backend()
    else:
        print("\n" + "="*60)
        print("DEVELOPMENT MODE")
        print("Backend will start on http://localhost:8000")
        print("Start frontend separately with: cd frontend && npm run dev")
        print("="*60 + "\n")
        run_backend()


if __name__ == "__main__":
    main()
