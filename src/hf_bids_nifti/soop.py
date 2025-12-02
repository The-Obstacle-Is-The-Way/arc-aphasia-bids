"""
SOOP (Study of Outcomes in aPhagia) dataset module.

This module provides STUB implementations for converting the SOOP BIDS dataset
(OpenNeuro ds004889) into a Hugging Face Dataset.

Dataset info:
- OpenNeuro ID: ds004889
- Description: Longitudinal stroke recovery imaging study
- License: CC0 (Public Domain)
- URL: https://openneuro.org/datasets/ds004889

The SOOP dataset contains:
- Multiple imaging sessions per subject
- T1-weighted structural MRI scans
- Lesion segmentation masks
- Longitudinal clinical outcomes

IMPORTANT: These are TEMPLATE/STUB implementations. The actual file-table
builder needs to be implemented based on the specific BIDS structure of ds004889.

To implement:
1. Download ds004889 from OpenNeuro
2. Examine the BIDS structure (participants.tsv, sessions, folder hierarchy)
3. Implement `build_soop_file_table()` to walk the directory and build a DataFrame
4. Update `get_soop_features()` with the actual schema
"""

from pathlib import Path

import pandas as pd
from datasets import Features, Nifti, Value

from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub


def build_soop_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the SOOP dataset.

    TEMPLATE/STUB - Not yet implemented.

    When implemented, this function will:
    - Read participants.tsv from the BIDS root
    - Walk the dataset directory structure to locate NIfTI files
    - Handle multiple sessions per subject (longitudinal data)
    - Build a DataFrame with one row per subject/session

    Expected columns (to be finalized):
        - subject_id (str): BIDS subject identifier
        - session_id (str): BIDS session identifier (e.g., "ses-01")
        - t1w_path (str): Path to T1-weighted NIfTI file
        - lesion_path (str): Path to lesion mask NIfTI file
        - days_post_stroke (int): Days since stroke onset
        - age (float): Subject age at scan
        - sex (str): Subject sex (M/F)

    Args:
        bids_root: Path to the root of the SOOP BIDS dataset (ds004889).

    Returns:
        DataFrame with one row per subject/session and columns for file paths + metadata.

    Raises:
        NotImplementedError: This is a stub; implementation is pending.
    """
    raise NotImplementedError(
        "SOOP file-table builder not implemented yet. "
        "Please download ds004889 from OpenNeuro and implement this function "
        "based on the actual BIDS structure."
    )


def get_soop_features() -> Features:
    """
    Get the Hugging Face Features schema for the SOOP dataset.

    Returns a TEMPLATE Features object demonstrating the expected schema.
    This should be updated once the actual SOOP data structure is known.

    Returns:
        Features object with Nifti() for image columns and Value() for metadata.
    """
    return Features(
        {
            "subject_id": Value("string"),
            "session_id": Value("string"),
            "t1w": Nifti(),
            "lesion": Nifti(),
            "days_post_stroke": Value("int32"),
            "age": Value("float32"),
            "sex": Value("string"),
        }
    )


def build_and_push_soop(config: DatasetBuilderConfig) -> None:
    """
    High-level pipeline: build SOOP file table, convert to HF Dataset, optionally push.

    This is the main entry point for processing the SOOP dataset. It:
    1. Calls `build_soop_file_table()` to create the file table
    2. Gets the features schema from `get_soop_features()`
    3. Uses `build_hf_dataset()` to create the HF Dataset
    4. Optionally pushes to Hub (unless dry_run=True)

    Args:
        config: Configuration with BIDS root path and HF repo info.

    Raises:
        NotImplementedError: Until `build_soop_file_table()` is implemented.
    """
    # Build the file table from BIDS directory
    file_table = build_soop_file_table(config.bids_root)

    # Get the features schema
    features = get_soop_features()

    # Build the HF Dataset
    ds = build_hf_dataset(config, file_table, features)

    # Push to Hub if not a dry run
    if not config.dry_run:
        push_dataset_to_hub(ds, config)
