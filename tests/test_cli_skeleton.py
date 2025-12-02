"""
Tests for the CLI skeleton.

These tests verify that the CLI is properly wired up and commands are registered,
without actually running the full dataset processing pipelines.
"""

from pathlib import Path

from typer.testing import CliRunner

from hf_bids_nifti.cli import app

runner = CliRunner()


class TestCliHelp:
    """Tests for CLI help output."""

    def test_main_help(self) -> None:
        """Test that main --help works."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "BIDS" in result.stdout or "bids" in result.stdout.lower()
        assert "arc" in result.stdout
        assert "soop" in result.stdout

    def test_arc_help(self) -> None:
        """Test that arc --help works."""
        result = runner.invoke(app, ["arc", "--help"])

        assert result.exit_code == 0
        assert "ARC" in result.stdout or "arc" in result.stdout.lower()
        assert "--hf-repo" in result.stdout
        assert "--dry-run" in result.stdout

    def test_soop_help(self) -> None:
        """Test that soop --help works."""
        result = runner.invoke(app, ["soop", "--help"])

        assert result.exit_code == 0
        assert "SOOP" in result.stdout or "soop" in result.stdout.lower()
        assert "--hf-repo" in result.stdout
        assert "--dry-run" in result.stdout


class TestCliCommands:
    """Tests for CLI command execution."""

    def test_arc_raises_not_implemented(self, tmp_path: Path) -> None:
        """Test that arc command raises NotImplementedError (expected for stub)."""
        result = runner.invoke(
            app,
            [
                "arc",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should fail because build_arc_file_table raises NotImplementedError
        assert result.exit_code != 0
        # Exception is captured in result.exception, not stdout
        assert isinstance(result.exception, NotImplementedError)
        assert "not implemented" in str(result.exception).lower()

    def test_soop_raises_not_implemented(self, tmp_path: Path) -> None:
        """Test that soop command raises NotImplementedError (expected for stub)."""
        result = runner.invoke(
            app,
            [
                "soop",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should fail because build_soop_file_table raises NotImplementedError
        assert result.exit_code != 0
        # Exception is captured in result.exception, not stdout
        assert isinstance(result.exception, NotImplementedError)
        assert "not implemented" in str(result.exception).lower()

    def test_arc_missing_hf_repo_fails(self, tmp_path: Path) -> None:
        """Test that arc command fails when --hf-repo is not provided."""
        result = runner.invoke(
            app,
            [
                "arc",
                str(tmp_path),
                # Missing --hf-repo
            ],
        )

        assert result.exit_code != 0

    def test_soop_missing_bids_root_fails(self) -> None:
        """Test that soop command fails when bids_root is not provided."""
        result = runner.invoke(
            app,
            [
                "soop",
                # Missing bids_root argument
                "--hf-repo",
                "test/test-repo",
            ],
        )

        assert result.exit_code != 0


class TestCliOutput:
    """Tests for CLI output messages."""

    def test_arc_shows_processing_message(self, tmp_path: Path) -> None:
        """Test that arc shows processing message before failing."""
        result = runner.invoke(
            app,
            [
                "arc",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should show processing message even if it fails later
        assert "Processing ARC" in result.stdout or "ARC" in result.stdout

    def test_soop_shows_processing_message(self, tmp_path: Path) -> None:
        """Test that soop shows processing message before failing."""
        result = runner.invoke(
            app,
            [
                "soop",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should show processing message even if it fails later
        assert "Processing SOOP" in result.stdout or "SOOP" in result.stdout
