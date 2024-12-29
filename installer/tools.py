import dataclasses
import functools
import pathlib
import shutil


class ToolNotFoundError(RuntimeError):
    """Raised if a specific tool was not found"""


@functools.cache
def which(name: str) -> pathlib.Path:
    exec_path = shutil.which(name)
    if exec_path is None:
        raise ToolNotFoundError(f"{name} executable not found")
    return pathlib.Path(exec_path)


@dataclasses.dataclass(frozen=True)
class Tool:
    name: str

    def available(self) -> bool:
        """Whether the tool is available"""
        try:
            return bool(self.path())
        except ToolNotFoundError:
            return False

    def path(self) -> pathlib.Path:
        return which(self.name)


curl = Tool("curl")
git = Tool("git")
sh = Tool("sh")
zsh = Tool("zsh")
code = Tool("code")
ssh_keygen = Tool("ssh-keygen")
brew = Tool("brew")

REQUIRED_TOOLS = (curl, git, sh, zsh)


def missing_required_tools() -> list[Tool]:
    missing_tools: list[Tool] = []
    for tool in REQUIRED_TOOLS:
        if not tool.available():
            missing_tools.append(tool)
    return missing_tools
