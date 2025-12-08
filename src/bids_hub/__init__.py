"""
bids_hub - Upload the Aphasia Recovery Cohort (ARC) to HuggingFace Hub.

This package converts the ARC BIDS dataset (OpenNeuro ds004884) into a
HuggingFace Dataset with NIfTI and tabular features.

Dataset: https://openneuro.org/datasets/ds004884
License: CC0 (Public Domain)

Workflow:
    1. Download ARC from OpenNeuro (AWS S3 or CLI)
    2. Build file table with `build_arc_file_table()`
    3. Create HF Dataset with `build_hf_dataset()`
    4. Push to Hub with `push_dataset_to_hub()`

Example:
    ```python
    from pathlib import Path
    from bids_hub import (
        DatasetBuilderConfig,
        build_arc_file_table,
        build_hf_dataset,
        get_arc_features,
    )

    # Build file table from BIDS directory
    file_table = build_arc_file_table(Path("data/openneuro/ds004884"))

    # Create HF Dataset
    config = DatasetBuilderConfig(
        bids_root=Path("data/openneuro/ds004884"),
        hf_repo_id="hugging-science/arc-aphasia-bids",
    )
    ds = build_hf_dataset(config, file_table, get_arc_features())
    ```

Modules:
    core: Generic BIDS → HF Dataset conversion utilities
    config: ARC dataset configuration
    arc: ARC-specific file table builder and features
    validation: Data integrity validation
    cli: Command-line interface
"""

from .arc import build_arc_file_table, get_arc_features
from .config import ARC_CONFIG, BidsDatasetConfig
from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub
from .validation import ValidationResult, validate_arc_download

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Config
    "ARC_CONFIG",
    "BidsDatasetConfig",
    # Core
    "DatasetBuilderConfig",
    "build_hf_dataset",
    "push_dataset_to_hub",
    # ARC
    "build_arc_file_table",
    "get_arc_features",
    # Validation
    "validate_arc_download",
    "ValidationResult",
]
