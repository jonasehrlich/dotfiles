from __future__ import annotations

import collections.abc
import contextlib
import difflib
import functools
import logging
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any, Generator, Literal


def configure_logging(logger: logging.Logger, verbose: bool) -> None:
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)


@contextlib.contextmanager
def indent_logger(logger: logging.Logger, indent: str = "  ") -> Generator[None, Any, None]:
    for handler in logger.handlers:
        if handler.formatter and handler.formatter._fmt:
            handler.setFormatter(logging.Formatter(indent + handler.formatter._fmt))
    try:
        yield
    finally:
        for handler in logger.handlers:
            if handler.formatter and handler.formatter._fmt:
                handler.setFormatter(logging.Formatter(handler.formatter._fmt[len(indent) :]))


def input_with_default(_prompt: str, default: str | None) -> str:
    """Prompt for a user input and return a default value on empty input

    :param _prompt: Prompt to write to stdout
    :param default: Default value
    :return: User input or default value
    """
    resp = input(_prompt + " ")
    if default and not resp:
        resp = default
    return resp


def confirm(prompt_: str, default: Literal["y", "n"] | None = None) -> bool:
    if default == "y":
        options = "(Y/n)"
    elif default == "n":
        options = "(y/N)"
    elif default is None:
        options = "(y/n)"

    resp = input_with_default(f"{prompt_} {options}", default)
    if resp.upper() == "Y":
        return True
    elif resp.upper() == "N":
        return False
    else:
        if resp.upper():
            print(f"Invalid input: '{resp}'")
        return confirm(prompt_, default)


def prompt(
    prompt_: str,
    default: str | None = None,
    confirm_required: bool = True,
    validator: collections.abc.Callable[[str], bool] | None = None,
) -> str:
    input_prompt = f"{prompt_} ({default})" if default is not None else prompt_

    resp = input_with_default(input_prompt, default)
    if resp == default:
        # No need to validate and confirm if we use the default
        return resp

    if validator is not None and not validator(resp):
        print(f"Invalid input: {resp}")
        return prompt(prompt_, default, confirm_required, validator)

    if confirm_required and not confirm(f"Confirm '{resp}'?", default="y"):
        return prompt(prompt_, default=default, confirm_required=confirm_required, validator=validator)
    return resp


def supports_color() -> bool:
    """
    Return True if the terminal supports color, False otherwise.
    """
    # Check if the output is a terminal
    if not sys.stdout.isatty():
        return False

    # Check for TERM environment variable
    term = os.environ.get("TERM", "")
    if term in ("xterm", "xterm-color", "xterm-256color", "linux", "screen", "screen-256color"):
        return True

    return False


def red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def colored_diff(text1: str, text2: str) -> Generator[str, Any, None]:
    diff = difflib.ndiff(text1.splitlines(), text2.splitlines())
    if not supports_color():
        for line in diff:
            yield line
        return

    for line in diff:
        if line.startswith("- "):
            yield red(line)
        elif line.startswith("+ "):
            yield green(line)
        elif line.startswith("? "):
            yield yellow(line)
        else:
            yield line


def symlink_exists(symlink: pathlib.Path, path: pathlib.Path) -> bool:
    return symlink.resolve() == path.resolve()


@functools.cache
def which(name: str) -> pathlib.Path:
    """Get the path of an executable with `name`

    :param name: Name of the executable
    :raises RuntimeError: Raised if the executable cannot be found
    :return: Path of the executable
    """
    exec_path = shutil.which(name)
    if exec_path is None:
        raise RuntimeError(f"{name} executable not found")

    return pathlib.Path(exec_path)


def curl() -> pathlib.Path:
    """Get the path of the `curl` executable"""
    return which("curl")


def sh() -> pathlib.Path:
    """Get the path of the `sh` executable"""
    return which("sh")


def git() -> pathlib.Path:
    """Get the path of the `git` executable"""
    return which("git")


@contextlib.contextmanager
def temp_dir(
    suffix: str | None = None,
    prefix: str | None = None,
    dir: pathlib.Path | None = None,
    ignore_cleanup_errors: bool = False,
) -> collections.abc.Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory(
        suffix=suffix, prefix=prefix, dir=dir, ignore_cleanup_errors=ignore_cleanup_errors
    ) as t:
        yield pathlib.Path(t)


@contextlib.contextmanager
def chdir(path: pathlib.Path) -> collections.abc.Generator[pathlib.Path, Any, None]:
    old_cwd = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(old_cwd)


@contextlib.contextmanager
def temp_cwd() -> collections.abc.Generator[pathlib.Path, Any, None]:
    with temp_dir() as t, chdir(t):
        yield t
