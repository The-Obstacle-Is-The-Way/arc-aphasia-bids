# Python API Reference

> Module and function reference for arc-bids.

---

## Module: `bids_hub.arc`

ARC dataset-specific functions.

### `build_arc_file_table(bids_root)`

Build a file table for the ARC dataset.

```python
from pathlib import Path
from bids_hub.arc import build_arc_file_table

file_table = build_arc_file_table(Path("data/openneuro/ds004884"))
```

**Parameters:**
- `bids_root` (`Path`): Path to the BIDS dataset root.

**Returns:**
- `pd.DataFrame`: One row per session with columns:
  - `subject_id` (str): BIDS subject ID (e.g., "sub-M2001")
  - `session_id` (str): BIDS session ID (e.g., "ses-1")
  - `t1w` (str | None): Absolute path to T1w NIfTI
  - `t2w` (str | None): Absolute path to T2w NIfTI
  - `flair` (str | None): Absolute path to FLAIR NIfTI
  - `bold` (str | None): Absolute path to BOLD fMRI NIfTI
  - `dwi` (str | None): Absolute path to DWI NIfTI
  - `sbref` (str | None): Absolute path to sbref NIfTI
  - `lesion` (str | None): Absolute path to lesion mask NIfTI
  - `age_at_stroke` (float | None): Age at stroke
  - `sex` (str | None): Biological sex
  - `wab_aq` (float | None): WAB Aphasia Quotient
  - `wab_type` (str | None): Aphasia type

**Raises:**
- `ValueError`: If `bids_root` doesn't exist or isn't a directory
- `FileNotFoundError`: If `participants.tsv` doesn't exist

---

### `get_arc_features()`

Get the HuggingFace Features schema for ARC.

```python
from bids_hub.arc import get_arc_features

features = get_arc_features()
```

**Returns:**
- `datasets.Features`: Schema with 13 columns (7 Nifti, 6 Value)

---

### `build_and_push_arc(config)`

High-level pipeline: build file table, create dataset, push to Hub.

```python
from pathlib import Path
from bids_hub.arc import build_and_push_arc
from bids_hub.core import DatasetBuilderConfig

config = DatasetBuilderConfig(
    bids_root=Path("data/openneuro/ds004884"),
    hf_repo_id="hugging-science/arc-aphasia-bids",
    dry_run=False,
)

build_and_push_arc(config)
```

**Parameters:**
- `config` (`DatasetBuilderConfig`): Configuration object

---

## Module: `bids_hub.core`

Generic BIDS → HuggingFace utilities.

### `DatasetBuilderConfig`

Configuration dataclass.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatasetBuilderConfig:
    bids_root: Path           # BIDS dataset root
    hf_repo_id: str           # HuggingFace repo (e.g., "org/name")
    split: str | None = None  # Optional split name
    dry_run: bool = False     # Skip Hub push if True
```

---

### `build_hf_dataset(config, file_table, features)`

Convert a pandas DataFrame to a HuggingFace Dataset.

```python
from bids_hub.core import build_hf_dataset

ds = build_hf_dataset(config, file_table, features)
```

**Parameters:**
- `config` (`DatasetBuilderConfig`): Configuration
- `file_table` (`pd.DataFrame`): File paths and metadata
- `features` (`datasets.Features`): Schema definition

**Returns:**
- `datasets.Dataset`: Dataset with columns cast to features

---

### `push_dataset_to_hub(ds, config, **kwargs)`

Push a dataset to HuggingFace Hub.

```python
from bids_hub.core import push_dataset_to_hub

push_dataset_to_hub(
    ds,
    config,
    num_shards=902,  # Critical for large datasets
)
```

**Parameters:**
- `ds` (`datasets.Dataset`): Dataset to push
- `config` (`DatasetBuilderConfig`): Configuration with repo ID
- `embed_external_files` (bool): Embed NIfTI bytes (default: True)
- `**kwargs`: Additional args passed to `ds.push_to_hub()`

**Important kwargs:**
- `num_shards` (int): Number of parquet shards. **Required for datasets >10GB.**

---

## Module: `bids_hub.validation`

Pre-upload validation.

### `validate_arc_download(bids_root)`

Validate an ARC dataset download.

```python
from pathlib import Path
from bids_hub.validation import validate_arc_download

result = validate_arc_download(Path("data/openneuro/ds004884"))

if result.all_passed:
    print("Ready for upload!")
else:
    print(result.summary())
```

**Parameters:**
- `bids_root` (`Path`): BIDS dataset root
- `run_bids_validator` (bool): Run external BIDS validator (default: False)
- `nifti_sample_size` (int): Number of NIfTIs to spot-check (default: 10)

**Returns:**
- `ValidationResult`: Object with `.all_passed`, `.summary()`, `.checks`

---

### `ValidationResult`

```python
@dataclass
class ValidationResult:
    bids_root: Path
    checks: list[ValidationCheck]

    @property
    def all_passed(self) -> bool: ...

    @property
    def passed_count(self) -> int: ...

    @property
    def failed_count(self) -> int: ...

    def summary(self) -> str: ...
```

---

### Expected Counts

From the Scientific Data paper (Gibson et al., 2024):

```python
EXPECTED_COUNTS = {
    "subjects": 230,
    "sessions": 902,
    "t1w_series": 441,
    "t2w_series": 447,
    "flair_series": 235,
    "bold_series": 850,
    "dwi_series": 613,
    "sbref_series": 88,
    "lesion_masks": 230,
}
```

---

## Related

- [CLI Reference](cli.md)
- [Schema Specification](schema.md)
