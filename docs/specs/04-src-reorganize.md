# Phase 04: Source Code Reorganization

> Status: Ready after Phase 03
> Blocking: No
> Estimated: 2-3 hours

---

## Goal

Reorganize `src/bids_hub/` to clearly separate:
- **Core** (generic, upstream candidate)
- **Datasets** (per-dataset modules)
- **Validation** (already done in Phase 02)

---

## Current State (after Phase 01a rename)

```
src/bids_hub/
├── __init__.py
├── core.py          # GENERIC - 288 lines
├── config.py        # ARC config - minor
├── arc.py           # DATASET-SPECIFIC
├── isles24.py       # DATASET-SPECIFIC
├── validation/      # After Phase 02
│   ├── __init__.py
│   ├── base.py
│   ├── arc.py
│   └── isles24.py
└── cli.py
```

---

## Target State

```
src/bids_hub/
├── __init__.py              # Public API exports
├── cli.py                   # CLI entry point
│
├── core/                    # GENERIC (upstream candidate)
│   ├── __init__.py          # Re-exports
│   ├── builder.py           # build_hf_dataset, push_dataset_to_hub
│   ├── config.py            # DatasetBuilderConfig
│   └── utils.py             # File discovery helpers
│
├── validation/              # From Phase 02
│   ├── __init__.py
│   ├── base.py
│   ├── arc.py
│   └── isles24.py
│
└── datasets/                # DATASET-SPECIFIC
    ├── __init__.py
    ├── arc.py               # ARC schema + file table
    └── isles24.py           # ISLES24 schema + file table
```

---

## Implementation Steps

### Step 1: Create Core Subpackage

```bash
mkdir -p src/bids_hub/core
```

**`src/bids_hub/core/__init__.py`**

```python
"""Core BIDS→HF conversion utilities (generic, upstream candidate)."""

from .builder import build_hf_dataset, push_dataset_to_hub
from .config import DatasetBuilderConfig

__all__ = [
    "DatasetBuilderConfig",
    "build_hf_dataset",
    "push_dataset_to_hub",
]
```

**`src/bids_hub/core/config.py`**

```python
"""Configuration dataclasses for BIDS→HF conversion."""

from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatasetBuilderConfig:
    """Configuration for building a HuggingFace Dataset from BIDS data."""
    bids_root: Path
    hf_repo_id: str
    split: str | None = None
    dry_run: bool = False
```

**`src/bids_hub/core/builder.py`**

```python
"""Core build and push functions."""

# Move from core.py:
# - validate_file_table_columns()
# - build_hf_dataset()
# - push_dataset_to_hub()
```

**`src/bids_hub/core/utils.py`**

```python
"""Generic file discovery utilities."""

from pathlib import Path

def find_single_nifti(search_dir: Path, pattern: str) -> str | None:
    """Find a single NIfTI file matching pattern."""
    if not search_dir.exists():
        return None
    matches = list(search_dir.rglob(pattern))
    if not matches:
        return None
    matches.sort(key=lambda p: p.name)
    return str(matches[0].resolve())

def find_all_niftis(search_dir: Path, pattern: str) -> list[str]:
    """Find all NIfTI files matching pattern."""
    if not search_dir.exists():
        return []
    matches = list(search_dir.rglob(pattern))
    matches.sort(key=lambda p: p.name)
    return [str(p.resolve()) for p in matches]
```

### Step 2: Create Datasets Subpackage

```bash
mkdir -p src/bids_hub/datasets
```

**`src/bids_hub/datasets/__init__.py`**

```python
"""Dataset-specific modules."""

from .arc import build_arc_file_table, build_and_push_arc, get_arc_features
from .isles24 import build_and_push_isles24, build_isles24_file_table, get_isles24_features

__all__ = [
    # ARC
    "build_arc_file_table",
    "build_and_push_arc",
    "get_arc_features",
    # ISLES24
    "build_isles24_file_table",
    "build_and_push_isles24",
    "get_isles24_features",
]
```

**`src/bids_hub/datasets/arc.py`**
- Move from `src/bids_hub/arc.py`
- Update imports: `from ..core import ...`

**`src/bids_hub/datasets/isles24.py`**
- Move from `src/bids_hub/isles24.py`
- Update imports: `from ..core import ...`

### Step 3: Update Root `__init__.py`

```python
"""bids_hub - Upload neuroimaging datasets to HuggingFace Hub."""

# Core (generic)
from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub

# Datasets
from .datasets import (
    build_arc_file_table,
    build_and_push_arc,
    get_arc_features,
    build_isles24_file_table,
    build_and_push_isles24,
    get_isles24_features,
)

# Validation
from .validation import ValidationResult, validate_arc_download, validate_isles24_download

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Core
    "DatasetBuilderConfig",
    "build_hf_dataset",
    "push_dataset_to_hub",
    # ARC
    "build_arc_file_table",
    "build_and_push_arc",
    "get_arc_features",
    "validate_arc_download",
    # ISLES24
    "build_isles24_file_table",
    "build_and_push_isles24",
    "get_isles24_features",
    "validate_isles24_download",
    # Validation
    "ValidationResult",
]
```

### Step 4: Update CLI

```python
# src/bids_hub/cli.py

from .datasets.arc import build_and_push_arc
from .datasets.isles24 import build_and_push_isles24
from .validation.arc import validate_arc_download
from .validation.isles24 import validate_isles24_download
```

### Step 5: Delete Old Files

```bash
rm src/bids_hub/core.py
rm src/bids_hub/config.py
rm src/bids_hub/arc.py
rm src/bids_hub/isles24.py
```

### Step 6: Update Tests

Reorganize test files to mirror src structure:

```
tests/
├── conftest.py
├── core/
│   ├── test_builder.py
│   └── test_config.py
├── datasets/
│   ├── test_arc.py
│   └── test_isles24.py
├── validation/
│   ├── test_base.py
│   ├── test_arc.py
│   └── test_isles24.py
└── test_cli.py
```

---

## Backward Compatibility

The root `__init__.py` re-exports everything, so existing code continues to work:

```python
# These work:
from bids_hub import build_hf_dataset, DatasetBuilderConfig
from bids_hub import build_arc_file_table, get_arc_features
from bids_hub import validate_arc_download
```

---

## Success Criteria

- [x] All imports in `__init__.py` work
- [x] `bids-hub arc build` CLI works
- [x] `bids-hub isles24 build` CLI works
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

---

## Next Phase

After src reorganization → Phase 05: Docs Cleanup
