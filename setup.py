import os
from setuptools import setup

setup(
    name="minty_py",
    version="0.0.0",
    py_modules=["minty_py"],
    entry_points={"console_scripts": ["minty = minty_py.index:main"]},
    
)
