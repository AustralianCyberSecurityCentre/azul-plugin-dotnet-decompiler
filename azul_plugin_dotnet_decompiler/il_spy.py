"""Runs the subprocess calls to the dotnet decompiler ILSpy."""

import os
import shutil
import subprocess  # nosec B404
from enum import Enum

ILSPY_BIN = "ilspycmd"


class NotDotnetFileError(Exception):
    """Exception that is raised when the provided file cannot be processed by ILSpy as a dotnet file."""

    pass


class UnprocessableInputError(Exception):
    """Exception that is raised when there is likely a bad input argument to ILSpy."""

    pass


class UnknownILSpyError(Exception):
    """Exception that is raised when ILSpy fails but there isn't a known reason."""

    pass


class UnsupportedPEError(Exception):
    """Exception that is raised when ILSpy fails to process the file because it does not support the PE provided."""

    pass


class PartialDotnetError(Exception):
    """Exception raised when a partial dotnet file was found.

    This typically occurs if the binary has been carved by other plugins e.g malcarve.
    """

    pass


class MissingOutFileError(Exception):
    """Exception raised when ILSpy was meant to create an output file but didn't."""

    pass


class NoILSpyFoundError(Exception):
    """Exception raised when ILSpy binary cannot be found."""

    pass


class IlSpyListTypes(str, Enum):
    """Different types that can be listed out by Ilspy."""

    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    DELEGATE = "delegate"
    ENUM = "enum"


def run_ilspy_list_type(file_path: str, list_type: IlSpyListTypes) -> list[str]:
    """Runs cmdilspy with the supplied options, returns a list of the requested types."""
    option_list = ["-l", list_type.value]
    result = _run_ilspy_and_process_errors(file_path, option_list)
    output = result.stdout

    lines = output.splitlines()
    out_lines = set()
    for line in lines:
        if line.lower().startswith(list_type.value):
            line = line[len(list_type.value) :]

        out_lines.add(line.strip())
    return list(out_lines)


def run_ilspy_decompile(file_path: str, output_dir: str, is_il_code: bool = False) -> str:
    """Runs cmdilspy will write the decompiled cs or il to an output file and then provide the path to the file."""
    option_list = ["--outputdir", output_dir]
    if is_il_code:
        option_list.append("--ilcode")

    _run_ilspy_and_process_errors(file_path, option_list)

    # Get the original filename with no path and no extension.
    base_path = os.path.basename(file_path)
    base_file_name = os.path.splitext(base_path)[0]

    # Get the path to the destination location.
    output_file_path = os.path.join(output_dir, base_file_name)
    if is_il_code:
        output_file_path = output_file_path + ".il"
    else:
        output_file_path = output_file_path + ".decompiled.cs"

    if not os.path.exists(output_file_path):
        raise MissingOutFileError("ILSpy has failed to create the expected output file.")
    return output_file_path


def _run_ilspy_and_process_errors(file_path: str, options: list[str]) -> subprocess.CompletedProcess[str]:
    """Runs ilspy and handle stderr, also provides stdout."""
    bin_abs_path = shutil.which(ILSPY_BIN)
    if not bin_abs_path:
        raise NoILSpyFoundError()

    if "--disable-updatecheck" not in options:
        options.append("--disable-updatecheck")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the file to run ilspy on path: '{file_path}'")
    options.append(file_path)

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [bin_abs_path] + options, capture_output=True, text=True
    )  # nosec B603

    if result.returncode != 0:
        errors = result.stderr
        if "System.BadImageFormatException" in errors:
            raise NotDotnetFileError(errors)
        if "Unhandled exception" in errors:
            raise UnprocessableInputError(errors)
        if "PEFileNotSupportedException" in errors:
            raise UnsupportedPEError(errors)
        if "System.NullReferenceException: Object reference not set to an instance of an object" in errors:
            raise PartialDotnetError(errors)
        raise UnknownILSpyError(errors)

    return result
