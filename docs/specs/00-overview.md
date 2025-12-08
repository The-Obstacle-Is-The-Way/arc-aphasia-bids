# Phase 00: Overview & Execution Order

> Status: MASTER INDEX
> Purpose: Map of all specs and execution order
> Updated: Integrated upstream specs from `specs_from_upstream/`

---

## What We're Building

**Core Infrastructure** (should go upstream to `datasets` library):
- `build_hf_dataset()` - Convert file table → HF Dataset
- `push_dataset_to_hub()` - Memory-safe sharded upload
- `ValidationCheck` / `ValidationResult` / `DatasetValidationConfig` - Generic validation framework
- `check_zero_byte_files()` - Fast corruption detection
- Workarounds for upstream bugs (#7894, #7893)

**Dataset Modules** (what researchers write per-dataset):
- Schema definition (`get_{dataset}_features()`)
- File discovery (`build_{dataset}_file_table()`)
- Validation config (expected counts, patterns)
- Download scripts

---

## Execution Order

| Phase | Spec File | Description | Status |
|-------|-----------|-------------|--------|
| 00-a | `00-isles24-download.md` | Download ISLES24 from Zenodo | ✅ DONE |
| 01 | `01-isles24-upload.md` | Upload ISLES24 NOW (no refactor) | ✅ DONE |
| 01a | `01a-package-rename.md` | Rename `arc-bids` → `bids-hub` | **BLOCKING** |
| 01b | `01b-cli-normalization.md` | Move ARC to subcommand | Ready |
| 02 | `02-validation-refactor.md` | Extract generic validation + DatasetValidationConfig | Ready |
| 03 | `03-scripts-reorganize.md` | DELETE validation scripts, use CLI | Ready |
| 04 | `04-src-reorganize.md` | Create core/, datasets/, validation/ subdirs | Ready |
| 05 | `05-docs-cleanup.md` | Dataset cards, consolidate docs | Ready |
| 06 | `06-root-files.md` | README, pyproject.toml updates | Ready |
| 07 | `07-upstream-contrib.md` | Future: contribute core to HF | Future |

### Recommended Execution Order

```
Phase 01a (Rename)       # Foundation - all imports change
    ↓
Phase 01b (CLI)          # Better UX immediately
    ↓
Phase 02 (Validation)    # Extract generic framework
    ↓
Phase 03 (Scripts)       # Delete after CLI works
    ↓
Phase 04 (SRC)           # Create subdirs
    ↓
Phase 05 (Docs)          # Update for new structure
    ↓
Phase 06 (Root)          # README, CLAUDE.md
    ↓
Phase 07 (Upstream)      # Future
```

---

## Current State

```
src/arc_bids/                # ← Will become src/bids_hub/
├── __init__.py              # Only exports ARC ❌
├── core.py                  # GENERIC ✅
├── config.py                # ARC + ISLES24 configs
├── arc.py                   # ARC-specific ✅
├── isles24.py               # ISLES24-specific ✅
├── validation.py            # ARC-only ❌ (needs split)
└── cli.py                   # ARC top-level, ISLES24 subcommand ❌

scripts/
├── download_arc.sh          # KEEP
├── validate_download.py     # DELETE (use CLI)
├── validate_hf_download.py  # DELETE (use CLI)
├── validate_isles24_download.py  # DELETE (use CLI)
└── validate_isles24_hf_upload.py # DELETE (use CLI)
```

---

## Target State

```
src/bids_hub/                # ← Renamed from arc_bids
├── __init__.py              # Exports ARC + ISLES24 + check_zero_byte_files
├── cli.py                   # Both arc & isles24 as subcommands
│
├── core/                    # GENERIC (upstream candidate)
│   ├── __init__.py
│   ├── builder.py           # build_hf_dataset, push_dataset_to_hub
│   ├── config.py            # DatasetBuilderConfig
│   └── utils.py             # find_single_nifti, find_all_niftis
│
├── validation/              # GENERIC + SPECIFIC
│   ├── __init__.py
│   ├── base.py              # ValidationCheck, ValidationResult, DatasetValidationConfig
│   ├── arc.py               # ARC_VALIDATION_CONFIG, validate_arc_download
│   └── isles24.py           # ISLES24_VALIDATION_CONFIG, validate_isles24_download
│
└── datasets/                # DATASET-SPECIFIC
    ├── __init__.py
    ├── arc.py               # build_arc_file_table, get_arc_features
    └── isles24.py           # build_isles24_file_table, get_isles24_features

scripts/
├── download_arc.sh          # Download ARC from OpenNeuro
└── download_isles24.sh      # Download ISLES24 from Zenodo

docs/
├── dataset-cards/
│   ├── arc-aphasia-bids.md
│   └── isles24-stroke.md
└── ...
```

---

## Key Changes from Upstream Integration

| Change | Source | Rationale |
|--------|--------|-----------|
| Package rename `bids-hub` | upstream 01 | Multi-dataset scope |
| CLI normalization | upstream 03 | Consistent UX |
| `DatasetValidationConfig` | upstream 02 | Config-driven validation |
| `check_zero_byte_files()` | upstream 02 | Fast corruption detection |
| DELETE scripts vs reorganize | upstream 04 | CLI replaces them |

---

## Rules

1. **One spec = one PR** (ideally)
2. **Tests before refactor** - Ensure coverage before moving code
3. **Phase 01a is blocking** - Package rename first
4. **Backward compatibility** - Re-export moved symbols in `__init__.py`
5. **Validate claims** - Specs were written without direct repo access; verify before implementing
