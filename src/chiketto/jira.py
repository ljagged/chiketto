"""The interface to Jira."""
import datetime
from typing import Any, List

import requests

from .parser import parse_issue, WorkItem

JIRA_ISSUE_URL: str = (
    "https://{host}.atlassian.net/rest/api/2/issue/{key}?fields=*all&expand=changelog"
)


class Client:
    """Accesses Jira instance via the REST API.

    More details go here

    Attributes:
        host: the abbreviated host of the Cloud Jira
            instance without the `atlassian.net` part.
        user: the username used for authentication
        token: the API token associated with the user

    """

    def __init__(self, host: str, user: str, token: str) -> None:
        """Initializes the object with the required attributes.

        Args:
            host:the abbreviated host of the Cloud Jira instance.
            user: the username used for authentication
            token: the API token associated with the user
        """
        self.user = user
        self.token = token
        self.host = host

    def _get_by_key_raw(self, key: str) -> Any:
        """Retrieves the issue by Jira key.

        Args:
            key: the Jira key associated with the issue. E.g.: XYZZY-1.

        Returns:
            the Dict representation of the JSON issue

        Raises:
            HTTPError: for any non 2xx response
        """
        headers = {"Content-Type": "application/json"}
        response = requests.get(
            JIRA_ISSUE_URL.format(host=self.host, key=key),
            auth=(self.user, self.token),
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def get_by_key(self, key: str) -> WorkItem:
        return parse_issue(self._get_by_key_raw(key))

    def find_work_items(
        self,
        project: str,
        start_on: datetime.date,
        end_on: datetime.date,
        use_modified: bool = False,
    ) -> List[WorkItem]:
        return []
