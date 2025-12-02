# Architecture Decisions

> Why this package is designed the way it is.

---

## Design Philosophy

**Make the hard parts invisible.**

Uploading NIfTI datasets to HuggingFace should be a one-liner, not a multi-day debugging session. This package encapsulates the workarounds so users don't need to discover them.

---

## Key Decisions

### 1. Per-Session Granularity

**Decision**: One row per scanning session, not per subject.

**Rationale**:
- ARC is longitudinal (902 sessions across 230 subjects)
- Sessions are independent data collection events
- Maps naturally to `num_shards` (one shard = one session)
- Maximizes data granularity for ML use cases

**Alternative rejected**: Per-subject rows would lose session-level tracking and create larger, uneven shards.

### 2. All Modalities Included

**Decision**: Include all 7 imaging modalities (T1w, T2w, FLAIR, BOLD, DWI, sbref, lesion).

**Rationale**:
- Full dataset is the goal, not a subset
- Nullable columns handle missing modalities gracefully
- Users can filter if they only need structural data

**Alternative rejected**: Structural-only would be ~13 GB instead of ~273 GB, but violates the "full dataset" requirement.

### 3. Explicit `num_shards`

**Decision**: Force `num_shards=len(file_table)` in the upload.

**Rationale**:
- Bypasses broken size estimation heuristics
- Bounds memory to largest session (~805 MB)
- Aligns shards with logical data structure
- Proven to work on 273 GB dataset

**Alternative rejected**: `max_shard_size` is unreliable per HF Issue #5386.

### 4. Git-Based `datasets` Dependency

**Decision**: Pin `datasets` to GitHub main branch, not PyPI.

**Rationale**:
- Stable release has `Nifti.embed_storage` bug
- Dev version fixes empty upload issue
- Explicit in `pyproject.toml` so it's not forgotten

**Future**: Will switch to PyPI stable once fix is released.

### 5. Absolute File Paths

**Decision**: Store absolute paths in the DataFrame, not relative.

**Rationale**:
- Avoids ambiguity about working directory
- `Path.resolve()` ensures consistency
- Required for `embed_external_files=True` to work

---

## Module Structure

```text
src/arc_bids/
├── __init__.py      # Package exports
├── arc.py           # ARC-specific: schema, file discovery, pipeline
├── core.py          # Generic: DataFrame → Dataset → Hub
├── cli.py           # Command-line interface
└── validation.py    # Pre-upload validation checks
```

### Separation of Concerns

- **`core.py`**: Dataset-agnostic utilities that can be reused for any BIDS dataset.
- **`arc.py`**: ARC-specific knowledge (modalities, directory structure, metadata columns).
- **`validation.py`**: Expected counts from the Scientific Data paper for verification.

---

## Schema Design

```python
Features({
    # Identifiers
    "subject_id": Value("string"),     # "sub-M2001"
    "session_id": Value("string"),     # "ses-1"

    # Structural (anat/)
    "t1w": Nifti(),
    "t2w": Nifti(),
    "flair": Nifti(),

    # Functional (func/)
    "bold": Nifti(),

    # Diffusion (dwi/)
    "dwi": Nifti(),
    "sbref": Nifti(),

    # Derivatives
    "lesion": Nifti(),

    # Demographics
    "age_at_stroke": Value("float32"),
    "sex": Value("string"),
    "wab_aq": Value("float32"),
    "wab_type": Value("string"),
})
```

### Why This Schema?

1. **Identifiers first**: Subject and session for filtering/grouping
2. **Modalities by type**: Structural, functional, diffusion, derivatives
3. **Demographics last**: Metadata that applies to subject, not session
4. **All nullable**: Sessions may not have all modalities

---

## Error Handling Strategy

### Fail Fast on Structure

```python
if not bids_root.exists():
    raise ValueError(f"BIDS root does not exist: {bids_root}")

if not participants_tsv.exists():
    raise FileNotFoundError(f"participants.tsv not found")
```

### Warn on Data Quality

```python
try:
    age_at_stroke = float(age_at_stroke_raw)
except (ValueError, TypeError):
    logger.warning("Invalid age_at_stroke for %s: %r", subject_id, age_at_stroke_raw)
    age_at_stroke = None
```

### Validate Before Upload

The `validation.py` module checks expected counts against the Scientific Data paper to catch download issues before attempting upload.

---

## Testing Philosophy

1. **Unit tests with synthetic data**: Fast, reproducible, CI-friendly
2. **Validation against real data**: Counts match published paper
3. **Dry run mode**: Test pipeline without actually uploading

---

## Future Considerations

1. **Streaming support**: For datasets too large for local storage
2. **Incremental uploads**: Resume from failure point
3. **Multi-dataset support**: Generic BIDS → HF pipeline
4. **PyPI `datasets` release**: Remove git dependency when fix is released
