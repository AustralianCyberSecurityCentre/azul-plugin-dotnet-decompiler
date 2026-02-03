"""Install dotnet ilspy command."""

# hatch_build.py
import logging
import subprocess
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build hook for running actions at build time."""

    def initialize(self, version, build_data):
        """Install dotnet ilspy command."""
        result = subprocess.run(["dotnet", "tool", "install", "ilspycmd", "-g"], stderr=subprocess.PIPE)  # noqa: S603  # nosec: B603 B607
        if result.returncode != 0 and "already installed" not in result.stderr.decode():
            logging.warning(f"Failed to install ilspycmd tool with error {result.stderr.decode()}")
            sys.exit(-1)
