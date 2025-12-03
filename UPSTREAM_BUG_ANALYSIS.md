# Upstream Bug Analysis: HuggingFace Datasets + Nifti Embedding

**Status**: ACTIVE BUG - No known upstream fix
**Date**: 2025-12-02
**Severity**: P0 (Blocking)

---

## The Symptom

Upload crashes at "Uploading Shards: 0%" with exit code 137 (SIGKILL).
The semaphore leak warning is a SYMPTOM, not the cause.

```text
Uploading Shards:   0%|          | 0/902 [00:00<?, ?it/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects
```

---

## Root Cause Analysis

### Verified Facts

1. **Crash occurs in `embed_table_storage()`** (from `datasets.table`)
2. **Exit code 137 = SIGKILL** (typically OOM killer or hard crash)
3. **Crashes on FIRST shard** - not a memory accumulation issue
4. **Single row data structure**:
   - `Sequence(Nifti())` columns: `bold` (2 files, ~400MB), `dwi` (4 files, ~600MB)
   - Total per row: ~1-1.5 GB of NIfTI bytes to embed

### Technical Cause: PyArrow 2GB Binary Limit

The `Nifti` feature in `datasets` uses `pa.binary()` for storing bytes:

```python
# From datasets/features/nifti.py
pa_type: ClassVar[Any] = pa.struct({"bytes": pa.binary(), "path": pa.string()})
```

**`pa.binary()` has a hard 2GB limit per array.**

When embedding multiple large NIfTI files in `Sequence(Nifti())` columns:
- The total bytes can approach or exceed 2GB
- PyArrow crashes at C++ level (no Python traceback)
- Process receives SIGKILL

### Evidence

1. **Minimal test works**: Single Nifti column with one small file succeeds
2. **Full test crashes**: Row with `Sequence(Nifti())` containing multiple large files crashes
3. **PyArrow documentation**: `pa.large_binary()` exists specifically for >2GB data
4. **GitHub issues**:
   - [apache/arrow#1677](https://github.com/apache/arrow/issues/1677) - "Crash for categorical column when exceeds 2GB on write"
   - [StackOverflow](https://stackoverflow.com/questions/59125984/python-ray-pyarrow-lib-arrowinvalid-maximum-size-exceeded-2gb) - "Maximum size exceeded (2GB)"

---

## Related Upstream Issues

### HuggingFace Datasets

| Issue | Title | Status | Relevance |
|-------|-------|--------|-----------|
| [#6360](https://github.com/huggingface/datasets/issues/6360) | Sequence(Audio/Image) not embedded in push_to_hub | Closed (Feb 2024) | Same code path, different symptom |
| [#5672](https://github.com/huggingface/datasets/issues/5672) | Pushing dataset to hub crash | Open | Similar symptom |
| [#5990](https://github.com/huggingface/datasets/issues/5990) | Large dataset push hangs | Open | Related |

### Apache Arrow

| Issue | Title | Status |
|-------|-------|--------|
| [#1677](https://github.com/apache/arrow/issues/1677) | Crash when column exceeds 2GB | Fixed (Arrow 5.0+) |
| [#41306](https://github.com/apache/arrow/issues/41306) | Segfault when casting sliced binary array | Fixed (Arrow 17.0+) |

---

## Attempted Fixes

1. **Custom upload loop** - Fixed OOM accumulation from upstream bug
2. **`combine_chunks()`** - Forces contiguous memory, crash still occurs
3. **Direct Arrow table access** - Correct API usage, crash still occurs
4. **`pa.large_binary()` monkey-patch** - Tested, crash still occurs (NOT the issue)
5. **Pandas round-trip (WORKS!)** - Converting shard to pandas and back breaks the crash

---

## The Actual Root Cause

The issue is **NOT** the 2GB binary limit. Testing showed:
- Single `Nifti()` columns: embed OK
- `Sequence(Nifti())` columns from sharded dataset: CRASH

The crash happens in the `bold` column (a `Sequence(Nifti())`), even when it's an empty list.

The real issue is that `ds.shard()` (or `ds.select()`) creates an Arrow table view with
**internal state that causes `embed_table_storage` to crash** when processing
`Sequence(Nifti())` columns. The exact C++ bug in PyArrow/datasets is unclear.

**Proof**: Converting the shard to pandas and recreating the Dataset breaks these
references and allows embedding to succeed:

```python
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)
# Now embed_table_storage works!
```

---

## The Working Fix (Implemented)

In `src/arc_bids/core.py`, we convert each shard to pandas and recreate the Dataset:

```python
# In the upload loop:
shard = ds.shard(num_shards=num_shards, index=i, contiguous=True)

# CRITICAL FIX: Convert to pandas and back to break internal Arrow references
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)

# Now get the clean Arrow table and embed
table = fresh_shard._data.table.combine_chunks()
embedded_table = embed_table_storage(table)
pq.write_table(embedded_table, str(local_parquet_path))
```

---

## Next Steps

1. **File upstream issue** on [huggingface/datasets](https://github.com/huggingface/datasets/issues/new) with:
   - Minimal reproduction (shard a dataset with `Sequence(Nifti())`, try to embed)
   - Environment details (macOS ARM64, Python 3.13, PyArrow 22, datasets dev)
   - The pandas round-trip workaround

---

## References

- [PyArrow large_binary docs](https://arrow.apache.org/docs/python/generated/pyarrow.large_binary.html)
- [datasets.table.embed_table_storage source](https://github.com/huggingface/datasets/blob/main/src/datasets/table.py)
- [datasets.features.nifti source](https://github.com/huggingface/datasets/blob/main/src/datasets/features/nifti.py)
