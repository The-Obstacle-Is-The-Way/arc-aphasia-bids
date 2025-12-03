---
license: cc0-1.0
language:
  - en
tags:
  - medical
  - neuroimaging
  - mri
  - brain
  - stroke
  - aphasia
  - lesion-segmentation
  - longitudinal
  - bids
  - nifti
  - fmri
  - diffusion
pretty_name: "Aphasia Recovery Cohort (ARC)"
size_categories:
  - 100K<n<1M
task_categories:
  - image-segmentation
  - image-classification
source_datasets:
  - openneuro/ds004884
dataset_info:
  features:
    - name: subject_id
      dtype: string
    - name: session_id
      dtype: string
    - name: t1w
      dtype: nifti
    - name: t2w
      dtype: nifti
    - name: flair
      dtype: nifti
    - name: bold
      sequence: nifti
    - name: dwi
      sequence: nifti
    - name: sbref
      sequence: nifti
    - name: lesion
      dtype: nifti
    - name: age_at_stroke
      dtype: float32
    - name: sex
      dtype: string
    - name: wab_aq
      dtype: float32
    - name: wab_type
      dtype: string
  splits:
    - name: train
      num_examples: 902
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/train-*.parquet
---

# Aphasia Recovery Cohort (ARC)

> **Multimodal neuroimaging dataset for stroke-induced aphasia research**

## Dataset Description

- **Homepage:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
- **Repository:** [arc-aphasia-bids](https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids)
- **Paper:** [Gibson et al., 2024 - Scientific Data](https://doi.org/10.1038/s41597-024-03819-7)
- **License:** CC0 1.0 (Public Domain)
- **Point of Contact:** [Aphasia Recovery Cohort Team](https://openneuro.org/datasets/ds004884)

### Dataset Summary

The Aphasia Recovery Cohort (ARC) is a large-scale, longitudinal neuroimaging dataset containing multimodal MRI scans from **230 chronic stroke patients with aphasia**. This HuggingFace-hosted version provides direct Python access to the BIDS-formatted data with embedded NIfTI files.

**Key Statistics:**

| Metric | Count |
|--------|-------|
| Subjects | 230 |
| Sessions | 902 |
| T1-weighted scans | 447 |
| T2-weighted scans | 441 |
| FLAIR scans | 235 |
| BOLD fMRI runs | 1,402 |
| Diffusion (DWI) runs | 2,089 |
| Single-band reference | 322 |
| Expert lesion masks | 228 |

### Supported Tasks

- **Lesion Segmentation**: Expert-drawn lesion masks enable training/evaluation of stroke lesion segmentation models
- **Aphasia Severity Prediction**: WAB-AQ scores (0-100) provide continuous severity labels for regression tasks
- **Aphasia Type Classification**: WAB-derived aphasia type labels (Broca's, Wernicke's, Anomic, etc.)
- **Longitudinal Analysis**: Multiple sessions per subject enable recovery trajectory modeling

### Languages

Clinical metadata and documentation are in English.

## Dataset Structure

### Data Instance

Each row represents a single **scanning session** (subject + timepoint):

```python
{
    "subject_id": "sub-M2001",
    "session_id": "ses-1",
    "t1w": <nibabel.Nifti1Image>,           # T1-weighted structural (256, 256, 176)
    "t2w": <nibabel.Nifti1Image>,           # T2-weighted structural
    "flair": <nibabel.Nifti1Image>,         # FLAIR structural
    "bold": [<Nifti1Image>, ...],           # List of BOLD fMRI runs (4D)
    "dwi": [<Nifti1Image>, ...],            # List of diffusion runs
    "sbref": [<Nifti1Image>, ...],          # List of single-band references
    "lesion": <nibabel.Nifti1Image>,        # Expert lesion mask (binary)
    "age_at_stroke": 58.0,                  # Age at stroke onset
    "sex": "M",                             # Biological sex (M/F)
    "wab_aq": 72.5,                         # WAB Aphasia Quotient (0-100)
    "wab_type": "Anomic"                    # Aphasia classification
}
```

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | `string` | BIDS subject identifier (e.g., "sub-M2001") |
| `session_id` | `string` | BIDS session identifier (e.g., "ses-1") |
| `t1w` | `Nifti` | T1-weighted structural MRI (nullable) |
| `t2w` | `Nifti` | T2-weighted structural MRI (nullable) |
| `flair` | `Nifti` | FLAIR structural MRI (nullable) |
| `bold` | `Sequence[Nifti]` | BOLD fMRI 4D time-series (all runs) |
| `dwi` | `Sequence[Nifti]` | Diffusion-weighted imaging (all runs) |
| `sbref` | `Sequence[Nifti]` | Single-band reference images (all runs) |
| `lesion` | `Nifti` | Expert-drawn lesion segmentation mask (nullable) |
| `age_at_stroke` | `float32` | Subject age at stroke onset in years |
| `sex` | `string` | Biological sex ("M" or "F") |
| `wab_aq` | `float32` | Western Aphasia Battery Aphasia Quotient (0-100) |
| `wab_type` | `string` | Aphasia type classification |

### Data Splits

| Split | Sessions | Description |
|-------|----------|-------------|
| `train` | 902 | All sessions (no predefined train/test split) |

> **Note:** Users should implement their own train/validation/test splits, ensuring no subject overlap between splits for valid evaluation.

## Dataset Creation

### Curation Rationale

The ARC dataset was created to address the lack of large-scale, publicly available neuroimaging data for aphasia research. It enables:
- Development of automated lesion segmentation algorithms
- Machine learning models for aphasia severity prediction
- Studies of brain plasticity and language recovery

### Source Data

#### Initial Data Collection

Data was collected at the University of South Carolina and Medical University of South Carolina as part of ongoing aphasia recovery research. All participants provided informed consent under IRB-approved protocols.

#### Who are the source language producers?

N/A - This is a neuroimaging dataset, not a language dataset.

### Annotations

#### Annotation Process

Lesion masks were manually traced by trained neuroimaging experts on T1-weighted or FLAIR images, following established stroke lesion delineation protocols.

#### Who are the annotators?

Trained neuroimaging researchers at academic medical centers with expertise in stroke neuroanatomy.

### Personal and Sensitive Information

- **De-identified**: All data has been de-identified per HIPAA guidelines
- **Defaced**: Structural MRI images have been defaced to prevent facial reconstruction
- **No PHI**: No protected health information is included
- **Consent**: All participants consented to public data sharing

## Considerations for Using the Data

### Social Impact

This dataset enables research into:
- Improved stroke rehabilitation through better outcome prediction
- Automated clinical tools for aphasia assessment
- Understanding of brain-language relationships

### Discussion of Biases

- **Geographic bias**: Data collected primarily from Southeastern US medical centers
- **Age bias**: Stroke predominantly affects older adults; pediatric cases underrepresented
- **Severity bias**: Very severe aphasia cases may be underrepresented due to consent requirements

### Other Known Limitations

- Not all sessions have all modalities (check for `None`/empty lists)
- Lesion masks available for 228/230 subjects
- Longitudinal follow-up varies by subject (1-12 sessions)

## Usage

### Loading the Dataset

```python
from datasets import load_dataset

# Load full dataset
ds = load_dataset("hugging-science/arc-aphasia-bids")

# Access a session
session = ds["train"][0]
print(f"Subject: {session['subject_id']}, Session: {session['session_id']}")

# Access structural imaging
if session["t1w"] is not None:
    t1_data = session["t1w"].get_fdata()
    print(f"T1w shape: {t1_data.shape}")

# Access multi-run functional data
for i, bold_run in enumerate(session["bold"]):
    print(f"BOLD run {i+1}: shape={bold_run.shape}")
```

### Filtering by Modality

```python
# Get only sessions with lesion masks
sessions_with_lesions = ds["train"].filter(lambda x: x["lesion"] is not None)

# Get sessions with BOLD fMRI
sessions_with_bold = ds["train"].filter(lambda x: len(x["bold"]) > 0)
```

### Clinical Metadata Analysis

```python
import pandas as pd

# Extract clinical metadata
df = ds["train"].to_pandas()[["subject_id", "session_id", "age_at_stroke", "sex", "wab_aq", "wab_type"]]
print(df.describe())
```

## Additional Information

### Dataset Curators

- **Original Dataset**: Gibson et al. (University of South Carolina)
- **HuggingFace Conversion**: [The-Obstacle-Is-The-Way](https://github.com/The-Obstacle-Is-The-Way)

### Licensing Information

This dataset is released under **CC0 1.0 Universal (Public Domain)**. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

### Citation Information

```bibtex
@article{gibson2024arc,
  title={A large-scale longitudinal multimodal neuroimaging dataset for aphasia},
  author={Gibson, M. and others},
  journal={Scientific Data},
  volume={11},
  year={2024},
  publisher={Nature Publishing Group},
  doi={10.1038/s41597-024-03819-7}
}
```

### Contributions

Thanks to [@The-Obstacle-Is-The-Way](https://github.com/The-Obstacle-Is-The-Way) for converting this dataset to HuggingFace format with native `Nifti()` feature support.

---

## Technical Notes

### Multi-Run Support

Functional and diffusion modalities (`bold`, `dwi`, `sbref`) support multiple runs per session. These are stored as lists:
- Empty list `[]` = no data for this session
- List with items = all runs for this session, sorted by filename

### Memory Considerations

NIfTI files are loaded on-demand. For large-scale processing, consider:

```python
# Stream without loading all into memory
for session in ds["train"]:
    process(session)
    # Data is garbage collected after each iteration
```

### Original BIDS Source

This dataset is derived from [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884). The original BIDS structure is preserved in the column naming and organization.
