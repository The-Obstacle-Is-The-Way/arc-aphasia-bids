# Reproducing huggingface/datasets#7894

**Bug:** `embed_table_storage` crashes (SIGKILL) on sharded datasets with `Sequence()` nested types

**Issue:** https://github.com/huggingface/datasets/issues/7894

---

## Environment (Tested & Confirmed Crash)

| Component | Version |
|-----------|---------|
| macOS | 26.0.1 (arm64) |
| Python | 3.13.5 |
| PyArrow | 22.0.0 |
| datasets | 4.4.2.dev0 (git main) |

---

## Quick Reproduction

### 1. Clone this branch

```bash
git clone -b sandbox/reproduce-bug-7894 \
    https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids.git
cd arc-aphasia-bids
```

### 2. Install dependencies

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv sync --all-extras
```

### 3. Download the ARC dataset (~273GB)

```bash
mkdir -p data/openneuro
aws s3 sync --no-sign-request \
    s3://openneuro.org/ds004884 \
    data/openneuro/ds004884
```

**Note:** This is 273GB and takes several hours. The dataset is from OpenNeuro: https://openneuro.org/datasets/ds004884

### 4. Run the upload (will crash)

```bash
uv run arc-bids build data/openneuro/ds004884 \
    --hf-repo YOUR_USERNAME/arc-test \
    --no-dry-run
```

### 5. Expected output

```
Casting the dataset: 100%|██████████| 902/902 [00:00<00:00, 82298.50 examples/s]
Uploading Shards:   0%|          | 0/902 [00:00<?, ?it/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown
```

**Exit code: 137 (SIGKILL)**

---

## What This Branch Contains

This branch is at commit `a1d9700` - BEFORE the pandas workaround fix.

The crash happens in `src/arc_bids/core.py` at:

```python
# Line 227-228 (NO pandas workaround)
table = shard._data.table
embedded_table = embed_table_storage(table)  # <-- CRASH HERE
```

The `embed_table_storage` function crashes when:
1. Dataset has `Sequence(Nifti())` columns (or likely `Sequence(Image())`, `Sequence(Audio())`)
2. Dataset is sharded with `ds.shard()`
3. Real data at scale (not reproducible with tiny synthetic files)

---

## The Fix (in main branch)

The workaround that allows upload to succeed:

```python
# Convert shard to pandas and back - breaks problematic Arrow references
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)

table = fresh_shard._data.table.combine_chunks()
embedded_table = embed_table_storage(table)  # <-- WORKS
```

See `main` branch for working implementation.

---

## Alternative: Reproduce with Standard `push_to_hub()`

To prove this is a library bug (not our custom code), you can also reproduce using standard `ds.push_to_hub()`:

```bash
# After downloading the dataset (step 3 above)
HF_REPO="YOUR_USERNAME/test-7894" uv run python test_prove_7894_standard.py
```

This script:
- Uses **standard `ds.push_to_hub()`** - no custom code
- Includes `Sequence(Nifti())` columns (bold, dwi, sbref)
- Crashes at 0% with same symptoms

**Output:**
```
Uploading the dataset shards:   0%|          | 0/902 [00:00<?, ? shards/s]
Map:   0%|          | 0/1 [00:00<?, ? examples/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects
```

This confirms the bug is in the datasets library's `.map(embed_table_storage)` code path, not just our custom uploader.

---

## Why Synthetic Tests Don't Reproduce This

We tested with small synthetic NIfTI files (2x2x2 voxels, 100 rows) - no crash.

The bug requires:
- **Real-scale data** (~273GB)
- **`Sequence()` nested types** with actual file paths
- **Sharding** via `ds.shard()`

This is why @lhoestq couldn't reproduce with "a nifti file I found online" - the bug is scale + structure dependent.

---

## Files in This Branch

| File | Purpose |
|------|---------|
| `src/arc_bids/core.py` | Contains the crash site (line 227-228) |
| `test_prove_7894_standard.py` | **Standard `push_to_hub()` reproduction** (crashes) |
| `test_pyarrow_bug.py` | Synthetic test (doesn't crash - too small) |
| `test_pyarrow_bug_large.py` | Larger synthetic test (still doesn't crash) |
| `REPRODUCE_BUG_7894.md` | This reproduction guide |

---

## Note on OOM Bug #7893

We also investigated **Issue #7893** (OOM during `push_to_hub`).
After extensive testing (uploading 625/902 shards successfully without memory growth), we concluded that #7893 **is NOT reproducible** when `free_memory=True` (default) is used.
The memory issues we originally observed were likely:
1. A misdiagnosis of this crash (Bug #7894)
2. Peak memory spikes during specific shard processing, not accumulation.

**Conclusion:** Bug #7894 (this crash) is the real issue. Bug #7893 is likely invalid.

---

## Contact

Repository: https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids
Issue: https://github.com/huggingface/datasets/issues/7894
