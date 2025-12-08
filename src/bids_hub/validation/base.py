"""Generic validation framework for BIDS datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationCheck:
    """Result of a single validation check."""

    name: str
    expected: str
    actual: str
    passed: bool
    details: str = ""


@dataclass
class ValidationResult:
    """Complete validation results for a BIDS download."""

    bids_root: Path
    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Return True if all checks passed."""
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        """Count of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    def add(self, check: ValidationCheck) -> None:
        """Add a validation check result."""
        self.checks.append(check)

    def summary(self) -> str:
        """Return a formatted summary of validation results."""
        lines = [
            f"Validation Results for: {self.bids_root}",
            "=" * 60,
        ]
        for check in self.checks:
            status = "✅ PASS" if check.passed else "❌ FAIL"
            lines.append(f"{status} {check.name}")
            lines.append(f"       Expected: {check.expected}")
            lines.append(f"       Actual:   {check.actual}")
            if check.details:
                lines.append(f"       Details:  {check.details}")

        lines.append("=" * 60)
        if self.all_passed:
            lines.append("✅ All validations passed! Data is ready for HF push.")
        else:
            lines.append(
                f"❌ {self.failed_count}/{len(self.checks)} checks failed. "
                "Check download or wait for completion."
            )
        return "\n".join(lines)
