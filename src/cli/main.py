"""CLI entry point for Agentic Document Extractor."""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

# Load .env before any OpenAI/API clients are created
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="docextract")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose: bool):
    """
    Agentic Document Extractor - Extract structured data from any document type.

    Schema-driven system supporting custom JSON schemas for extracting data from
    invoices, forms, tables, receipts, and any other document type.

    Examples:

        docextract process document.pdf --output results/

        docextract extract document.pdf --schema generic_form --output data.json

        docextract extract invoice.pdf --schema examples/schemas/invoice_schema.json --output invoice.json

        docextract visualize document.pdf --output layout.png
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.argument("document", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Output directory for results",
)
@click.option(
    "--schema", "-s",
    type=str,
    help="Schema name (generic_form, table) or path to JSON schema file",
)
@click.option(
    "--no-analyze",
    is_flag=True,
    help="Skip VLM-based region analysis",
)
@click.option(
    "--dpi",
    type=int,
    default=150,
    help="DPI for document conversion",
)
@click.option(
    "--max-pages",
    type=int,
    default=100,
    help="Maximum pages to process",
)
@click.option(
    "--language", "-l",
    type=click.Choice(["hi", "en", "mixed"]),
    default="mixed",
    help="Document language",
)
@click.pass_context
def process(
    ctx,
    document: str,
    output: str,
    schema: Optional[str],
    no_analyze: bool,
    dpi: int,
    max_pages: int,
    language: str,
):
    """
    Process a document through the full pipeline.

    DOCUMENT: Path to the document (PDF, image, or DOCX)

    This command runs OCR, layout detection, and optional analysis/extraction.
    """
    from ..pipelines.document_processor import DocumentProcessor

    # Set up languages
    if language == "mixed":
        ocr_languages = ("hi", "en")
    else:
        ocr_languages = (language,)

    # Create processor
    processor = DocumentProcessor(
        ocr_languages=ocr_languages,
        verbose=ctx.obj.get("verbose", False),
        dpi=dpi,
        max_pages=max_pages,
    )

    click.echo(f"Processing: {document}")
    click.echo(f"Output directory: {output}")

    try:
        # Process document with layout images saved to output dir
        layout_dir = Path(output) / "layout_images"
        result = processor.process(
            document,
            analyze_regions=not no_analyze,
            layout_output_dir=layout_dir,
        )

        # Extract with schema if specified
        if schema:
            click.echo(f"Extracting with schema: {schema}")
            extraction = processor.extract_schema(result, schema)
            click.echo(f"Extraction complete: {json.dumps(extraction, indent=2)[:500]}...")

        # Generate outputs
        output_path = Path(output)
        generated = processor.generate_report(result, output_path)

        click.echo("\n[OK] Processing complete!")
        click.echo(f"  Pages processed: {result.page_count}")
        click.echo(f"  Processing time: {result.processing_time:.2f}s")

        if generated:
            click.echo("\nGenerated files:")
            for name, path in generated.items():
                click.echo(f"  - {name}: {path}")

        if result.errors:
            click.echo("\nErrors:")
            for error in result.errors:
                click.echo(f"  ! {error}")

    except Exception as e:
        logger.exception("Processing failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("document", type=click.Path(exists=True))
@click.option(
    "--schema", "-s",
    type=str,
    required=True,
    help="Schema name (generic_form, table) or path to a JSON schema file",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="extraction.json",
    help="Output JSON file",
)
@click.option(
    "--page", "-p",
    type=int,
    default=0,
    help="Page number (0-indexed)",
)
@click.option(
    "--save-layout/--no-save-layout",
    default=True,
    help="Save layout detection images (default: on)",
)
@click.pass_context
def extract(ctx, document: str, schema: str, output: str, page: int, save_layout: bool):
    """
    Extract structured data from a document using a schema.

    DOCUMENT: Path to the document

    SCHEMA: A predefined name (generic_form, table) or a path to a JSON schema file.
    """
    from ..pipelines.document_processor import DocumentProcessor
    from ..extractors.schemas import get_schema

    click.echo(f"Extracting from: {document}")
    click.echo(f"Schema: {schema}")
    click.echo(f"Page: {page}")

    try:
        # Create minimal processor
        processor = DocumentProcessor(
            verbose=ctx.obj.get("verbose", False),
        )

        # Determine layout output directory (sibling to output file)
        layout_output_dir = None
        if save_layout:
            output_path = Path(output)
            layout_output_dir = output_path.parent / "layout_images"

        # Process document first
        result = processor.process(
            document,
            analyze_regions=False,
            layout_output_dir=layout_output_dir,
        )

        if page >= result.page_count:
            click.echo(f"Error: Page {page} not found (document has {result.page_count} pages)")
            sys.exit(1)

        # Resolve schema: file path or predefined name
        schema_path = Path(schema)
        if schema_path.is_file() and schema_path.suffix == ".json":
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_dict = json.load(f)
        else:
            schema_dict = get_schema(schema)
        extraction = processor.extract_schema(result, schema_dict, page)

        # Save output
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extraction, f, indent=2, ensure_ascii=False)

        click.echo(f"\n[OK] Extraction complete!")
        click.echo(f"Output saved to: {output_path}")

        if save_layout and layout_output_dir and layout_output_dir.exists():
            layout_files = list(layout_output_dir.glob("*.png"))
            if layout_files:
                click.echo(f"Layout images saved to: {layout_output_dir}/")
                for lf in layout_files:
                    click.echo(f"  - {lf.name}")

        # Show summary (generic - auto-detect array fields and key fields)
        if "error" not in extraction:
            for field_name, field_value in extraction.items():
                if isinstance(field_value, list) and field_name != "errors":
                    click.echo(f"Extracted {len(field_value)} {field_name}")
                elif field_name in ["name", "title", "form_type", "document_type"]:
                    click.echo(f"{field_name.replace('_', ' ').title()}: {field_value}")

    except Exception as e:
        logger.exception("Extraction failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("document", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="layout.png",
    help="Output image path",
)
@click.option(
    "--page", "-p",
    type=int,
    default=0,
    help="Page number (0-indexed)",
)
@click.option(
    "--no-ocr",
    is_flag=True,
    help="Don't show OCR regions",
)
@click.pass_context
def visualize(ctx, document: str, output: str, page: int, no_ocr: bool):
    """
    Visualize document layout detection.

    DOCUMENT: Path to the document
    """
    from ..pipelines.document_processor import DocumentProcessor
    from ..utils.visualization import draw_layout

    click.echo(f"Visualizing: {document}")

    try:
        processor = DocumentProcessor(
            verbose=ctx.obj.get("verbose", False),
        )

        # Process document
        result = processor.process(document, analyze_regions=False)

        if page >= result.page_count:
            click.echo(f"Error: Page {page} not found")
            sys.exit(1)

        # Create visualization
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        image = result.images[page] if page < len(result.images) else None

        draw_layout(
            layout=result.layouts[page],
            image=image,
            output_path=output_path,
            show_labels=True,
            show_reading_order=True,
            show_ocr=not no_ocr,
        )

        click.echo(f"\n[OK] Visualization saved to: {output_path}")

    except Exception as e:
        logger.exception("Visualization failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--check-env", is_flag=True, help="Check environment configuration")
@click.pass_context
def info(ctx, check_env: bool):
    """Show system information and configuration."""
    import platform

    click.echo("Agentic Document Extractor v0.1.0")
    click.echo("=" * 40)
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Python: {sys.version}")

    if check_env:
        import os
        from dotenv import load_dotenv

        load_dotenv()

        click.echo("\nEnvironment:")
        click.echo(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
        click.echo(f"  OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', 'default')}")

    # Check optional dependencies
    click.echo("\nDependencies:")

    optional_deps = {
        "paddleocr": "OCR engine",
        "fitz": "PDF processing",
        "langchain": "Agent framework",
        "transformers": "Layout understanding",
    }

    for module, description in optional_deps.items():
        try:
            __import__(module)
            click.echo(f"  [OK] {module}: {description}")
        except ImportError:
            click.echo(f"  [X] {module}: {description} (not installed)")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
