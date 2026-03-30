from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-document-extractor",
    version="0.1.0",
    author="IPAC",
    description="End-to-end robust agentic document extractor using DPT architecture for Indian government documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["agentic_document_extractor"] + [
        f"agentic_document_extractor.{p}" for p in find_packages(where="src")
    ],
    package_dir={"agentic_document_extractor": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docextract=agentic_document_extractor.cli.main:cli",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
)
