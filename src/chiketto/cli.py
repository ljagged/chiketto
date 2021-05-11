import click

from . import __version__

@click.command()
@click.version_option(version=__version__)
def main():
    """Chiketto: Jira metrics for Kanban"""
    click.echo("Hello world")