# Tutorial: Upload ISLES24 Dataset

> **Time**: 20 minutes (excluding upload time)
> **Prerequisites**: Python 3.10+, uv, HuggingFace account

This tutorial walks you through uploading the **ISLES 2024 (Ischemic Stroke Lesion Segmentation)** dataset to HuggingFace Hub.

---

## Step 1: Download ISLES24

Use the provided script to download from Zenodo (Record 17652035):

```bash
# Download training set (~99GB)
./scripts/download_isles24.sh data/zenodo/isles24
```

This will download `train.7z`, extract it, and verify the MD5 checksum.

---

## Step 2: Validate Download

Ensure data integrity before uploading:

```bash
uv run bids-hub isles24 validate data/zenodo/isles24/train
```

Expected output:

```text
Validation Results for: data/zenodo/isles24/train
============================================================
✅ PASS zero_byte_files
✅ PASS required_files
✅ PASS subjects
✅ PASS ncct_count
...
✅ All validations passed! Data is ready for HF push.
```

---

## Step 3: Build and Upload

Run the build command. This will flatten the session structure into one row per subject.

```bash
# Dry run (safe, no upload)
uv run bids-hub isles24 build data/zenodo/isles24/train --dry-run

# Full upload (requires authentication)
huggingface-cli login
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
```

---

## Step 4: Verify on HuggingFace

Go to your dataset page (e.g., `https://huggingface.co/datasets/hugging-science/isles24-stroke`) and check the viewer. You should see paired Acute (CT) and Follow-up (DWI) scans for each subject.
