#!/usr/bin/env python3
"""
Reproduction script for huggingface/datasets#7894

Tests whether embed_table_storage crashes on sharded datasets
with Sequence() nested types.
"""

import sys
import tempfile
from pathlib import Path

import pyarrow as pa

print(f"Python: {sys.version}")
print(f"PyArrow: {pa.__version__}")

# Import after printing versions (in case import crashes)
import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402
from datasets import Dataset, Features, Sequence, Value  # noqa: E402
from datasets.features import Nifti  # noqa: E402
from datasets.table import embed_table_storage  # noqa: E402


# Create a minimal NIfTI file for testing
def create_test_nifti(path: Path) -> None:
    """Create a tiny valid NIfTI file."""
    data = np.zeros((2, 2, 2), dtype=np.float32)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, path)


# Test 1: Full dataset (should work)
print("\n--- Test 1: Full dataset with Sequence(Nifti()) ---")
with tempfile.TemporaryDirectory() as tmpdir:
    nifti_path = Path(tmpdir) / "test.nii.gz"
    create_test_nifti(nifti_path)

    features = Features(
        {
            "id": Value("string"),
            "images": Sequence(Nifti()),
        }
    )

    ds = Dataset.from_dict(
        {
            "id": ["a", "b"],
            "images": [[str(nifti_path)], []],  # One with file, one empty
        }
    ).cast(features)

    try:
        table = ds._data.table.combine_chunks()
        embedded = embed_table_storage(table)
        print("PASS: Full dataset embedding works")
    except Exception as e:
        print(f"FAIL: {e}")

# Test 2: Sharded dataset (this is where the bug occurs)
print("\n--- Test 2: Sharded dataset with Sequence(Nifti()) ---")
with tempfile.TemporaryDirectory() as tmpdir:
    nifti_path = Path(tmpdir) / "test.nii.gz"
    create_test_nifti(nifti_path)

    features = Features(
        {
            "id": Value("string"),
            "images": Sequence(Nifti()),
        }
    )

    ds = Dataset.from_dict(
        {
            "id": ["a", "b"],
            "images": [[str(nifti_path)], []],
        }
    ).cast(features)

    # Create a shard
    shard = ds.shard(num_shards=2, index=0, contiguous=True)

    try:
        shard_table = shard._data.table.combine_chunks()
        embedded = embed_table_storage(shard_table)
        print("PASS: Sharded dataset embedding works")
        print("\n*** BUG MAY BE FIXED IN THIS PYARROW VERSION ***")
    except Exception as e:
        print(f"FAIL: {e}")
        print("\n*** BUG CONFIRMED ***")

# Test 3: Sharded with pandas workaround (should always work)
print("\n--- Test 3: Sharded dataset WITH pandas workaround ---")
with tempfile.TemporaryDirectory() as tmpdir:
    nifti_path = Path(tmpdir) / "test.nii.gz"
    create_test_nifti(nifti_path)

    features = Features(
        {
            "id": Value("string"),
            "images": Sequence(Nifti()),
        }
    )

    ds = Dataset.from_dict(
        {
            "id": ["a", "b"],
            "images": [[str(nifti_path)], []],
        }
    ).cast(features)

    shard = ds.shard(num_shards=2, index=0, contiguous=True)

    # WORKAROUND: pandas round-trip
    shard_df = shard.to_pandas()
    fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
    fresh_shard = fresh_shard.cast(ds.features)

    try:
        table = fresh_shard._data.table.combine_chunks()
        embedded = embed_table_storage(table)
        print("PASS: Pandas workaround works")
    except Exception as e:
        print(f"FAIL: {e}")

print("\n--- Done ---")
