# How to Fix Empty/Zero-Byte Uploads

> **Problem**: Dataset uploads "successfully" but NIfTI files are 0 bytes on the Hub
> **Solution**: Install `datasets` from GitHub, not PyPI

---

## Symptoms

- Upload completes without errors
- Dataset appears on HuggingFace Hub
- When loading, NIfTI files are empty or throw errors
- File sizes on Hub show 0 bytes for parquet shards

---

## Quick Fix

Reinstall `datasets` from the GitHub main branch:

```bash
# Using uv
uv add "datasets @ git+https://github.com/huggingface/datasets.git"

# Using pip
pip install --force-reinstall "datasets @ git+https://github.com/huggingface/datasets.git"
```

---

## Verification

Check your version:

```python
import datasets
print(datasets.__version__)
```

| Version | Status |
|---------|--------|
| `4.4.2.dev0` or similar with `dev` | Correct |
| `4.x.x` or `3.x.x` without `dev` | Wrong - will cause empty uploads |

---

## Why This Happens

The stable PyPI release of `datasets` has a bug in `Nifti.embed_storage`. When you call:

```python
ds.push_to_hub(..., embed_external_files=True)
```

The stable version fails to properly read and embed the NIfTI file bytes. The upload "succeeds" but files are empty.

This is a **silent failure** - no error is raised.

---

## pyproject.toml Configuration

If using uv:

```toml
[project]
dependencies = [
    "datasets>=3.4.0",
    "huggingface-hub>=0.32.0",
    "nibabel>=5.0.0",
]

[tool.uv.sources]
# CRITICAL: Override to use git version
datasets = { git = "https://github.com/huggingface/datasets.git" }
```

---

## After Fixing

1. Delete the broken dataset from HuggingFace Hub
2. Re-run your upload script
3. Verify files have actual content:

```python
from datasets import load_dataset

ds = load_dataset("your-org/your-dataset")
item = ds["train"][0]

# Should show actual NIfTI data, not None
print(item["t1w"])
print(item["t1w"].shape)  # Should show dimensions like (256, 256, 176)
```

---

## Related

- [Why Uploads Fail](../explanation/why-uploads-fail.md) - Background on these issues
- [UPSTREAM_BUG.md](/UPSTREAM_BUG.md) - Technical details on sharding crashes
