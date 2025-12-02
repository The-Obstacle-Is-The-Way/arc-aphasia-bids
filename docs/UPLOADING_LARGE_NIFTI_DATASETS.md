# Uploading Large NIfTI Datasets to HuggingFace Hub

> **TL;DR**: If you're uploading >10GB of NIfTI files to HuggingFace, you WILL hit obscure bugs. This doc saves you days of debugging.

---

## The Problem Nobody Warns You About

HuggingFace's `datasets` library with `Nifti()` feature type is powerful but has critical edge cases with large datasets. We learned this uploading a 273GB neuroimaging dataset (902 sessions, 5,164 NIfTI files).

**What should be a one-liner becomes a multi-day debugging nightmare.**

---

## Pitfall #1: The Empty Upload Bug

### Symptom
Your dataset uploads successfully, but all NIfTI files are **0 bytes** on the Hub.

### Root Cause
The stable PyPI release of `datasets` has a bug where `Nifti.embed_storage` doesn't work correctly. Files appear to upload but contain no data.

### Fix
**You MUST install `datasets` from the GitHub main branch:**

```bash
# Using uv
uv add "datasets @ git+https://github.com/huggingface/datasets.git"

# Using pip
pip install "datasets @ git+https://github.com/huggingface/datasets.git"
```

In `pyproject.toml` with uv:
```toml
[project]
dependencies = [
    "datasets>=3.4.0",
]

[tool.uv.sources]
datasets = { git = "https://github.com/huggingface/datasets.git" }
```

### Verification
```python
import datasets
print(datasets.__version__)  # Should show "4.4.2.dev0" or similar dev version
```

---

## Pitfall #2: The OOM Crash at 0%

### Symptom
```
Uploading the dataset shards:   0%|          | 0/1 [00:00<?, ? shards/s]
Map:   0%|          | 0/902 [00:00<?, ? examples/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects
[Process killed]
```

Upload crashes immediately at 0% with semaphore leak.

### Root Cause
The `datasets` library estimates shard count from the **input data size**, not the **embedded file size**:

1. Your DataFrame has file paths (strings) → estimated size ~1MB
2. Library decides: "1MB < 500MB default shard size → use 1 shard"
3. With `embed_external_files=True`, it reads actual NIfTI bytes (273GB)
4. Tries to buffer 273GB into single shard → OOM → crash

**The library is tricked by the metadata size.**

### Fix
Force explicit sharding with `num_shards`:

```python
# One shard per row is safe and maps to logical data structure
ds.push_to_hub(
    repo_id,
    embed_external_files=True,
    num_shards=len(your_dataframe),  # e.g., 902 for 902 sessions
)
```

### Why This Works
| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Shards | 1 | 902 |
| RAM needed | 273GB | ~300MB (largest session) |
| Result | OOM crash | Success |

---

## Pitfall #3: `max_shard_size` Doesn't Work

### Symptom
You try `max_shard_size="500MB"` but get shards that are 2GB+.

### Root Cause
Per [HuggingFace Issue #5386](https://github.com/huggingface/datasets/issues/5386):
> "we don't always embed image bytes in the underlying arrow table, which can lead to bad size estimation"

The library samples the first 1000 rows to estimate size, but file sizes vary wildly.

### Fix
Don't rely on `max_shard_size`. Use explicit `num_shards` instead.

---

## Pitfall #4: Silent Failures

### Symptom
Upload "completes" but dataset is broken or incomplete.

### Prevention
Always validate before upload:

```python
# Check your file table
print(f"Rows: {len(file_table)}")
print(f"Columns: {list(file_table.columns)}")
print(f"Non-null counts:\n{file_table.notna().sum()}")

# Verify a sample loads correctly
ds = Dataset.from_pandas(file_table)
ds = ds.cast(features)
print(ds[0])  # Should show actual data, not None
```

---

## Complete Working Example

```python
from pathlib import Path
import pandas as pd
from datasets import Dataset, Features, Value, Nifti

# 1. Build file table (paths as strings)
file_table = pd.DataFrame({
    "subject_id": ["sub-001", "sub-002", ...],
    "session_id": ["ses-1", "ses-1", ...],
    "t1w": ["/abs/path/to/t1w.nii.gz", ...],
    "bold": ["/abs/path/to/bold.nii.gz", ...],  # Can be None
})

# 2. Define schema
features = Features({
    "subject_id": Value("string"),
    "session_id": Value("string"),
    "t1w": Nifti(),
    "bold": Nifti(),
})

# 3. Create dataset
ds = Dataset.from_pandas(file_table, preserve_index=False)
ds = ds.cast(features)

# 4. Push with explicit sharding (THE CRITICAL PART)
ds.push_to_hub(
    "your-org/your-dataset",
    embed_external_files=True,
    num_shards=len(file_table),  # REQUIRED for large datasets
)
```

---

## Checklist Before Upload

- [ ] Using `datasets` from git, not PyPI stable
- [ ] `embed_external_files=True` (default, but be explicit)
- [ ] `num_shards=len(file_table)` for datasets >10GB
- [ ] File paths are **absolute**, not relative
- [ ] Validated sample loads correctly
- [ ] Running in `tmux`/`screen` (upload takes hours)
- [ ] Log file capturing output

---

## Why This Is Hard

1. **No error messages**: OOM crashes don't explain the sharding issue
2. **Misleading defaults**: Library "helpfully" picks shard count based on wrong size
3. **Stable release is broken**: Must use dev version for NIfTI
4. **Documentation gaps**: These issues aren't in official docs
5. **Silent failures**: Empty uploads don't raise exceptions

---

## References

- [HF Issue #5386: max_shard_size breaks with large files](https://github.com/huggingface/datasets/issues/5386)
- [HF Issue #5990: Large dataset uploads hang](https://github.com/huggingface/datasets/issues/5990)
- [HF Forum: push_to_hub limits](https://discuss.huggingface.co/t/any-workaround-for-push-to-hub-limits/59274)

---

## About This Document

Written after spending multiple days debugging a 273GB neuroimaging dataset upload. Every pitfall here caused real failures. If this saves you time, it was worth documenting.

**Dataset**: ARC (Aphasia Recovery Cohort) - ds004884 on OpenNeuro
**Target**: hugging-science/arc-aphasia-bids on HuggingFace Hub
