"""
Command-line interface for BIDS → Hugging Face NIfTI dataset tools.

This CLI provides subcommands for processing specific BIDS datasets:
- `arc`: Process the ARC dataset (ds004884)
- `soop`: Process the SOOP dataset (ds004889)

Usage:
    # Show help
    hf-bids-nifti --help

    # Process ARC dataset (dry run - won't push to Hub)
    hf-bids-nifti arc /path/to/ds004884 --hf-repo user/arc-dataset --dry-run

    # Process SOOP dataset and push to Hub
    hf-bids-nifti soop /path/to/ds004889 --hf-repo user/soop-dataset --no-dry-run

Note: ARC and SOOP commands are currently TEMPLATES and will raise
NotImplementedError until their file-table builders are implemented.
"""

from pathlib import Path

import typer

from .arc import build_and_push_arc
from .core import DatasetBuilderConfig
from .soop import build_and_push_soop

app = typer.Typer(
    name="hf-bids-nifti",
    help="BIDS → Hugging Face NIfTI dataset tools.",
    add_completion=False,
)


@app.command()
def arc(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ARC BIDS root directory (ds004884).",
        exists=False,  # Don't validate existence; may be a remote path or not downloaded yet
    ),
    hf_repo: str = typer.Option(
        ...,
        "--hf-repo",
        "-r",
        help="Hugging Face dataset repo ID (e.g., 'user/arc-bids-demo').",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If true (default), build dataset but do not push to Hub.",
    ),
) -> None:
    """
    Build (and optionally push) the ARC HF dataset.

    TEMPLATE: This command will raise NotImplementedError until
    the ARC file-table builder is implemented.

    Example:
        hf-bids-nifti arc /data/ds004884 --hf-repo myuser/arc-demo --dry-run
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
def soop(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to SOOP BIDS root directory (ds004889).",
        exists=False,
    ),
    hf_repo: str = typer.Option(
        ...,
        "--hf-repo",
        "-r",
        help="Hugging Face dataset repo ID (e.g., 'user/soop-bids-demo').",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If true (default), build dataset but do not push to Hub.",
    ),
) -> None:
    """
    Build (and optionally push) the SOOP HF dataset.

    TEMPLATE: This command will raise NotImplementedError until
    the SOOP file-table builder is implemented.

    Example:
        hf-bids-nifti soop /data/ds004889 --hf-repo myuser/soop-demo --dry-run
    """
    config = DatasetBuilderConfig(
        bids_root=bids_root,
        hf_repo_id=hf_repo,
        dry_run=dry_run,
    )

    typer.echo(f"Processing SOOP dataset from: {bids_root}")
    typer.echo(f"Target HF repo: {hf_repo}")
    typer.echo(f"Dry run: {dry_run}")

    build_and_push_soop(config)

    if dry_run:
        typer.echo("Dry run complete. Dataset built but not pushed.")
    else:
        typer.echo(f"Dataset pushed to: https://huggingface.co/datasets/{hf_repo}")


if __name__ == "__main__":
    app()
