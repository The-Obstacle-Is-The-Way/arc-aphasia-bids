# Upstream Issue Brainstorm: huggingface/datasets

**Date**: 2025-12-02
**Purpose**: Research existing issues/PRs before filing new ones

---

## GitHub CLI Scan Results

### Existing NIfTI Issues

| # | Title | State | Relevance |
|---|-------|-------|-----------|
| [#7852](https://github.com/huggingface/datasets/issues/7852) | Problems with NifTI | CLOSED | Fixed by PR #7853 - `embed_storage` was missing |
| [#7804](https://github.com/huggingface/datasets/issues/7804) | Support scientific data formats | OPEN | General request |

### Existing NIfTI PRs

| # | Title | State | Relevance |
|---|-------|-------|-----------|
| [#7853](https://github.com/huggingface/datasets/pull/7853) | Fix embed storage nifti | MERGED | Fixed missing `embed_storage` function |
| [#7892](https://github.com/huggingface/datasets/pull/7892) | encode nifti correctly when uploading lazily | OPEN | Different issue (lazy upload encoding) |
| [#7815](https://github.com/huggingface/datasets/pull/7815) | Add nifti support | MERGED | Original NIfTI feature |

### Related Large Upload Issues

| # | Title | State | Relevance |
|---|-------|-------|-----------|
| [#5990](https://github.com/huggingface/datasets/issues/5990) | Pushing a large dataset on the hub consistently hangs | OPEN | Similar symptom (hanging), different root cause? |
| [#5672](https://github.com/huggingface/datasets/issues/5672) | Pushing dataset to hub crash | CLOSED | Different bug (StopIteration on README) |
| [#6360](https://github.com/huggingface/datasets/issues/6360) | Sequence(Audio/Image) in push_to_hub | CLOSED | Embedding Sequence types fixed |

---

## Our Bugs vs Existing Issues

### Bug 1: Memory Accumulation in `_push_parquet_shards_to_hub`

**Searched for**: "push_to_hub OOM", "memory leak upload", "additions memory", "shard memory"
**Result**: **NO EXISTING ISSUE FOUND**

This is a **novel bug report** opportunity. The `additions` list in `_push_parquet_shards_to_hub` keeps all shard bytes in memory until the final commit.

**Potential PR**: Modify the loop to release `CommitOperationAdd` objects after `preupload_lfs_files` succeeds.

### Bug 2: `embed_table_storage` Crash on Sharded Datasets with `Sequence(Nifti())`

**Searched for**: "embed_table_storage crash", "shard crash", "Sequence embed"
**Result**: **NO EXISTING ISSUE FOUND**

This is also a **novel bug report** opportunity. The crash happens when:
1. Dataset has `Sequence(Nifti())` columns
2. You call `ds.shard()` or `ds.select()`
3. Then call `embed_table_storage()` on the resulting table

**Note**: This may be a PyArrow issue surfacing through datasets, not a datasets bug per se.

---

## Proposed Issues to File

### Issue 1: Memory Accumulation in Large Dataset Uploads

**Title**: `push_to_hub` accumulates all shard bytes in memory, causing OOM on large datasets

**Labels**: `bug`

**Body Draft**:
```markdown
### Describe the bug

When uploading large datasets with `push_to_hub()`, the function accumulates ALL shard
byte-strings in memory before finalizing the commit. For datasets with hundreds of shards,
this causes OOM crashes.

### Root Cause

In `_push_parquet_shards_to_hub`, the `additions` list keeps references to every
`CommitOperationAdd` object, which contains the full Parquet bytes:

```python
additions = []
for shard in shards:
    parquet_content = shard.to_parquet_bytes()  # ~300 MB
    shard_addition = CommitOperationAdd(path_or_fileobj=parquet_content)
    api.preupload_lfs_files(additions=[shard_addition])
    additions.append(shard_addition)  # <-- THE BUG: bytes stay in memory
```

For 902 shards × 300 MB = ~270 GB RAM requested → OOM.

### Suggested Fix

After `preupload_lfs_files` succeeds, the bytes could be released:
- Store only the file path reference in additions
- Or commit incrementally instead of batching

### Environment

- datasets version: main branch (post-0.22.0)
- Platform: macOS 14.x ARM64
- Python: 3.13
- Dataset: 902 shards, ~270 GB total (embedded NIfTI files)
```

### Issue 2: `embed_table_storage` Crashes on Sharded Datasets with Nested Types

**Title**: `embed_table_storage` crashes (SIGKILL) on sharded datasets with `Sequence(Nifti())`

**Labels**: `bug`

**Body Draft**:
```markdown
### Describe the bug

When embedding external files in a sharded dataset that contains `Sequence(Nifti())` columns,
`embed_table_storage` crashes with SIGKILL (exit code 137).

### Steps to Reproduce

```python
from datasets import Dataset, Features, Sequence, Value
from datasets.features import Nifti
from datasets.table import embed_table_storage

features = Features({
    "id": Value("string"),
    "images": Sequence(Nifti()),
})

ds = Dataset.from_dict({
    "id": ["a", "b"],
    "images": [["/path/to/file.nii.gz"], []],
}).cast(features)

# This works:
table = ds._data.table.combine_chunks()
embedded = embed_table_storage(table)  # OK

# This crashes:
shard = ds.shard(num_shards=2, index=0)
shard_table = shard._data.table.combine_chunks()
embedded = embed_table_storage(shard_table)  # SIGKILL
```

### Workaround

Convert shard to pandas and recreate the Dataset:
```python
shard_df = shard.to_pandas()
fresh = Dataset.from_pandas(shard_df, preserve_index=False).cast(ds.features)
# Now embedding works
```

### Environment

- datasets version: main branch (post-0.22.0)
- Platform: macOS 14.x ARM64
- Python: 3.13
- PyArrow: 18.1.0
```

---

## Next Steps

1. [ ] Wait for upload to complete (verify the fix works end-to-end)
2. [ ] File Issue 1 (memory accumulation) with minimal reproduction
3. [ ] File Issue 2 (embed crash) - may need to determine if this is PyArrow or datasets
4. [ ] Optionally offer PR for Issue 1 (simpler fix)

---

## References

- Our workarounds: `src/arc_bids/core.py`
- Full analysis: `UPSTREAM_BUG_ANALYSIS.md`
