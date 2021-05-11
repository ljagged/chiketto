import requests

JIRA_ISSUE_URL = "https://{host}.atlassian.net/rest/api/2/issue/{key}"

class Client:
    def __init__(self, host:str, user: str, token: str):
        self.user = user
        self.token = token
        self.host = host

    def get_by_key(self, key:str) -> str:
        headers = {'Content-Type': 'application/json'}
        with requests.get(JIRA_ISSUE_URL.format(host=self.host, key=key), auth=(self.user, self.token), headers=headers) as response:
            response.raise_for_status()
            return response.json()