# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This package uploads the **Aphasia Recovery Cohort (ARC)** neuroimaging dataset (OpenNeuro ds004884) to HuggingFace Hub. It converts BIDS-formatted NIfTI files to HuggingFace's `Dataset` format with proper `Nifti()` feature types.

## Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_arc.py::TestBuildArcFileTable::test_build_file_table_returns_dataframe -v

# Lint
uv run ruff check .

# Type check (strict)
uv run mypy src tests

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files

# CLI commands
uv run bids-hub --help
uv run bids-hub info
uv run bids-hub validate data/openneuro/ds004884
uv run bids-hub build data/openneuro/ds004884 --dry-run
uv run bids-hub build data/openneuro/ds004884 --no-dry-run  # Actually push to Hub
```

## Architecture

### Data Flow

```
OpenNeuro BIDS (ds004884)
        │
        ▼ build_arc_file_table()
pandas DataFrame (paths + metadata, one row per SESSION)
        │
        ▼ build_hf_dataset()
datasets.Dataset with Nifti() features
        │
        ▼ push_dataset_to_hub(num_shards=len(file_table))
HuggingFace Hub
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `core.py` | Generic BIDS→HF conversion (reusable for any dataset) |
| `arc.py` | ARC-specific: schema, file discovery, pipeline |
| `validation.py` | Pre-upload integrity checks against Sci Data paper |
| `cli.py` | Typer CLI with `build`, `validate`, `info` commands |

### Key Design Decisions

1. **One row per SESSION** (not per subject): ARC is longitudinal with 902 sessions across 230 subjects. This maps naturally to `num_shards`.

2. **Explicit `num_shards=len(file_table)`**: The `datasets` library estimates shard count based on file path sizes (~1MB), but embedded NIfTIs are ~278GB. Without explicit sharding, it tries to build 1 giant shard → OOM crash.

3. **Git-based `datasets` dependency**: PyPI stable has a bug where `Nifti.embed_storage` silently creates empty files. Must use git main until fix is released. See `[tool.uv.sources]` in pyproject.toml.

4. **Absolute file paths**: Required for `embed_external_files=True` to work correctly.

## Dataset Schema

```python
Features({
    "subject_id": Value("string"),    # e.g., "sub-M2001"
    "session_id": Value("string"),    # e.g., "ses-1"
    "t1w": Nifti(),                   # T1-weighted structural
    "t2w": Nifti(),                   # T2-weighted structural
    "flair": Nifti(),                 # FLAIR structural
    "bold": Nifti(),                  # fMRI 4D time-series
    "dwi": Nifti(),                   # Diffusion-weighted
    "sbref": Nifti(),                 # Single-band reference
    "lesion": Nifti(),                # Expert lesion mask
    "age_at_stroke": Value("float32"),
    "sex": Value("string"),
    "wab_aq": Value("float32"),       # Aphasia severity score
    "wab_type": Value("string"),
})
```

All NIfTI columns are nullable (sessions may not have all modalities).

## Testing

Tests use synthetic BIDS structures with minimal NIfTI files (2x2x2 voxels). The fixture `synthetic_bids_root` creates a complete multi-session dataset with all modalities for comprehensive coverage.

Key test patterns:
- `_create_minimal_nifti()`: Creates valid NIfTI files quickly
- Mocking `push_dataset_to_hub` for dry-run tests
- Validation tests check counts against Sci Data paper expectations
