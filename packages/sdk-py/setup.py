from setuptools import setup, find_packages

setup(
    name="cyber-werewolves-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "typing-extensions>=4.0.0",
    ],
)