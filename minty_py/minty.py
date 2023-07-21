import asyncio
import json
from pathlib import Path

import aiofiles
import aiohttp
from web3 import AsyncHTTPProvider, AsyncWeb3

from minty_py.config.local_info import (
    INFURA_IPFS_API_KEY,
    INFURA_IPFS_API_KEY_SECRET,
    INFURA_IPFS_ENDPOINT,
    INFURA_SEPOLIA_URL,
)
from minty_py.deploy import load_deployment_info
from minty_py.ipfs_client import IPFSClient
from minty_py.minty_types import NFTOptions


async def make_minty():
    m = await Minty()
    return m


class Minty:
    def __init__(self):
        self._initialized = False
        self.contract = None
        self.deploy_info = None
        self.ipfs = None
        self.w3 = None

    def __await__(self):
        if self._initialized:
            return

        async def closure():
            self.deploy_info = await load_deployment_info()

            abi, address = (
                self.deploy_info["abi"],
                self.deploy_info["contract_address"],
            )
            self.w3 = AsyncWeb3(AsyncHTTPProvider(INFURA_SEPOLIA_URL))
            # breakpoint()
            self.contract = self.w3.eth.contract(abi=abi, address=address)

            self.ipfs = IPFSClient(
                INFURA_IPFS_API_KEY,
                INFURA_IPFS_API_KEY_SECRET,
                INFURA_IPFS_ENDPOINT,
            )

            self._initialized = True

            return self

        return closure().__await__()

    async def create_nft_from_asset_file(self, options: NFTOptions):
        async with aiofiles.open(options.image_path, mode="rb") as f:
            content = await f.read()
            breakpoint()
        return await self.create_nft_from_asset_data(content, options)

    async def create_nft_from_asset_data(self, content, options):
        basename = Path(options.image_path)

        ipfs_path = "/nft/" + basename
        breakpoint()
        asset_cid = await self.ipfs.add(
            {"path": ipfs_path, "content": content}, ipfs_add_options
        )

        asset_uri = ensure_ipfs_uri_prefix(asset_cid) + "/" + basename
        metadata = await self.make_nft_metadata(asset_uri, options)

        metadata_cid = await self.ipfs.add(
            {"path": "/nft/metadata.json", "content": json.dumps(metadata)},
            ipfs_add_options,
        )
        metadata_uri = ensure_ipfs_uri_prefix(metadata_cid) + "/metadata.json"

        owner_address = options.get("owner")
        if not owner_address:
            owner_address = await self.default_owner_address()

        token_id = await self.mint_token(owner_address, metadata_uri)

        return {
            "tokenId": token_id,
            "ownerAddress": owner_address,
            "metadata": metadata,
            "assetURI": asset_uri,
            "metadataURI": metadata_uri,
            "assetGatewayURL": make_gateway_url(asset_uri),
            "metadataGatewayURL": make_gateway_url(metadata_uri),
        }

    async def make_nft_metadata(self, asset_uri, options):
        name, description = options.get("name"), options.get("description")
        asset_uri = ensure_ipfs_uri_prefix(asset_uri)
        return {"name": name, "description": description, "image": asset_uri}

    async def get_nft(self, token_id, opts):
        metadata, metadata_uri = await self.get_nft_metadata(token_id)
        owner_address = await self.get_token_owner(token_id)
        metadata_gateway_url = make_gateway_url(metadata_uri)
        nft = {
            "tokenId": token_id,
            "metadata": metadata,
            "metadataURI": metadata_uri,
            "metadataGatewayURL": metadata_gateway_url,
            "ownerAddress": owner_address,
        }

        fetch_asset, fetch_creation_info = opts.get("fetchAsset"), opts.get(
            "fetchCreationInfo"
        )
        if metadata.get("image"):
            nft["assetURI"] = metadata["image"]
            nft["assetGatewayURL"] = make_gateway_url(metadata["image"])
            if fetch_asset:
                nft["assetDataBase64"] = await self.get_ipfs_base64(metadata["image"])

        if fetch_creation_info:
            nft
