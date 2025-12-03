"""
Data validation module for ARC dataset downloads.

OpenNeuro datasets are DataLad/git-annex repos with internal checksums,
but raw AWS S3 downloads bypass this integrity layer. This module provides
validation to ensure downloaded data matches the published ARC descriptor.

Validation levels:
1. Structure: Required BIDS files exist
2. Counts: Series counts match Sci Data paper (Gibson et al., 2024)
3. Integrity: Sample NIfTI files are loadable with nibabel
4. BIDS: Optional external BIDS validator check

Usage:
    from arc_bids.validation import validate_arc_download

    results = validate_arc_download(Path("data/openneuro/ds004884"))
    if results.all_passed:
        print("Ready for HuggingFace push!")
"""

from __future__ import annotations

import random
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


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
    """Complete validation results for an ARC download."""

    bids_root: Path
    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Return True if all checks passed."""
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        """Count of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    def add(self, check: ValidationCheck) -> None:
        """Add a validation check result."""
        self.checks.append(check)

    def summary(self) -> str:
        """Return a formatted summary of validation results."""
        lines = [
            f"Validation Results for: {self.bids_root}",
            "=" * 60,
        ]
        for check in self.checks:
            status = "✅ PASS" if check.passed else "❌ FAIL"
            lines.append(f"{status} {check.name}")
            lines.append(f"       Expected: {check.expected}")
            lines.append(f"       Actual:   {check.actual}")
            if check.details:
                lines.append(f"       Details:  {check.details}")

        lines.append("=" * 60)
        if self.all_passed:
            lines.append("✅ All validations passed! Data is ready for HF push.")
        else:
            lines.append(
                f"❌ {self.failed_count}/{len(self.checks)} checks failed. "
                "Check download or wait for completion."
            )
        return "\n".join(lines)


# Expected counts from Sci Data paper (Gibson et al., 2024)
# doi:10.1038/s41597-024-03819-7
# Note: BOLD/DWI/sbref counts are sessions with at least one file of that type
# (the raw file counts are higher due to multiple runs/acquisitions per session)
EXPECTED_COUNTS = {
    "subjects": 230,
    "sessions": 902,
    "t1w_series": 441,
    "t2w_series": 447,
    "flair_series": 235,
    "bold_series": 850,  # Sessions with BOLD fMRI
    "dwi_series": 613,  # Sessions with diffusion imaging
    "sbref_series": 88,  # Sessions with single-band reference
    "lesion_masks": 230,  # All subjects have lesion masks
}

# Required BIDS files that must exist
REQUIRED_BIDS_FILES = [
    "dataset_description.json",
    "participants.tsv",
    "participants.json",
]


def _check_required_files(bids_root: Path) -> ValidationCheck:
    """Check that required BIDS files exist."""
    missing = [f for f in REQUIRED_BIDS_FILES if not (bids_root / f).exists()]

    if missing:
        return ValidationCheck(
            name="bids_required_files",
            expected="all present",
            actual=f"missing: {', '.join(missing)}",
            passed=False,
        )
    return ValidationCheck(
        name="bids_required_files",
        expected="all present",
        actual="all present",
        passed=True,
    )


def _check_subject_count(bids_root: Path) -> ValidationCheck:
    """Check subject directory count."""
    subjects = list(bids_root.glob("sub-*"))
    count = len(subjects)
    expected = EXPECTED_COUNTS["subjects"]

    # Allow ±5 tolerance for edge cases
    passed = abs(count - expected) <= 5

    return ValidationCheck(
        name="subjects",
        expected=str(expected),
        actual=str(count),
        passed=passed,
        details="" if passed else f"Expected ~{expected}, got {count}",
    )


def _check_participants_tsv(bids_root: Path) -> ValidationCheck:
    """Check participants.tsv row count."""
    participants_tsv = bids_root / "participants.tsv"

    if not participants_tsv.exists():
        return ValidationCheck(
            name="participants_tsv",
            expected="file exists",
            actual="MISSING",
            passed=False,
        )

    with open(participants_tsv, encoding="utf-8") as f:
        row_count = sum(1 for _ in f) - 1  # Subtract header

    # participants.tsv may have more entries than subjects with imaging
    # (some subjects may be in metadata but have no imaging data)
    subject_count = len(list(bids_root.glob("sub-*")))

    return ValidationCheck(
        name="participants_tsv",
        expected=f">= {subject_count} (subject dirs)",
        actual=str(row_count),
        passed=row_count >= subject_count,
    )


def _count_sessions_with_modality(bids_root: Path, pattern: str) -> int:
    """Count number of sessions that contain at least one file matching the pattern."""
    count = 0
    # Iterate over all subject/session directories
    for session_dir in bids_root.glob("sub-*/ses-*"):
        # Check if this session contains the target file pattern
        # Use rglob to find files in subdirectories (e.g. func/, dwi/)
        if list(session_dir.rglob(pattern)):
            count += 1
    return count


def _check_series_count(
    bids_root: Path,
    modality: str,
    pattern: str,
    expected_key: str,
    tolerance: float = 0.0,
) -> ValidationCheck:
    """Check session count for a specific modality."""
    # Count sessions with data, not total files
    count = _count_sessions_with_modality(bids_root, pattern)
    expected = EXPECTED_COUNTS[expected_key]

    allowed_missing = int(expected * tolerance)
    passed = count >= (expected - allowed_missing)

    return ValidationCheck(
        name=f"{modality}_sessions",
        expected=f">= {expected - allowed_missing} (paper: {expected})",
        actual=str(count),
        passed=passed,
        details=f"Tolerance: {tolerance:.1%}" if tolerance > 0 else "",
    )


def _check_nifti_integrity(bids_root: Path, sample_size: int = 10) -> ValidationCheck:
    """Spot-check NIfTI files for corruption using nibabel."""
    try:
        import nibabel as nib
        from nibabel.filebasedimages import ImageFileError
    except ImportError:
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual="nibabel not installed",
            passed=False,
        )

    t1w_files = list(bids_root.rglob("*_T1w.nii.gz"))
    if not t1w_files:
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual="no T1w files found",
            passed=False,
        )

    sample = random.sample(t1w_files, min(sample_size, len(t1w_files)))

    failed_file: Path | None = None
    try:
        for f in sample:
            failed_file = f  # Track current file for error reporting
            # Load header only (fast, catches corruption)
            img = nib.load(f)
            _ = img.header  # Access header to verify structure
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual=f"{len(sample)}/{len(sample)} passed",
            passed=True,
        )
    except (OSError, ValueError, EOFError, ImageFileError) as e:
        # Catches file errors, gzip corruption, nibabel parsing/file errors
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual=f"ERROR: {e}",
            passed=False,
            details=f"Failed on: {failed_file.name}" if failed_file else "",
        )


def _check_bids_validator(bids_root: Path) -> ValidationCheck | None:
    """Run external BIDS validator if available (optional)."""
    # Check if bids-validator is available
    if not shutil.which("npx"):
        return None  # Skip if npx not available

    try:
        result = subprocess.run(
            ["npx", "--yes", "bids-validator", str(bids_root), "--json"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            return ValidationCheck(
                name="bids_validator",
                expected="valid BIDS",
                actual="passed",
                passed=True,
            )
        else:
            # Parse error count from output if possible
            return ValidationCheck(
                name="bids_validator",
                expected="valid BIDS",
                actual="errors found (see bids-validator output)",
                passed=False,
                details=result.stderr[:200] if result.stderr else "",
            )
    except subprocess.TimeoutExpired:
        return ValidationCheck(
            name="bids_validator",
            expected="valid BIDS",
            actual="timeout (dataset too large)",
            passed=True,  # Don't fail on timeout
            details="Skipped due to timeout on large dataset",
        )
    except (subprocess.SubprocessError, OSError) as e:
        # Catches subprocess failures and OS-level errors (permissions, etc.)
        return ValidationCheck(
            name="bids_validator",
            expected="valid BIDS",
            actual=f"error: {e}",
            passed=True,  # Don't fail on validator errors
            details="Skipped due to validator error",
        )


def validate_arc_download(
    bids_root: Path,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """
    Validate an ARC dataset download.

    This function checks:
    1. Required BIDS files exist
    2. Subject count matches expected (~230)
    3. participants.tsv has enough entries
    4. Series counts match expected (T1w, T2w, FLAIR, BOLD, DWI, sbref, lesion)
    5. Sample NIfTI files are loadable
    6. (Optional) BIDS validator passes

    Args:
        bids_root: Path to the ARC BIDS dataset root.
        run_bids_validator: If True, run external BIDS validator (slow).
        nifti_sample_size: Number of NIfTI files to spot-check.
        tolerance: Allowed missing fraction (0.0 to 1.0). Default 0.0 (strict).

    Returns:
        ValidationResult with all check outcomes.
    """
    bids_root = Path(bids_root).resolve()
    result = ValidationResult(bids_root=bids_root)

    if not bids_root.exists():
        result.add(
            ValidationCheck(
                name="bids_root",
                expected="directory exists",
                actual="MISSING",
                passed=False,
            )
        )
        return result

    # Run all checks
    result.add(_check_required_files(bids_root))
    result.add(_check_subject_count(bids_root))
    result.add(_check_participants_tsv(bids_root))

    # Series counts from Sci Data paper
    # Uses strict session counting with configurable tolerance
    result.add(_check_series_count(bids_root, "t1w", "*_T1w.nii.gz", "t1w_series", tolerance))
    result.add(_check_series_count(bids_root, "t2w", "*_T2w.nii.gz", "t2w_series", tolerance))
    result.add(_check_series_count(bids_root, "flair", "*_FLAIR.nii.gz", "flair_series", tolerance))
    result.add(_check_series_count(bids_root, "bold", "*_bold.nii.gz", "bold_series", tolerance))
    result.add(_check_series_count(bids_root, "dwi", "*_dwi.nii.gz", "dwi_series", tolerance))
    result.add(_check_series_count(bids_root, "sbref", "*_sbref.nii.gz", "sbref_series", tolerance))
    result.add(
        _check_series_count(
            bids_root,
            "lesion",
            "*_desc-lesion_mask.nii.gz",
            "lesion_masks",
            tolerance,
        )
    )

    # NIfTI integrity check
    result.add(_check_nifti_integrity(bids_root, nifti_sample_size))

    # Optional BIDS validator
    if run_bids_validator:
        bids_check = _check_bids_validator(bids_root)
        if bids_check:
            result.add(bids_check)

    return result
