from __future__ import annotations

import collections.abc
import contextlib
import dataclasses
import datetime
import difflib
import getpass
import logging
import os
import pathlib
import platform
import pwd
import sys
from typing import TYPE_CHECKING, Any, Callable, Generator, Literal, cast

if sys.version_info > (3, 11):
    from typing import Self
elif TYPE_CHECKING:
    from typing_extensions import Self

Platforms = Literal["Linux", "Darwin", "Java", "Windows"]


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


@dataclasses.dataclass
class Config:
    username: str
    full_name: str
    email: str | None
    confirm_all_stages: bool
    platform: Platforms = dataclasses.field(default_factory=cast(Callable[[], Platforms], platform.system))
    skipped_stages: list[str] = dataclasses.field(default_factory=list)
    only_stages: list[str] = dataclasses.field(default_factory=list)
    timestamp: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)

    @classmethod
    def from_env(
        cls,
        email: str | None,
        skipped_stages: list[str] | None,
        only_stages: list[str] | None,
        confirm_all_stages: bool,
        **kwargs: Any,
    ) -> Self:
        if skipped_stages and only_stages:
            raise ValueError("Cannot set skip and only flags in parallel")

        username = getpass.getuser()
        full_name = pwd.getpwnam(username).pw_gecos.split(",", 1)[0]
        return cls(
            username=username,
            full_name=full_name,
            email=email,
            confirm_all_stages=confirm_all_stages,
            skipped_stages=skipped_stages or [],
            only_stages=only_stages or [],
        )


class DotfileManager:
    def __init__(self, timestamp: datetime.datetime, logger: logging.Logger) -> None:
        self._timestamp = timestamp
        self._logger = logger
        self._backup_suffix = f".pre-dotfiles-installer-{self._timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

    def _cleanup_destination_path(self, path: pathlib.Path) -> None:
        self._backup_file(path)
        self._cleanup_symlink(path)

    def _backup_file(self, path: pathlib.Path) -> pathlib.Path | None:
        """Backup an existing file in `path`

        :param path: Path to back-up
        :return: Back-up path if backed-up, else None
        """
        if path.is_file():
            backup_path = path.parent / f"{path.name}{self._backup_suffix}"
            self._logger.info(f"Rename existing {path.name} file to {backup_path}")
            path.rename(backup_path)
            return backup_path
        return None

    def _cleanup_symlink(self, path: pathlib.Path) -> None:
        """Remove a symlink in `path` if it exists

        :param path: Path to remove the symlink from
        """
        if path.is_symlink():
            self._logger.info("Remove symlink of %s to %s", path, path.resolve())
            path.unlink()

    def _file_content_matches(self, text: str, path: pathlib.Path) -> bool:
        """Check if the content of a file matches a string

        :param text: Text to check the file content against
        :param path: Path to check
        :return: Whether the content of `path` matches `text`
        """
        if path.is_file() and path.read_text() == text:
            return True
        return False

    def safe_symlink(self, source: pathlib.Path, destination: pathlib.Path) -> None:
        """Create a symlink. If `destination` is an existing file, back it up.
        If `destination` is a symlink, remove it first.

        :param source: Source file
        :param destination: Path to create the symlink in
        """
        if destination.is_dir():
            destination = destination / source.name

        self._cleanup_destination_path(destination)
        self._logger.info("Create symlink from %s to %s", destination, source)
        destination.symlink_to(source)

    def safe_write(self, text: str, destination: pathlib.Path) -> None:
        """Write `text` to a file if it differs. If the file exists already back it up first

        :param text: Text to write to `destination`
        :param destination: Path of the file to write to
        """
        if self._file_content_matches(text, destination):
            self._logger.info("%s is up-to-date", destination)
            return
        else:
            self._logger.info("%s differs from desired content", destination)

        self._cleanup_destination_path(destination)
        self._logger.info("Write %s", destination)
        destination.write_text(text)


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
