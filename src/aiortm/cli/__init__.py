"""Provide a CLI for aiortm."""

import asyncio
from collections.abc import Callable, Coroutine
import json
import logging
from pathlib import Path
from typing import Annotated, Any, cast
import webbrowser

import aiohttp
from rich import print as rich_print
import typer

from aiortm.client import Auth

cli = typer.Typer()
logging.basicConfig(level=logging.DEBUG)

DEFAULT_CREDENTIALS_FILE = Path("credentials.json")


def load_credentials(path: Path) -> dict[str, str]:
    """Load credentials from a JSON file, or return an empty dict if absent."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except OSError as err:
        typer.echo(f"Error: Cannot read credentials file {path}: {err}", err=True)
        raise typer.Exit(code=1) from err
    except json.JSONDecodeError as err:
        typer.echo(f"Error: Invalid credentials file {path}: {err}", err=True)
        raise typer.Exit(code=1) from err


def resolve_credentials(
    credentials_file: Path,
    api_key: str | None,
    secret: str | None,
    token: str | None = None,
    *,
    require_token: bool,
) -> tuple[str, str, str | None]:
    """Merge CLI options over file values; error if a required value is missing."""
    stored = load_credentials(credentials_file)
    api_key = api_key or stored.get("api_key")
    secret = secret or stored.get("secret")
    token = token or stored.get("token")

    missing = [
        name
        for name, value, required in (
            ("--api-key", api_key, True),
            ("--secret", secret, True),
            ("--token", token, require_token),
        )
        if required and not value
    ]
    if missing:
        typer.echo(
            f"Error: Missing credentials: {', '.join(missing)}. "
            f"Pass them as options or add them to {credentials_file}.",
            err=True,
        )
        raise typer.Exit(code=1)
    return cast("str", api_key), cast("str", secret), token


def save_credentials(path: Path, api_key: str, secret: str, token: str) -> None:
    """Write credentials to a JSON file with owner-only permissions."""
    path.write_text(
        json.dumps({"api_key": api_key, "secret": secret, "token": token}, indent=2),
        encoding="utf-8",
    )
    path.chmod(0o600)


@cli.command()
def authorize(
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="API key."),
    ] = None,
    secret: Annotated[
        str | None,
        typer.Option("--secret", "-s", help="Shared secret."),
    ] = None,
    credentials_file: Annotated[
        Path,
        typer.Option("--credentials-file", "-c", help="Path to credentials JSON file."),
    ] = DEFAULT_CREDENTIALS_FILE,
) -> None:
    """Authorize the app."""
    api_key_r, secret_r, _ = resolve_credentials(
        credentials_file,
        api_key,
        secret,
        require_token=False,
    )
    run_app(authorize_app, api_key_r, secret_r, credentials_file)


@cli.command()
def check_token(
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="API key."),
    ] = None,
    secret: Annotated[
        str | None,
        typer.Option("--secret", "-s", help="Shared secret."),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", help="Authentication token."),
    ] = None,
    credentials_file: Annotated[
        Path,
        typer.Option("--credentials-file", "-c", help="Path to credentials JSON file."),
    ] = DEFAULT_CREDENTIALS_FILE,
) -> None:
    """Check if the authentication token is valid."""
    api_key_r, secret_r, token_r = resolve_credentials(
        credentials_file,
        api_key,
        secret,
        token,
        require_token=True,
    )
    run_app(check_auth_token, api_key_r, secret_r, token=token_r)


@cli.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def api_method(
    ctx: typer.Context,
    method: Annotated[
        str,
        typer.Argument(
            help=(
                "The method to run. "
                "Pass parameters as param_name=param_value after the method name."
            ),
        ),
    ],
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="API key."),
    ] = None,
    secret: Annotated[
        str | None,
        typer.Option("--secret", "-s", help="Shared secret."),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", help="Authentication token."),
    ] = None,
    credentials_file: Annotated[
        Path,
        typer.Option("--credentials-file", "-c", help="Path to credentials JSON file."),
    ] = DEFAULT_CREDENTIALS_FILE,
) -> None:
    """Run an arbitrary API method."""
    api_key_r, secret_r, token_r = resolve_credentials(
        credentials_file,
        api_key,
        secret,
        token,
        require_token=True,
    )
    method_params = dict([item.strip("-").split("=") for item in ctx.args])
    run_app(
        run_method,
        api_key_r,
        secret_r,
        token=token_r,
        method=method,
        **method_params,
    )


def run_app(
    command: Callable[..., Coroutine[Any, Any, None]],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> None:
    """Run the app."""
    rich_print("Starting app")
    try:
        asyncio.run(command(*args, **kwargs))
    except KeyboardInterrupt:
        pass
    finally:
        rich_print("Exiting app")


async def authorize_app(api_key: str, secret: str, credentials_file: Path) -> None:
    """Authorize the application."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(client_session=session, api_key=api_key, shared_secret=secret)

        url, frob = await auth.authenticate_desktop()
        await asyncio.to_thread(webbrowser.open, url)

        if not typer.confirm("Have you authorized this app at RTM?"):
            rich_print("Exiting")
            return

        result = await auth.get_token(frob)
        token = result["token"]

        save_credentials(credentials_file, api_key, secret, token)
        rich_print(f"Token: {token}")
        rich_print(f"Saved credentials to {credentials_file}")


async def check_auth_token(api_key: str, secret: str, token: str) -> None:
    """Check the authentication token."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(
            client_session=session,
            api_key=api_key,
            shared_secret=secret,
            auth_token=token,
        )

        result = await auth.check_token()

        rich_print(f"Token is valid: {result}")


async def run_method(
    api_key: str,
    secret: str,
    token: str,
    method: str,
    **params: str,
) -> None:
    """Run an API method."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(
            client_session=session,
            api_key=api_key,
            shared_secret=secret,
            auth_token=token,
        )

        result = await auth.call_api_auth(method, **params)

        rich_print(f"Method result: {result}")
