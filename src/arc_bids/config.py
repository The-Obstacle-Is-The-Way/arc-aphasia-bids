"""
Configuration for the ARC (Aphasia Recovery Cohort) dataset.

This module provides:
- `BidsDatasetConfig`: A dataclass for dataset configuration
- `ARC_CONFIG`: Pre-defined config for the ARC dataset

Dataset: https://openneuro.org/datasets/ds004884
License: CC0 (Public Domain)

Example:
    ```python
    from arc_bids.config import ARC_CONFIG
    from pathlib import Path

    # Override with your local path
    my_config = BidsDatasetConfig(
        name="arc",
        bids_root=Path("data/openneuro/ds004884"),
        default_hf_repo="hugging-science/arc-aphasia-bids",
    )
    ```
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BidsDatasetConfig:
    """
    Configuration for a BIDS dataset.

    Attributes:
        name: Short identifier for the dataset.
        bids_root: Path to the root of the BIDS dataset directory.
        default_hf_repo: Default HuggingFace Hub repository ID.
    """

    name: str
    bids_root: Path
    default_hf_repo: str | None = None


# =============================================================================
# ARC Dataset Configuration
#
# OpenNeuro: https://openneuro.org/datasets/ds004884
# Paper: https://www.nature.com/articles/s41597-024-03819-7
# License: CC0 (Public Domain)
# =============================================================================

ARC_CONFIG = BidsDatasetConfig(
    name="arc",
    bids_root=Path("data/openneuro/ds004884"),  # Default local path
    default_hf_repo="hugging-science/arc-aphasia-bids",
)
