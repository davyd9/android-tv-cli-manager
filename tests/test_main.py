from typer.testing import CliRunner

from android_tv_cli_manager import __version__
from android_tv_cli_manager.main import app

runner = CliRunner()


def test_app_version_long_option() -> None:
    """Test the --version option."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"Android TV CLI Manager version {__version__}" in result.stdout


def test_app_version_short_option() -> None:
    """Test the -v short option for version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert f"Android TV CLI Manager version {__version__}" in result.stdout


def test_app_no_command() -> None:
    """Test running the app without any command."""
    result = runner.invoke(app)
    assert result.exit_code == 1
    assert "No command specified." in result.stdout
    assert "atv-cli --help" in result.stdout


def test_app_help_option() -> None:
    """Test the --help option."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage: main" in result.stdout
    assert "Your ultimate tool for taming Android TV devices." in result.stdout
