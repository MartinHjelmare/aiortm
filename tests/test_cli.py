"""Test the CLI."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from aiortm.cli import (
    DEFAULT_CREDENTIALS_FILE,
    cli,
    load_credentials,
    resolve_credentials,
)

runner = CliRunner()


def test_help() -> None:
    """The help message includes the CLI name."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Authorize the app." in result.stdout


def test_default_credentials_file() -> None:
    """The default credentials file path is credentials.json in the CWD."""
    assert Path("credentials.json") == DEFAULT_CREDENTIALS_FILE


def test_load_credentials_missing_file(tmp_path: Path) -> None:
    """Loading credentials from a missing file returns an empty dict."""
    result = load_credentials(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_credentials_valid_file(tmp_path: Path) -> None:
    """Loading credentials from a valid JSON file returns the stored values."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps({"api_key": "k", "secret": "s", "token": "t"}),
        encoding="utf-8",
    )
    assert load_credentials(creds_file) == {"api_key": "k", "secret": "s", "token": "t"}


def test_load_credentials_invalid_json(tmp_path: Path) -> None:
    """Loading credentials from an invalid JSON file exits with an error."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("not json", encoding="utf-8")
    with pytest.raises(typer.Exit) as exc_info:
        load_credentials(creds_file)
    assert exc_info.value.exit_code == 1


def test_resolve_credentials_from_file(tmp_path: Path) -> None:
    """Credentials are resolved from the file when CLI options are None."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps(
            {"api_key": "file-key", "secret": "file-secret", "token": "file-token"},
        ),
        encoding="utf-8",
    )
    api_key, secret, token = resolve_credentials(
        creds_file,
        None,
        None,
        None,
        require_token=True,
    )
    assert api_key == "file-key"
    assert secret == "file-secret"
    assert token == "file-token"


def test_resolve_credentials_cli_overrides_file(tmp_path: Path) -> None:
    """CLI options take precedence over values in the credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps(
            {"api_key": "file-key", "secret": "file-secret", "token": "file-token"},
        ),
        encoding="utf-8",
    )
    api_key, secret, token = resolve_credentials(
        creds_file,
        "cli-key",
        None,
        None,
        require_token=True,
    )
    assert api_key == "cli-key"
    assert secret == "file-secret"
    assert token == "file-token"


def test_resolve_credentials_missing_exits(tmp_path: Path) -> None:
    """typer.Exit is raised when required credentials are missing."""
    creds_file = tmp_path / "nonexistent.json"
    with pytest.raises(typer.Exit) as exc_info:
        resolve_credentials(creds_file, None, None, None, require_token=True)
    assert exc_info.value.exit_code == 1


def test_resolve_credentials_no_token_not_required(tmp_path: Path) -> None:
    """Missing token does not cause an error when require_token is False."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps({"api_key": "k", "secret": "s"}),
        encoding="utf-8",
    )
    api_key, secret, token = resolve_credentials(
        creds_file,
        None,
        None,
        require_token=False,
    )
    assert api_key == "k"
    assert secret == "s"
    assert token is None


def test_check_token_from_file(tmp_path: Path) -> None:
    """check-token reads credentials from the file when no options are passed."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps(
            {
                "api_key": "test-api-key",
                "secret": "test-shared-secret",
                "token": "test-token",
            },
        ),
        encoding="utf-8",
    )
    mock = AsyncMock()
    with patch("aiortm.cli.check_auth_token", mock):
        result = runner.invoke(
            cli,
            ["check-token", "--credentials-file", str(creds_file)],
        )
    assert result.exit_code == 0
    mock.assert_awaited_once_with(
        "test-api-key",
        "test-shared-secret",
        token="test-token",
    )


def test_check_token_missing_credentials(tmp_path: Path) -> None:
    """check-token exits with an error when no credentials are available."""
    creds_file = tmp_path / "nonexistent.json"
    result = runner.invoke(
        cli,
        ["check-token", "--credentials-file", str(creds_file)],
    )
    assert result.exit_code != 0
    assert "Missing credentials" in result.output


def test_check_token_cli_overrides_file(tmp_path: Path) -> None:
    """CLI --api-key takes precedence over the api_key in the credentials file."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text(
        json.dumps(
            {
                "api_key": "file-key",
                "secret": "test-shared-secret",
                "token": "test-token",
            },
        ),
        encoding="utf-8",
    )
    mock = AsyncMock()
    with patch("aiortm.cli.check_auth_token", mock):
        result = runner.invoke(
            cli,
            [
                "check-token",
                "--api-key",
                "cli-key",
                "--credentials-file",
                str(creds_file),
            ],
        )
    assert result.exit_code == 0
    mock.assert_awaited_once_with(
        "cli-key",
        "test-shared-secret",
        token="test-token",
    )


def test_authorize_writes_credentials_file(tmp_path: Path) -> None:
    """Credentials are saved to the JSON file after a successful authorize run."""
    creds_file = tmp_path / "credentials.json"
    mock_auth_cls = MagicMock()
    mock_auth = mock_auth_cls.return_value
    mock_auth.authenticate_desktop = AsyncMock(
        return_value=("https://example.com/auth", "test-frob"),
    )
    mock_auth.get_token = AsyncMock(
        return_value={"token": "new-token", "perms": "delete", "user": {}},
    )

    with (
        patch("aiortm.cli.Auth", mock_auth_cls),
        patch("webbrowser.open"),
    ):
        result = runner.invoke(
            cli,
            [
                "authorize",
                "--api-key",
                "test-api-key",
                "--secret",
                "test-secret",
                "--credentials-file",
                str(creds_file),
            ],
            input="y\n",
        )

    assert result.exit_code == 0, result.output
    assert creds_file.is_file()
    data = json.loads(creds_file.read_text(encoding="utf-8"))
    assert data["api_key"] == "test-api-key"
    assert data["secret"] == "test-secret"
    assert data["token"] == "new-token"
    assert oct(creds_file.stat().st_mode)[-3:] == "600"
