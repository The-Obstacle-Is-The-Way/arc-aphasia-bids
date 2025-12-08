# Bug Spec: Arrow Format Scalar Extraction

## Summary

Validation scripts incorrectly extract scalar values from Arrow-formatted dataset rows, causing:

1. Subject ID lookup failures (observed)
2. Latent crash on modality access (hidden by bug #1)

## Severity

**High** - Validation passes with 0 files checked, AND fixing bug #1 alone would cause a crash.

## Root Cause

When `ds.set_format("arrow")` is called on a HuggingFace Dataset:

1. `ds[idx]` returns a `pyarrow.lib.Table`, not a `dict`
2. `row["subject_id"]` returns a `pyarrow.lib.ChunkedArray`, not a `str`
3. `str(row["subject_id"])` produces nested array representation instead of the scalar value

### Demonstration

```python
from datasets import load_dataset

ds = load_dataset('hugging-science/isles24-stroke', split='train[:1]')

# Default format (correct)
row = ds[0]
print(type(row))                    # <class 'dict'>
print(row["subject_id"])            # "sub-stroke0001"

# Arrow format (bug)
ds.set_format("arrow")
row = ds[0]
print(type(row))                    # <class 'pyarrow.lib.Table'>
print(row["subject_id"])            # ChunkedArray with nested brackets
print(str(row["subject_id"]))       # "[\n  [\n    \"sub-stroke0001\"\n  ]\n]"
```

### Observed Output

```text
⚠️  Warning: [
  [
    "sub-stroke0001"
  ]
] not found in source
```

The string comparison `original_table["subject_id"] == subject_id` fails because:

- `subject_id` = `'[\n  [\n    "sub-stroke0001"\n  ]\n]'` (malformed)
- Expected = `'sub-stroke0001'` (correct)

## Affected Files

### Bug #1: Subject ID Extraction (Observed)

| File | Line(s) | Buggy Code |
|------|---------|------------|
| `scripts/validate_isles24_hf_upload.py` | 109 | `subject_id = str(row["subject_id"])` |
| `scripts/validate_hf_download.py` | 114-115 | `subject_id = str(row["subject_id"])` and `session_id = str(row["session_id"])` |

### Bug #2: Modality Access (Latent - Hidden by Bug #1)

| File | Line(s) | Buggy Code |
|------|---------|------------|
| `scripts/validate_isles24_hf_upload.py` | 120 | `hf_data = row[modality].as_py()` |
| `scripts/validate_hf_download.py` | 128 | `t1w_struct = row["t1w"].as_py()` |
| `scripts/validate_hf_download.py` | 140 | `bold_list = row["bold"].as_py()` |

**Critical**: `ChunkedArray` does NOT have `.as_py()` method - it throws `AttributeError`:

```python
>>> row["ncct"].as_py()
AttributeError: 'pyarrow.lib.ChunkedArray' object has no attribute 'as_py'
```

This bug is currently hidden because Bug #1 causes `continue` before reaching the modality access code.

## Impact

- **Bug #1**: Hash validation silently skipped (0 files checked)
- **Bug #2**: Would crash with `AttributeError` if Bug #1 were fixed alone
- **Combined**: False positive "VALIDATION PASSED" with no actual validation
- **No data corruption**: The uploaded data itself is correct; only validation is broken

## Fix: Use `.to_pylist()[0]` for ALL Arrow Column Access

The fix is simple and consistent: replace ALL `str(row["col"])` and `row["col"].as_py()` with `row["col"].to_pylist()[0]`.

### ISLES24 Validation Script (`validate_isles24_hf_upload.py`)

```python
# Line 109 - Bug #1: Subject ID
# Before (buggy)
subject_id = str(row["subject_id"])
# After (fixed)
subject_id = row["subject_id"].to_pylist()[0]

# Line 120 - Bug #2: Modality access
# Before (buggy - would crash with AttributeError)
hf_data = row[modality].as_py()
# After (fixed)
hf_data = row[modality].to_pylist()[0]
```

### ARC Validation Script (`validate_hf_download.py`)

```python
# Lines 114-115 - Bug #1: Subject/Session ID
# Before (buggy)
subject_id = str(row["subject_id"])
session_id = str(row["session_id"])
# After (fixed)
subject_id = row["subject_id"].to_pylist()[0]
session_id = row["session_id"].to_pylist()[0]

# Line 128 - Bug #2: T1w access
# Before (buggy - would crash)
t1w_struct = row["t1w"].as_py()
# After (fixed)
t1w_struct = row["t1w"].to_pylist()[0]

# Line 140 - Bug #2: BOLD access
# Before (buggy - would crash)
bold_list = row["bold"].as_py()
# After (fixed)
bold_list = row["bold"].to_pylist()[0]
```

## Why `.to_pylist()[0]` and not `[0].as_py()`?

Both work, but `.to_pylist()[0]` is preferred because:

1. **Explicit**: Clearly shows we're converting Arrow → Python list → element
2. **Consistent**: Works identically for all column types (string, struct, list)
3. **Safe**: `[0]` on ChunkedArray accesses chunk 0, not element 0 in some PyArrow versions

## Testing

After fix, re-run validation and verify:

### ISLES24 (`validate_isles24_hf_upload.py`)

```bash
uv run python scripts/validate_isles24_hf_upload.py
```

Expected:

- No "Warning: ... not found in source" messages
- "✅ All 150 sampled NIfTIs have matching hashes" (not "0 sampled")

### ARC (`validate_hf_download.py`)

```bash
uv run python scripts/validate_hf_download.py
```

Expected:

- No warnings about missing subject/session IDs
- Actual hash count > 0

## Verification Evidence

```python
# Verified behavior on 2024-12-08
from datasets import load_dataset
ds = load_dataset('hugging-science/isles24-stroke', split='train[:1]')
ds.set_format('arrow')
row = ds[0]

# Bug #1: str() on ChunkedArray
str(row["subject_id"])  # Returns '[\n  [\n    "sub-stroke0001"\n  ]\n]' (WRONG)

# Bug #2: .as_py() doesn't exist on ChunkedArray
row["ncct"].as_py()  # Raises AttributeError (CRASH)

# Correct: .to_pylist()[0]
row["subject_id"].to_pylist()[0]  # Returns 'sub-stroke0001' (CORRECT)
row["ncct"].to_pylist()[0]        # Returns {'bytes': ..., 'path': ...} (CORRECT)
```

## Related

- [HuggingFace datasets library Arrow format](https://huggingface.co/docs/datasets/use_with_pytorch#format-type)
- [PyArrow ChunkedArray](https://arrow.apache.org/docs/python/generated/pyarrow.ChunkedArray.html)
