"""Command line interface for Jira metrics extraction."""
import datetime
from typing import IO, List, Text

import click

from . import __version__


@click.command()
@click.argument("projects", nargs=-1)
@click.version_option(version=__version__, prog_name="chiketto")
@click.option("--start-date", "-s", "start_on", type=click.DateTime(), required=True)
@click.option(
    "--end-date", "-e", "end_on", type=click.DateTime(), default=datetime.datetime.now()
)
@click.option("--jira-username", "-u", "username", envvar="JIRA_USERNAME")
@click.option("--jira-token", "-t", "token", envvar="JIRA_TOKEN")
@click.option("--output", "-o", "output", type=click.File("w"), default="-")
@click.option(
    "--format", "-f", type=click.Choice(("csv", "json"), case_sensitive=False)
)
@click.option("--last-modified", is_flag=True)
def main(
    projects: List[str],
    start_on: datetime.datetime,
    end_on: datetime.datetime,
    username: str,
    token: str,
    output: IO[Text],
    format: str,
    last_modified: bool,
) -> None:
    """Chiketto: Jira metrics for Kanban.

    Args:
        projects: the Jira projects that should be used as a source of data
        start_on: the ISO-8601 date representing the lower bound of the time interval
        end_on: the ISO-8601 date representing the upper bound of the time interval
        username: the name of the account to use for calling the Jira API
        token: the API token associated with the user
        output: the name of the file to write the data to (default: stdout)
        format: one of ``csv`` or ``json``.
        last_modified: if true, calculate the interval based on last modified
            instead of when the issue was created

    """
    pass
