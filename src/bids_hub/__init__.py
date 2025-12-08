"""bids_hub - Upload neuroimaging datasets to HuggingFace Hub."""

from __future__ import annotations

# Core (generic)
from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub

# Datasets
from .datasets import (
    build_and_push_arc,
    build_and_push_isles24,
    build_arc_file_table,
    build_isles24_file_table,
    get_arc_features,
    get_isles24_features,
)

# Validation
from .validation import (
    ValidationResult,
    validate_arc_download,
    validate_isles24_download,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Core
    "DatasetBuilderConfig",
    "build_hf_dataset",
    "push_dataset_to_hub",
    # ARC
    "build_arc_file_table",
    "build_and_push_arc",
    "get_arc_features",
    "validate_arc_download",
    # ISLES24
    "build_isles24_file_table",
    "build_and_push_isles24",
    "get_isles24_features",
    "validate_isles24_download",
    # Validation
    "ValidationResult",
]
