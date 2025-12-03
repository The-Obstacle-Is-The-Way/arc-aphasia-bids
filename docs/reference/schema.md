# Schema Specification

> Dataset schema for the ARC (Aphasia Recovery Cohort) dataset.

---

## Overview

| Attribute | Value |
|-----------|-------|
| Rows | 902 (one per session) |
| Columns | 13 |
| NIfTI columns | 7 |
| Metadata columns | 6 |

---

## Column Definitions

### Identifiers

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `subject_id` | `string` | BIDS subject identifier | `"sub-M2001"` |
| `session_id` | `string` | BIDS session identifier | `"ses-1"` |

### Structural Imaging (anat/)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `t1w` | `Nifti` | Yes | T1-weighted structural MRI |
| `t2w` | `Nifti` | Yes | T2-weighted structural MRI |
| `flair` | `Nifti` | Yes | FLAIR structural MRI |

### Functional Imaging (func/)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `bold` | `Nifti` | Yes | BOLD fMRI 4D time-series (first run only) |

> **Note**: If a session contains multiple BOLD runs (e.g., `run-01`, `run-02`), only the **first** run is included. See [BUGS.md](../../BUGS.md) for details.

### Diffusion Imaging (dwi/)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `dwi` | `Nifti` | Yes | Diffusion-weighted imaging (first run only) |
| `sbref` | `Nifti` | Yes | Single-band reference image (first run only) |

> **Note**: If a session contains multiple DWI runs, only the **first** run is included.

### Derivatives

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `lesion` | `Nifti` | Yes | Expert-drawn lesion segmentation mask |

### Demographics

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `age_at_stroke` | `float32` | Yes | Age at time of stroke (years) |
| `sex` | `string` | Yes | Biological sex (`"M"` or `"F"`) |
| `wab_aq` | `float32` | Yes | WAB Aphasia Quotient (0-100) |
| `wab_type` | `string` | Yes | Aphasia type classification |

---

## Features Definition

```python
from datasets import Features, Value, Nifti

features = Features({
    # Identifiers
    "subject_id": Value("string"),
    "session_id": Value("string"),

    # Structural imaging
    "t1w": Nifti(),
    "t2w": Nifti(),
    "flair": Nifti(),

    # Functional imaging
    "bold": Nifti(),

    # Diffusion imaging
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

---

## File Counts

From the Scientific Data paper (Gibson et al., 2024):

| Modality | Sessions with Data | Raw File Count |
|----------|-------------------|----------------|
| T1w | 441 | 447 |
| T2w | 447 | 441 |
| FLAIR | 235 | 235 |
| BOLD | 850 | 1,402 |
| DWI | 613 | 2,089 |
| sbref | 88 | 322 |
| Lesion | 230 | 228 |

Note: Raw file counts may exceed session counts due to multiple runs/acquisitions per session.

---

## NIfTI Column Behavior

### Nullable Columns

All NIfTI columns are nullable. A session may not have all modalities:

```python
ds = load_dataset("hugging-science/arc-aphasia-bids")
item = ds["train"][0]

# May be None if this session doesn't have T2w
if item["t2w"] is not None:
    print(item["t2w"].shape)
```

### Accessing NIfTI Data

```python
# Get nibabel image object
nifti = item["t1w"]

# Access properties
print(nifti.shape)      # (256, 256, 176)
print(nifti.affine)     # 4x4 transformation matrix
print(nifti.header)     # NIfTI header

# Get numpy array
data = nifti.get_fdata()
```

---

## BIDS Directory Mapping

| Column | BIDS Directory | Pattern |
|--------|---------------|---------|
| `t1w` | `sub-*/ses-*/anat/` | `*_T1w.nii.gz` |
| `t2w` | `sub-*/ses-*/anat/` | `*_T2w.nii.gz` |
| `flair` | `sub-*/ses-*/anat/` | `*_FLAIR.nii.gz` |
| `bold` | `sub-*/ses-*/func/` | `*_bold.nii.gz` |
| `dwi` | `sub-*/ses-*/dwi/` | `*_dwi.nii.gz` |
| `sbref` | `sub-*/ses-*/dwi/` | `*_sbref.nii.gz` |
| `lesion` | `derivatives/lesion_masks/sub-*/ses-*/anat/` | `*_desc-lesion_mask.nii.gz` |

---

## Source Dataset

| Attribute | Value |
|-----------|-------|
| Name | Aphasia Recovery Cohort (ARC) |
| OpenNeuro ID | ds004884 |
| Version | 1.0.1 |
| DOI | 10.18112/openneuro.ds004884.v1.0.1 |
| License | CC0 (Public Domain) |
| Subjects | 230 |
| Sessions | 902 |
| Population | Chronic post-stroke aphasia |

---

## Related

- [API Reference](api.md)
- [Why Uploads Fail](../explanation/why-uploads-fail.md)
