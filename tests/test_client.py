from typing import Any

from chiketto.jira import Client


def test_client(mock_requests_get: Any) -> None:
    c: Client = Client("host", "foo", "bar")
    j = c.get_by_key("CHIK-1")
    assert j["key"] == "CHIK-1"
