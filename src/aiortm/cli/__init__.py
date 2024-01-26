"""Provide a CLI for aiortm."""

import logging

import click

from .. import __version__
from .app import api_method, authorize, check_token

SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(
    options_metavar="", subcommand_metavar="<command>", context_settings=SETTINGS
)
@click.option("--debug", is_flag=True, help="Start aiortm in debug mode.")
@click.version_option(__version__)
def cli(debug: bool) -> None:
    """Run aiortm as an app for testing purposes."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


cli.add_command(authorize)
cli.add_command(check_token)
cli.add_command(api_method)
