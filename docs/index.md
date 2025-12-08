# bids-hub Documentation

Upload BIDS neuroimaging datasets to HuggingFace Hub.

## Supported Datasets

| Dataset | HuggingFace Repo | Size |
|---------|------------------|------|
| ARC (Aphasia Recovery Cohort) | [hugging-science/arc-aphasia-bids](https://hf.co/datasets/hugging-science/arc-aphasia-bids) | 293 GB |
| ISLES 2024 | [hugging-science/isles24-stroke](https://hf.co/datasets/hugging-science/isles24-stroke) | ~100 GB |

## Quick Start

### ARC Dataset
```bash
# Download
./scripts/download_arc.sh

# Validate
uv run bids-hub arc validate data/openneuro/ds004884

# Upload
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

### ISLES24 Dataset
```bash
# Download
./scripts/download_isles24.sh

# Validate
uv run bids-hub isles24 validate data/zenodo/isles24/train

# Upload
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
```

---

## Documentation

### Tutorials
**Learning-oriented:** Get started from scratch

- [Upload ARC Dataset](tutorials/upload-arc.md)
- [Upload ISLES24 Dataset](tutorials/upload-isles24.md)

### How-to Guides
**Task-oriented:** Solve specific problems

- [Fix Empty/Zero-Byte Uploads](how-to/fix-empty-uploads.md)
- [Validate Before Upload](how-to/validate-before-upload.md)

### Reference
**Information-oriented:** Technical specifications

- [CLI Reference](reference/cli.md) - Command-line interface
- [Python API](reference/api.md) - Module and function reference
- [Schema Specification](reference/schema.md) - Dataset schema for ARC and ISLES24

### Explanation
**Understanding-oriented:** Background and concepts

- [Why Uploads Fail](explanation/why-uploads-fail.md) - The "metadata trap" and other pitfalls
- [Architecture Decisions](explanation/architecture.md) - Design rationale
