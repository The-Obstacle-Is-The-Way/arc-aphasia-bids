#!/usr/bin/env python3
"""
Reproduction script for huggingface/datasets#7894 - LARGER FILES

Tests with more realistic file sizes and multiple files per Sequence.
"""

import sys
import tempfile
from pathlib import Path

import pyarrow as pa

print(f"Python: {sys.version}")
print(f"PyArrow: {pa.__version__}")

# Import after printing versions
import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402
from datasets import Dataset, Features, Sequence, Value  # noqa: E402
from datasets.features import Nifti  # noqa: E402
from datasets.table import embed_table_storage  # noqa: E402


def create_test_nifti(path: Path, size: int = 64) -> None:
    """Create a NIfTI file with specified dimension (size^3 voxels)."""
    data = np.random.randn(size, size, size).astype(np.float32)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, path)
    print(f"  Created {path.name}: {path.stat().st_size / 1024:.1f} KB")


print("\n--- Creating test files ---")
with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)

    # Create multiple NIfTI files (64^3 = 262k voxels each, ~1MB compressed)
    files = []
    for i in range(4):
        p = tmp / f"test_{i}.nii.gz"
        create_test_nifti(p, size=64)
        files.append(str(p))

    features = Features(
        {
            "id": Value("string"),
            "images": Sequence(Nifti()),
        }
    )

    # More realistic: multiple rows, multiple files per row
    ds = Dataset.from_dict(
        {
            "id": ["a", "b", "c", "d"],
            "images": [
                [files[0], files[1]],  # 2 files
                [files[2]],  # 1 file
                [],  # empty
                [files[3]],  # 1 file
            ],
        }
    ).cast(features)

    print(f"\nDataset: {len(ds)} rows")

    # Test: Shard and embed
    print("\n--- Test: Sharded dataset with Sequence(Nifti()) ---")
    for shard_idx in range(2):
        print(f"\nShard {shard_idx}:")
        shard = ds.shard(num_shards=2, index=shard_idx, contiguous=True)
        print(f"  Rows in shard: {len(shard)}")

        try:
            shard_table = shard._data.table.combine_chunks()
            embedded = embed_table_storage(shard_table)
            print("  PASS: Embedding succeeded")
        except Exception as e:
            print(f"  FAIL: {e}")
            print("\n*** BUG CONFIRMED ***")
            sys.exit(1)

print("\n*** ALL TESTS PASSED - Bug may be fixed ***")
