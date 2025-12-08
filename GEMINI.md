# bids-hub

## Project Overview

**bids-hub** is a Python pipeline that uploads BIDS neuroimaging datasets to HuggingFace Hub. It converts raw BIDS data (NIfTI images + metadata) into sharded HuggingFace Datasets (parquet), enabling direct cloud streaming and visualization.

**Supported Datasets:**

| Dataset | Source | Subjects | Size |
|---------|--------|----------|------|
| ARC (Aphasia Recovery Cohort) | OpenNeuro ds004884 | 230 | ~293GB |
| ISLES 2024 (Stroke Lesion Segmentation) | Zenodo 17652035 | 149 | ~100GB |

**Key Features:**

* **Multi-Dataset:** Supports ARC and ISLES24 with dataset-specific schemas.
* **Multimodal:** Handles T1w, T2w, FLAIR, BOLD fMRI, DWI, CT, CTA, CTP, perfusion maps.
* **Validation:** Includes strict integrity checks against published dataset descriptors.
* **Optimized:** Uses specific sharding strategies to handle large NIfTI data without OOM crashes.

## Critical Technical Mandates

### 1. The Embedding Bug Fix (Sharding)

**Problem:** The `datasets` library's `embed_table_storage` crashes with SIGKILL when processing sharded datasets containing `Sequence()` nested types like `Sequence(Nifti())`.

**Solution:** We **MUST** use the pandas workaround in `push_dataset_to_hub` that converts shards to pandas and recreates them to break problematic Arrow slice references.

**Code Location:** `src/bids_hub/core/builder.py` (search for "pandas workaround")

**Upstream Bug:** See `UPSTREAM_BUG.md` for full details and tracking.

### 2. The Development Dependency

**Problem:** Stable versions of `datasets` (PyPI) have bugs affecting NIfTI uploads.

**Solution:** We **MUST** use a pinned development version from GitHub.

**Configuration:** In `pyproject.toml`:

```toml
[tool.uv.sources]
datasets = { git = "https://github.com/huggingface/datasets.git", rev = "..." }
```

## Building and Running

This project uses `uv` for dependency management and `make` for orchestration.

### Key Commands

| Goal | Command | Description |
|:-----|:--------|:------------|
| **Install** | `make install` | Installs dependencies via `uv sync`. |
| **Test** | `make test` | Runs `pytest`. |
| **Lint** | `make lint` | Runs `ruff check`. |
| **Format** | `make format` | Runs `ruff format`. |
| **ARC Validate** | `uv run bids-hub arc validate <path>` | Validates a local ARC BIDS download. |
| **ARC Build** | `uv run bids-hub arc build <path> --no-dry-run` | Builds and pushes ARC to HuggingFace. |
| **ISLES24 Validate** | `uv run bids-hub isles24 validate <path>` | Validates a local ISLES24 download. |
| **ISLES24 Build** | `uv run bids-hub isles24 build <path> --no-dry-run` | Builds and pushes ISLES24 to HuggingFace. |

### Local Development Loop

```bash
# 1. Ensure environment is clean and dependencies are synced
uv sync --all-extras

# 2. Run the full quality suite
make all

# 3. Run validation on local data
uv run bids-hub arc validate data/openneuro/ds004884
uv run bids-hub isles24 validate data/zenodo/isles24/train
```

## Architecture

### Codebase Structure

```text
src/bids_hub/
├── __init__.py          # Public API re-exports
├── cli.py               # Typer CLI with subcommands
├── core/                # Generic BIDS→HF utilities
│   ├── __init__.py
│   ├── builder.py       # build_hf_dataset, push_dataset_to_hub
│   ├── config.py        # DatasetBuilderConfig
│   └── utils.py         # File discovery helpers
├── datasets/            # Per-dataset modules
│   ├── __init__.py
│   ├── arc.py           # ARC schema + pipeline
│   └── isles24.py       # ISLES24 schema + pipeline
└── validation/          # Per-dataset validation
    ├── __init__.py
    ├── base.py          # Generic validation framework
    ├── arc.py           # ARC validation rules
    └── isles24.py       # ISLES24 validation rules
```

### Module Responsibilities

* **`core/builder.py`**: Generic BIDS→HF conversion. Contains `build_hf_dataset` and `push_dataset_to_hub`.
* **`core/config.py`**: `DatasetBuilderConfig` dataclass for pipeline configuration.
* **`core/utils.py`**: File discovery helpers (`find_single_nifti`, `find_all_niftis`).
* **`datasets/arc.py`**: ARC-specific schema (`get_arc_features`) and file table builder (`build_arc_file_table`).
* **`datasets/isles24.py`**: ISLES24-specific schema and pipeline.
* **`validation/base.py`**: Generic validation framework with `ValidationResult` dataclass.
* **`validation/arc.py`**: ARC-specific validation rules (file counts per ARC paper).
* **`validation/isles24.py`**: ISLES24-specific validation rules.
* **`cli.py`**: Typer CLI with `arc` and `isles24` subcommand groups.

### Data Flow

1. **Input:** Local BIDS directory (e.g., `data/openneuro/ds004884` or `data/zenodo/isles24/train`).
2. **Discovery:** Dataset module walks directories to build a Pandas DataFrame.
3. **Schema:** `datasets.Features` defines columns (`Nifti()` for images, `Value()` for metadata).
4. **Build:** `datasets.Dataset.from_pandas()` creates the dataset object.
5. **Upload:** `push_dataset_to_hub()` embeds NIfTI bytes into Parquet shards and uploads.

## Development Conventions

* **Typing:** Strict `mypy` compliance is required. Use `from __future__ import annotations`.
* **Formatting:** `ruff` is the authority.
* **Testing:** All new features must have `pytest` coverage. Use `synthetic_bids_root` (ARC) or `synthetic_isles24_root` (ISLES24) fixtures for filesystem tests.
* **No "Hacky" Fixes:** If a library fails, fix the dependency version or configuration, do not patch the library code locally.
