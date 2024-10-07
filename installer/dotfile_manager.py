import datetime
import logging
import pathlib

__all__ = ["DotfileManager"]


class DotfileManager:
    def __init__(self, timestamp: datetime.datetime, logger: logging.Logger) -> None:
        self._timestamp = timestamp
        self._logger = logger
        self._backup_suffix = f".pre-dotfiles-installer-{self._timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

    def backup_path(self, path: pathlib.Path) -> pathlib.Path:
        """Get the backup path for a file"""
        return path.parent / f"{path.name}{self._backup_suffix}"

    def safe_symlink(self, source: pathlib.Path, destination: pathlib.Path) -> None:
        """Create a symlink. If `destination` is an existing file, back it up.
        If `destination` is a symlink, remove it first.

        :param source: Source file
        :param destination: Path to create the symlink in
        """
        if destination.is_dir():
            destination = destination / source.name

        self.cleanup_path(destination)
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

        self.cleanup_path(destination)
        self._logger.info("Write %s", destination)
        destination.write_text(text)

    def cleanup_path(self, path: pathlib.Path) -> pathlib.Path | None:
        """Clean up a path. Depending on the type of the path, one of the following two steps is done:

        1. If the path is a symlink, it is removed
        2. If the path is a file, it is moved to the backup path

        :return: The new path if a file is moved to the backup path, otherwise None
        """
        if path.is_symlink():
            self._logger.info("Remove symlink of %s to %s", path, path.resolve())
            path.unlink()
            return None

        if path.is_file():
            backup_path = self.backup_path(path)
            self._logger.info(f"Rename existing {path.name} file to {backup_path}")
            path.rename(backup_path)
            return backup_path
        return None

    def _file_content_matches(self, text: str, path: pathlib.Path) -> bool:
        """Check if the content of a file matches a string

        :param text: Text to check the file content against
        :param path: Path to check
        :return: Whether the content of `path` matches `text`
        """
        if path.is_file() and path.read_text() == text:
            return True
        return False
