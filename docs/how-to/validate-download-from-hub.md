# How to Validate Downloaded Data from HuggingFace Hub

> **Problem**: Data was uploaded to HuggingFace Hub, but how do I verify the download matches the original source?
> **Solution**: Round-trip validation - download from HF, compare to OpenNeuro source, verify byte-level integrity

---

## Why Round-Trip Validation Matters

Professional data engineering requires verifying data integrity after transfers. Even with checksums and robust upload processes, you should validate that:

1. All records transferred correctly (902 sessions)
2. Metadata columns match exactly (subject_id, session_id, clinical data)
3. NIfTI byte content is identical (not corrupted or truncated)
4. NIfTI headers and voxel data are scientifically valid

This is especially critical for neuroimaging data where silent corruption can invalidate research results.

---

## Directory Structure

Keep source and downloaded data separate for comparison:

```text
data/
├── openneuro/ds004884/           # Original BIDS source (OpenNeuro)
└── huggingface/arc-aphasia-bids/ # Downloaded from HuggingFace Hub
```

---

## Step 1: Download from HuggingFace Hub

```python
from datasets import load_dataset
from pathlib import Path

# Download the dataset (this may take a while for 293 GB)
ds = load_dataset(
    "hugging-science/arc-aphasia-bids",
    split="train",
    # verification_mode="all_checks",  # Enable for checksum verification
)

print(f"Downloaded {len(ds)} records")
# Expected: 902 sessions
```

**Note**: The `verification_mode="all_checks"` parameter enables HuggingFace's built-in SHA256 checksum verification during download.

---

## Step 2: Verify Record Count

```python
EXPECTED_SESSIONS = 902

if len(ds) != EXPECTED_SESSIONS:
    raise ValueError(f"Expected {EXPECTED_SESSIONS} sessions, got {len(ds)}")

print(f"✅ Record count matches: {len(ds)} sessions")
```

---

## Step 3: Verify Metadata Columns

```python
import pandas as pd
from pathlib import Path

# Load the original file table (if you saved it during upload)
# Or rebuild from BIDS source
from arc_bids.arc import build_arc_file_table

bids_root = Path("data/openneuro/ds004884")
original_table = build_arc_file_table(bids_root)

# Convert HF dataset to DataFrame for comparison
downloaded_df = ds.to_pandas()

# Compare subject/session IDs
original_ids = set(zip(original_table["subject_id"], original_table["session_id"]))
downloaded_ids = set(zip(downloaded_df["subject_id"], downloaded_df["session_id"]))

missing = original_ids - downloaded_ids
extra = downloaded_ids - original_ids

if missing:
    print(f"❌ Missing sessions: {len(missing)}")
    print(missing)
elif extra:
    print(f"❌ Extra sessions: {len(extra)}")
else:
    print("✅ All subject/session IDs match")
```

---

## Step 4: Verify NIfTI Byte Integrity

Compare a sample of NIfTI files by computing checksums.

**Critical**: We must access the raw bytes stored in the Parquet file *before* they are decoded into `nibabel` objects. We do this by switching the dataset format to `arrow`.

```python
import hashlib
from tqdm.auto import tqdm

def compute_nifti_hash(nifti_struct: dict) -> str:
    """Compute SHA256 hash of NIfTI byte content from HF struct."""
    if not nifti_struct or "bytes" not in nifti_struct:
        return None
    return hashlib.sha256(nifti_struct["bytes"]).hexdigest()

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file on disk."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# Switch to Arrow format to access raw bytes (bypassing nibabel decoding)
ds.set_format("arrow")

# Sample validation
sample_size = 50
sample_indices = list(range(0, len(ds), len(ds) // sample_size))[:sample_size]

mismatches = []
for idx in tqdm(sample_indices, desc="Validating NIfTI hashes"):
    # Get row as Arrow scalar, convert to Python dict
    row = ds[idx]
    subject_id = str(row["subject_id"])
    session_id = str(row["session_id"])

    # Get original file path from BIDS source
    original_row = original_table[
        (original_table["subject_id"] == subject_id) &
        (original_table["session_id"] == session_id)
    ].iloc[0]

    # 1. Validate T1w (Single File)
    t1w_struct = row["t1w"].as_py()
    if t1w_struct and pd.notna(original_row["t1w"]):
        downloaded_hash = compute_nifti_hash(t1w_struct)
        original_hash = compute_file_hash(Path(original_row["t1w"]))

        if downloaded_hash != original_hash:
            mismatches.append(f"{subject_id}/{session_id} [T1w]")

    # 2. Validate BOLD (List of Files)
    bold_list = row["bold"].as_py() # List of structs
    original_bolds = original_row["bold"] # List of paths

    if bold_list and original_bolds:
        # Check first run as sample
        if len(bold_list) > 0 and len(original_bolds) > 0:
            dl_hash = compute_nifti_hash(bold_list[0])
            orig_hash = compute_file_hash(Path(original_bolds[0]))

            if dl_hash != orig_hash:
                 mismatches.append(f"{subject_id}/{session_id} [BOLD-run1]")

if mismatches:
    print(f"❌ Found {len(mismatches)} hash mismatches!")
    print(mismatches[:5])
else:
    print(f"✅ All {len(sample_indices)} sampled NIfTIs have matching hashes")

# Reset format for other operations
ds.reset_format()
```

---

## Step 5: Deep Validation with nibabel

For scientific validation, compare NIfTI headers and voxel data.

**Key insight**: In normal format (not arrow), `Nifti()` features are already decoded to `nibabel.Nifti1Image` objects. We can compare them directly against the original files.

```python
import nibabel as nib
import numpy as np

def compare_nifti_images(
    original: nib.Nifti1Image,
    downloaded: nib.Nifti1Image,
    atol: float = 1e-6,
) -> dict:
    """
    Compare two NIfTI images for equality.

    Returns dict with comparison results.
    """
    result = {
        "shapes_match": original.shape == downloaded.shape,
        "affines_match": np.allclose(original.affine, downloaded.affine, atol=atol),
        "dtypes_match": original.get_data_dtype() == downloaded.get_data_dtype(),
    }

    # Only compare data if shapes match (expensive operation)
    if result["shapes_match"]:
        original_data = original.get_fdata()
        downloaded_data = downloaded.get_fdata()
        result["data_match"] = np.allclose(original_data, downloaded_data, atol=atol)
    else:
        result["data_match"] = False

    return result

# Ensure we're in normal format (Nifti() decodes to nibabel objects)
ds.reset_format()

# Deep validation on a small sample
deep_sample_size = 5
for idx in range(deep_sample_size):
    row = ds[idx]

    # row["t1w"] is already a nibabel.Nifti1Image (decoded by Nifti() feature)
    if row["t1w"] is None:
        continue

    original_row = original_table[
        (original_table["subject_id"] == row["subject_id"]) &
        (original_table["session_id"] == row["session_id"])
    ].iloc[0]

    if pd.isna(original_row["t1w"]):
        continue

    # Load original from disk
    original_img = nib.load(original_row["t1w"])

    # row["t1w"] is already decoded to nibabel object
    downloaded_img = row["t1w"]

    comparison = compare_nifti_images(original_img, downloaded_img)

    if all(comparison.values()):
        print(f"✅ {row['subject_id']}/{row['session_id']} T1w: all checks passed")
    else:
        print(f"❌ {row['subject_id']}/{row['session_id']} T1w: {comparison}")
```

---

## Automated Validation Script

For convenience, here's a complete validation script:

```bash
# Save as scripts/validate_hf_download.py
uv run python scripts/validate_hf_download.py
```

```python
#!/usr/bin/env python3
"""Validate HuggingFace download against OpenNeuro source."""

import hashlib
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from tqdm.auto import tqdm

from arc_bids.arc import build_arc_file_table

EXPECTED_SESSIONS = 902
BIDS_ROOT = Path("data/openneuro/ds004884")
SAMPLE_SIZE = 50  # Number of NIfTIs to hash-check


def main() -> int:
    print("Loading HuggingFace dataset...")
    ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")

    # Check 1: Record count
    if len(ds) != EXPECTED_SESSIONS:
        print(f"❌ Record count mismatch: expected {EXPECTED_SESSIONS}, got {len(ds)}")
        return 1
    print(f"✅ Record count: {len(ds)} sessions")

    # Check 2: Build original file table
    print("Building original file table from BIDS source...")
    original_table = build_arc_file_table(BIDS_ROOT)

    # Check 3: Compare IDs
    downloaded_df = ds.to_pandas()
    original_ids = set(zip(original_table["subject_id"], original_table["session_id"]))
    downloaded_ids = set(zip(downloaded_df["subject_id"], downloaded_df["session_id"]))

    if original_ids != downloaded_ids:
        print(f"❌ ID mismatch: {len(original_ids - downloaded_ids)} missing")
        return 1
    print("✅ All subject/session IDs match")

    # Check 4: Sample hash validation
    print(f"Validating {SAMPLE_SIZE} NIfTI hashes (T1w & BOLD)...")

    # CRITICAL: Switch to Arrow format to access raw bytes
    ds.set_format("arrow")

    sample_indices = list(range(0, len(ds), len(ds) // SAMPLE_SIZE))[:SAMPLE_SIZE]
    mismatches = 0

    for idx in tqdm(sample_indices):
        row = ds[idx]
        subject_id = str(row["subject_id"])
        session_id = str(row["session_id"])

        original_row = original_table[
            (original_table["subject_id"] == subject_id) &
            (original_table["session_id"] == session_id)
        ].iloc[0]

        # Validate T1w
        t1w_struct = row["t1w"].as_py()
        if t1w_struct and pd.notna(original_row["t1w"]):
            if "bytes" in t1w_struct:
                dl_hash = hashlib.sha256(t1w_struct["bytes"]).hexdigest()
                with open(original_row["t1w"], "rb") as f:
                    orig_hash = hashlib.sha256(f.read()).hexdigest()

                if dl_hash != orig_hash:
                    print(f"Mismatch: {subject_id}/{session_id} T1w")
                    mismatches += 1

        # Validate BOLD (first run)
        bold_list = row["bold"].as_py()
        if bold_list and original_row["bold"]:
            # Check first run
            dl_bold = bold_list[0]
            orig_bold_path = original_row["bold"][0]

            if dl_bold and "bytes" in dl_bold:
                dl_hash = hashlib.sha256(dl_bold["bytes"]).hexdigest()
                with open(orig_bold_path, "rb") as f:
                    orig_hash = hashlib.sha256(f.read()).hexdigest()

                if dl_hash != orig_hash:
                     print(f"Mismatch: {subject_id}/{session_id} BOLD-run1")
                     mismatches += 1

    if mismatches > 0:
        print(f"❌ {mismatches} hash mismatches in sample")
        return 1
    print(f"✅ All {SAMPLE_SIZE} sampled sessions matched (T1w + BOLD)")

    print("\n" + "=" * 60)
    print("✅ VALIDATION PASSED: Download matches source")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Validation Levels Summary

| Level | What It Checks | Speed | Confidence |
|-------|----------------|-------|------------|
| 1. Record count | 902 sessions exist | Instant | Low |
| 2. Metadata match | subject_id, session_id | Fast | Medium |
| 3. Hash sample | SHA256 of ~50 NIfTIs | Minutes | High |
| 4. Full hash | SHA256 of all NIfTIs | Hours | Very High |
| 5. nibabel deep | Header + voxel data | Hours | Scientific |

For most use cases, **Levels 1-3** provide sufficient confidence. Use Level 4-5 for publication-quality validation.

---

## Related

- [Validate Before Upload](validate-before-upload.md) - Pre-upload validation
- [HuggingFace verification_mode](https://huggingface.co/docs/datasets/en/package_reference/loading_methods) - Built-in checksum verification
- [nibabel diff utilities](https://nipy.org/nibabel/reference/nibabel.cmdline.html) - NIfTI comparison tools
