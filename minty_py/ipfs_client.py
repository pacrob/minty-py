import requests


class IPFSClient:
    def __init__(self, key: str, secret: str, api_endpoint: str):
        self.key = key
        self.secret = secret
        self.api_endpoint = api_endpoint

    def add(self, path, content):
        infura_add_endpoint = self.api_endpoint + "/api/v0/add"

        file_to_add = {"file": open(path, "rb")}

        response = requests.post(
            infura_add_endpoint, files=file_to_add, auth=(self.key, self.secret)
        )

        if response.status_code == 200:
            return response.json()["cid"]
        else:
            raise Exception(f"Failed to add content to IPFS: {response.text}")
