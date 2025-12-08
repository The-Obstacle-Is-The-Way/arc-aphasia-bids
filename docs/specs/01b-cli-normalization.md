# Phase 01b: CLI Structure Normalization

> Status: Ready after Phase 01a
> Blocking: No (but improves UX immediately)
> Estimated: 1 hour
> Source: Adapted from upstream `specs_from_upstream/03-cli-normalization.md`

---

## Problem

Current CLI has inconsistent structure:

```bash
# ARC commands (top-level - legacy)
arc-bids build ...
arc-bids validate ...
arc-bids info

# ISLES24 commands (subcommand group)
arc-bids isles24 build ...
```

**Why is ARC special?** It shouldn't be. This is legacy from when the package only supported ARC.

---

## Solution

All datasets as subcommand groups:

```bash
bids-hub arc build /path/to/ds004884 --hf-repo user/arc-dataset
bids-hub arc validate /path/to/ds004884
bids-hub arc info

bids-hub isles24 build /path/to/isles24 --hf-repo user/isles24-dataset
bids-hub isles24 validate /path/to/isles24
bids-hub isles24 info

bids-hub list  # Show all supported datasets
```

---

## Implementation

### New CLI Structure

```python
# cli.py
import typer

app = typer.Typer(
    name="bids-hub",
    help="Upload BIDS neuroimaging datasets to HuggingFace Hub.",
    add_completion=False,
)

# --- ARC Subcommand Group ---
arc_app = typer.Typer(help="ARC (Aphasia Recovery Cohort) dataset commands.")
app.add_typer(arc_app, name="arc")

@arc_app.command("build")
def arc_build(
    bids_root: Path,
    hf_repo: str = typer.Option("hugging-science/arc-aphasia-bids"),
    dry_run: bool = typer.Option(True),
) -> None:
    """Build and push ARC dataset to HuggingFace Hub."""
    ...

@arc_app.command("validate")
def arc_validate(bids_root: Path, ...) -> None:
    """Validate ARC dataset download."""
    ...

@arc_app.command("info")
def arc_info() -> None:
    """Show ARC dataset information."""
    ...

# --- ISLES24 Subcommand Group ---
isles24_app = typer.Typer(help="ISLES24 stroke dataset commands.")
app.add_typer(isles24_app, name="isles24")

@isles24_app.command("build")
def isles24_build(bids_root: Path, ...) -> None:
    """Build and push ISLES24 dataset to HuggingFace Hub."""
    ...

@isles24_app.command("validate")
def isles24_validate(bids_root: Path, ...) -> None:
    """Validate ISLES24 dataset download."""
    ...

@isles24_app.command("info")
def isles24_info() -> None:
    """Show ISLES24 dataset information."""
    ...

# --- Global Commands ---
@app.command("list")
def list_datasets() -> None:
    """List all supported datasets."""
    typer.echo("Supported datasets:")
    typer.echo("  arc     - Aphasia Recovery Cohort (OpenNeuro ds004884)")
    typer.echo("  isles24 - ISLES 2024 Stroke (Zenodo)")
```

---

## Implementation Checklist

### Step 1: Restructure `cli.py`

- Create `arc_app` subcommand group
- Move existing `build`, `validate`, `info` from top-level to `arc_app`
- Keep `isles24_app` (already exists)
- Add `list` command

### Step 2: Remove Top-Level Legacy Commands

Delete these from `cli.py`:

```python
# DELETE these
@app.command()
def build(...): ...

@app.command()
def validate(...): ...

@app.command()
def info(): ...
```

### Step 3: Update Help Text

```python
arc_app = typer.Typer(
    help="ARC (Aphasia Recovery Cohort) dataset commands.\n\n"
         "Source: OpenNeuro ds004884\n"
         "License: CC0 (Public Domain)"
)
```

### Step 4: Update Documentation

Update all CLI examples in:
- `docs/tutorials/*.md`
- `docs/how-to/*.md`
- `README.md`
- `CLAUDE.md`

Old → New:
```bash
# Old
arc-bids build /path/to/arc

# New
bids-hub arc build /path/to/arc
```

---

## Verification

```bash
# Help should show subcommands
bids-hub --help
# Output: Commands: arc, isles24, list

# ARC commands
bids-hub arc --help
bids-hub arc build --help
bids-hub arc validate --help
bids-hub arc info

# ISLES24 commands
bids-hub isles24 --help
bids-hub isles24 build --help
bids-hub isles24 validate --help
bids-hub isles24 info

# List supported datasets
bids-hub list
```

---

## Success Criteria

- [ ] `bids-hub arc build --help` works
- [ ] `bids-hub isles24 build --help` works
- [ ] `bids-hub list` shows both datasets
- [ ] No top-level `build`/`validate`/`info` commands
- [ ] All tests pass

---

## Next Phase

After CLI normalization → Phase 02: Validation Refactor
