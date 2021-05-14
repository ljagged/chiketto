"""Command line interface for Jira metrics extraction."""
import datetime
from typing import List

import click

from . import __version__


@click.command()
@click.argument("projects", nargs=-1)
@click.version_option(version=__version__)
@click.option("--from-date", "-f", "from_date", type=click.DateTime(), required=True)
def main(projects: List[str], from_date: datetime.datetime) -> None:
    """Chiketto: Jira metrics for Kanban.

    Args:
        projects: the Jira projects that should be used as a source of data
        from_date: the lower bound (inclusive) for data selection

    """
    click.echo("Hello world")
