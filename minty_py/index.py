import asyncio
import json
import os
from functools import wraps

import click

from minty_py.deploy import deploy_contract
from minty_py.minty import make_minty
from minty_py.minty_types import NFTOptions


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
def main():
    pass


### MINT nft
@main.command()
@click.argument("image_path")
@click.option(
    "-n", "--name", default="Test Mint", prompt="NFT Name", help="The name of the NFT"
)
@click.option(
    "-d",
    "--description",
    default="A basic test of mint",
    prompt="NFT Description",
    help="A description of the NFT",
)
@click.option(
    "-o",
    "--owner",
    default="0x8d009B14CE7c2A51A97888710F221DD94aC2361D",
    prompt="Owner Address",
    help="The Ethereum address that should own the NFT.",
)
@coro
async def mint(image_path, name, description, owner):
    await create_nft(image_path, name, description, owner)


### GET nft information
@main.command()
@click.argument("token_id")
@click.option(
    "-c",
    "--creation_info",
    is_flag=True,
    help="Include the creator address and block number the NFT was minted",
)
@coro
async def show(token_id, creation_info):
    await get_nft(token_id, creation_info)


### TRANSFER nft to an address
@main.command()
@click.argument("token_id")
@click.argument("to_address")
@coro
async def transfer(token_id, to_address):
    await transfer_nft(token_id, to_address)


### PIN nft data to ipfs
@main.command()
@click.argument("token_id")
@coro
async def pin(token_id):
    await pin_nft_data(token_id)


### DEPLOY new contract
@main.command()
@click.option(
    "-c",
    "--contract",
    default="minty_py/contracts/minty_py_contract.py",
    help="Python file containing contract abi and bytecode",
)
@click.option(
    "-o",
    "--output",
    default="minty_py/contracts/minty_py_deployment.json",
    help="Path to write deployment info to",
)
@click.option("-n", "--name", default="Julep", help="The name of the token contract")
@click.option(
    "-s",
    "--symbol",
    default="JLP",
    help="A short symbol for the tokens in this contract",
)
@coro
async def deploy(contract, output, name, symbol):
    await deploy_contract(contract, output, name, symbol)


# --- functions --- #


async def create_nft(image_path, name, description, owner):
    print("You called create_nft")
    minty = await make_minty()

    # breakpoint()
    options = NFTOptions(name=name, description=description, owner=owner, image_path=image_path)
    
    nft = await minty.create_nft_from_asset_file(options)
    print("🌿 Minted a new NFT: ")

    align_output(
        [
            ["Token ID:", nft["tokenId"]],
            ["Metadata Address:", nft["metadataURI"]],
            ["Metadata Gateway URL:", nft["metadataGatewayURL"]],
            ["Asset Address:", nft["assetURI"]],
            ["Asset Gateway URL:", nft["assetGatewayURL"]],
        ]
    )
    print("NFT Metadata:")
    print(json.dumps(nft["metadata"], indent=2))


async def get_nft(token_id, creation_info):
    print("You called get_nft")
    minty = await make_minty()

    breakpoint()

    nft = await minty.get_nft(token_id, creation_info)

    output = [
        ["Token ID:", nft["tokenId"]],
        ["Owner Address:", nft["ownerAddress"]],
    ]
    if nft.get("creationInfo"):
        output.append(["Creator Address:", nft["creationInfo"]["creatorAddress"]])
        output.append(["Block Number:", nft["creationInfo"]["blockNumber"]])
    output.append(["Metadata Address:", nft["metadataURI"]])
    output.append(["Metadata Gateway URL:", nft["metadataGatewayURL"]])
    output.append(["Asset Address:", nft["assetURI"]])
    output.append(["Asset Gateway URL:", nft["assetGatewayURL"]])
    align_output(output)

    print("NFT Metadata:")
    print(json.dumps(nft["metadata"], indent=2))


async def transfer_nft(token_id, to_address):
    print("You called transfer_nft")
    minty = await make_minty()

    await minty.transfer_token(token_id, to_address)
    print(f"🌿 Transferred token {token_id} to {to_address}")


async def pin_nft_data(token_id):
    print("You called pin_nft_data")
    minty = await make_minty()
    asset_uri, metadata_uri = await minty.pin_token_data(token_id)
    print(f"🌿 Pinned all data for token id {token_id}")


# --- helpers --- #


def align_output(label_value_pairs):
    max_label_length = max(len(label) for label, _ in label_value_pairs)
    for label, value in label_value_pairs:
        print(label.ljust(max_label_length + 1), value)


if __name__ == "__main__":
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    os.chdir(root_dir)
    main()
