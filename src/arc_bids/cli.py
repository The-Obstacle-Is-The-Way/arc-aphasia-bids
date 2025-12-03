"""
Command-line interface for uploading ARC dataset to HuggingFace Hub.

Usage:
    # Show help
    arc-bids --help

    # Validate downloaded dataset before pushing
    arc-bids validate data/openneuro/ds004884

    # Process ARC dataset (dry run - won't push to Hub)
    arc-bids build /path/to/ds004884 --hf-repo user/arc-dataset --dry-run

    # Process ARC dataset and push to Hub
    arc-bids build /path/to/ds004884 --hf-repo user/arc-dataset --no-dry-run

Note: The `build` command expects the ARC BIDS tree (ds004884) to exist locally.
It will build the HF dataset and optionally push it to the Hub.
"""

from pathlib import Path

import typer

from .arc import build_and_push_arc
from .core import DatasetBuilderConfig
from .validation import validate_arc_download

app = typer.Typer(
    name="arc-bids",
    help="Upload the Aphasia Recovery Cohort (ARC) dataset to HuggingFace Hub.",
    add_completion=False,
)


@app.command()
def build(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ARC BIDS root directory (ds004884).",
        exists=False,  # Don't validate existence; may not be downloaded yet
    ),
    hf_repo: str = typer.Option(
        "hugging-science/arc-aphasia-bids",
        "--hf-repo",
        "-r",
        help="HuggingFace dataset repo ID.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If true (default), build dataset but do not push to Hub.",
    ),
) -> None:
    """
    Build (and optionally push) the ARC HF dataset.

    Walks the BIDS directory, builds a file table with NIfTI paths and
    participant metadata, converts to HF Dataset, and optionally pushes
    to the Hub.

    Example:
        arc-bids build data/openneuro/ds004884 --dry-run
    """
    config = DatasetBuilderConfig(
        bids_root=bids_root,
        hf_repo_id=hf_repo,
        dry_run=dry_run,
    )

    typer.echo(f"Processing ARC dataset from: {bids_root}")
    typer.echo(f"Target HF repo: {hf_repo}")
    typer.echo(f"Dry run: {dry_run}")

    build_and_push_arc(config)

    if dry_run:
        typer.echo("Dry run complete. Dataset built but not pushed.")
    else:
        typer.echo(f"Dataset pushed to: https://huggingface.co/datasets/{hf_repo}")


@app.command()
def validate(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ARC BIDS root directory (ds004884).",
    ),
    run_bids_validator: bool = typer.Option(
        False,
        "--bids-validator/--no-bids-validator",
        help="Run external BIDS validator (requires npx, slow on large datasets).",
    ),
    sample_size: int = typer.Option(
        10,
        "--sample-size",
        "-n",
        help="Number of NIfTI files to spot-check for integrity.",
    ),
    tolerance: float = typer.Option(
        0.0,
        "--tolerance",
        "-t",
        min=0.0,
        max=1.0,
        help="Allowed fraction of missing files (0.0 to 1.0). Default 0.0 (strict).",
    ),
) -> None:
    """
    Validate an ARC dataset download before pushing to HuggingFace.

    Checks:
    - Required BIDS files exist (dataset_description.json, participants.tsv)
    - Subject count matches expected (~230 from Sci Data paper)
    - Series counts match paper (T1w: 441, T2w: 447, FLAIR: 235)
    - Sample NIfTI files are loadable with nibabel
    - (Optional) External BIDS validator passes

    Run this after downloading to ensure data integrity before HF push.

    Example:
        arc-bids validate data/openneuro/ds004884
    """
    result = validate_arc_download(
        bids_root,
        run_bids_validator=run_bids_validator,
        nifti_sample_size=sample_size,
        tolerance=tolerance,
    )

    typer.echo(result.summary())

    if not result.all_passed:
        raise typer.Exit(code=1)


@app.command()
def info() -> None:
    """
    Show information about the ARC dataset.
    """
    typer.echo("Aphasia Recovery Cohort (ARC)")
    typer.echo("=" * 40)
    typer.echo("OpenNeuro ID: ds004884")
    typer.echo("URL: https://openneuro.org/datasets/ds004884")
    typer.echo("License: CC0 (Public Domain)")
    typer.echo("")
    typer.echo("Contains:")
    typer.echo("  - 230 chronic stroke patients")
    typer.echo("  - 902 scanning sessions")
    typer.echo("  - T1w, T2w, FLAIR, diffusion, fMRI")
    typer.echo("  - Expert lesion masks")
    typer.echo("  - WAB (Western Aphasia Battery) scores")
    typer.echo("")
    typer.echo("Expected series counts (from Sci Data paper):")
    typer.echo("  - T1w: 441 series")
    typer.echo("  - T2w: 447 series")
    typer.echo("  - FLAIR: 235 series")
    typer.echo("  - Lesion masks: 230")


if __name__ == "__main__":
    app()
