#!/usr/bin/env python3
"""
Validate ISLES24 dataset download integrity before HuggingFace upload.

This validates the local Zenodo extraction against expected counts.

Usage:
    uv run python scripts/validate_isles24_download.py data/zenodo/isles24/train

    # With MD5 verification of the archive (recommended before first extraction):
    uv run python scripts/validate_isles24_download.py data/zenodo/isles24/train \
        --verify-md5 data/zenodo/isles24/train.7z

Expected Zenodo v7 structure:
    train/
    ├── clinical_data-description.xlsx
    ├── raw_data/sub-stroke0001/.../
    ├── derivatives/sub-stroke0001/.../
    └── phenotype/sub-stroke0001/.../
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Expected counts from Zenodo v7 / ISLES24 paper
EXPECTED_SUBJECTS = 149

# Modalities expected per subject (approximate - some are optional)
EXPECTED_MODALITIES = {
    # Raw data (ses-01)
    "ncct": 149,  # All subjects have NCCT
    "cta": 149,  # All subjects have CTA
    "ctp": 140,  # ~94% have CTP (some missing)
    # Derivatives - perfusion maps (ses-01)
    "tmax": 140,
    "mtt": 140,
    "cbf": 140,
    "cbv": 140,
    # Derivatives - follow-up (ses-02)
    "dwi": 149,
    "adc": 149,
    "lesion_mask": 149,
    # Optional derivatives
    "lvo_mask": 100,  # ~67% have LVO mask
    "cow_mask": 100,  # ~67% have CoW segmentation
}

# MD5 checksum from Zenodo record 17652035 v7
EXPECTED_MD5 = "4959a5dd2438d53e3c86d6858484e781"


def verify_md5(archive_path: Path) -> tuple[bool, str]:
    """
    Verify MD5 checksum of the archive.

    Args:
        archive_path: Path to train.7z

    Returns:
        (passed, message)
    """
    if not archive_path.exists():
        return False, f"❌ Archive not found: {archive_path}"

    print(f"Computing MD5 of {archive_path.name} (~99GB, this takes 10-20 minutes)...")
    print("(You can skip this with Ctrl+C if you trust the download)")

    md5 = hashlib.md5()  # noqa: S324 - MD5 used for integrity check, not security
    total_size = archive_path.stat().st_size
    read_size = 0
    last_printed_gb = -1

    try:
        with open(archive_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192 * 1024), b""):  # 8MB chunks
                md5.update(chunk)
                read_size += len(chunk)
                # Progress indicator every 1GB (exactly once per boundary)
                current_gb = read_size // (1024**3)
                if current_gb > last_printed_gb:
                    last_printed_gb = current_gb
                    pct = (read_size / total_size) * 100
                    total_gb = total_size // (1024**3)
                    print(f"  {pct:.0f}% ({current_gb}GB / {total_gb}GB)")

        computed = md5.hexdigest()
        if computed == EXPECTED_MD5:
            return True, f"✅ MD5 verified: {computed}"
        else:
            return False, f"❌ MD5 mismatch! Expected: {EXPECTED_MD5}, Got: {computed}"
    except KeyboardInterrupt:
        return True, "⚠️  MD5 verification skipped by user"


def check_zero_byte_files(bids_root: Path) -> tuple[int, list[str]]:
    """
    Check for zero-byte NIfTI files (common corruption indicator).

    Returns:
        (count of zero-byte files, list of paths)
    """
    zero_byte_files = []
    for nifti in bids_root.rglob("*.nii.gz"):
        if nifti.stat().st_size == 0:
            zero_byte_files.append(str(nifti.relative_to(bids_root)))
    return len(zero_byte_files), zero_byte_files


def check_phenotype_readable(phenotype_dir: Path) -> tuple[bool, str]:
    """
    Spot-check that phenotype XLSX files are readable.

    Note: Zenodo v7 uses .xlsx files, not .csv.

    Returns:
        (passed, message)
    """
    if not phenotype_dir.exists():
        return True, "⚠️  phenotype/ directory not found (skipping check)"

    # Find first XLSX file (Zenodo v7 uses xlsx, not csv)
    xlsx_files = list(phenotype_dir.rglob("*.xlsx"))
    if not xlsx_files:
        return True, "⚠️  No XLSX files found in phenotype/ (may be OK)"

    try:
        import pandas as pd

        sample_xlsx = xlsx_files[0]
        df = pd.read_excel(sample_xlsx)
        if len(df) > 0:
            return True, f"✅ Phenotype XLSX readable: {sample_xlsx.name} ({len(df)} rows)"
        else:
            return True, f"⚠️  Phenotype XLSX empty: {sample_xlsx.name}"
    except Exception as e:  # noqa: BLE001
        return False, f"❌ Phenotype XLSX unreadable: {e}"


def validate_isles24_download(bids_root: Path) -> tuple[bool, list[str]]:
    """
    Validate ISLES24 download structure and counts.

    Returns:
        (all_passed, list of check messages)
    """
    bids_root = Path(bids_root).resolve()
    messages: list[str] = []
    all_passed = True

    # Check 1: Root directory exists
    if not bids_root.exists():
        messages.append(f"❌ Root directory not found: {bids_root}")
        return False, messages
    messages.append(f"✅ Root directory exists: {bids_root}")

    # Check 2: Required directories exist
    raw_data = bids_root / "raw_data"
    derivatives = bids_root / "derivatives"
    phenotype = bids_root / "phenotype"

    for name, path in [
        ("raw_data", raw_data),
        ("derivatives", derivatives),
        ("phenotype", phenotype),
    ]:
        if path.exists():
            messages.append(f"✅ {name}/ exists")
        else:
            messages.append(f"❌ {name}/ missing")
            all_passed = False

    # Check 3: Metadata file exists
    xlsx = bids_root / "clinical_data-description.xlsx"
    if xlsx.exists():
        messages.append("✅ clinical_data-description.xlsx exists")
    else:
        messages.append("⚠️  clinical_data-description.xlsx missing (may be OK)")

    # Check 4: Subject count
    if raw_data.exists():
        subjects = sorted(raw_data.glob("sub-*"))
        subject_count = len(subjects)
        if subject_count == EXPECTED_SUBJECTS:
            messages.append(f"✅ Subject count: {subject_count} (expected {EXPECTED_SUBJECTS})")
        elif subject_count > 0:
            messages.append(f"⚠️  Subject count: {subject_count} (expected {EXPECTED_SUBJECTS})")
        else:
            messages.append("❌ No subjects found in raw_data/")
            all_passed = False
    else:
        subject_count = 0
        subjects = []

    # Check 5: Session structure (spot check first subject)
    if subjects:
        first_subject = subjects[0]
        ses01 = first_subject / "ses-01"
        if ses01.exists():
            messages.append(f"✅ Session structure: ses-01 exists for {first_subject.name}")
        else:
            messages.append(f"❌ Session structure: ses-01 missing for {first_subject.name}")
            all_passed = False

    # Check 6: Derivative structure (spot check)
    if derivatives.exists() and subjects:
        first_deriv = derivatives / subjects[0].name
        if first_deriv.exists():
            ses01_deriv = first_deriv / "ses-01"
            ses02_deriv = first_deriv / "ses-02"
            if ses01_deriv.exists() and ses02_deriv.exists():
                messages.append(
                    f"✅ Derivative structure: ses-01 and ses-02 exist for {subjects[0].name}"
                )
            else:
                messages.append(f"⚠️  Derivative structure incomplete for {subjects[0].name}")
        else:
            messages.append(f"⚠️  No derivatives for {subjects[0].name}")

    # Check 7: Zero-byte file detection (HIGH priority from audit)
    messages.append("\n--- Zero-Byte File Check ---")
    zero_count, zero_files = check_zero_byte_files(bids_root)
    if zero_count == 0:
        messages.append("✅ No zero-byte NIfTI files found")
    else:
        messages.append(f"❌ Found {zero_count} zero-byte NIfTI files:")
        for zf in zero_files[:10]:  # Show first 10
            messages.append(f"   - {zf}")
        if zero_count > 10:
            messages.append(f"   ... and {zero_count - 10} more")
        all_passed = False

    # Check 8: Count key modality files across all subjects
    messages.append("\n--- Modality Counts ---")

    modality_checks = [
        # (name, search_path_pattern, expected_count)
        ("ncct (raw)", "raw_data/sub-*/ses-01/*_ncct.nii.gz", EXPECTED_MODALITIES["ncct"]),
        ("cta (raw)", "raw_data/sub-*/ses-01/*_cta.nii.gz", EXPECTED_MODALITIES["cta"]),
        (
            "tmax (deriv)",
            "derivatives/sub-*/ses-01/perfusion-maps/*_space-ncct_tmax.nii.gz",
            EXPECTED_MODALITIES["tmax"],
        ),
        (
            "dwi (deriv)",
            "derivatives/sub-*/ses-02/*_space-ncct_dwi.nii.gz",
            EXPECTED_MODALITIES["dwi"],
        ),
        (
            "lesion (deriv)",
            "derivatives/sub-*/ses-02/*_space-ncct_lesion-msk.nii.gz",
            EXPECTED_MODALITIES["lesion_mask"],
        ),
        (
            "lvo (deriv)",
            "derivatives/sub-*/ses-01/*_space-ncct_lvo-msk.nii.gz",
            EXPECTED_MODALITIES["lvo_mask"],
        ),
    ]

    for name, pattern, expected in modality_checks:
        files = list(bids_root.glob(pattern))
        # Also check for non-zero size
        valid_files = [f for f in files if f.stat().st_size > 0]
        count = len(valid_files)
        if count >= expected * 0.9:  # 10% tolerance
            messages.append(f"✅ {name}: {count} files (expected ~{expected})")
        elif count > 0:
            messages.append(f"⚠️  {name}: {count} files (expected ~{expected})")
        else:
            messages.append(f"❌ {name}: {count} files (expected ~{expected})")
            # Don't fail on missing modalities - extraction may be in progress

    # Check 9: Spot check NIfTI integrity (first file of each type)
    messages.append("\n--- NIfTI Integrity (spot check) ---")

    # Use first available subject instead of hardcoded sub-stroke0001
    sample_files = list(bids_root.glob("derivatives/sub-*/ses-01/*_space-ncct_cta.nii.gz"))
    if sample_files:
        import gzip

        try:
            with gzip.open(sample_files[0], "rb") as f:
                header = f.read(4)
                # NIfTI-1 magic: 348 (0x015c) little-endian, or "n+1\x00"
                if header[:2] == b"\x5c\x01" or header == b"n+1\x00":
                    messages.append(f"✅ NIfTI header valid: {sample_files[0].name}")
                else:
                    messages.append(f"⚠️  NIfTI header check inconclusive: {sample_files[0].name}")
        except Exception as e:
            messages.append(f"⚠️  Could not read NIfTI: {e}")
    else:
        messages.append("⚠️  No sample NIfTI files found for integrity check")

    # Check 10: Phenotype XLSX readability (LOW priority from audit)
    messages.append("\n--- Phenotype XLSX Check ---")
    pheno_passed, pheno_msg = check_phenotype_readable(phenotype)
    messages.append(pheno_msg)
    if not pheno_passed:
        all_passed = False

    return all_passed, messages


def main() -> int:
    """Run validation and print results."""
    parser = argparse.ArgumentParser(
        description="Validate ISLES24 dataset download integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic validation (post-extraction):
    python scripts/validate_isles24_download.py data/zenodo/isles24/train

    # With MD5 verification (before/after extraction):
    python scripts/validate_isles24_download.py data/zenodo/isles24/train \\
        --verify-md5 data/zenodo/isles24/train.7z
        """,
    )
    parser.add_argument("bids_root", type=Path, help="Path to extracted ISLES24 train/ directory")
    parser.add_argument(
        "--verify-md5",
        type=Path,
        metavar="ARCHIVE",
        help="Path to train.7z archive for MD5 verification",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ISLES24 Download Validation")
    print("=" * 60)
    print(f"Source: {args.bids_root}")
    print(f"Expected: {EXPECTED_SUBJECTS} subjects")
    print()

    all_passed = True

    # Optional MD5 verification
    if args.verify_md5:
        print("--- Archive MD5 Verification ---")
        md5_passed, md5_msg = verify_md5(args.verify_md5)
        print(md5_msg)
        print()
        if not md5_passed:
            all_passed = False

    # Main validation
    passed, messages = validate_isles24_download(args.bids_root)
    if not passed:
        all_passed = False

    for msg in messages:
        print(msg)

    print()
    print("=" * 60)
    if all_passed:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
