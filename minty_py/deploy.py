import asyncio
import importlib
import json
import os.path

from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.types import HexBytes

from minty_py.config.local_info import INFURA_SEPOLIA_URL, SECRET_KEY


async def deploy_contract(
    contract_file: str, output_file: str, token_name: str, token_symbol: str
):
    """
    Requires contract_file be a .py file that contains two constants:
     - CONTRACT_ABI - a list of dicts that is the contract abi
     - CONTRACT_BYTECODE - a 0x-prefixed string that is the contract's compiled bytecode
    """

    # parse input file name
    if contract_file.endswith(".py"):
        contract_file = contract_file[:-3]
    contract_file = contract_file.replace("/", ".")
    contract_info = importlib.import_module(contract_file)
    abi = contract_info.CONTRACT_ABI
    bytecode = contract_info.CONTRACT_BYTECODE

    w3 = AsyncWeb3(AsyncHTTPProvider(INFURA_SEPOLIA_URL))

    is_connected = await w3.is_connected()

    if is_connected:
        print("connected to provider")
        account = w3.eth.account.from_key(SECRET_KEY)
        account_address = account.address

        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # construct the deploy transaction
        nonce = await w3.eth.get_transaction_count(account_address)
        deploy_txn = await contract.constructor(
            tokenName=token_name, symbol=token_symbol
        ).build_transaction(
            {
                "from": account_address,
                "nonce": nonce,
            }
        )

        # sign the deploy transaction
        signed_txn = w3.eth.account.sign_transaction(deploy_txn, SECRET_KEY)

        # send signed transaction and wait for receipt
        print("sending transaction")
        tx_hash = await w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
        print("transaction completed")

        # parse receipt
        dict_receipt = dict(tx_receipt)
        for key in dict_receipt.keys():
            if isinstance(dict_receipt[key], HexBytes):
                dict_receipt[key] = dict_receipt[key].hex()

        deployment_info = {
            "contract_address": dict_receipt["contractAddress"],
            "token_name": token_name,
            "token_symbol": token_symbol,
            "abi": abi,
            "tx_receipt": dict_receipt,
        }

        with open(output_file, "w") as f:
            json.dump(dict(deployment_info), f, indent=4)

        print(f"transaction receipt saved as {output_file}")
        return

    else:
        print("Unable to connect to provider")
        return


async def load_deployment_info():
    filename = "minty_py/contracts/minty_py_deployment.json"

    def file_exists():
        return os.path.isfile(filename)

    def load_json():
        with open(filename, "r") as f:
            return json.load(f)

    def validate_keys(data):
        required_keys = {
            "contract_address",
            "token_name",
            "token_symbol",
            "abi",
            "tx_receipt",
        }
        keys = set(data.keys())

        missing_keys = required_keys - keys
        extra_keys = keys - required_keys

        return missing_keys, extra_keys

    # Check if the file exists
    if not await asyncio.to_thread(file_exists):
        raise FileNotFoundError(f"{filename} not found")

    # Load the JSON data
    data = await asyncio.to_thread(load_json)

    # Validate the keys
    missing_keys, extra_keys = validate_keys(data)

    if missing_keys or extra_keys:
        error_message = []

        if missing_keys:
            error_message.append(f"Missing keys: {', '.join(missing_keys)}")
        if extra_keys:
            error_message.append(f"Extra keys: {', '.join(extra_keys)}")

        raise ValueError("; ".join(error_message))

    return data
