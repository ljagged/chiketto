import json
from pathlib import Path
from typing import Any, Dict

from dateutil.parser import parse as parse_date
import pytest

import chiketto.parser as p


def test_extract_workflow_state() -> None:
    event = {"items": [{"field": "status", "toString": "Accepted"}]}
    actual = p._extract_workflow_state(event)
    assert actual == "accepted"


def test_extract_workflow_state_not_workflow() -> None:
    event = {"items": [{"field": "priority", "toString": "Standard"}]}
    with pytest.raises(ValueError):
        p._extract_workflow_state(event)


def test_is_workflow_event_empty() -> None:
    assert p._is_workflow_event({"items": []}) is False


def test_is_workflow_event_no_items() -> None:
    assert p._is_workflow_event({"foo": "bar"}) is False


def test_is_workflow_event_items_no_status() -> None:
    event = {"items": [{"field": "priority", "toString": "Standard"}]}
    assert p._is_workflow_event(event) is False


def test_is_workflow_event_happy() -> None:
    event = {"items": [{"field": "status", "toString": "Accepted"}]}
    assert p._is_workflow_event(event)


@pytest.mark.parametrize(
    "input,expected",
    [
        ("requested", "optional"),
        ("accepted", "optional"),
        ("done", "delivered"),
        ("not delivered", "delivered"),
        ("anything", "committed"),
    ],
)
def test_resolve_category(input: str, expected: str) -> None:
    assert expected == p._resolve_category(input)


def test_extract_workflow_event() -> None:
    created = "2021-01-01T12:00:00.000-0500"
    name = "Dimwit Flathead"
    email = "dimwit@gflatheadia.que"
    expected = p.Event(
        state=p.State(name="accepted", category="optional"),
        changed_on=parse_date(created),
        agent=p.User(name=name, email=email),
    )
    input = {
        "author": {
            "emailAddress": email,
            "displayName": name,
        },
        "created": created,
        "items": [{"field": "status", "toString": "Accepted"}],
    }
    actual = p._extract_workflow_event(input)
    assert expected == actual


def test_extract_state_transforms_to_lower() -> None:
    """Validates that extract_state normalizes the data by converting to lower case.

    Note: the "business logic" of this function is already tested in _extract_workflow_event
    """
    expected = p.State(name="done", category="delivered")
    actual = p._extract_state({"name": "Done"})
    assert expected == actual


def test_extract_user_none() -> None:
    assert p._extract_user(None) is None


def test_extract_user_happy() -> None:
    name = "Dimwit Flathead"
    email = "dimwit@gflatheadia.que"
    assert p._extract_user({"displayName": name, "emailAddress": email}) == p.User(
        name=name, email=email
    )


FIXTURE_DIR = Path(__file__).parent.parent / "assets"


@pytest.fixture
def issue() -> Dict[str, Any]:
    fixture = FIXTURE_DIR / "CHIK-1.json"
    with open(fixture, "r") as f:
        return json.load(f)


def test_parse_issue_top_level_non_derived(issue: Dict[str, Any]) -> None:
    actual = p.parse_issue(issue)
    fields = issue["fields"]
    assert actual.key == issue["key"]
    assert actual.summary == fields["summary"]
    assert actual.requested_by == p.User(
        name=fields["creator"]["displayName"], email=fields["creator"]["emailAddress"]
    )
    assert actual.assigned_to == p.User(
        name=fields["assignee"]["displayName"], email=fields["assignee"]["emailAddress"]
    )
    assert actual.class_of_service == fields["priority"]["name"]
    assert actual.current_state == p.State(
        name=fields["status"]["name"].lower(), category="committed"
    )
    assert actual.created_on == parse_date(fields["created"])
    assert actual.last_modified == parse_date(fields["updated"])
