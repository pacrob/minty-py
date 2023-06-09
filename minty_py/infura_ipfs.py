import requests


class IPFSClient:
    def __init__(self, key, secret, api_endpoint):
        self.key = key
        self.secret = secret
        self.api_endpoint = api_endpoint

    def add(self, path, content):
        infura_add_endpoint = self.api_endpoint + "/api/v0/add"

        # headers = {
        #     'Authorization': f'Bearer {self.key}:{self.secret}'
        # }
        headers = {"Content-Type": "multipart/form-data"}

        payload = {"path": path, "content": content}

        response = requests.post(infura_add_endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["cid"]
        else:
            raise Exception(f"Failed to add content to IPFS: {response.text}")


from minty_py.config.local_info import (
    INFURA_IPFS_API_KEY,
    INFURA_IPFS_API_KEY_SECRET,
    INFURA_IPFS_ENDPOINT,
    INFURA_SEPOLIA_URL,
)

new_client = IPFSClient(INFURA_IPFS_API_KEY, INFURA_IPFS_API_KEY_SECRET, INFURA_IPFS_ENDPOINT)

