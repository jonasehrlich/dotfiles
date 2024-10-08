import dataclasses
from typing import Any, Generator
from unittest import mock

import pytest

from installer.config import Config
from installer.stages import Stage, stage


@pytest.fixture  # type:ignore
def mock_stage_func() -> Generator[mock.MagicMock, Any, None]:
    yield mock.MagicMock()


@pytest.fixture  # type: ignore
def config() -> Generator[Config, Any, None]:
    yield Config.from_env(email=None, skipped_stages=None, only_stages=None, confirm_all_stages=False)


@pytest.fixture  # type: ignore
def test_stage_name() -> str:
    return "test"


def test_stage_executed(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name)(mock_stage_func)
    s(config)
    mock_stage_func.assert_called_once_with(config)
    assert s.status == Stage.Status.SUCCESS


def test_stage_exclude_predicate(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name, predicate=lambda: False)(mock_stage_func)
    s(config)
    mock_stage_func.assert_not_called()
    assert s.status == Stage.Status.SKIPPED


def test_stage_skip_cli_flag(test_stage_name: str, mock_stage_func: mock.MagicMock) -> None:
    s = stage(test_stage_name)(mock_stage_func)
    s(Config.from_env(email=None, skipped_stages=[test_stage_name], only_stages=[], confirm_all_stages=False))
    mock_stage_func.assert_not_called()
    assert s.status == Stage.Status.SKIPPED


def test_stage_only_other_stage(test_stage_name: str, mock_stage_func: mock.MagicMock) -> None:
    s = stage(test_stage_name)(mock_stage_func)
    s(Config.from_env(email=None, only_stages=[test_stage_name + "foo"], skipped_stages=[], confirm_all_stages=False))
    mock_stage_func.assert_not_called()
    assert s.status == Stage.Status.SKIPPED


def test_stage_only_stage(test_stage_name: str, mock_stage_func: mock.MagicMock) -> None:
    cfg: Config = Config.from_env(
        email=None, only_stages=[test_stage_name], skipped_stages=[], confirm_all_stages=False
    )
    s = stage(test_stage_name)(mock_stage_func)
    s(cfg)
    mock_stage_func.assert_called_once_with(cfg)
    assert s.status == Stage.Status.SUCCESS


def test_stage_error_abort(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name, abort_on_error=True)(mock_stage_func)
    mock_stage_func.side_effect = Exception("test")
    with pytest.raises(SystemExit):
        s(config)
    assert s.status == Stage.Status.FAILURE


def test_stage_error_no_abort(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name)(mock_stage_func)
    mock_stage_func.side_effect = Exception("test")
    s(config)
    assert s.status == Stage.Status.FAILURE


def test_stage_interactive_confirm(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name, interactive_confirm=True)(mock_stage_func)
    with mock.patch("installer.stages.confirm", return_value=True) as confirm_mock:
        s(config)
        confirm_mock.assert_called_once()
    mock_stage_func.assert_called_once_with(config)
    assert s.status == Stage.Status.SUCCESS


def test_stage_interactive_confirm_no(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    s = stage(test_stage_name, interactive_confirm=True)(mock_stage_func)
    with mock.patch("installer.stages.confirm", return_value=False) as confirm_mock:
        s(config)
        confirm_mock.assert_called_once()
    mock_stage_func.assert_not_called()
    assert s.status == Stage.Status.SKIPPED


def test_stage_interactive_confirm_all(test_stage_name: str, mock_stage_func: mock.MagicMock, config: Config) -> None:
    cfg: Config = dataclasses.replace(config, confirm_all_stages=True)
    s = stage(test_stage_name, interactive_confirm=True)(mock_stage_func)
    with mock.patch("installer.stages.confirm", return_value=False) as confirm_mock:
        s(cfg)
        confirm_mock.assert_not_called()
    mock_stage_func.assert_called_once_with(cfg)
    assert s.status == Stage.Status.SUCCESS
