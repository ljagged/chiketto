"""Pytest-bdd steps for behavior tests."""

from typing import Any, Dict

from _pytest.fixtures import fixture
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then
from pytest_bdd.steps import when

from chiketto import __version__, cli

# Scenarios

Context = Dict[str, Any]

scenarios("../features/cli.feature", example_converters=dict(phrase=str))


# Fixtures
@fixture
def ctx() -> Context:
    """Creates a context for shared state between steps.

    Returns:
        An empty dict

    """
    return {}


# Common steps
@given("the cli is runnable", target_fixture="runner")
def runner() -> CliRunner:
    """Creates an isolated environment for the CLI to be tested.

    Returns:
        a click.testing.CliRunner for executing the system under test (SUT)
    """
    return CliRunner()


@then(parsers.parse("the application ends with an exit code of {code:d}"))
def check_for_exit_code(ctx: Context, code: int) -> None:
    """Asserts that the expected exit code matches the actual exit code.

    Args:
        ctx:
            the shared context containing the actual exit code
        code:
            the expected code

    Raises:
        AssertionError: when the expected and actual don't match
    """
    assert ctx["result"].exit_code == code


@then(parsers.parse("the application has an error message with: {error_message}"))
def check_for_error_message(ctx: Context, error_message: str) -> None:
    """Asserts that the expected error message appears in the output.

    Args:
        ctx:
            the shared context containing output from execution
        error_message:
            the expected error message

    Raises:
        AssertionError: when the expected and actual don't match
    """
    assert error_message in ctx["result"].output


# Specific steps
@when("the cli is invoked with the version flag")
def invoke_with_version(ctx: Context, runner: CliRunner) -> None:
    """Executes the CLI with the --version flag.

    Args:
        ctx: the shared context for storing the result
        runner: the CliRunner

    """
    ctx["result"] = runner.invoke(cli.main, "--version")


@then("the version is displayed on stdout")
def check_for_version(ctx: Context) -> None:
    """Asserts that the version of the application appears in the output.

    Args:
        ctx:
            the shared context containing output from execution

    Raises:
        AssertionError: when the expected and actual don't match
    """
    assert __version__ in ctx["result"].output


@when("the cli is invoked with no projects")
def invoke_with_no_projects(ctx: Context, runner: CliRunner) -> None:
    """Executes the CLI with no projects.

    The purpose of this is to ensure that the program still works, even if
    no projects are specified. This could happen if the projects are accumulated
    from some other place and passed to the script, e.g., a unix glob or a
    web/GUI front end. The expected behavior in that situation is for the
    execution to be a NOOP.

    Args:
        ctx: the shared context for storing the result
        runner: the CliRunner

    """
    ctx["result"] = runner.invoke(cli.main, "--start-date=2021-01-01")


@when("the cli is invoked with no from date")
def invoke_with_no_from_date(ctx: Context, runner: CliRunner) -> None:
    """Executes the CLI with no from date.

    This should fail because the only reasonable default for no from date
    is to pull everything and that doesn't seem like a reasonable default.

    Args:
        ctx: the shared context for storing the result
        runner: the CliRunner

    """
    ctx["result"] = runner.invoke(cli.main)
