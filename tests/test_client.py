from chiketto.jira import Client
import pytest


def test_client(mock_requests_get):
    c = Client("host", "foo", "bar")
    j = c.get_by_key("CHIK-1")
    assert j["key"] == "CHIK-1"
    