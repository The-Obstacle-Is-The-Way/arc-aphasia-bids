# Phase 01a: Package Renaming

> Status: Ready
> Blocking: YES - Must be done first (all imports change)
> Estimated: 1-2 hours
> Source: Adapted from upstream `specs_from_upstream/01-package-renaming.md`

---

## Problem

Package is named `arc-bids` / `arc_bids` but now supports multiple datasets (ARC, ISLES24). The name implies ARC-only scope.

```toml
# Current pyproject.toml
[project]
name = "arc-bids"  # Misleading - not ARC-only anymore
```

---

## Solution

Rename to `bids-hub` - clear, generic, reflects multi-dataset purpose.

```
bids-hub/
└── src/bids_hub/
    ├── core.py
    ├── arc.py
    ├── isles24.py
    └── ...
```

**CLI**: `bids-hub arc build ...`

---

## Implementation Checklist

### Step 1: Directory Rename

```bash
mv src/arc_bids src/bids_hub
```

### Step 2: Update `pyproject.toml`

```toml
[project]
name = "bids-hub"
description = "Upload BIDS neuroimaging datasets to HuggingFace Hub"
keywords = ["bids", "nifti", "neuroimaging", "huggingface", "datasets", "mri", "stroke", "aphasia", "isles"]

[project.scripts]
bids-hub = "bids_hub.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/bids_hub"]

[tool.ruff.lint.isort]
known-first-party = ["bids_hub"]
```

### Step 3: Update All Imports

Find and replace across all files:

| Old | New |
|-----|-----|
| `from arc_bids` | `from bids_hub` |
| `import arc_bids` | `import bids_hub` |
| `arc_bids.` | `bids_hub.` |

Files to update:
- `src/bids_hub/__init__.py`
- `src/bids_hub/cli.py`
- `src/bids_hub/arc.py`
- `src/bids_hub/isles24.py`
- `src/bids_hub/config.py`
- `src/bids_hub/core.py`
- `src/bids_hub/validation.py`
- `tests/*.py`
- `scripts/*.py`

### Step 4: Update CLI Help Text

```python
# cli.py
app = typer.Typer(
    name="bids-hub",
    help="Upload BIDS neuroimaging datasets to HuggingFace Hub.",
)
```

### Step 5: Update `__init__.py` Docstring

```python
"""
bids_hub - Upload BIDS neuroimaging datasets to HuggingFace Hub.

Supported datasets:
- ARC (Aphasia Recovery Cohort) - OpenNeuro ds004884
- ISLES24 (Ischemic Stroke Lesion Segmentation) - Zenodo
...
"""
```

### Step 6: Update Documentation

Files to update:
- `README.md`
- `CLAUDE.md`
- `GEMINI.md`
- `docs/**/*.md`

### Step 7: Run Tests

```bash
uv run pytest -v
```

Fix any import errors.

---

## Verification

```bash
# CLI should work
bids-hub --help
bids-hub arc build --help
bids-hub isles24 build --help

# Imports should work
python -c "from bids_hub import build_hf_dataset, build_arc_file_table"
python -c "from bids_hub.isles24 import build_isles24_file_table"

# Tests should pass
uv run pytest -v
```

---

## Note on GitHub Repo Name

Keep repo as `arc-aphasia-bids` for now. Renaming GitHub repo breaks links and is optional. The package name (`bids-hub`) and repo name can differ.

---

## Success Criteria

- [ ] `src/bids_hub/` directory exists
- [ ] `src/arc_bids/` deleted
- [ ] `bids-hub --help` works
- [ ] All imports work
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

---

## Next Phase

After package rename → Phase 01b: CLI Normalization
