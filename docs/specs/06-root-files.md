# Phase 06: Root Files Update

> Status: Ready after Phase 05
> Blocking: No
> Estimated: 1-2 hours

---

## Goal

Update root-level files to reflect multi-dataset support and new structure.

---

## Files to Update

1. `README.md` - Main repo documentation
2. `CLAUDE.md` - AI assistant instructions
3. `pyproject.toml` - Package metadata
4. `UPSTREAM_BUG.md` - May need updates

---

## Implementation Steps

### Step 1: Update README.md

Key changes:
- Title: "arc-bids" → "bids-hub" (already renamed in Phase 01a)
- Add ISLES24 to supported datasets table
- Update quick start with both datasets
- Update architecture diagram
- Add links to both HF repos

```markdown
# bids-hub

Upload BIDS neuroimaging datasets to HuggingFace Hub.

## Supported Datasets

| Dataset | HuggingFace | Size | License |
|---------|-------------|------|---------|
| [ARC](https://openneuro.org/datasets/ds004884) | [hugging-science/arc-aphasia-bids](https://hf.co/datasets/hugging-science/arc-aphasia-bids) | 293 GB | CC0 |
| [ISLES24](https://isles-24.grand-challenge.org/) | [hugging-science/isles24-stroke](https://hf.co/datasets/hugging-science/isles24-stroke) | ~100 GB | CC BY-NC-SA 4.0 |

## Quick Start

### ARC Dataset
\`\`\`bash
# Validate local download
uv run bids-hub arc validate data/openneuro/ds004884

# Upload to HuggingFace
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
\`\`\`

### ISLES24 Dataset
\`\`\`bash
# Validate local download
uv run bids-hub isles24 validate data/zenodo/isles24/train

# Upload to HuggingFace
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
\`\`\`

## Architecture

\`\`\`
src/bids_hub/
├── core/           # Generic BIDS→HF utilities (upstream candidate)
├── datasets/       # Per-dataset modules (ARC, ISLES24)
├── validation/     # Per-dataset validation
└── cli.py          # Command-line interface
\`\`\`

See [docs/explanation/architecture.md](docs/explanation/architecture.md) for details.
```

### Step 2: Update CLAUDE.md

Key changes:
- Update module responsibilities table
- Add ISLES24 commands
- Update architecture section
- Add ISLES24 schema

```markdown
## Commands

\`\`\`bash
# ARC commands
uv run bids-hub arc validate data/openneuro/ds004884
uv run bids-hub arc build data/openneuro/ds004884 --dry-run
uv run bids-hub arc info

# ISLES24 commands
uv run bids-hub isles24 validate data/zenodo/isles24/train
uv run bids-hub isles24 build data/zenodo/isles24/train --dry-run
\`\`\`

## Architecture

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `core/builder.py` | Generic BIDS→HF conversion |
| `core/config.py` | DatasetBuilderConfig dataclass |
| `datasets/arc.py` | ARC schema, file discovery, pipeline |
| `datasets/isles24.py` | ISLES24 schema, file discovery, pipeline |
| `validation/base.py` | Generic validation framework |
| `validation/arc.py` | ARC validation rules |
| `validation/isles24.py` | ISLES24 validation rules |
| `cli.py` | Typer CLI with subcommands |
```

### Step 3: Update pyproject.toml

Key changes:
- Package already renamed in Phase 01a
- Update description
- Add ISLES24 keywords

```toml
[project]
name = "bids-hub"
version = "0.2.0"  # Bump version
description = "Upload BIDS neuroimaging datasets (ARC, ISLES24) to HuggingFace Hub"
keywords = [
    "bids", "nifti", "neuroimaging", "huggingface", "datasets",
    "arc", "aphasia", "stroke",
    "isles", "isles24",
    "mri", "ct", "perfusion"
]
```

### Step 4: Review UPSTREAM_BUG.md

Check if any bug info is stale or resolved.

---

## Success Criteria

- [x] README reflects multi-dataset support
- [x] CLAUDE.md has updated commands and architecture
- [x] pyproject.toml description updated
- [x] Version bumped appropriately
- [x] No stale references to old structure

---

## Next Phase

After root files update → Phase 07: Upstream Contribution (Future)
