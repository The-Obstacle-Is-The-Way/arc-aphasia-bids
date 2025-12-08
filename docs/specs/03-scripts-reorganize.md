# Phase 03: Scripts Cleanup

> Status: Ready after Phase 02
> Blocking: No
> Estimated: 30 minutes
> Updated: Aligned with upstream `specs_from_upstream/04-export-cleanup.md`

---

## Goal

**DELETE** validation scripts that duplicate CLI functionality.
**KEEP** download scripts (useful standalone utilities).

---

## Current State

```
scripts/
├── download_arc.sh               # KEEP - useful standalone
├── validate_download.py          # DELETE - use CLI
├── validate_hf_download.py       # DELETE - use CLI
├── validate_isles24_download.py  # DELETE - use CLI
└── validate_isles24_hf_upload.py # DELETE - use CLI
```

**Problem**: Validation scripts duplicate CLI functionality, causing maintenance burden.

---

## Target State

```
scripts/
├── download_arc.sh      # Download ARC from OpenNeuro
└── download_isles24.sh  # Download ISLES24 from Zenodo (NEW)
```

All validation is done via CLI:
```bash
bids-hub arc validate /path/to/arc
bids-hub isles24 validate /path/to/isles24
```

---

## Why DELETE Instead of Reorganize?

**Original plan**: Reorganize scripts into `scripts/{arc,isles24}/`

**Upstream recommendation**: DELETE and use CLI instead

**Rationale**:
1. CLI provides the same functionality
2. Scripts duplicate module logic → maintenance burden
3. CLI has better UX (help text, consistent flags)
4. Reduces code to maintain

---

## Implementation Checklist

### Step 1: Ensure CLI Validation Works

Before deleting scripts, verify CLI works:

```bash
bids-hub arc validate data/openneuro/ds004884
bids-hub isles24 validate data/zenodo/isles24/train
```

### Step 2: Delete Validation Scripts

```bash
rm scripts/validate_download.py
rm scripts/validate_hf_download.py
rm scripts/validate_isles24_download.py
rm scripts/validate_isles24_hf_upload.py
```

### Step 3: Create ISLES24 Download Script

```bash
#!/usr/bin/env bash
# scripts/download_isles24.sh
# Download ISLES24 from Zenodo
# Requires: curl, 7z (p7zip)
#
# Usage:
#   ./scripts/download_isles24.sh [target_dir]

set -euo pipefail

ZENODO_RECORD="17652035"
ZENODO_URL="https://zenodo.org/records/${ZENODO_RECORD}/files/train.7z"
TARGET_DIR="${1:-data/zenodo/isles24}"

echo "=== ISLES24 Download ==="
echo "Source: Zenodo record ${ZENODO_RECORD}"
echo "Target: ${TARGET_DIR}"
echo ""

mkdir -p "${TARGET_DIR}"

echo "Downloading train.7z (~99GB)..."
curl -L -C - -o "${TARGET_DIR}/train.7z" "${ZENODO_URL}"

echo "Extracting..."
7z x "${TARGET_DIR}/train.7z" -o"${TARGET_DIR}/" -y

echo ""
echo "=== Download Complete ==="
echo "Validate with:"
echo "  bids-hub isles24 validate ${TARGET_DIR}/train"
```

### Step 4: Update Documentation

Update docs to use CLI instead of scripts:

**Old:**
```bash
python scripts/validate_download.py data/openneuro/ds004884
```

**New:**
```bash
bids-hub arc validate data/openneuro/ds004884
```

Files to update:
- `docs/how-to/validate-before-upload.md`
- `CLAUDE.md`
- `README.md`

---

## Success Criteria

- [ ] `bids-hub arc validate` works
- [ ] `bids-hub isles24 validate` works
- [ ] Validation scripts deleted
- [ ] `scripts/download_arc.sh` still works
- [ ] `scripts/download_isles24.sh` created and works
- [ ] Docs updated to use CLI

---

## Next Phase

After scripts cleanup → Phase 04: SRC Reorganization
