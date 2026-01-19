#!/usr/bin/env python3
"""Setup script."""

import logging
import os
import subprocess  # noqa S404  # nosec: B404
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


class Build(build_py):
    """Install ILSpyCmd (dotnet tool) packages."""

    def run(self):
        """Install ILSpyCmd (dotnet tool)."""
        result = subprocess.run(
            ["dotnet", "tool", "install", "ilspycmd", "-g"], stderr=subprocess.PIPE
        )  # noqa: S603  # nosec: B603 B607
        if result.returncode != 0 and "already installed" not in result.stderr.decode():
            logging.warning(f"Failed to install ilspycmd tool with error {result.stderr.decode()}")
            sys.exit(-1)
        build_py.run(self)


def open_file(fname):
    """Open and return a file-like object for the relative filename."""
    return open(os.path.join(os.path.dirname(__file__), fname))


setup(
    name="azul-plugin-dotnet-decompiler",
    description="Decompiles dotnet using ILSpy's commandline tool",
    cmdclass={"build_py": Build},
    author="Azul",
    author_email="azul@asd.gov.au",
    url="https://www.asd.gov.au/",
    packages=["azul_plugin_dotnet_decompiler"],
    include_package_data=True,
    python_requires=">=3.12",
    classifiers=[],
    entry_points={
        "console_scripts": [
            "azul-plugin-dotnet-decompiler = azul_plugin_dotnet_decompiler.main:main",
        ]
    },
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=[r.strip() for r in open_file("requirements.txt") if not r.startswith("#")],
)
