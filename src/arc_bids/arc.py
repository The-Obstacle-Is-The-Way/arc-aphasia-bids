"""
ARC (Aphasia Recovery Cohort) dataset module.

This module converts the ARC BIDS dataset (OpenNeuro ds004884) into a
Hugging Face Dataset.

Dataset info:
- OpenNeuro ID: ds004884
- Description: Structural MRI and lesion masks for aphasia patients
- License: CC0 (Public Domain)
- URL: https://openneuro.org/datasets/ds004884

The ARC dataset contains:
- 230 chronic stroke patients with aphasia
- 902 scanning sessions (longitudinal)
- T1-weighted structural MRI scans
- T2-weighted structural MRI scans
- Expert-drawn lesion segmentation masks
- Demographic and clinical metadata (age, sex, WAB-AQ scores)
"""

from pathlib import Path

import pandas as pd
from datasets import Features, Nifti, Value

from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub


def _find_first_nifti(directory: Path, pattern: str) -> str | None:
    """Find the first NIfTI file matching a pattern in a directory tree.

    Args:
        directory: Root directory to search.
        pattern: Glob pattern to match (e.g., "*_T1w.nii.gz").

    Returns:
        Absolute path to the first matching file, or None if not found.
    """
    matches = list(directory.rglob(pattern))
    if matches:
        return str(matches[0].resolve())
    return None


def _read_nifti_bytes(path: str | None) -> dict[str, bytes | str] | None:
    """Read a NIfTI file and return bytes dict for HF Nifti feature.

    The HuggingFace Nifti() feature type doesn't have embed_storage support
    (unlike Image/Audio), so we must read bytes explicitly for push_to_hub
    to embed the file contents in Parquet shards.

    Args:
        path: Absolute path to NIfTI file, or None.

    Returns:
        Dict with 'bytes' and 'path' keys, or None if path is None.
    """
    if path is None:
        return None

    with open(path, "rb") as f:
        file_bytes = f.read()

    return {"bytes": file_bytes, "path": path}


def build_arc_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the ARC dataset.

    Walks the BIDS directory structure and builds a pandas DataFrame with
    one row per subject containing paths to imaging data and metadata.

    The function:
    1. Reads participants.tsv for demographics (age, sex, WAB scores)
    2. For each subject, finds T1w and T2w images in sub-*/ses-*/anat/
    3. Finds lesion masks in derivatives/lesion_masks/sub-*/ses-*/anat/
    4. Returns a DataFrame ready for HF Dataset conversion

    Args:
        bids_root: Path to the root of the ARC BIDS dataset (ds004884).

    Returns:
        DataFrame with columns:
            - subject_id (str): BIDS subject identifier (e.g., "sub-M2001")
            - t1w (str | None): Absolute path to T1-weighted NIfTI
            - t2w (str | None): Absolute path to T2-weighted NIfTI
            - lesion (str | None): Absolute path to lesion mask NIfTI
            - age_at_stroke (float): Subject age at stroke
            - sex (str): Subject sex (M/F)
            - wab_aq (float): WAB Aphasia Quotient (severity score)
            - wab_type (str): Aphasia type classification

    Raises:
        FileNotFoundError: If participants.tsv doesn't exist.
        ValueError: If bids_root doesn't exist or is not a directory.
    """
    bids_root = Path(bids_root).resolve()

    if not bids_root.exists():
        raise ValueError(f"BIDS root does not exist: {bids_root}")
    if not bids_root.is_dir():
        raise ValueError(f"BIDS root is not a directory: {bids_root}")

    # Read participants.tsv
    participants_tsv = bids_root / "participants.tsv"
    if not participants_tsv.exists():
        raise FileNotFoundError(f"participants.tsv not found at {participants_tsv}")

    participants = pd.read_csv(participants_tsv, sep="\t")

    # Build file table
    # Note: NIfTI columns store dict with 'bytes' and 'path' keys because
    # HF Nifti() doesn't have embed_storage support (unlike Image/Audio)
    rows: list[dict[str, str | float | dict[str, bytes | str] | None]] = []

    for _, row in participants.iterrows():
        subject_id = str(row["participant_id"])
        subject_dir = bids_root / subject_id

        # Find and read T1w image (search all sessions)
        t1w_path = _find_first_nifti(subject_dir, "*_T1w.nii.gz") if subject_dir.exists() else None
        t1w_data = _read_nifti_bytes(t1w_path)

        # Find and read T2w image (search all sessions)
        t2w_path = _find_first_nifti(subject_dir, "*_T2w.nii.gz") if subject_dir.exists() else None
        t2w_data = _read_nifti_bytes(t2w_path)

        # Find and read lesion mask in derivatives
        lesion_dir = bids_root / "derivatives" / "lesion_masks" / subject_id
        lesion_path = (
            _find_first_nifti(lesion_dir, "*_desc-lesion_mask.nii.gz")
            if lesion_dir.exists()
            else None
        )
        lesion_data = _read_nifti_bytes(lesion_path)

        # Extract metadata with safe type conversion
        age_at_stroke = row.get("age_at_stroke")
        try:
            age_at_stroke = float(age_at_stroke) if pd.notna(age_at_stroke) else None
        except (ValueError, TypeError):
            age_at_stroke = None

        wab_aq = row.get("wab_aq")
        try:
            wab_aq = float(wab_aq) if pd.notna(wab_aq) else None
        except (ValueError, TypeError):
            wab_aq = None

        sex = str(row.get("sex", "")) if pd.notna(row.get("sex")) else None
        wab_type = str(row.get("wab_type", "")) if pd.notna(row.get("wab_type")) else None

        rows.append({
            "subject_id": subject_id,
            "t1w": t1w_data,
            "t2w": t2w_data,
            "lesion": lesion_data,
            "age_at_stroke": age_at_stroke,
            "sex": sex,
            "wab_aq": wab_aq,
            "wab_type": wab_type,
        })

    return pd.DataFrame(rows)


def get_arc_features() -> Features:
    """
    Get the Hugging Face Features schema for the ARC dataset.

    Schema:
        - subject_id: BIDS identifier (e.g., "sub-M2001")
        - t1w: T1-weighted structural MRI (Nifti)
        - t2w: T2-weighted structural MRI (Nifti, nullable)
        - lesion: Expert-drawn lesion mask (Nifti)
        - age_at_stroke: Age at time of stroke (float)
        - sex: Biological sex (M/F)
        - wab_aq: WAB Aphasia Quotient (severity score, 0-100)
        - wab_type: Aphasia type classification

    Returns:
        Features object with Nifti() for image columns and Value() for metadata.
    """
    return Features(
        {
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "t2w": Nifti(),
            "lesion": Nifti(),
            "age_at_stroke": Value("float32"),
            "sex": Value("string"),
            "wab_aq": Value("float32"),
            "wab_type": Value("string"),
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
        FileNotFoundError: If participants.tsv doesn't exist.
        ValueError: If bids_root doesn't exist or is not a directory.
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
