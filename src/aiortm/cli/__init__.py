"""Provide a CLI for aiortm."""

import asyncio
from collections.abc import Callable, Coroutine
import logging
from typing import Annotated, Any
import webbrowser

import aiohttp
from rich import print as rich_print
import typer

from aiortm.client import Auth

cli = typer.Typer()
logging.basicConfig(level=logging.DEBUG)


@cli.command()
def authorize(
    api_key: Annotated[str, typer.Option("--api-key", "-k", help="API key.")],
    secret: Annotated[str, typer.Option("--secret", "-s", help="Shared secret.")],
) -> None:
    """Authorize the app."""
    run_app(authorize_app, api_key, secret)


@cli.command()
def check_token(
    api_key: Annotated[str, typer.Option("--api-key", "-k", help="API key.")],
    secret: Annotated[str, typer.Option("--secret", "-s", help="Shared secret.")],
    token: Annotated[str, typer.Option("--token", "-t", help="Authentication token.")],
) -> None:
    """Check if the authentication token is valid."""
    run_app(check_auth_token, api_key, secret, token=token)


@cli.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def api_method(
    ctx: typer.Context,
    api_key: Annotated[str, typer.Option("--api-key", "-k", help="API key.")],
    secret: Annotated[str, typer.Option("--secret", "-s", help="Shared secret.")],
    token: Annotated[str, typer.Option("--token", "-t", help="Authentication token.")],
    method: Annotated[
        str,
        typer.Argument(
            help=(
                "The method to run. "
                "Pass parameters as param_name=param_value after the method name."
            ),
        ),
    ],
) -> None:
    """Run an arbitrary API method."""
    method_params = dict([item.strip("-").split("=") for item in ctx.args])
    run_app(run_method, api_key, secret, token=token, method=method, **method_params)


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


async def authorize_app(api_key: str, secret: str) -> None:
    """Authorize the application."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(client_session=session, api_key=api_key, shared_secret=secret)

        url, frob = await auth.authenticate_desktop()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, webbrowser.open, url)

        if not typer.confirm("Have you authorized this app at RTM?"):
            rich_print("Exiting")
            return

        result = await auth.get_token(frob)
        token = result["token"]

        rich_print(f"Token: {token}")


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
