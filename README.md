# arc-bids

Upload the **Aphasia Recovery Cohort (ARC)** dataset to HuggingFace Hub.

> **Status**: Phase 0 (Setup & Exploration)
> **Target HF Repo**: `hugging-science/arc-aphasia-bids`

## What is ARC?

The [Aphasia Recovery Cohort (ARC)](https://openneuro.org/datasets/ds004884) is a BIDS-formatted neuroimaging dataset containing:

- **230 chronic stroke patients** with aphasia
- **902 scanning sessions** (longitudinal)
- **Imaging**: T1w, T2w, FLAIR, diffusion, fMRI, resting-state (NIfTI)
- **Annotations**: Expert-drawn lesion maps
- **Tabular**: Demographics + WAB (Western Aphasia Battery) scores

**Source**: [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884/versions/1.0.1)
**Paper**: [Scientific Data (2024)](https://www.nature.com/articles/s41597-024-03819-7)
**License**: CC0 (Public Domain) - Redistribution OK

## Goal

Convert ARC from BIDS → HuggingFace Dataset that:

1. Works with `datasets.load_dataset()`
2. Uses HF's `Nifti()` feature type for NIfTI loading
3. Enables `push_to_hub()` workflow
4. Renders in HF Hub viewer via NiiVue integration

## Architecture

### Data Flow

```text
OpenNeuro ds004884 (BIDS)
        │
        ▼ AWS S3 or OpenNeuro CLI
Local: data/openneuro/ds004884/  (gitignored)
        │
        ▼ Python walks BIDS tree
pandas DataFrame (paths + metadata)
        │
        ▼ build_hf_dataset()
datasets.Dataset with Nifti() features
        │
        ▼ push_to_hub()
HF Hub (via XET storage)
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/arc_bids/core.py` | Generic BIDS→HF Dataset conversion |
| `src/arc_bids/arc.py` | ARC dataset builder (file table + HF features) |
| `src/arc_bids/validation.py` | Download integrity validation |
| `src/arc_bids/cli.py` | Typer CLI |
| `scripts/download_arc.sh` | Download ARC from OpenNeuro |

## Quickstart

```bash
# Clone
git clone https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids.git
cd arc-aphasia-bids

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# See CLI help
uv run arc-bids --help

# Show dataset info
uv run arc-bids info

# Download ARC dataset
./scripts/download_arc.sh

# Validate download integrity
uv run arc-bids validate data/openneuro/ds004884

# Build dataset (dry run):
uv run arc-bids build data/openneuro/ds004884 --dry-run
```

## Downloading ARC

### Option 1: AWS S3 (Recommended - No Auth)

```bash
aws s3 sync --no-sign-request s3://openneuro.org/ds004884 data/openneuro/ds004884
```

### Option 2: Interactive Script

```bash
./scripts/download_arc.sh
# Choose: 1) Full dataset, 2) Subset for testing, 3) OpenNeuro CLI
```

### Option 3: OpenNeuro CLI (Deno)

```bash
# Install Deno + CLI
curl -fsSL https://deno.land/install.sh | sh
deno install -A --global jsr:@openneuro/cli -n openneuro
openneuro login  # requires API key

# Download
openneuro download ds004884 data/openneuro/ds004884
```

## Validating Downloads

Before pushing to HuggingFace, validate your download to ensure data integrity:

```bash
uv run arc-bids validate data/openneuro/ds004884
```

This checks:

- Required BIDS files exist (dataset_description.json, participants.tsv, participants.json)
- Subject count matches expected (~230 ±5 from Sci Data paper)
- participants.tsv row count matches subject directories
- Series counts match paper (T1w: 441, T2w: 447, FLAIR: 235, lesion masks: 230)
- Sample NIfTI files are loadable with nibabel (random sample, spot-check)

For optional BIDS validator integration (slower but more thorough):

```bash
uv run arc-bids validate data/openneuro/ds004884 --bids-validator
```

## Project Structure

```text
arc-aphasia-bids/
├── src/arc_bids/
│   ├── __init__.py      # Package exports
│   ├── core.py          # Generic BIDS→HF logic
│   ├── config.py        # ARC configuration
│   ├── arc.py           # ARC dataset builder
│   ├── validation.py    # Download integrity checks
│   └── cli.py           # Typer CLI
├── scripts/
│   ├── download_arc.sh  # Download script
│   └── validate_download.py  # Standalone validation
├── tests/
│   ├── test_arc.py          # ARC module tests
│   ├── test_core_nifti.py   # Core functionality tests
│   ├── test_cli_skeleton.py # CLI tests
│   └── test_validation.py   # Validation tests
├── data/                # (gitignored) Local data
│   └── openneuro/ds004884/
├── pyproject.toml       # PEP 621 project config
├── mypy.ini             # Strict typing config
├── CITATION.cff         # Citation metadata
└── README.md
```

## Usage

### As a Library

```python
from pathlib import Path
import pandas as pd
from datasets import Features, Nifti, Value

from arc_bids.core import DatasetBuilderConfig, build_hf_dataset

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
    hf_repo_id="hugging-science/arc-aphasia-bids",
    dry_run=True,
)
ds = build_hf_dataset(config, file_table, features)

# Access NIfTI data
img = ds[0]["t1w"]  # Returns nibabel.Nifti1Image
data = img.get_fdata()  # Convert to numpy array
```

### CLI

```bash
# Show dataset info
uv run arc-bids info

# Build dataset (dry run - won't push to Hub)
uv run arc-bids build data/openneuro/ds004884 --dry-run

# Build and push to Hub
uv run arc-bids build data/openneuro/ds004884 --no-dry-run
```

## Development

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Setup

```bash
# Install all dependencies (including dev)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Quality Checks

```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Type check (strict everywhere)
uv run mypy src tests
```

## Citation

If you use the ARC dataset, please cite both the paper and the dataset:

### Paper

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. The Aphasia Recovery Cohort, an open-source chronic stroke repository. Scientific Data. 2024;11:981. doi:10.1038/s41597-024-03819-7.

### Dataset

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. Aphasia Recovery Cohort (ARC). OpenNeuro [dataset]. 2023. doi:10.18112/openneuro.ds004884.v1.0.1.

### BibTeX

```bibtex
@article{gibson2024aphasia,
  title={The Aphasia Recovery Cohort, an open-source chronic stroke repository},
  author={Gibson, Makayla and Newman-Norlund, Roger and Bonilha, Leonardo and Fridriksson, Julius and Hickok, Gregory and Hillis, Argye E and den Ouden, Dirk-Bart and Rorden, Christopher},
  journal={Scientific Data},
  volume={11},
  pages={981},
  year={2024},
  publisher={Nature Publishing Group},
  doi={10.1038/s41597-024-03819-7}
}

@misc{gibson2023arc,
  title={Aphasia Recovery Cohort (ARC)},
  author={Gibson, Makayla and Newman-Norlund, Roger and Bonilha, Leonardo and Fridriksson, Julius and Hickok, Gregory and Hillis, Argye E and den Ouden, Dirk-Bart and Rorden, Christopher},
  year={2023},
  publisher={OpenNeuro},
  doi={10.18112/openneuro.ds004884.v1.0.1}
}
```

## References

- Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. *The Aphasia Recovery Cohort, an open-source chronic stroke repository.* Scientific Data. 2024;11:981. doi:[10.1038/s41597-024-03819-7](https://doi.org/10.1038/s41597-024-03819-7).

- Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. *Aphasia Recovery Cohort (ARC).* OpenNeuro [dataset]. 2023. doi:[10.18112/openneuro.ds004884.v1.0.1](https://doi.org/10.18112/openneuro.ds004884.v1.0.1).

- OpenNeuro. *OpenNeuro brain imaging data repository.* CC0-licensed BIDS datasets. <https://openneuro.org>.

- [HuggingFace Datasets - NIfTI](https://huggingface.co/docs/datasets/nifti_dataset)
- [BIDS Specification](https://bids-specification.readthedocs.io/)
- [nibabel Documentation](https://nipy.org/nibabel/)

## License

**This package**: Apache-2.0

**ARC dataset**: The ARC dataset (OpenNeuro ds004884) is released under a Creative Commons CC0 license via OpenNeuro, meaning it can be freely reused, redistributed, and mirrored (including to Hugging Face), with appropriate scholarly citation.
