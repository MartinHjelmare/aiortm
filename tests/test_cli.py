"""Test the CLI."""

from typer.testing import CliRunner

from aiortm.cli import cli

runner = CliRunner()


def test_help() -> None:
    """The help message includes the CLI name."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Authorize the app." in result.stdout
