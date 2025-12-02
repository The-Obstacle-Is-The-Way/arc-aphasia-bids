"""
Tests for core BIDS → HF Dataset conversion functionality.

These tests use fake/minimal data to verify the core plumbing works
without requiring real NIfTI files or BIDS datasets.
"""

import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from datasets import Dataset, Features, Nifti, Value

from hf_bids_nifti.core import (
    DatasetBuilderConfig,
    build_hf_dataset,
    validate_file_table_columns,
)


@pytest.fixture
def dummy_config() -> DatasetBuilderConfig:
    """Create a dummy config for testing."""
    return DatasetBuilderConfig(
        bids_root=Path("/tmp/fake-bids"),
        hf_repo_id="test-user/test-dataset",
        dry_run=True,
    )


@pytest.fixture
def simple_features() -> Features:
    """Create a simple Features schema for testing."""
    return Features(
        {
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "age": Value("float32"),
        }
    )


@pytest.fixture
def temp_nifti_dir():
    """Create a temporary directory with fake NIfTI files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create minimal NIfTI files using nibabel
        for i in range(3):
            # Create a tiny 2x2x2 image (minimal valid NIfTI)
            data = np.ones((2, 2, 2), dtype=np.float32) * (i + 1)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, tmppath / f"sub-{i:03d}_T1w.nii.gz")

        yield tmppath


class TestValidateFileTableColumns:
    """Tests for validate_file_table_columns function."""

    def test_valid_columns(self, simple_features: Features) -> None:
        """Test that validation passes when all columns are present."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001", "sub-002"],
                "t1w": ["path/to/001.nii.gz", "path/to/002.nii.gz"],
                "age": [25.0, 30.0],
            }
        )

        # Should not raise
        validate_file_table_columns(file_table, simple_features)

    def test_extra_columns_allowed(self, simple_features: Features) -> None:
        """Test that extra columns in file_table are allowed."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001"],
                "t1w": ["path/to/001.nii.gz"],
                "age": [25.0],
                "extra_column": ["extra_value"],  # Not in features
            }
        )

        # Should not raise
        validate_file_table_columns(file_table, simple_features)

    def test_missing_columns_raises(self, simple_features: Features) -> None:
        """Test that missing columns raise ValueError."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001"],
                # Missing: t1w, age
            }
        )

        with pytest.raises(ValueError, match="missing columns"):
            validate_file_table_columns(file_table, simple_features)


class TestBuildHfDataset:
    """Tests for build_hf_dataset function."""

    def test_build_dataset_returns_dataset(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that build_hf_dataset returns a Dataset object."""
        # Create file table with real NIfTI paths
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000", "sub-001", "sub-002"],
                "t1w": [
                    str(temp_nifti_dir / "sub-000_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-001_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-002_T1w.nii.gz"),
                ],
                "age": [25.0, 30.0, 35.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert isinstance(ds, Dataset)
        assert len(ds) == 3

    def test_build_dataset_has_correct_columns(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that the resulting dataset has the expected columns."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000", "sub-001"],
                "t1w": [
                    str(temp_nifti_dir / "sub-000_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-001_T1w.nii.gz"),
                ],
                "age": [25.0, 30.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert set(ds.column_names) == {"subject_id", "t1w", "age"}

    def test_build_dataset_excludes_extra_columns(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that columns not in features are excluded from the dataset."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
                "extra_column": ["should_be_excluded"],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert "extra_column" not in ds.column_names

    def test_build_dataset_nifti_feature_type(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that Nifti columns have the correct feature type."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        # Check that the t1w feature is a Nifti type
        assert isinstance(ds.features["t1w"], Nifti)

    def test_build_dataset_can_load_nifti(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that NIfTI files can be loaded from the dataset."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        # Access the first example's NIfTI image
        example = ds[0]
        nifti_img = example["t1w"]

        # Should be a nibabel Nifti1Image
        assert isinstance(nifti_img, nib.nifti1.Nifti1Image)

        # Check we can get the data
        data = nifti_img.get_fdata()
        assert data.shape == (2, 2, 2)
        assert np.allclose(data, 1.0)  # First subject has all 1s


class TestDatasetBuilderConfig:
    """Tests for DatasetBuilderConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test that config can be created with required fields."""
        config = DatasetBuilderConfig(
            bids_root=Path("/path/to/bids"),
            hf_repo_id="user/dataset",
        )

        assert config.bids_root == Path("/path/to/bids")
        assert config.hf_repo_id == "user/dataset"
        assert config.split is None
        assert config.dry_run is False

    def test_config_with_optional_fields(self) -> None:
        """Test that optional fields can be set."""
        config = DatasetBuilderConfig(
            bids_root=Path("/path/to/bids"),
            hf_repo_id="user/dataset",
            split="train",
            dry_run=True,
        )

        assert config.split == "train"
        assert config.dry_run is True
