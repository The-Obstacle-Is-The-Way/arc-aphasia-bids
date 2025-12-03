# Known Bugs & Limitations

## P2: Multiple Run Data Loss (CRITICAL)
**Status**: Open
**Severity**: High (Data Loss)
**Location**: `src/arc_bids/arc.py` -> `_find_nifti_in_session`

### Description
The ARC dataset contains multiple runs for certain modalities. The current pipeline **silently drops all runs except the first one**.

```python
matches = list(session_dir.rglob(pattern))
if matches:
    return str(matches[0].resolve())  # <-- SILENT DATA LOSS
```

### Impact
**SEVERE**. We are deleting 70% of the diffusion data and 40% of the fMRI data from the dataset.
*   **BOLD**: 39.4% lost (552 files dropped)
*   **DWI**: 70.7% lost (1,476 files dropped)
*   **sbref**: 72.7% lost (234 files dropped)

## P3: Unsafe Validation Tolerance
**Status**: Open
**Severity**: Medium (Integrity Risk)
**Location**: `src/arc_bids/validation.py`

### Description
The validation logic allows **10% of files to be missing** without error.
```python
tolerance = int(expected * 0.1) # <-- UNSAFE
```
This means up to ~44 structural scans or ~85 functional scans can be missing, and the validator will still say "PASS". This hides download corruption.

## P3: Invalid Validation Metric
**Status**: Open
**Severity**: Medium (Logic Error)
**Location**: `src/arc_bids/validation.py`

### Description
The code compares "Total Files on Disk" against "Total Sessions in Paper".
*   Code counts: `1402` (total files)
*   Paper expects: `850` (sessions)
*   Result: `1402 > 850` -> PASS.

**This is a logic error.** A user could be missing 500 specific sessions, but because the remaining sessions have multiple runs (pushing the file count high), the validation would falsely pass. It fails to verify that *every session* has data.
