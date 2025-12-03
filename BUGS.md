# Known Bugs & Limitations

## P2: Multiple Run Data Loss
**Status**: Open
**Severity**: Medium (Data Loss)
**Location**: `src/arc_bids/arc.py` -> `_find_nifti_in_session`

### Description
The ARC dataset contains multiple runs for certain modalities (e.g., BOLD fMRI has ~1,402 files for 850 sessions). The current pipeline design assumes one file per modality per session.

When multiple files match a pattern (e.g., `*bold.nii.gz` matches `run-01_bold.nii.gz` and `run-02_bold.nii.gz`), the code arbitrarily selects the **first match** returned by `pathlib.Path.rglob`.

```python
# src/arc_bids/arc.py
matches = list(session_dir.rglob(pattern))
if matches:
    return str(matches[0].resolve())  # <-- Drops matches[1:]
```

### Impact
Approximately ~40% of BOLD fMRI files and ~50% of DWI files (runs 2+) are excluded from the uploaded dataset. The dataset contains only one representative scan per session for each modality.

### Workaround
No current workaround. Future versions should either:
1. Change schema to `Sequence(Nifti())` to support multiple runs.
2. explode the DataFrame to have one row per *run* (e.g., `sub-01_ses-1_run-1`, `sub-01_ses-1_run-2`).

## P3: Validation Tolerance is Loose
**Status**: Open
**Severity**: Low
**Location**: `src/arc_bids/validation.py` -> `_check_series_count`

### Description
The validation logic uses a 10% tolerance for file counts to account for potential minor download failures or specific exclusion criteria.

```python
tolerance = int(expected * 0.1)
passed = count >= expected - tolerance
```

This allows up to ~44 missing structural scans or ~85 missing functional scans to pass validation silently.

## P3: Validation Logic Mismatch
**Status**: Open
**Severity**: Low
**Location**: `src/arc_bids/validation.py`

### Description
`EXPECTED_COUNTS` values for functional data (BOLD, DWI) are based on the number of *sessions* with that modality (from the paper), but the code counts *total files* on disk.

Since `Files (1402) > Sessions (850)`, the validation always passes if the full dataset is present. However, it does not strictly validate that *every* expected file is present, only that the total count exceeds the session count.
