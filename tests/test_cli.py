import click.testing
from click.testing import CliRunner
import pytest

from chiketto import cli


@pytest.fixture
def runner() -> CliRunner:
    return click.testing.CliRunner()


def test_main_succeeds(runner: CliRunner) -> None:
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
