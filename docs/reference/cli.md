# CLI Reference

> Command-line interface for arc-bids.

---

## Installation

```bash
uv add arc-bids
# or
pip install arc-bids
```

---

## Commands

### `arc-bids build`

Build and upload a BIDS dataset to HuggingFace Hub.

```bash
arc-bids build <bids_root> --hf-repo <repo_id> [options]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `bids_root` | Path to the BIDS dataset root directory |

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--hf-repo`, `-r` | `hugging-science/arc-aphasia-bids` | HuggingFace repo ID (e.g., `org/dataset-name`) |
| `--dry-run` | `True` | Build dataset locally without pushing to Hub |
| `--no-dry-run` | - | Explicitly disable dry run (push to Hub) |

#### Examples

```bash
# Dry run (build locally, don't upload)
arc-bids build data/openneuro/ds004884 --hf-repo hugging-science/arc-aphasia-bids

# Full upload
arc-bids build data/openneuro/ds004884 --hf-repo hugging-science/arc-aphasia-bids --no-dry-run
```

#### Output

```text
Processing ARC dataset from: data/openneuro/ds004884
Target HF repo: hugging-science/arc-aphasia-bids
Dry run: False
Building file table...
File table has 902 rows
Building HF dataset...
Pushing to Hub with num_shards=902 to prevent OOM
Uploading the dataset shards:   5%|█▌        | 45/902 [02:15<42:30, 3.0s/shard]
```

---

### `arc-bids validate`

Validate an ARC dataset download before pushing to HuggingFace.

```bash
arc-bids validate <bids_root> [options]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `bids_root` | Path to the BIDS dataset root directory |

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--bids-validator/--no-bids-validator` | `False` | Run external BIDS validator (requires npx, slow) |
| `--sample-size`, `-n` | `10` | Number of NIfTI files to spot-check for integrity |

#### Validation Checks

1. Required BIDS files exist (`dataset_description.json`, `participants.tsv`)
2. Subject count matches expected (~230 from Sci Data paper)
3. Series counts match paper (T1w, T2w, FLAIR, BOLD, DWI, sbref, lesion)
4. Sample NIfTI files are loadable with nibabel
5. (Optional) External BIDS validator passes

#### Example

```bash
# Basic validation
arc-bids validate data/openneuro/ds004884

# With NIfTI integrity check on 20 files
arc-bids validate data/openneuro/ds004884 --sample-size 20

# With external BIDS validator (slow)
arc-bids validate data/openneuro/ds004884 --bids-validator
```

---

### `arc-bids info`

Show information about the ARC dataset.

```bash
arc-bids info
```

#### Output

```text
Aphasia Recovery Cohort (ARC)
========================================
OpenNeuro ID: ds004884
URL: https://openneuro.org/datasets/ds004884
License: CC0 (Public Domain)

Contains:
  - 230 chronic stroke patients
  - 902 scanning sessions
  - T1w, T2w, FLAIR, diffusion, fMRI
  - Expert lesion masks
  - WAB (Western Aphasia Battery) scores

Expected series counts (from Sci Data paper):
  - T1w: 441 series
  - T2w: 447 series
  - FLAIR: 235 series
  - Lesion masks: 230
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | HuggingFace API token (alternative to `huggingface-cli login`) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (check stderr for details) |

---

## Related

- [Tutorial: First Upload](../tutorials/first-upload.md)
- [Python API](api.md)
