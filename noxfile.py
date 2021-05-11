import nox
from nox.sessions import Session


@nox.session(python=["3.9", "3.8", "3.7"])
def tests(session: Session) -> None:
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)

@nox.session(python=["3.9", "3.8", "3.7"])
def coverage(session: Session) -> None:
    """Upload coverage data."""
    install_with_constraints(session, "coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)