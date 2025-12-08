# Phase 02: Validation Module Refactor

> Status: Ready after Phase 01b
> Blocking: No
> Estimated: 2-3 hours
> Enhanced with: upstream `specs_from_upstream/02-validation-framework.md`

---

## Goal

Split `validation.py` into:
- `validation/base.py` - Generic framework (upstream candidate)
- `validation/arc.py` - ARC-specific validation config
- `validation/isles24.py` - ISLES24-specific validation config (NEW)

**Key addition from upstream**: Config-driven validation with `DatasetValidationConfig` dataclass.

---

## Current State

```python
# src/arc_bids/validation.py (387 lines)

# GENERIC (should be reusable)
@dataclass
class ValidationCheck: ...
@dataclass
class ValidationResult: ...
def _check_nifti_integrity(): ...
def _check_bids_validator(): ...

# ARC-SPECIFIC (should move)
EXPECTED_COUNTS = {...}  # ARC paper counts
REQUIRED_BIDS_FILES = [...]  # ARC requirements
def _check_required_files(): ...
def _check_subject_count(): ...
def _check_series_count(): ...
def validate_arc_download(): ...
```

---

## Target State

```
src/arc_bids/validation/
├── __init__.py          # Re-exports for backward compat
├── base.py              # Generic validation framework
├── arc.py               # ARC-specific
└── isles24.py           # ISLES24-specific (NEW)
```

---

## Implementation Steps

### Step 1: Create Directory Structure

```bash
mkdir -p src/arc_bids/validation
touch src/arc_bids/validation/__init__.py
```

### Step 2: Create `base.py`

```python
# src/bids_hub/validation/base.py
"""Generic validation framework for BIDS datasets."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    name: str
    expected: str
    actual: str
    passed: bool
    details: str = ""

@dataclass
class ValidationResult:
    """Complete validation results for a BIDS download."""
    bids_root: Path
    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool: ...

    @property
    def passed_count(self) -> int: ...

    @property
    def failed_count(self) -> int: ...

    def add(self, check: ValidationCheck) -> None: ...

    def summary(self) -> str: ...

# NEW: Config-driven validation (from upstream)
@dataclass
class DatasetValidationConfig:
    """Configuration for validating a specific dataset."""
    name: str
    expected_counts: dict[str, int]
    required_files: list[str]
    modality_patterns: dict[str, str]  # e.g., {"t1w": "*_T1w.nii.gz"}
    custom_checks: list[Callable[[Path], ValidationCheck]] = field(default_factory=list)

# NEW: Fast corruption detection (from upstream - HIGH PRIORITY)
def check_zero_byte_files(bids_root: Path) -> tuple[int, list[str]]:
    """
    CRITICAL: Fast detection of zero-byte NIfTI files (common corruption indicator).

    This check is HIGH PRIORITY - faster than nibabel integrity checks
    and catches obvious corruption before expensive decompression.

    Returns:
        (count of zero-byte files, list of relative paths)
    """
    zero_byte_files = []
    for nifti in bids_root.rglob("*.nii.gz"):
        if nifti.stat().st_size == 0:
            zero_byte_files.append(str(nifti.relative_to(bids_root)))
    return len(zero_byte_files), zero_byte_files

# NEW: Generic validation runner (from upstream)
def validate_dataset(
    bids_root: Path,
    config: DatasetValidationConfig,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """
    Generic validation using dataset-specific config.

    Always runs:
    1. Required files check
    2. Zero-byte file detection (fast, catches obvious corruption)
    3. Subject/session counts (with tolerance)
    4. Modality counts (based on config patterns)
    5. Optional: BIDS validator
    6. Optional: NIfTI integrity spot-check (nibabel)
    """
    ...

# Generic helpers
def check_nifti_integrity(
    bids_root: Path,
    pattern: str = "*_T1w.nii.gz",
    sample_size: int = 10,
) -> ValidationCheck: ...

def check_bids_validator(bids_root: Path) -> ValidationCheck | None: ...

def check_file_exists(path: Path, name: str) -> ValidationCheck: ...

def check_count(
    name: str,
    actual: int,
    expected: int,
    tolerance: float = 0.0,
) -> ValidationCheck: ...
```

### Step 3: Create `arc.py`

```python
# src/bids_hub/validation/arc.py
"""ARC dataset validation."""

from pathlib import Path
from .base import DatasetValidationConfig, ValidationResult, validate_dataset

# From Sci Data paper (Gibson et al., 2024)
ARC_VALIDATION_CONFIG = DatasetValidationConfig(
    name="arc",
    expected_counts={
        "subjects": 230,
        "sessions": 902,
        "t1w_series": 441,
        "t2w_series": 447,
        "flair_series": 235,
        "bold_series": 850,
        "dwi_series": 613,
        "sbref_series": 88,
        "lesion_masks": 230,
    },
    required_files=[
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
    ],
    modality_patterns={
        "t1w": "*_T1w.nii.gz",
        "t2w": "*_T2w.nii.gz",
        "flair": "*_FLAIR.nii.gz",
        "bold": "*_bold.nii.gz",
        "dwi": "*_dwi.nii.gz",
        "sbref": "*_sbref.nii.gz",
        "lesion": "*_desc-lesion_mask.nii.gz",
    },
)

# Backward compat alias
EXPECTED_COUNTS = ARC_VALIDATION_CONFIG.expected_counts

def validate_arc_download(
    bids_root: Path,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """Convenience wrapper for ARC validation."""
    return validate_dataset(
        bids_root, ARC_VALIDATION_CONFIG,
        run_bids_validator=run_bids_validator,
        nifti_sample_size=nifti_sample_size,
        tolerance=tolerance,
    )
```

### Step 4: Create `isles24.py`

```python
# src/bids_hub/validation/isles24.py
"""ISLES24 dataset validation."""

from pathlib import Path
from .base import DatasetValidationConfig, ValidationResult, validate_dataset

# From Zenodo v7 / ISLES24 challenge
ISLES24_VALIDATION_CONFIG = DatasetValidationConfig(
    name="isles24",
    expected_counts={
        "subjects": 149,
        "ncct": 149,
        "cta": 149,
        "ctp": 140,        # ~94% have CTP
        "dwi": 149,
        "adc": 149,
        "lesion_mask": 149,
        "tmax": 140,
        "mtt": 140,
        "cbf": 140,
        "cbv": 140,
        "lvo_mask": 100,   # Optional (~67%)
        "cow_mask": 100,   # Optional (~67%)
    },
    required_files=[
        "clinical_data-description.xlsx",  # NOTE: NOT participants.tsv!
    ],
    modality_patterns={
        "ncct": "*_ncct.nii.gz",
        "cta": "*_cta.nii.gz",
        "tmax": "*_tmax.nii.gz",
        "dwi": "*_dwi.nii.gz",
        "lesion": "*_lesion-msk.nii.gz",
    },
)

def validate_isles24_download(
    bids_root: Path,
    nifti_sample_size: int = 10,
    tolerance: float = 0.1,  # 10% tolerance for optional modalities
) -> ValidationResult:
    """Convenience wrapper for ISLES24 validation."""
    return validate_dataset(
        bids_root, ISLES24_VALIDATION_CONFIG,
        nifti_sample_size=nifti_sample_size,
        tolerance=tolerance,
    )
```

### Step 5: Update `__init__.py`

```python
# src/bids_hub/validation/__init__.py
"""Validation module - re-exports for backward compatibility."""

from .base import (
    ValidationCheck,
    ValidationResult,
    DatasetValidationConfig,
    validate_dataset,
    check_zero_byte_files,  # Fast corruption detection
)
from .arc import (
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,  # Backward compat
    validate_arc_download,
)
from .isles24 import (
    ISLES24_VALIDATION_CONFIG,
    validate_isles24_download,
)

__all__ = [
    # Generic framework
    "ValidationCheck",
    "ValidationResult",
    "DatasetValidationConfig",
    "validate_dataset",
    "check_zero_byte_files",
    # ARC
    "ARC_VALIDATION_CONFIG",
    "EXPECTED_COUNTS",
    "validate_arc_download",
    # ISLES24
    "ISLES24_VALIDATION_CONFIG",
    "validate_isles24_download",
]
```

### Step 6: Update Imports

Files to update:
- `src/arc_bids/__init__.py`
- `src/arc_bids/cli.py`
- `scripts/validate_download.py`

### Step 7: Delete Old File

```bash
rm src/arc_bids/validation.py
```

---

## Tests

### Existing Tests (Move)

```bash
# Rename/move existing tests
mv tests/test_validation.py tests/validation/test_arc.py
```

### New Tests

```python
# tests/validation/test_base.py
def test_validation_check_creation(): ...
def test_validation_result_all_passed_true(): ...
def test_validation_result_all_passed_false(): ...
def test_validation_result_summary_format(): ...
def test_check_nifti_integrity_valid(): ...
def test_check_nifti_integrity_corrupt(): ...

# tests/validation/test_isles24.py
def test_validate_isles24_download_valid(synthetic_isles24_root): ...
def test_validate_isles24_download_missing_modality(): ...
def test_validate_isles24_tolerance(): ...
```

---

## CLI Update

Add `isles24 validate` subcommand:

```python
# src/arc_bids/cli.py

@isles_app.command("validate")
def validate_isles(
    bids_root: Path = typer.Argument(...),
    sample_size: int = typer.Option(10),
    tolerance: float = typer.Option(0.1),
) -> None:
    """Validate an ISLES24 dataset download."""
    from .validation.isles24 import validate_isles24_download

    result = validate_isles24_download(bids_root, sample_size, tolerance)
    typer.echo(result.summary())

    if not result.all_passed:
        raise typer.Exit(code=1)
```

---

## Success Criteria

- [ ] `from arc_bids.validation import validate_arc_download` still works
- [ ] `from arc_bids.validation import validate_isles24_download` works
- [ ] `arc-bids validate` still works (ARC)
- [ ] `arc-bids isles24 validate` works (NEW)
- [ ] All existing tests pass
- [ ] New ISLES24 validation tests pass
- [ ] mypy passes
- [ ] ruff passes

---

## Next Phase

After validation refactor → Phase 03: Scripts Reorganization
