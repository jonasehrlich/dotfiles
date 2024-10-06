from __future__ import annotations

import collections.abc
import logging
import sys
from typing import Any, Protocol

from .config import Config
from .utils import confirm, indent_logger

_logger = logging.getLogger(__name__)

__all__ = ["stage", "Stage", "STAGE_REGISTRY"]


class ActionsContainer(Protocol):
    def add_argument(*args: Any, **kwargs: Any) -> Any: ...


class StageFunc(Protocol):
    def __call__(self, cfg: Config) -> Any: ...


class _StageRegistry:
    _stages: dict[str, Stage] = {}

    @classmethod
    def register(cls, stage: Stage) -> None:
        _logger.debug("Register '%s' stage", stage.name)
        cls._stages[stage.flag_name] = stage

    def __iter__(self) -> collections.abc.Iterator[Stage]:
        return iter(self._stages.values())


STAGE_REGISTRY = _StageRegistry()


class Stage:
    def __init__(  # noqa: PLR0913
        self,
        name: str,
        func: StageFunc,
        interactive_confirm: bool,
        predicate: collections.abc.Callable[[], bool] | None,
        abort_on_error: bool,
        help: str = "",
        dependencies: list[str | Stage] | None = None,
    ) -> None:
        self._name = name
        self._flag_name = self.name.lower().replace(" ", "-").replace(".", "")
        self._func = func
        self._help = help or name
        self._dependencies = dependencies or []

        self._interactive_confirm = interactive_confirm
        self._predicate = predicate
        self._abort_on_error = abort_on_error

        self._logger = logging.getLogger(self.flag_name)
        if dependencies:
            self._logger.warning("dependencies are not supported yet")

    @property
    def name(self) -> str:
        return self._name

    @property
    def help(self) -> str:
        return self._help

    @property
    def flag_name(self) -> str:
        return self._flag_name

    def __call__(self, cfg: Config) -> None:
        flag_name = self.flag_name
        if flag_name in cfg.skipped_stages:
            return
        if cfg.only_stages and flag_name not in cfg.only_stages:
            return

        if self._predicate is not None and not self._predicate():
            _logger.info(f"{self._name} is not required, skip")
            return
        if not cfg.confirm_all_stages and self._interactive_confirm and not confirm(f"{self.name}?", default="y"):
            return

        _logger.info(f"{self.name} ...")
        try:
            with indent_logger(_logger):
                self._func(cfg)
        except Exception as exc:
            self._logger.error("Error: %s", exc)
            if self._abort_on_error:
                sys.exit(1)
        else:
            _logger.info(f"{self._name} - done")
        self._func(cfg)


def stage(
    name: str,
    interactive_confirm: bool = False,
    predicate: collections.abc.Callable[[], bool] | None = None,
    abort_on_error: bool = False,
) -> collections.abc.Callable[..., Stage]:
    """Make a function to wrap a function as a stage of the installation

    :param name: Name of the stage
    :param interactive_confirm: Whether execution of this stage requires an interactive confirm, defaults to False
    :param predicate: Function returning at runtime whether this stage should run, defaults to None
    :param abort_on_error: Whether to abort installation on error, defaults to False
    :return: Decorator function
    """

    def dec(func: StageFunc) -> Stage:
        _stage = Stage(
            name=name,
            func=func,
            interactive_confirm=interactive_confirm,
            predicate=predicate,
            abort_on_error=abort_on_error,
        )
        _StageRegistry.register(_stage)
        return _stage

    return dec
