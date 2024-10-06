from __future__ import annotations

import collections.abc
import dataclasses
import datetime
import getpass
import platform
import pwd
import sys
from typing import TYPE_CHECKING, Any, Literal, cast

if sys.version_info > (3, 11):
    from typing import Self
elif TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ["Config"]

Platform = Literal["Linux", "Darwin", "Java", "Windows"]


@dataclasses.dataclass
class Config:
    """Global configuration object for the installer"""

    username: str
    full_name: str
    email: str | None
    confirm_all_stages: bool
    platform: Platform = dataclasses.field(
        default_factory=cast(collections.abc.Callable[[], Platform], platform.system)
    )
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
