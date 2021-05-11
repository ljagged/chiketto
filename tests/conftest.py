from unittest.mock import Mock

import pytest
from pytest_mock import MockFixture


@pytest.fixture
def mock_requests_get(mocker: MockFixture) -> Mock:
    mock = mocker.patch("requests.get")
    mock.return_value.__enter__.return_value.json.return_value = {"key": "CHIK-1"}
    return mock
