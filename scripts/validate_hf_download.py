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

from bids_hub.arc import build_arc_file_table

# Configuration (per Scientific Data paper: Gibson et al., 2024)
EXPECTED_SESSIONS = 902
EXPECTED_SUBJECTS = 230
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

    # MEMORY-SAFE: Extract IDs by iterating, not loading entire dataset to pandas
    # (ds.to_pandas() would try to load 293GB into memory → OOM)
    print("Extracting IDs from HuggingFace dataset (memory-safe iteration)...")
    downloaded_ids = set()
    for row in tqdm(ds, desc="Extracting IDs", total=len(ds)):
        downloaded_ids.add((row["subject_id"], row["session_id"]))

    original_ids = set(
        zip(
            original_table["subject_id"],
            original_table["session_id"],
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

    # Optional: Verify subject count matches paper
    subject_count = len(original_table["subject_id"].unique())
    if subject_count != EXPECTED_SUBJECTS:
        print(f"⚠️  Warning: Expected {EXPECTED_SUBJECTS} subjects, found {subject_count}")

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
        # Extract scalars from Arrow ChunkedArray (not str() which returns array repr)
        subject_id = row["subject_id"].to_pylist()[0]
        session_id = row["session_id"].to_pylist()[0]

        # Defensive check: ensure we find the matching row
        filtered = original_table[
            (original_table["subject_id"] == subject_id)
            & (original_table["session_id"] == session_id)
        ]
        if len(filtered) == 0:
            print(f"   ⚠️  Warning: {subject_id}/{session_id} not found in source")
            continue
        original_row = filtered.iloc[0]

        # Validate T1w (single file)
        # Extract scalar from Arrow ChunkedArray (ChunkedArray has no .as_py())
        t1w_struct = row["t1w"].to_pylist()[0]
        if t1w_struct and pd.notna(original_row["t1w"]) and "bytes" in t1w_struct:
            dl_hash = hashlib.sha256(t1w_struct["bytes"]).hexdigest()
            with open(original_row["t1w"], "rb") as f:
                orig_hash = hashlib.sha256(f.read()).hexdigest()

            if dl_hash != orig_hash:
                print(f"   ❌ Mismatch: {subject_id}/{session_id} T1w")
                mismatches += 1
            checked += 1

        # Validate BOLD (first run of list)
        # Extract scalar from Arrow ChunkedArray (ChunkedArray has no .as_py())
        bold_list = row["bold"].to_pylist()[0]
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
