"""
Configuration structures for BIDS dataset definitions.

This module provides:
- `BidsDatasetConfig`: A dataclass for storing dataset-specific configuration
- Pre-defined config placeholders for known datasets (ARC, SOOP)

These configurations are meant to be customized by users who have downloaded
the actual BIDS data locally from OpenNeuro or other sources.

Example usage:
    ```python
    from hf_bids_nifti.config import BidsDatasetConfig
    from pathlib import Path

    my_config = BidsDatasetConfig(
        name="my-dataset",
        bids_root=Path("/data/openneuro/ds000001"),
        default_hf_repo="myuser/my-dataset-hf",
    )
    ```
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BidsDatasetConfig:
    """
    Configuration for a specific BIDS dataset.

    This is used to register known datasets and provide default paths/repos.
    Users should customize `bids_root` to point to their local copy of the data.

    Attributes:
        name: Short identifier for the dataset (e.g., "arc", "soop").
        bids_root: Path to the root of the BIDS dataset directory.
            NOTE: This is a placeholder and MUST be customized by the user.
        default_hf_repo: Optional default Hugging Face Hub repository ID.
            If None, the user must specify a repo when pushing.
    """

    name: str
    bids_root: Path
    default_hf_repo: str | None = None


# =============================================================================
# Pre-defined dataset configurations (PLACEHOLDERS)
#
# These paths are examples only. Users must download the actual data from
# OpenNeuro and update these paths accordingly.
#
# ARC Dataset: https://openneuro.org/datasets/ds004884
# SOOP Dataset: https://openneuro.org/datasets/ds004889
# =============================================================================

ARC_CONFIG = BidsDatasetConfig(
    name="arc",
    bids_root=Path("/path/to/ds004884"),  # USER MUST OVERRIDE with actual path
    default_hf_repo=None,  # e.g., "The-Obstacle-Is-The-Way/arc-bids"
)

SOOP_CONFIG = BidsDatasetConfig(
    name="soop",
    bids_root=Path("/path/to/ds004889"),  # USER MUST OVERRIDE with actual path
    default_hf_repo=None,  # e.g., "The-Obstacle-Is-The-Way/soop-bids"
)

# Registry of known dataset configs for easy lookup
DATASET_REGISTRY: dict[str, BidsDatasetConfig] = {
    "arc": ARC_CONFIG,
    "soop": SOOP_CONFIG,
}


def get_dataset_config(name: str) -> BidsDatasetConfig:
    """
    Retrieve a registered dataset configuration by name.

    Args:
        name: The dataset identifier (e.g., "arc", "soop").

    Returns:
        The BidsDatasetConfig for the requested dataset.

    Raises:
        KeyError: If the dataset name is not registered.
    """
    if name not in DATASET_REGISTRY:
        available = sorted(DATASET_REGISTRY.keys())
        raise KeyError(f"Unknown dataset '{name}'. Available: {available}")
    return DATASET_REGISTRY[name]
