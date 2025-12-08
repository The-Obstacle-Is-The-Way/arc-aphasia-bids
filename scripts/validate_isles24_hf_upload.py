#!/usr/bin/env python3
"""
Validate ISLES24 HuggingFace upload against Zenodo source.

This script performs round-trip validation to ensure the uploaded dataset
on HuggingFace Hub matches the original Zenodo extraction.

Usage:
    uv run python scripts/validate_isles24_hf_upload.py

Requirements:
    - Original Zenodo extraction at: data/zenodo/isles24/train/
    - HuggingFace authentication: huggingface-cli login
    - ~100 GB disk space for download cache
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm

from arc_bids.isles24 import build_isles24_file_table

# Configuration (per Zenodo v7)
EXPECTED_SUBJECTS = 149
BIDS_ROOT = Path("data/zenodo/isles24/train")
HF_REPO = "hugging-science/isles24-stroke"
SAMPLE_SIZE = 30  # Number of subjects to hash-check

# Modalities to validate (single NIfTI per subject)
MODALITIES_TO_CHECK = ["ncct", "cta", "tmax", "dwi", "lesion_mask"]


def main() -> int:
    """Run validation checks and return exit code."""
    print("=" * 60)
    print("ISLES24 HuggingFace Upload Validation")
    print("=" * 60)
    print(f"Source: {BIDS_ROOT}")
    print(f"Target: {HF_REPO}")
    print()

    # Verify source exists
    if not BIDS_ROOT.exists():
        print(f"❌ Source directory not found: {BIDS_ROOT}")
        return 1
    print(f"✅ Source directory exists: {BIDS_ROOT}")

    # Check 1: Load HuggingFace dataset
    print("\n[1/4] Loading HuggingFace dataset (this may download ~100 GB)...")
    try:
        ds = load_dataset(HF_REPO, split="train")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Failed to load dataset: {e}")
        return 1
    print(f"✅ Dataset loaded: {len(ds)} rows")

    # Check 2: Record count
    print("\n[2/4] Verifying record count...")
    if len(ds) != EXPECTED_SUBJECTS:
        print(f"❌ Record count mismatch: expected {EXPECTED_SUBJECTS}, got {len(ds)}")
        return 1
    print(f"✅ Record count: {len(ds)} subjects (expected {EXPECTED_SUBJECTS})")

    # Check 3: Build original file table and compare IDs
    print("\n[3/4] Comparing subject IDs...")
    print("Building original file table from Zenodo source...")
    original_table = build_isles24_file_table(BIDS_ROOT)

    # Extract IDs from HuggingFace dataset (memory-safe iteration)
    print("Extracting IDs from HuggingFace dataset...")
    downloaded_ids = set()
    for row in tqdm(ds, desc="Extracting IDs", total=len(ds)):
        downloaded_ids.add(row["subject_id"])

    original_ids = set(original_table["subject_id"])

    if original_ids != downloaded_ids:
        missing = original_ids - downloaded_ids
        extra = downloaded_ids - original_ids
        print("❌ ID mismatch!")
        if missing:
            print(f"   Missing from download: {len(missing)}")
            for m in list(missing)[:5]:
                print(f"      - {m}")
        if extra:
            print(f"   Extra in download: {len(extra)}")
            for ex in list(extra)[:5]:
                print(f"      - {ex}")
        return 1
    print(f"✅ All {len(original_ids)} subject IDs match")

    # Check 4: Sample hash validation
    print(f"\n[4/4] Validating NIfTI hashes ({SAMPLE_SIZE} subjects)...")

    # Switch to Arrow format to access raw bytes
    ds.set_format("arrow")

    sample_indices = list(range(0, len(ds), max(1, len(ds) // SAMPLE_SIZE)))[:SAMPLE_SIZE]
    mismatches = 0
    checked = 0

    for idx in tqdm(sample_indices, desc="Hashing"):
        row = ds[idx]
        subject_id = str(row["subject_id"])

        # Find matching row in original table
        filtered = original_table[original_table["subject_id"] == subject_id]
        if len(filtered) == 0:
            print(f"   ⚠️  Warning: {subject_id} not found in source")
            continue
        original_row = filtered.iloc[0]

        # Validate each modality
        for modality in MODALITIES_TO_CHECK:
            hf_data = row[modality].as_py()
            orig_path = original_row[modality]

            # Skip if either side is missing
            if not hf_data or not orig_path or "bytes" not in hf_data:
                continue

            # Compare hashes
            dl_hash = hashlib.sha256(hf_data["bytes"]).hexdigest()
            with open(orig_path, "rb") as f:
                orig_hash = hashlib.sha256(f.read()).hexdigest()

            if dl_hash != orig_hash:
                print(f"   ❌ Mismatch: {subject_id} {modality}")
                mismatches += 1
            checked += 1

    if mismatches > 0:
        print(f"❌ {mismatches}/{checked} hash mismatches in sample")
        return 1
    print(f"✅ All {checked} sampled NIfTIs have matching hashes")

    # Success
    print("\n" + "=" * 60)
    print("✅ VALIDATION PASSED: HuggingFace upload matches Zenodo source")
    print("=" * 60)
    print(f"\nDataset verified: {HF_REPO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
