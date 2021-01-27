from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='Ga4Sci GA demographic map',
    version="0.1",
    packages=[],
    description="Collection of utilities for mapping and getting started with the dataset",
    long_description=open("README.md").read(),
    install_requires=requirements,
    license="MIT"
)
