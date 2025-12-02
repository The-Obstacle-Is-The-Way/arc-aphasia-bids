# hf-bids-nifti-datasets

Template for converting BIDS neuroimaging datasets (e.g., ARC, SOOP) into Hugging Face Datasets with NIfTI + tabular features.

## Overview

This repository provides a **reusable template** for:

```
BIDS dataset on disk → Pandas table of NIfTI file paths + metadata → HF Dataset with Nifti features → optional push_to_hub()
```

**Key points:**

- **No real data in this repo** - Only code and scaffolding
- Data will be mirrored from OpenNeuro directly to Hugging Face datasets
- Respects CC0 licensing from source datasets
- Designed for TDD with fake-data tests

### Target Datasets

| Dataset | OpenNeuro ID | Description |
|---------|--------------|-------------|
| ARC | [ds004884](https://openneuro.org/datasets/ds004884) | Aphasia Recovery Cohort - structural MRI & lesion masks |
| SOOP | [ds004889](https://openneuro.org/datasets/ds004889) | Study of Outcomes in aPhagia - longitudinal stroke recovery |

## Quickstart

```bash
# Clone
git clone https://github.com/The-Obstacle-Is-The-Way/hf-bids-nifti-datasets.git
cd hf-bids-nifti-datasets

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Run tests
uv run pytest

# See CLI help
uv run hf-bids-nifti --help
```

> **Note:** ARC and SOOP commands are templates that will raise `NotImplementedError` until their file-table builders are implemented.

## Project Structure

```
hf-bids-nifti-datasets/
├── src/
│   └── hf_bids_nifti/
│       ├── __init__.py      # Package exports
│       ├── core.py          # Generic BIDS→HF Dataset logic
│       ├── config.py        # Dataset configuration objects
│       ├── arc.py           # ARC-specific STUB
│       ├── soop.py          # SOOP-specific STUB
│       └── cli.py           # Typer CLI
├── tests/
│   ├── test_core_nifti.py   # Core functionality tests
│   └── test_cli_skeleton.py # CLI tests
├── pyproject.toml           # PEP 621 project config
├── uv.lock                  # Reproducible dependencies
├── Makefile                 # Dev workflow automation
├── .pre-commit-config.yaml  # Pre-commit hooks
├── mypy.ini                 # Type checking config
└── README.md
```

## Usage

### As a Library

```python
from pathlib import Path
import pandas as pd
from datasets import Features, Nifti, Value

from hf_bids_nifti.core import DatasetBuilderConfig, build_hf_dataset

# Create a file table with paths to NIfTI files
file_table = pd.DataFrame({
    "subject_id": ["sub-001", "sub-002"],
    "t1w": ["/path/to/sub-001_T1w.nii.gz", "/path/to/sub-002_T1w.nii.gz"],
    "age": [25.0, 30.0],
})

# Define the HF Features schema
features = Features({
    "subject_id": Value("string"),
    "t1w": Nifti(),
    "age": Value("float32"),
})

# Build the dataset
config = DatasetBuilderConfig(
    bids_root=Path("/path/to/bids"),
    hf_repo_id="your-username/your-dataset",
    dry_run=True,
)
ds = build_hf_dataset(config, file_table, features)

# Access NIfTI data
img = ds[0]["t1w"]  # Returns nibabel.Nifti1Image
data = img.get_fdata()  # Convert to numpy array
```

### CLI (Templates)

```bash
# ARC dataset (template - will raise NotImplementedError)
uv run hf-bids-nifti arc /path/to/ds004884 --hf-repo user/arc-demo --dry-run

# SOOP dataset (template - will raise NotImplementedError)
uv run hf-bids-nifti soop /path/to/ds004889 --hf-repo user/soop-demo --dry-run
```

## Development

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Setup

```bash
# Install all dependencies (including dev)
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Common Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Type check
make typecheck

# Run all pre-commit hooks
make pre-commit
```

### Adding a New Dataset

1. Create a new module (e.g., `src/hf_bids_nifti/mydataset.py`)
2. Implement `build_mydataset_file_table(bids_root: Path) -> pd.DataFrame`
3. Define `get_mydataset_features() -> Features`
4. Create `build_and_push_mydataset(config: DatasetBuilderConfig)`
5. Add CLI command in `cli.py`
6. Add tests in `tests/test_mydataset.py`

## Architecture

### Core Concepts

- **`DatasetBuilderConfig`**: Configuration dataclass holding BIDS root path, HF repo ID, and options
- **`build_hf_dataset()`**: Generic function that converts a pandas DataFrame with NIfTI paths to an HF Dataset
- **`Features` with `Nifti()`**: HF schema that enables automatic NIfTI loading via nibabel

### Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  BIDS Directory │────▶│  File Table (df) │────▶│  HF Dataset     │
│  (on disk)      │     │  paths + metadata│     │  Nifti + Values │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        │                        │                        │
   walk directory         pandas DataFrame          ds.push_to_hub()
   extract metadata       with NIfTI paths          to HF Hub
```

## References

- [HuggingFace Datasets - NIfTI](https://huggingface.co/docs/datasets/en/nifti_dataset)
- [BIDS Specification](https://bids-specification.readthedocs.io/)
- [OpenNeuro](https://openneuro.org/)
- [nibabel Documentation](https://nipy.org/nibabel/)

## License

Apache-2.0

The source datasets (ARC, SOOP) are released under CC0 (Public Domain) on OpenNeuro.
