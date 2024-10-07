from __future__ import annotations

import collections.abc
import enum
import logging
import platform
import sys
from typing import Any, Protocol

from .config import Config, Platform
from .utils import confirm, indent_logger

_logger = logging.getLogger(__name__)

__all__ = ["stage", "Stage", "STAGE_REGISTRY"]


class ActionsContainer(Protocol):
    """Protocol to define the interface for a argparse._ActionsContainer object"""

    def add_argument(*args: Any, **kwargs: Any) -> Any: ...


class StageFunc(Protocol):
    __name__: str

    def __call__(self, cfg: Config) -> Any: ...


class _StageRegistry:
    _stages: dict[str, Stage] = {}

    @classmethod
    def register(cls, stage: Stage) -> None:
        if not stage.is_valid_for_current_platform():
            return
        _logger.debug("Register '%s' stage", stage.name)
        cls._stages[stage.flag_name] = stage

    def __iter__(self) -> collections.abc.Iterator[Stage]:
        return iter(self._stages.values())

    def resolve_dependencies(self) -> None:
        """Resolve dependencies in all stages"""
        for _stage in self._stages.values():
            _stage.resolve_dependencies(self._stages)

    @classmethod
    def clear(cls) -> None:
        cls._stages.clear()


STAGE_REGISTRY = _StageRegistry()


class Stage:
    class Status(enum.Enum):
        NOT_EXECUTED = "not executed"
        SUCCESS = "success"
        FAILURE = "failure"
        SKIPPED = "skipped"

        def __str__(self) -> str:
            return self.value

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        func: StageFunc,
        interactive_confirm: bool,
        predicate: collections.abc.Callable[[], bool] | None,
        abort_on_error: bool,
        details: str | None,
        platforms: collections.abc.Sequence[Platform] | None,
        dependencies: list[str | Stage] | None = None,
    ) -> None:
        self._name = name
        self._flag_name = self.name.lower().replace(" ", "-").replace(".", "")
        self._func = func
        self._details = details
        self._platforms = platforms or []

        self._raw_dependencies = dependencies or []
        self._resolved_dependencies: list[Stage] = []

        self._interactive_confirm = interactive_confirm
        self._predicate = predicate
        self._abort_on_error = abort_on_error

        self._logger = logging.getLogger(self.flag_name)
        self._status = Stage.Status.NOT_EXECUTED

        if dependencies:
            self._logger.warning("dependencies are not supported yet")

    @property
    def name(self) -> str:
        return self._name

    @property
    def details(self) -> str | None:
        return self._details

    @property
    def flag_name(self) -> str:
        return self._flag_name

    @property
    def status(self) -> Stage.Status:
        return self._status

    def is_valid_for_current_platform(self) -> bool:
        """Return whether this stage is supported on the current platform"""
        return not self._platforms or platform.system() in self._platforms

    def func_name(self) -> str:
        return self._func.__name__

    def resolve_dependencies(self, stage_map: dict[str, Stage]) -> None:
        """Resolve the string dependencies to

        :param stage_map: Map of flag names to stage objects
        """
        func_name_map = {stage.func_name: stage for stage in stage_map.values()}

        for dep in enumerate(self._raw_dependencies):
            if isinstance(dep, str):
                # The stage was only provided as a string, replace all dependency names with their real stages

                stage = stage_map.get(dep)
                if not stage:
                    stage = func_name_map.get(dep)

                if stage:
                    self._resolved_dependencies.append(stage_map[dep])

                self._logger.warning(
                    "Dependency '%s' defined on '%s' is not a valid stage, ignoring", dep, self.flag_name
                )
                continue
            elif isinstance(dep, Stage):
                self._resolved_dependencies.append(dep)
            else:
                self._logger.warning("Invalid type %s for %r", type(dep), dep)

    def __call__(self, cfg: Config) -> None:
        flag_name = self.flag_name
        skip = False
        if flag_name in cfg.skipped_stages:
            skip = True
            _logger.debug(f"{self._name} is skipped")

        if cfg.only_stages and flag_name not in cfg.only_stages:
            skip = True
            _logger.debug(f"{self._name} is not selected, skip")

        if not skip and self._predicate is not None and not self._predicate():
            skip = True
            _logger.info(f"{self._name} is not required, skip")

        if (
            not skip
            and not cfg.confirm_all_stages
            and self._interactive_confirm
            and not confirm(f"{self.name}?", default="y")
        ):
            skip = True

        if skip:
            self._status = Stage.Status.SKIPPED
            return

        _logger.info(f"{self.name} ...")
        try:
            with indent_logger(_logger):
                self._func(cfg)
        except Exception as exc:
            self._status = Stage.Status.FAILURE
            self._logger.error("Error: %s", exc)
            if self._abort_on_error:
                sys.exit(1)
        else:
            self._status = Stage.Status.SUCCESS
            _logger.info(f"{self._name} - done")


def stage(  # noqa: PLR0913
    name: str,
    help: str | None = None,
    interactive_confirm: bool = False,
    predicate: collections.abc.Callable[[], bool] | None = None,
    abort_on_error: bool = False,
    details: str | None = None,
    platforms: collections.abc.Sequence[Platform] | None = None,
    dependencies: list[str | Stage] | None = None,
) -> collections.abc.Callable[..., Stage]:
    """Make a function to wrap a function as a stage of the installation

    :param name: Name of the stage
    :param interactive_confirm: Whether execution of this stage requires an interactive confirm, defaults to False
    :param predicate: Function returning at runtime whether this stage should run, defaults to None
    :param abort_on_error: Whether to abort installation on error, defaults to False
    :param details: Additional details on the stage
    :param platforms: List of platforms where this stage should run, defaults to None
    :return: Decorator function
    """

    def dec(func: StageFunc) -> Stage:
        _stage = Stage(
            name=name,
            func=func,
            interactive_confirm=interactive_confirm,
            predicate=predicate,
            abort_on_error=abort_on_error,
            details=details,
            platforms=platforms,
            dependencies=dependencies,
        )
        _StageRegistry.register(_stage)
        return _stage

    return dec
