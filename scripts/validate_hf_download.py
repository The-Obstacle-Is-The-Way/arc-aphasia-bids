#!/usr/bin/env python3
"""
Validate HuggingFace download against OpenNeuro source.

This script performs round-trip validation to ensure the uploaded dataset
on HuggingFace Hub matches the original OpenNeuro BIDS source.

Usage:
    uv run python scripts/validate_hf_download.py

Requirements:
    - Original OpenNeuro data at: data/openneuro/ds004884/
    - HuggingFace authentication: huggingface-cli login
    - ~293 GB disk space for download cache
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from tqdm.auto import tqdm

from arc_bids.arc import build_arc_file_table

# Configuration
EXPECTED_SESSIONS = 902
BIDS_ROOT = Path("data/openneuro/ds004884")
HF_REPO = "hugging-science/arc-aphasia-bids"
SAMPLE_SIZE = 50  # Number of sessions to hash-check


def main() -> int:
    """Run validation checks and return exit code."""
    print("=" * 60)
    print("ARC-BIDS Round-Trip Validation")
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
    print("\n[1/4] Loading HuggingFace dataset (this may download ~293 GB)...")
    try:
        ds = load_dataset(HF_REPO, split="train")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return 1

    # Check 2: Record count
    print("\n[2/4] Verifying record count...")
    if len(ds) != EXPECTED_SESSIONS:
        print(f"❌ Record count mismatch: expected {EXPECTED_SESSIONS}, got {len(ds)}")
        return 1
    print(f"✅ Record count: {len(ds)} sessions")

    # Check 3: Build original file table and compare IDs
    print("\n[3/4] Comparing subject/session IDs...")
    print("Building original file table from BIDS source...")
    original_table = build_arc_file_table(BIDS_ROOT)

    downloaded_df = ds.to_pandas()
    original_ids = set(
        zip(
            original_table["subject_id"],
            original_table["session_id"],
            strict=True,
        )
    )
    downloaded_ids = set(
        zip(
            downloaded_df["subject_id"],
            downloaded_df["session_id"],
            strict=True,
        )
    )

    if original_ids != downloaded_ids:
        missing = original_ids - downloaded_ids
        extra = downloaded_ids - original_ids
        print("❌ ID mismatch!")
        if missing:
            print(f"   Missing from download: {len(missing)}")
        if extra:
            print(f"   Extra in download: {len(extra)}")
        return 1
    print("✅ All subject/session IDs match")

    # Check 4: Sample hash validation
    print(f"\n[4/4] Validating NIfTI hashes ({SAMPLE_SIZE} sessions)...")

    # CRITICAL: Switch to Arrow format to access raw bytes
    # (bypasses nibabel decoding which would lose original bytes)
    ds.set_format("arrow")

    sample_indices = list(range(0, len(ds), len(ds) // SAMPLE_SIZE))[:SAMPLE_SIZE]
    mismatches = 0
    checked = 0

    for idx in tqdm(sample_indices, desc="Hashing"):
        row = ds[idx]
        subject_id = str(row["subject_id"])
        session_id = str(row["session_id"])

        original_row = original_table[
            (original_table["subject_id"] == subject_id)
            & (original_table["session_id"] == session_id)
        ].iloc[0]

        # Validate T1w (single file)
        t1w_struct = row["t1w"].as_py()
        if t1w_struct and pd.notna(original_row["t1w"]) and "bytes" in t1w_struct:
            dl_hash = hashlib.sha256(t1w_struct["bytes"]).hexdigest()
            with open(original_row["t1w"], "rb") as f:
                orig_hash = hashlib.sha256(f.read()).hexdigest()

            if dl_hash != orig_hash:
                print(f"   ❌ Mismatch: {subject_id}/{session_id} T1w")
                mismatches += 1
            checked += 1

        # Validate BOLD (first run of list)
        bold_list = row["bold"].as_py()
        if bold_list and original_row["bold"]:
            dl_bold = bold_list[0]
            orig_bold_path = original_row["bold"][0]

            if dl_bold and "bytes" in dl_bold:
                dl_hash = hashlib.sha256(dl_bold["bytes"]).hexdigest()
                with open(orig_bold_path, "rb") as f:
                    orig_hash = hashlib.sha256(f.read()).hexdigest()

                if dl_hash != orig_hash:
                    print(f"   ❌ Mismatch: {subject_id}/{session_id} BOLD-run1")
                    mismatches += 1
                checked += 1

    if mismatches > 0:
        print(f"❌ {mismatches}/{checked} hash mismatches in sample")
        return 1
    print(f"✅ All {checked} sampled NIfTIs have matching hashes")

    # Success
    print("\n" + "=" * 60)
    print("✅ VALIDATION PASSED: Download matches source")
    print("=" * 60)
    print("\nThe HuggingFace dataset is verified to match the OpenNeuro source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
