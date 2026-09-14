# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Logger level resolution contract. 日志级别解析合同。

The engine must stay quiet by default: DEBUG output is opt-in through the
PRISM_LOG_LEVEL environment variable or an explicit set_level() call.
引擎默认必须安静：DEBUG 输出只能通过 PRISM_LOG_LEVEL 环境变量或显式 set_level() 开启。
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from uuid import uuid4

import pytest


SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "prismqml" / "python" / "core" / "logger.py"
)

ENV_NAME = "PRISM_LOG_LEVEL"


def _load_isolated_module():
    """Load logger.py as a private module with its own singleton state.
    以私有模块加载 logger.py，获得独立的单例状态。"""
    module_name = f"_prismqml_level_test_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SOURCE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unique_logger_name() -> str:
    return f"PrismQML.Test.Level.{uuid4().hex}"


def _cleanup_logger(logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logging.Logger.manager.loggerDict.pop(logger.name, None)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    return monkeypatch


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_default_level_is_info_and_named_default_is_exported(clean_env):
    module = _load_isolated_module()
    assert module.DEFAULT_LOG_LEVEL == logging.INFO
    assert module.LOG_LEVEL_ENV == ENV_NAME
    assert module.resolve_log_level() == logging.INFO


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("DEBUG", logging.DEBUG),
        ("debug", logging.DEBUG),
        ("  Warning  ", logging.WARNING),
        ("10", logging.DEBUG),
        ("30", logging.WARNING),
    ),
)
def test_environment_variable_selects_level(monkeypatch, raw, expected):
    monkeypatch.setenv(ENV_NAME, raw)
    module = _load_isolated_module()
    assert module.resolve_log_level() == expected


@pytest.mark.parametrize("raw", ("", "   ", "verbose", "INFOO", "level-5"))
def test_invalid_or_blank_environment_falls_back_to_info_with_warning(
    monkeypatch, raw, caplog
):
    monkeypatch.setenv(ENV_NAME, raw)
    module = _load_isolated_module()
    with caplog.at_level(logging.WARNING):
        assert module.resolve_log_level() == logging.INFO
    if raw.strip():
        assert any(ENV_NAME in record.getMessage() for record in caplog.records)


def test_explicit_argument_wins_over_environment(monkeypatch):
    monkeypatch.setenv(ENV_NAME, "DEBUG")
    module = _load_isolated_module()
    assert module.resolve_log_level(logging.ERROR) == logging.ERROR


def test_singleton_and_console_handler_take_resolved_level(monkeypatch):
    monkeypatch.setenv(ENV_NAME, "DEBUG")
    module = _load_isolated_module()
    wrapper = module.getLogger(_unique_logger_name(), colored=False)
    try:
        assert wrapper.logger.level == logging.DEBUG
        assert all(handler.level == logging.DEBUG for handler in wrapper.logger.handlers)
    finally:
        _cleanup_logger(wrapper.logger)


def test_debug_suppressed_by_default_and_visible_after_set_level(clean_env):
    module = _load_isolated_module()
    wrapper = module.getLogger(_unique_logger_name(), colored=False)
    capture = _Capture()
    wrapper.logger.addHandler(capture)
    try:
        assert wrapper.logger.level == logging.INFO

        wrapper.debug("hidden debug marker")
        wrapper.info("visible info marker")
        assert [record.getMessage() for record in capture.records] == [
            "visible info marker"
        ]

        wrapper.set_level(logging.DEBUG)
        wrapper.debug("shown debug marker")
        assert [record.getMessage() for record in capture.records] == [
            "visible info marker",
            "shown debug marker",
        ]
        assert all(handler.level == logging.DEBUG for handler in wrapper.logger.handlers)
    finally:
        wrapper.logger.removeHandler(capture)
        _cleanup_logger(wrapper.logger)


def test_suppressed_level_skips_caller_tag_stack_walk(clean_env, monkeypatch):
    module = _load_isolated_module()
    wrapper = module.getLogger(_unique_logger_name(), colored=False)

    def _fail_tag_lookup(_self, _stack_level=4):
        raise AssertionError("tag lookup must not run for suppressed levels")

    monkeypatch.setattr(module.Logger, "_get_caller_tag", _fail_tag_lookup)
    try:
        wrapper.debug("must be filtered before tag resolution")
        with pytest.raises(AssertionError, match="tag lookup"):
            wrapper.info("must resolve tag at INFO")
    finally:
        _cleanup_logger(wrapper.logger)


def test_set_level_exported_from_core_and_root_packages():
    import prismqml
    from prismqml.python import core

    assert "set_level" in prismqml.__all__
    assert "set_level" in core.__all__
    assert callable(prismqml.set_level)
    assert core.set_level is prismqml.python.core.logger.set_level
