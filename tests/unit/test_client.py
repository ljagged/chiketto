from datetime import datetime
from typing import Any, Dict, List

import pytest
from pytest import MonkeyPatch
import requests

import chiketto.jira
from chiketto.jira import Client
from chiketto.parser import State, User, WorkItem

WORK_ITEM_STUB = WorkItem(
    key="XYZZY-1",
    summary="summary",
    requested_by=User(name="Dimwit Flathead", email="dimwit@gflatheadia.que"),
    assigned_to=None,
    contributors=None,
    class_of_service="important",
    events=[],
    current_state=State(name="foo", category="optional"),
    created_on=datetime.now(),
    last_modified=datetime.now(),
)


class MockResponse:
    @staticmethod
    def json() -> Dict[str, str]:
        return {"foo": "bar"}

    @staticmethod
    def raise_for_status() -> None:
        pass


@pytest.fixture
def client() -> Client:
    return Client("foo", "user", "token")


def test_get_by_key_raw_happy_path(monkeypatch: MonkeyPatch, client: Client) -> None:
    def mock_get(*args: List[Any], **kwargs: Dict[str, Any]) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    result = client._get_by_key_raw("XYZZY-1")
    assert result["foo"] == "bar"


def test_init_saves_values(client: Client) -> None:
    assert client.host == "foo"
    assert client.user == "user"
    assert client.token == "token"


def test_get_by_key_happy_path(monkeypatch: MonkeyPatch, client: Client) -> None:
    def mock_parse_issue(*args: List[Any], **kwargs: Dict[str, Any]) -> WorkItem:
        return WORK_ITEM_STUB

    monkeypatch.setattr(chiketto.jira, "parse_issue", mock_parse_issue)
    monkeypatch.setattr(Client, "_get_by_key_raw", mock_parse_issue)

    r = client.get_by_key("XYZZY-1")
    assert r == WORK_ITEM_STUB


def test_find_work_items_empty(client: Client) -> None:
    assert client.find_work_items("proj", datetime.now(), datetime.now()) == []
