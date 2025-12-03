# How to Validate Before Upload

> **Problem**: Uploads fail or produce broken datasets due to data issues
> **Solution**: Validate your file table and test locally before pushing

---

## Pre-Upload Checklist

Run through these checks before calling `push_to_hub()`:

### 1. Verify File Table Structure

```python
import pandas as pd

# Check dimensions
print(f"Rows: {len(file_table)}")
print(f"Columns: {list(file_table.columns)}")

# Check for expected columns
required = ["subject_id", "session_id", "t1w"]  # your columns
missing = set(required) - set(file_table.columns)
if missing:
    raise ValueError(f"Missing columns: {missing}")
```

### 2. Check File Paths Are Absolute

```python
from pathlib import Path

for col in ["t1w", "bold", "dwi"]:  # your NIfTI columns
    for path in file_table[col].dropna():
        if not Path(path).is_absolute():
            raise ValueError(f"Relative path found: {path}")
        if not Path(path).exists():
            raise ValueError(f"File not found: {path}")
```

### 3. Verify Non-Null Counts

```python
print("Non-null counts:")
print(file_table.notna().sum())

# Example output:
# subject_id    902
# session_id    902
# t1w           447
# bold          850
# dwi           613
```

### 4. Test Local Loading

```python
from datasets import Dataset, Features, Value, Nifti

# Create dataset
ds = Dataset.from_pandas(file_table.head(5), preserve_index=False)
ds = ds.cast(features)

# Verify first item loads
item = ds[0]
print(item)

# Verify NIfTI is accessible
if item["t1w"] is not None:
    print(f"T1w shape: {item['t1w'].shape}")
```

---

## Using the Built-in Validator

This package includes a validation module:

```python
from arc_bids.validation import validate_arc_download

# Strict validation (default - no missing files allowed)
result = validate_arc_download(Path("data/openneuro/ds004884"))

# Or with tolerance for partial downloads
result = validate_arc_download(
    Path("data/openneuro/ds004884"),
    tolerance=0.1  # Allow up to 10% missing
)

if result.all_passed:
    print("Ready for upload!")
else:
    print(result.summary())
```

Or via CLI:

```bash
# Strict validation
arc-bids validate data/openneuro/ds004884

# With 10% tolerance
arc-bids validate data/openneuro/ds004884 --tolerance 0.1
```

---

## Common Validation Failures

| Issue | Check | Fix |
|-------|-------|-----|
| Missing files | `Path(path).exists()` | Re-download or fix paths |
| Relative paths | `Path(path).is_absolute()` | Use `.resolve()` |
| Wrong column names | Compare to features | Rename columns |
| Type mismatches | Check dtypes | Cast appropriately |
| Corrupt NIfTI | `nibabel.load(path)` | Re-download file |

---

## NIfTI Integrity Check

Spot-check a sample of files:

```python
import nibabel as nib
import random

nifti_paths = file_table["t1w"].dropna().tolist()
sample = random.sample(nifti_paths, min(10, len(nifti_paths)))

for path in sample:
    try:
        img = nib.load(path)
        _ = img.header  # Access header to verify structure
        print(f"OK: {Path(path).name}")
    except Exception as e:
        print(f"FAIL: {path} - {e}")
```

---

## Related

- [Tutorial: First Upload](../tutorials/first-upload.md) - Complete walkthrough
- [Fix Empty Uploads](fix-empty-uploads.md) - If validation passes but upload is broken
