"""Generic file discovery utilities."""

from __future__ import annotations

from pathlib import Path


def find_single_nifti(search_dir: Path, pattern: str) -> str | None:
    """Find a single NIfTI file matching pattern.

    Returns the absolute path if exactly one match is found; otherwise None.
    """
    if not search_dir.is_dir():
        return None
    matches = sorted(search_dir.rglob(pattern), key=lambda p: p.name)
    if len(matches) != 1:
        return None
    return str(matches[0].resolve())


def find_all_niftis(search_dir: Path, pattern: str) -> list[str]:
    """Find all NIfTI files matching pattern."""
    if not search_dir.is_dir():
        return []
    matches = list(search_dir.rglob(pattern))
    matches.sort(key=lambda p: p.name)
    return [str(p.resolve()) for p in matches]
