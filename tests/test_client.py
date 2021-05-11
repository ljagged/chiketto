from unittest.mock import Mock

from chiketto.jira import Client


def test_client(mock_requests_get: Mock) -> None:
    c: Client = Client("host", "foo", "bar")
    j = c.get_by_key("CHIK-1")
    assert j["key"] == "CHIK-1"
