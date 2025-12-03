# arc-bids

## Project Overview
**arc-bids** is a specialized Python pipeline designed to upload the **Aphasia Recovery Cohort (ARC)** neuroimaging dataset (OpenNeuro `ds004884`) to the HuggingFace Hub. It converts raw BIDS data (NIfTI images + metadata) into a sharded HuggingFace Dataset (`parquet`), enabling direct cloud streaming and visualization.

**Key Features:**

* **Multimodal:** Handles T1w, T2w, FLAIR, BOLD fMRI, DWI, sbref, and Lesion Masks.
* **Session-Based:** Iterates per *scanning session* (902 rows), not just per subject.
* **Validation:** Includes strict integrity checks against the published ARC descriptor.
* **Optimized:** Uses specific sharding strategies to handle 278GB of NIfTI data without OOM crashes.

## Critical Technical Mandates

### 1. The OOM Crash Fix (Sharding)
**Problem:** The `datasets` library underestimates the dataset size (based on file paths) and defaults to 1 shard. When `embed_external_files=True` loads the actual NIfTI bytes (278GB), the process crashes with Out-Of-Memory (OOM).
**Solution:** We **MUST** force sharding by passing `num_shards=len(file_table)` to `push_dataset_to_hub`. This ensures 1 shard per session (~300MB), keeping RAM usage low.
**Code Location:** `src/arc_bids/arc.py` inside `build_and_push_arc`.

### 2. The 0-Byte NIfTI Fix (Dependency)
**Problem:** Stable versions of `datasets` (PyPI) have a bug where `Nifti()` files upload as 0 bytes.
**Solution:** We **MUST** use the development version from GitHub.
**Configuration:** In `pyproject.toml`:

```toml
[tool.uv.sources]
datasets = { git = "https://github.com/huggingface/datasets.git" }
```

## Building and Running

This project uses `uv` for dependency management and `make` for orchestration.

### Key Commands

| Goal | Command | Description |
| :--- | :--- | :--- |
| **Install** | `make install` | Installs dependencies via `uv sync`. |
| **Test** | `make test` | Runs `pytest` (includes strict type checking). |
| **Lint** | `make lint` | Runs `ruff check`. |
| **Format** | `make format` | Runs `ruff format`. |
| **Validate** | `uv run arc-bids validate <path>` | Validates a local BIDS download integrity. |
| **Build & Push** | `uv run arc-bids build <path> --hf-repo <id>` | Builds the dataset and pushes to HuggingFace. |

### Local Development Loop

```bash
# 1. Ensure environment is clean and dependencies are synced
uv sync --all-extras

# 2. Run the full quality suite
make all

# 3. Run validation on a local sample
uv run arc-bids validate data/openneuro/ds004884
```

## Architecture

### Codebase Structure

* **`src/arc_bids/arc.py`**: **The Brain.** Contains `build_arc_file_table` (iterates BIDS structure) and `get_arc_features` (defines HF schema). This is where the dataset logic lives.
* **`src/arc_bids/core.py`**: **The Tooling.** Generic helpers for any BIDS-to-HF conversion. Contains `build_hf_dataset` and `push_dataset_to_hub`.
* **`src/arc_bids/validation.py`**: **The Guard.** Checks file counts (T1w, BOLD, etc.) against the official ARC paper specs before upload.
* **`tests/test_arc.py`**: **The Verification.** Uses a synthetic BIDS fixture to verify that all 7 modalities are correctly discovered.

### Data Flow

1. **Input:** Local BIDS directory (`data/openneuro/ds004884`).
2. **Discovery:** `arc.py` walks directories (`anat/`, `func/`, `dwi/`) to build a Pandas DataFrame.
3. **Schema:** `datasets.Features` defines columns (`Nifti()` for images).
4. **Build:** `datasets.Dataset.from_pandas()` creates the dataset object.
5. **Upload:** `ds.push_to_hub(..., num_shards=902)` embeds NIfTI bytes into Parquet shards and uploads to HF.

## Development Conventions

* **Typing:** Strict `mypy` compliance is required. Use `from __future__ import annotations`.
* **Formatting:** `ruff` is the authority.
* **Testing:** All new features must have `pytest` coverage. Use `synthetic_bids_root` fixture for filesystem tests.
* **No "Hacky" Fixes:** If a library fails (like `datasets`), fix the dependency version or configuration, do not patch the library code locally.
