#!/usr/bin/env python3
"""
Test to prove/disprove huggingface/datasets#7894 using STANDARD push_to_hub

Bug claim: embed_table_storage crashes on sharded Sequence(Nifti())

This test:
1. Uses STANDARD ds.push_to_hub() - NO custom uploader
2. Uses Sequence(Nifti()) columns (bold, dwi, sbref)
3. See if it crashes

If it crashes: #7894 is PROVEN in library code (not just our custom code)
If it works: #7894 might be specific to our custom code
"""

import os
import sys
from pathlib import Path

# Check if we have the real dataset
BIDS_ROOT = Path("data/openneuro/ds004884")
if not BIDS_ROOT.exists():
    print(f"ERROR: Dataset not found at {BIDS_ROOT}")
    print("Download with:")
    print("  aws s3 sync --no-sign-request s3://openneuro.org/ds004884 \\")
    print("      data/openneuro/ds004884")
    sys.exit(1)

print("=" * 60)
print("TEST: Proving/Disproving #7894 with STANDARD push_to_hub")
print("=" * 60)
print()
print("Using STANDARD ds.push_to_hub() - no custom uploader")
print("Using Sequence(Nifti()) columns (bold, dwi, sbref)")
print()

# Import after checks (intentional - fail fast if dataset missing)
import pandas as pd  # noqa: E402
from datasets import Dataset, Features, Sequence, Value  # noqa: E402
from datasets.features import Nifti  # noqa: E402

# Full schema WITH Sequence(Nifti()) columns
FEATURES_WITH_SEQUENCE = Features(
    {
        "subject_id": Value("string"),
        "session_id": Value("string"),
        "t1w": Nifti(),
        "t2w": Nifti(),
        "flair": Nifti(),
        "bold": Sequence(Nifti()),  # SEQUENCE - this triggers #7894
        "dwi": Sequence(Nifti()),  # SEQUENCE
        "sbref": Sequence(Nifti()),  # SEQUENCE
        "lesion": Nifti(),
    }
)


def build_full_file_table(bids_root: Path) -> pd.DataFrame:
    """Build file table WITH Sequence columns."""
    rows = []

    for sub_dir in sorted(bids_root.glob("sub-*")):
        subject_id = sub_dir.name
        for ses_dir in sorted(sub_dir.glob("ses-*")):
            session_id = ses_dir.name

            anat_dir = ses_dir / "anat"
            func_dir = ses_dir / "func"
            dwi_dir = ses_dir / "dwi"
            deriv_dir = (
                bids_root / "derivatives" / "lesion_masks" / subject_id / session_id / "anat"
            )

            # Single Nifti columns
            t1w = list(anat_dir.glob("*_T1w.nii.gz")) if anat_dir.exists() else []
            t2w = list(anat_dir.glob("*_T2w.nii.gz")) if anat_dir.exists() else []
            flair = list(anat_dir.glob("*_FLAIR.nii.gz")) if anat_dir.exists() else []
            lesion = list(deriv_dir.glob("*_lesion.nii.gz")) if deriv_dir.exists() else []

            # SEQUENCE columns - multiple files per session
            bold = [str(p) for p in func_dir.glob("*_bold.nii.gz")] if func_dir.exists() else []
            dwi = [str(p) for p in dwi_dir.glob("*_dwi.nii.gz")] if dwi_dir.exists() else []
            sbref = [str(p) for p in func_dir.glob("*_sbref.nii.gz")] if func_dir.exists() else []

            rows.append(
                {
                    "subject_id": subject_id,
                    "session_id": session_id,
                    "t1w": str(t1w[0]) if t1w else None,
                    "t2w": str(t2w[0]) if t2w else None,
                    "flair": str(flair[0]) if flair else None,
                    "bold": bold,  # List of paths
                    "dwi": dwi,  # List of paths
                    "sbref": sbref,  # List of paths
                    "lesion": str(lesion[0]) if lesion else None,
                }
            )

    return pd.DataFrame(rows)


# Build file table
print("Building file table (WITH Sequence columns)...")
file_table = build_full_file_table(BIDS_ROOT)
print(f"  Rows: {len(file_table)}")
print(f"  Columns: {list(file_table.columns)}")

# Count Sequence entries
bold_count = sum(len(x) for x in file_table["bold"])
dwi_count = sum(len(x) for x in file_table["dwi"])
sbref_count = sum(len(x) for x in file_table["sbref"])
print(f"  BOLD files: {bold_count}")
print(f"  DWI files: {dwi_count}")
print(f"  SBRef files: {sbref_count}")
print()

# Create dataset
print("Creating dataset...")
ds = Dataset.from_pandas(file_table, preserve_index=False)
ds = ds.cast(FEATURES_WITH_SEQUENCE)
print(f"  Dataset: {ds}")
print()

# Test parameters
HF_REPO = os.environ.get("HF_REPO", "hugging-science/test-7894-standard")
NUM_SHARDS = len(file_table)

print(f"Target repo: {HF_REPO}")
print(f"Num shards: {NUM_SHARDS}")
print()

print("Starting upload with STANDARD push_to_hub...")
print("If it crashes at 0%: #7894 is PROVEN in library code")
print("If it works: #7894 might be specific to our custom code")
print()

# Use STANDARD push_to_hub - this is the test!
try:
    ds.push_to_hub(
        HF_REPO,
        num_shards=NUM_SHARDS,
        embed_external_files=True,
        private=True,
    )
    print()
    print("SUCCESS! Upload completed without crash.")
    print("RESULT: #7894 may NOT exist in standard library code")
    print("        (might be specific to our custom uploader)")
except Exception as e:
    print()
    print(f"CRASHED: {e}")
    print("RESULT: #7894 is PROVEN in standard library code")
