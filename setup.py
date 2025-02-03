from setuptools import setup, find_packages

setup(
    name="ffdusd",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "ccxt",
        "pyyaml",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "project_name=ffdusd.main:main",
        ],
    },
)
