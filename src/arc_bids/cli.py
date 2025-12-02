"""
Command-line interface for uploading ARC dataset to HuggingFace Hub.

Usage:
    # Show help
    arc-bids --help

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
        "the-obstacle-is-the-way/arc-aphasia-bids",
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


if __name__ == "__main__":
    app()
