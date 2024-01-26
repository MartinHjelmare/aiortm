"""Provide an application to run the client."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
import logging
from typing import Any
import webbrowser

import aiohttp
import click

from ..client import Auth

LOGGER = logging.getLogger("aiortm")


@click.command(options_metavar="<options>")
@click.option("-k", "--api_key", required=True, help="API key.")
@click.option("-s", "--secret", required=True, help="Shared secret.")
def authorize(api_key: str, secret: str) -> None:
    """Authorize the app."""
    run_app(authorize_app, api_key, secret)


@click.command(options_metavar="<options>")
@click.option("-k", "--api-key", required=True, help="API key.")
@click.option("-s", "--secret", required=True, help="Shared secret.")
@click.option("-t", "--token", required=True, help="Authentication token.")
def check_token(api_key: str, secret: str, token: str) -> None:
    """Check if the authentication token is valid."""
    run_app(check_auth_token, api_key, secret, token=token)


@click.command(
    options_metavar="<options>",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.option("-k", "--api-key", required=True, help="API key.")
@click.option("-s", "--secret", required=True, help="Shared secret.")
@click.option("-t", "--token", required=True, help="Authentication token.")
@click.argument("method")
@click.pass_context
def api_method(
    ctx: click.Context, api_key: str, secret: str, token: str, method: str
) -> None:
    """Run an arbitrary API method."""
    method_params = dict([item.strip("--").split("=") for item in ctx.args])
    run_app(run_method, api_key, secret, token=token, method=method, **method_params)


def run_app(
    command: Callable[..., Coroutine[Any, Any, None]],
    api_key: str,
    secret: str,
    **kwargs: Any,
) -> None:
    """Run the app."""
    LOGGER.debug("Starting app")
    try:
        asyncio.run(command(api_key, secret, **kwargs))
    except KeyboardInterrupt:
        pass
    finally:
        LOGGER.debug("Exiting app")


async def authorize_app(api_key: str, secret: str, **kwargs: Any) -> None:
    """Authorize the application."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(client_session=session, api_key=api_key, shared_secret=secret)

        url, frob = await auth.authenticate_desktop()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, webbrowser.open, url)

        if not click.confirm("Have you authorized this app at RTM?"):
            click.echo("Exiting")
            return

        result = await auth.get_token(frob)
        token = result["token"]

        click.echo(f"Token: {token}")


async def check_auth_token(
    api_key: str, secret: str, token: str, **kwargs: Any
) -> None:
    """Check the authentication token."""
    async with aiohttp.ClientSession() as session:
        auth = Auth(
            client_session=session,
            api_key=api_key,
            shared_secret=secret,
            auth_token=token,
        )

        result = await auth.check_token()

        click.echo(f"Token is valid: {result}")


async def run_method(
    api_key: str,
    secret: str,
    token: str,
    method: str,
    **params: Any,
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

        click.echo(f"Method result: {result}")
