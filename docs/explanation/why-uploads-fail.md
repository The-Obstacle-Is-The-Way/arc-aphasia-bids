# Why Large NIfTI Uploads Fail

> Understanding the root causes of upload failures so you can avoid them.

This document explains **why** HuggingFace dataset uploads fail with large NIfTI files.
For solutions, see the [How-to Guides](../how-to/).

---

## The "Metadata Trap"

The fundamental problem is a **size estimation mismatch**.

### What the Library Sees

When you create a dataset from a DataFrame:

```python
file_table = pd.DataFrame({
    "subject_id": ["sub-001", "sub-002", ...],  # 902 rows
    "t1w": ["/path/to/file1.nii.gz", ...],      # Strings, not bytes
})

ds = Dataset.from_pandas(file_table)
```

The `datasets` library estimates the dataset size by looking at the DataFrame:
- 902 rows of text strings
- **Estimated size: ~1 MB**

### What Actually Gets Uploaded

When you call `push_to_hub(embed_external_files=True)`:

1. The library reads each file path
2. Opens the actual NIfTI file
3. Embeds the binary content into Parquet

For a real neuroimaging dataset:

| Modality | Count | Typical Size | Total |
|----------|-------|--------------|-------|
| T1w | 447 | ~10 MB | ~4.5 GB |
| T2w | 441 | ~10 MB | ~4.4 GB |
| FLAIR | 235 | ~10 MB | ~2.4 GB |
| BOLD fMRI | 1,402 | ~150 MB | **~210 GB** |
| DWI | 2,089 | ~30 MB | ~63 GB |
| sbref | 322 | ~5 MB | ~1.6 GB |
| Lesion masks | 228 | ~1 MB | ~0.2 GB |
| **Total** | **5,164** | - | **~273 GB** |

**The library is tricked into thinking it's uploading 1 MB when it's actually 273 GB.**

---

## The Sharding Problem

### Why `max_shard_size` Doesn't Help

You might think: "I'll just set `max_shard_size='500MB'`"

This doesn't work because of how size estimation happens:

> "we don't always embed image bytes in the underlying arrow table, which can
> lead to bad size estimation"
>
> — [HuggingFace Issue #5386](https://github.com/huggingface/datasets/issues/5386)

The library samples rows to estimate average size, but:
- File sizes vary wildly (1.7 MB to 804.8 MB per session in our data)
- The sample may not be representative
- External file sizes aren't known until embedding time

### Why `num_shards` Alone Doesn't Fix It

Explicit sharding helps but doesn't fix the underlying crash:

```python
ds.push_to_hub(
    repo_id,
    embed_external_files=True,
    num_shards=902,  # One per session
)
```

**This still crashes** due to an upstream bug in `embed_table_storage`.

---

## The Real Bug: Arrow Slice References (huggingface/datasets#7894)

When `ds.shard()` creates a subset, the resulting Arrow table has internal slice
references. When `embed_table_storage` processes nested types like `Sequence(Nifti())`,
these references cause a crash at the C++ level.

### Symptoms

- Exit code 137 (SIGKILL)
- "semaphore leak" warning (symptom, not cause)
- Crash at 0% on the first shard
- No Python traceback

### What Triggers It

| Scenario | Result |
|----------|--------|
| Single `Nifti()` column | Works |
| `Sequence(Nifti())` on full dataset | Works |
| `Sequence(Nifti())` after `ds.shard()` | **CRASHES** |

### The Workaround

Convert shard to pandas and recreate the Dataset:

```python
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)
# Now embedding works
```

This breaks the problematic Arrow slice references.

See [UPSTREAM_BUG.md](/UPSTREAM_BUG.md) for full technical details.

---

## Why the Stable Release Has Empty Uploads

The stable PyPI release of `datasets` has a bug in `Nifti.embed_storage`.

When you call:
```python
ds.push_to_hub(..., embed_external_files=True)
```

The embedding logic fails to properly read NIfTI bytes. The upload "succeeds"
but parquet files contain no actual image data.

**This is a silent failure** - no error is raised.

The fix exists in the GitHub main branch but hasn't been released to PyPI yet.

---

## Summary of Failure Modes

| Failure | Root Cause | Fix |
|---------|------------|-----|
| SIGKILL at 0% | Arrow slice references in sharded datasets | Pandas round-trip workaround |
| Empty files | Bug in stable `datasets` release | Install from git |
| Huge shards | `max_shard_size` uses bad estimates | Use `num_shards` instead |

---

## References

- [huggingface/datasets#7894](https://github.com/huggingface/datasets/issues/7894): The Arrow slice crash bug
- [huggingface/datasets#5386](https://github.com/huggingface/datasets/issues/5386): `max_shard_size` issues
- [UPSTREAM_BUG.md](/UPSTREAM_BUG.md): Our detailed bug analysis

---

## Related

- [Fix Empty Uploads](../how-to/fix-empty-uploads.md) - The other major pitfall
- [UPSTREAM_BUG.md](/UPSTREAM_BUG.md) - Full technical details on the workaround
