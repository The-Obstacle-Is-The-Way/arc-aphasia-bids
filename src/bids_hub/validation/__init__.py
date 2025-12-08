"""Validation module - re-exports for backward compatibility."""

from .arc import (
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,  # Backward compat
    REQUIRED_BIDS_FILES,  # Backward compat
    validate_arc_download,
)
from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    check_zero_byte_files,
    validate_dataset,
    verify_md5,
)
from .isles24 import (
    ISLES24_ARCHIVE_MD5,
    ISLES24_VALIDATION_CONFIG,
    check_phenotype_readable,
    validate_isles24_download,
    verify_isles24_archive,
)

__all__ = [
    # Generic framework
    "DatasetValidationConfig",
    "ValidationCheck",
    "ValidationResult",
    "check_count",
    "check_zero_byte_files",
    "validate_dataset",
    "verify_md5",
    # ARC
    "ARC_VALIDATION_CONFIG",
    "EXPECTED_COUNTS",
    "REQUIRED_BIDS_FILES",
    "validate_arc_download",
    # ISLES24
    "ISLES24_ARCHIVE_MD5",
    "ISLES24_VALIDATION_CONFIG",
    "check_phenotype_readable",
    "validate_isles24_download",
    "verify_isles24_archive",
]
