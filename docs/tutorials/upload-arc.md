# Tutorial: Upload ARC Dataset

> **Time**: 30 minutes (excluding upload time)
> **Prerequisites**: Python 3.11+, uv, HuggingFace account

This tutorial walks you through uploading the **ARC (Aphasia Recovery Cohort)** dataset to HuggingFace Hub.

---

## Step 1: Download ARC

Use the provided script to download from OpenNeuro (ds004884):

```bash
# Download full dataset (~278GB)
./scripts/download_arc.sh data/openneuro/ds004884
```

---

## Step 2: Validate Download

Ensure data integrity before uploading:

```bash
uv run bids-hub arc validate data/openneuro/ds004884
```

Expected output:

```text
Validation Results for: data/openneuro/ds004884
============================================================
✅ PASS bids_required_files
✅ PASS subjects
✅ PASS participants_tsv
✅ PASS t1w_sessions
...
✅ All validations passed! Data is ready for HF push.
```

---

## Step 3: Build and Upload

Run the build command. Use `--dry-run` first to verify the file table construction.

```bash
# Dry run (safe, no upload)
uv run bids-hub arc build data/openneuro/ds004884 --dry-run

# Full upload (requires authentication)
huggingface-cli login
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

---

## Step 4: Verify on HuggingFace

Go to your dataset page (e.g., `https://huggingface.co/datasets/hugging-science/arc-aphasia-bids`) and check the viewer. You should see NIfTI files rendered with NiiVue.
