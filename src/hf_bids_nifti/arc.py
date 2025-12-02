"""
ARC (Aphasia Recovery Cohort) dataset module.

This module provides STUB implementations for converting the ARC BIDS dataset
(OpenNeuro ds004884) into a Hugging Face Dataset.

Dataset info:
- OpenNeuro ID: ds004884
- Description: Structural MRI and lesion masks for aphasia patients
- License: CC0 (Public Domain)
- URL: https://openneuro.org/datasets/ds004884

The ARC dataset contains:
- T1-weighted structural MRI scans
- Lesion segmentation masks
- Demographic and clinical metadata (age, sex, WAB-AQ scores, etc.)

IMPORTANT: These are TEMPLATE/STUB implementations. The actual file-table
builder needs to be implemented based on the specific BIDS structure of ds004884.

To implement:
1. Download ds004884 from OpenNeuro
2. Examine the BIDS structure (participants.tsv, folder hierarchy)
3. Implement `build_arc_file_table()` to walk the directory and build a DataFrame
4. Update `get_arc_features()` with the actual schema
"""

from pathlib import Path

import pandas as pd
from datasets import Features, Nifti, Value

from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub


def build_arc_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the ARC dataset.

    TEMPLATE/STUB - Not yet implemented.

    When implemented, this function will:
    - Read participants.tsv from the BIDS root
    - Walk the dataset directory structure to locate NIfTI files
    - Build a DataFrame with one row per subject (or subject/session)

    Expected columns (to be finalized):
        - subject_id (str): BIDS subject identifier (e.g., "sub-M2001")
        - t1w_path (str): Path to T1-weighted NIfTI file
        - lesion_path (str): Path to lesion mask NIfTI file
        - age (float): Subject age at scan
        - sex (str): Subject sex (M/F)
        - wab_aq (float): Western Aphasia Battery - Aphasia Quotient

    Args:
        bids_root: Path to the root of the ARC BIDS dataset (ds004884).

    Returns:
        DataFrame with one row per subject and columns for file paths + metadata.

    Raises:
        NotImplementedError: This is a stub; implementation is pending.
    """
    raise NotImplementedError(
        "ARC file-table builder not implemented yet. "
        "Please download ds004884 from OpenNeuro and implement this function "
        "based on the actual BIDS structure."
    )


def get_arc_features() -> Features:
    """
    Get the Hugging Face Features schema for the ARC dataset.

    Returns a TEMPLATE Features object demonstrating the expected schema.
    This should be updated once the actual ARC data structure is known.

    Returns:
        Features object with Nifti() for image columns and Value() for metadata.
    """
    return Features(
        {
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "lesion": Nifti(),
            "age": Value("float32"),
            "sex": Value("string"),
            "wab_aq": Value("float32"),
        }
    )


def build_and_push_arc(config: DatasetBuilderConfig) -> None:
    """
    High-level pipeline: build ARC file table, convert to HF Dataset, optionally push.

    This is the main entry point for processing the ARC dataset. It:
    1. Calls `build_arc_file_table()` to create the file table
    2. Gets the features schema from `get_arc_features()`
    3. Uses `build_hf_dataset()` to create the HF Dataset
    4. Optionally pushes to Hub (unless dry_run=True)

    Args:
        config: Configuration with BIDS root path and HF repo info.

    Raises:
        NotImplementedError: Until `build_arc_file_table()` is implemented.
    """
    # Build the file table from BIDS directory
    file_table = build_arc_file_table(config.bids_root)

    # Get the features schema
    features = get_arc_features()

    # Build the HF Dataset
    ds = build_hf_dataset(config, file_table, features)

    # Push to Hub if not a dry run
    if not config.dry_run:
        push_dataset_to_hub(ds, config)
