# How to Fix OOM Crashes on Large Datasets

> **Problem**: Upload crashes at 0% with "leaked semaphore" warning
> **Solution**: Force explicit sharding with `num_shards`

---

## Symptoms

```text
Uploading the dataset shards:   0%|          | 0/1 [00:00<?, ? shards/s]
Map:   0%|          | 0/902 [00:00<?, ? examples/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects
[Process killed]
```

The upload crashes immediately at 0% before processing any data.

---

## Quick Fix

Add `num_shards` to your `push_to_hub()` call:

```python
ds.push_to_hub(
    "your-org/your-dataset",
    embed_external_files=True,
    num_shards=len(your_dataframe),  # Add this line
)
```

---

## Why This Works

The `datasets` library estimates how many shards to create based on your **input data size**:

| What Library Sees | Actual Size |
|-------------------|-------------|
| DataFrame with file paths (strings) | ~1 MB |
| Embedded NIfTI bytes | ~273 GB |

Because 1 MB < 500 MB (default shard size), it creates **1 shard** for everything.

When `embed_external_files=True` kicks in, it tries to load 273 GB into that single shard in RAM → OOM.

**With `num_shards=N`**, you force N separate shards, each processed independently with bounded memory.

---

## Choosing num_shards

| Dataset Size | Recommendation |
|--------------|----------------|
| < 10 GB | Default is fine |
| 10-100 GB | `num_shards=100` or row count |
| > 100 GB | `num_shards=len(dataframe)` |

**When is `len(dataframe)` safe?**
This strategy works well for datasets with **hundreds to low thousands of rows** (e.g., neuroimaging sessions). If you have **millions** of small files (e.g., 2D JPEGs), creating millions of shards is inefficient. In that case, aim for ~500MB per shard (e.g., `total_size_mb / 500`).

For neuroimaging (NIfTI), one shard per session is a robust heuristic:
- Aligns with logical data structure
- ~300 MB average is efficient (well below the 2GB shard limit)
- Easy to reason about

---

## Full Example

```python
from datasets import Dataset, Features, Value, Nifti
import pandas as pd

# Your file table
file_table = pd.DataFrame({...})  # 902 rows

# Schema
features = Features({
    "subject_id": Value("string"),
    "t1w": Nifti(),
    "bold": Nifti(),
})

# Create dataset
ds = Dataset.from_pandas(file_table, preserve_index=False)
ds = ds.cast(features)

# Upload with explicit sharding
ds.push_to_hub(
    "your-org/your-dataset",
    embed_external_files=True,
    num_shards=len(file_table),  # 902 shards, ~300 MB each
)
```

---

## Verification

After applying the fix, you should see progress like:

```text
Uploading the dataset shards:   0%|          | 2/902 [00:07<47:55, 3.20s/shard]
```

Note: `2/902` instead of `0/1` - the sharding is working.

---

## Related

- [Why Uploads Fail](../explanation/why-uploads-fail.md) - Full explanation of the metadata trap
- [Fix Empty Uploads](fix-empty-uploads.md) - Another common issue
