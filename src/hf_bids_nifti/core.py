"""
Core module for BIDS → Hugging Face Dataset conversion.

This module provides generic, dataset-agnostic utilities for:
- Building HF Datasets from pandas DataFrames containing NIfTI file paths
- Pushing datasets to the Hugging Face Hub

The typical workflow for a specific BIDS dataset (e.g., ARC, SOOP) is:
1. Implement a `build_*_file_table()` function that walks the BIDS directory
   and returns a pandas DataFrame with one row per subject/session
2. Define a `get_*_features()` function that returns the HF Features schema
3. Call `build_hf_dataset()` with the file table and features
4. Optionally push to Hub with `push_dataset_to_hub()`

Example usage:
    ```python
    from hf_bids_nifti.core import DatasetBuilderConfig, build_hf_dataset
    from datasets import Features, Nifti, Value

    # Your file table with paths to NIfTI files
    file_table = pd.DataFrame({
        "subject_id": ["sub-001", "sub-002"],
        "t1w": ["/path/to/sub-001_T1w.nii.gz", "/path/to/sub-002_T1w.nii.gz"],
        "age": [25.0, 30.0],
    })

    features = Features({
        "subject_id": Value("string"),
        "t1w": Nifti(),
        "age": Value("float32"),
    })

    config = DatasetBuilderConfig(
        bids_root=Path("/path/to/bids"),
        hf_repo_id="user/my-dataset",
    )

    ds = build_hf_dataset(config, file_table, features)
    ```
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Dataset, Features


@dataclass
class DatasetBuilderConfig:
    """
    Configuration for building a Hugging Face Dataset from BIDS data.

    Attributes:
        bids_root: Path to the root of the BIDS dataset directory.
        hf_repo_id: Hugging Face Hub repository ID (e.g., "username/dataset-name").
        split: Optional split name (e.g., "train", "test"). If None, no split is assigned.
        dry_run: If True, skip pushing to Hub (useful for testing).
    """

    bids_root: Path
    hf_repo_id: str
    split: str | None = None
    dry_run: bool = False


def validate_file_table_columns(
    file_table: pd.DataFrame,
    features: Features,
) -> None:
    """
    Validate that all columns defined in features exist in the file table.

    Args:
        file_table: DataFrame containing file paths and metadata.
        features: HF Features schema defining expected columns.

    Raises:
        ValueError: If any feature column is missing from the file table.
    """
    expected_columns = set(features.keys())
    actual_columns = set(file_table.columns)
    missing = expected_columns - actual_columns

    if missing:
        raise ValueError(
            f"File table is missing columns required by features: {sorted(missing)}. "
            f"Expected: {sorted(expected_columns)}, Got: {sorted(actual_columns)}"
        )


def build_hf_dataset(
    config: DatasetBuilderConfig,  # noqa: ARG001 - reserved for future path resolution
    file_table: pd.DataFrame,
    features: Features,
) -> Dataset:
    """
    Build a Hugging Face Dataset from a pandas DataFrame with NIfTI file paths.

    This is the core generic function that converts a BIDS file table into an
    HF Dataset with properly typed columns (including Nifti columns).

    Args:
        config: Configuration containing BIDS root path and HF repo info.
            Currently used for API consistency; will be used in future versions
            for resolving relative file paths against bids_root.
        file_table: DataFrame with one row per "example" containing:
            - One or more columns with NIfTI file paths (as strings)
            - Scalar metadata columns (subject_id, age, etc.)
        features: HF Features object defining the schema, including:
            - `Nifti()` for NIfTI image columns
            - `Value("string")`, `Value("float32")`, etc. for metadata

    Returns:
        A Hugging Face Dataset with columns cast to the specified features.

    Raises:
        ValueError: If file_table is missing columns required by features.

    Example:
        ```python
        from datasets import Features, Nifti, Value

        file_table = pd.DataFrame({
            "subject_id": ["sub-001", "sub-002"],
            "t1w": ["path/to/t1w_001.nii.gz", "path/to/t1w_002.nii.gz"],
            "age": [25.0, 30.0],
        })

        features = Features({
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "age": Value("float32"),
        })

        ds = build_hf_dataset(config, file_table, features)
        ```
    """
    # Validate columns before processing
    validate_file_table_columns(file_table, features)

    # Select only the columns defined in features (in case file_table has extras)
    columns_to_use = list(features.keys())
    file_table_subset = file_table[columns_to_use].copy()

    # Create dataset from pandas DataFrame
    ds = Dataset.from_pandas(file_table_subset, preserve_index=False)

    # Cast columns to the specified features (this enables Nifti loading)
    ds = ds.cast(features)

    return ds


def push_dataset_to_hub(
    ds: Dataset,
    config: DatasetBuilderConfig,
    **push_kwargs: Any,
) -> None:
    """
    Push a dataset to the Hugging Face Hub.

    Assumes the user has already authenticated via `huggingface-cli login`
    or has set the HF_TOKEN environment variable.

    Args:
        ds: The Hugging Face Dataset to push.
        config: Configuration containing the target repo ID.
        **push_kwargs: Additional keyword arguments passed to `ds.push_to_hub()`.

    Example:
        ```python
        push_dataset_to_hub(ds, config, private=True)
        ```
    """
    ds.push_to_hub(config.hf_repo_id, **push_kwargs)
