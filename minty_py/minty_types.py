from dataclasses import dataclass


@dataclass
class NFTOptions:
    name: str
    description: str
    owner: str
    image_path: str