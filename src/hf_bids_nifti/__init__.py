"""
hf_bids_nifti - Convert BIDS neuroimaging datasets to Hugging Face Datasets.

This package provides tools for converting BIDS (Brain Imaging Data Structure)
datasets into Hugging Face Datasets with NIfTI and tabular features.

Typical workflow:
    1. Download a BIDS dataset from OpenNeuro
    2. Implement a file-table builder for your specific dataset
    3. Use `build_hf_dataset()` to create an HF Dataset
    4. Optionally push to Hugging Face Hub

Example:
    ```python
    from hf_bids_nifti.core import DatasetBuilderConfig, build_hf_dataset
    from datasets import Features, Nifti, Value

    # Create a file table with paths to NIfTI files
    file_table = pd.DataFrame({
        "subject_id": ["sub-001", "sub-002"],
        "t1w": ["path/to/t1w_001.nii.gz", "path/to/t1w_002.nii.gz"],
        "age": [25.0, 30.0],
    })

    # Define the schema
    features = Features({
        "subject_id": Value("string"),
        "t1w": Nifti(),
        "age": Value("float32"),
    })

    # Build the dataset
    config = DatasetBuilderConfig(
        bids_root=Path("/path/to/bids"),
        hf_repo_id="user/my-dataset",
    )
    ds = build_hf_dataset(config, file_table, features)
    ```

Modules:
    core: Generic BIDS → HF Dataset conversion utilities
    config: Dataset configuration structures
    arc: ARC dataset (ds004884) specific code (STUB)
    soop: SOOP dataset (ds004889) specific code (STUB)
    cli: Typer-based command-line interface
"""

from .config import ARC_CONFIG, DATASET_REGISTRY, SOOP_CONFIG, BidsDatasetConfig
from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Config (alphabetical)
    "ARC_CONFIG",
    "BidsDatasetConfig",
    "DATASET_REGISTRY",
    "SOOP_CONFIG",
    # Core (alphabetical)
    "DatasetBuilderConfig",
    "build_hf_dataset",
    "push_dataset_to_hub",
]
