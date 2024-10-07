import datetime
import logging
import pathlib
from typing import Any, Generator

import pytest

from installer import DotfileManager, temp_dir


@pytest.fixture  # type: ignore
def dotfile_manager() -> Generator[DotfileManager, Any, None]:
    now = datetime.datetime.now().astimezone()
    yield DotfileManager(now, logging.getLogger("test"))


@pytest.fixture  # type: ignore
def path() -> Generator[pathlib.Path, Any, None]:
    with temp_dir() as t:
        yield (t / "foo").resolve()


@pytest.fixture  # type: ignore
def file(path: pathlib.Path) -> Generator[pathlib.Path, Any, None]:
    path.touch()
    yield path


@pytest.fixture  # type: ignore
def content() -> str:
    return "Lorem ipsum dolor sit amet"


@pytest.fixture  # type: ignore
def file_with_content(file: pathlib.Path, content: str) -> Generator[pathlib.Path, Any, None]:
    file.write_text(content)
    yield file


def test_safe_symlink_to_file(dotfile_manager: DotfileManager, file: pathlib.Path) -> None:
    """Test that a symlink is created"""
    symlink_path = file.parent / "bar"
    dotfile_manager.safe_symlink(file, symlink_path)
    assert symlink_path.resolve() == file


def test_safe_symlink_in_dir(dotfile_manager: DotfileManager, file: pathlib.Path) -> None:
    """Test symlink has the same name as the file when symlinking to a directory"""
    symlink_dir_path = file.parent / "bar"
    symlink_dir_path.mkdir()
    dotfile_manager.safe_symlink(file, symlink_dir_path)
    symlink_path = symlink_dir_path / file.name
    assert symlink_path.resolve() == file
    assert symlink_path.name == file.name


def test_symlink_same_is_updated(dotfile_manager: DotfileManager, file: pathlib.Path) -> None:
    """Test that an existing symlink is updated"""
    symlink_path = file.parent / "bar"
    dotfile_manager.safe_symlink(file, symlink_path)
    stat1 = symlink_path.stat(follow_symlinks=False)
    dotfile_manager.safe_symlink(file, symlink_path)
    stat2 = symlink_path.stat(follow_symlinks=False)
    assert stat1 != stat2

    example_file2 = (file.parent / "baz").resolve()
    example_file2.touch()
    dotfile_manager.safe_symlink(example_file2, symlink_path)
    assert symlink_path.resolve() == example_file2
    assert example_file2.stat() != stat2


def test_safe_write(dotfile_manager: DotfileManager, path: pathlib.Path, content: str) -> None:
    """Test that a file is written and not changed if the content matches"""
    assert not path.is_file()
    dotfile_manager.safe_write(content, path)
    assert path.is_file()
    assert path.read_text() == content
    stat1 = path.stat()

    dotfile_manager.safe_write(content, path)
    assert path.stat() == stat1


def test_safe_write_file_exists_content_differs(
    dotfile_manager: DotfileManager, file: pathlib.Path, content: str
) -> None:
    """Test that the file is replaced if the content differs and a backup is created"""
    stat1 = file.stat()
    dotfile_manager.safe_write(content, file)

    assert file.stat() != stat1
    assert dotfile_manager.backup_path(file).is_file()
    assert dotfile_manager.backup_path(file).read_text() == ""


def test_safe_write_is_symlink(dotfile_manager: DotfileManager, file: pathlib.Path, content: str) -> None:
    """Test that a safe write on an existing symlink removes the symlink and writes the file"""
    symlink_path = file.parent / "bar"
    dotfile_manager.safe_symlink(file, symlink_path)
    symlink_stat = symlink_path.stat()
    dotfile_manager.safe_write(content, symlink_path)
    assert symlink_path.is_file()
    assert symlink_path.stat() != symlink_stat
