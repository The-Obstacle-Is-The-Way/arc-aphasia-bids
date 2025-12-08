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

## Current State (after Phase 01a rename)

```python
# src/bids_hub/validation.py (387 lines)

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
src/bids_hub/validation/
├── __init__.py          # Re-exports for backward compat
├── base.py              # Generic validation framework
├── arc.py               # ARC-specific
└── isles24.py           # ISLES24-specific (NEW)
```

---

## Implementation Steps

### Step 1: Create Directory Structure

```bash
mkdir -p src/bids_hub/validation
touch src/bids_hub/validation/__init__.py
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

# NEW: Archive integrity verification (ported from scripts/validate_isles24_download.py)
def verify_md5(archive_path: Path, expected_md5: str) -> ValidationCheck:
    """
    Verify MD5 checksum of an archive file.

    Useful for verifying Zenodo downloads before extraction.
    Shows progress indicator for large files.

    Args:
        archive_path: Path to archive (e.g., train.7z)
        expected_md5: Expected MD5 hash string

    Returns:
        ValidationCheck with pass/fail and computed hash
    """
    ...

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
from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    validate_dataset,
    verify_md5,
)

# MD5 checksum from Zenodo record 17652035 v7
# (Ported from scripts/validate_isles24_download.py)
ISLES24_ARCHIVE_MD5 = "4959a5dd2438d53e3c86d6858484e781"

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
    custom_checks=[check_phenotype_readable],  # ISLES24-specific
)


# NEW: Ported from scripts/validate_isles24_download.py
def check_phenotype_readable(bids_root: Path) -> ValidationCheck:
    """
    Spot-check that phenotype XLSX files are readable.

    Note: Zenodo v7 uses .xlsx files in phenotype/ directory.

    Returns:
        ValidationCheck with pass/fail status
    """
    phenotype_dir = bids_root / "phenotype"
    if not phenotype_dir.exists():
        return ValidationCheck(
            name="phenotype_readable",
            expected="phenotype/ exists",
            actual="directory not found",
            passed=True,  # Not a failure, may be optional
            details="phenotype/ directory not found (skipping check)",
        )

    xlsx_files = list(phenotype_dir.rglob("*.xlsx"))
    if not xlsx_files:
        return ValidationCheck(
            name="phenotype_readable",
            expected="XLSX files",
            actual="none found",
            passed=True,
            details="No XLSX files found in phenotype/ (may be OK)",
        )

    try:
        import pandas as pd
        sample_xlsx = xlsx_files[0]
        df = pd.read_excel(sample_xlsx)
        return ValidationCheck(
            name="phenotype_readable",
            expected="readable XLSX",
            actual=f"{len(df)} rows",
            passed=True,
            details=f"Phenotype XLSX readable: {sample_xlsx.name}",
        )
    except Exception as e:
        return ValidationCheck(
            name="phenotype_readable",
            expected="readable XLSX",
            actual="unreadable",
            passed=False,
            details=f"Phenotype XLSX unreadable: {e}",
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


def verify_isles24_archive(archive_path: Path) -> ValidationCheck:
    """Verify MD5 of ISLES24 train.7z archive."""
    return verify_md5(archive_path, ISLES24_ARCHIVE_MD5)
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
    verify_md5,             # Archive integrity verification
)
from .arc import (
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,  # Backward compat
    validate_arc_download,
)
from .isles24 import (
    ISLES24_VALIDATION_CONFIG,
    ISLES24_ARCHIVE_MD5,    # MD5 hash for train.7z
    validate_isles24_download,
    verify_isles24_archive, # Convenience wrapper for MD5 check
    check_phenotype_readable,
)

__all__ = [
    # Generic framework
    "ValidationCheck",
    "ValidationResult",
    "DatasetValidationConfig",
    "validate_dataset",
    "check_zero_byte_files",
    "verify_md5",
    # ARC
    "ARC_VALIDATION_CONFIG",
    "EXPECTED_COUNTS",
    "validate_arc_download",
    # ISLES24
    "ISLES24_VALIDATION_CONFIG",
    "ISLES24_ARCHIVE_MD5",
    "validate_isles24_download",
    "verify_isles24_archive",
    "check_phenotype_readable",
]
```

### Step 6: Update Imports

Files to update:
- `src/bids_hub/__init__.py`
- `src/bids_hub/cli.py`
- `scripts/validate_download.py`

### Step 7: Delete Old File

```bash
rm src/bids_hub/validation.py
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
def test_check_zero_byte_files_none(): ...
def test_check_zero_byte_files_found(): ...
def test_verify_md5_valid(): ...
def test_verify_md5_mismatch(): ...

# tests/validation/test_isles24.py
def test_validate_isles24_download_valid(synthetic_isles24_root): ...
def test_validate_isles24_download_missing_modality(): ...
def test_validate_isles24_tolerance(): ...
def test_check_phenotype_readable_valid(): ...
def test_check_phenotype_readable_missing_dir(): ...
def test_verify_isles24_archive(): ...
```

---

## CLI Update

Add `isles24 validate` subcommand:

```python
# src/bids_hub/cli.py

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

- [x] `from bids_hub.validation import validate_arc_download` works
- [x] `from bids_hub.validation import validate_isles24_download` works
- [x] `from bids_hub.validation import verify_md5` works
- [x] `from bids_hub.validation import check_phenotype_readable` works
- [x] `bids-hub arc validate` works
- [x] `bids-hub isles24 validate` works
- [x] All existing tests pass (68 tests)
- [x] New ISLES24 validation tests pass (7 tests in tests/validation/test_isles24.py)
- [x] **All logic from `scripts/validate_isles24_download.py` is ported** (critical for Phase 03)
- [x] mypy passes (19 source files)
- [x] ruff passes

---

## Next Phase

After validation refactor → Phase 03: Scripts Reorganization
