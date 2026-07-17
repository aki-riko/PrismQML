# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Logger initialization characterization. Logger 初始化特征回归。"""

from __future__ import annotations

import importlib.util
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

import pytest


SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "prismqml" / "python" / "core" / "logger.py"
)


def _load_isolated_module():
    module_name = f"_prismqml_logger_test_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SOURCE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unique_logger_name() -> str:
    return f"PrismQML.Test.Logger.{uuid4().hex}"


def _cleanup_logger(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logging.Logger.manager.loggerDict.pop(logger.name, None)


def test_logger_initialization_configures_real_console_and_rotating_file(tmp_path):
    module = _load_isolated_module()
    name = _unique_logger_name()
    log_file = tmp_path / "nested" / "prism.log"
    logger_wrapper = module.Logger(
        name,
        str(log_file),
        logging.INFO,
        max_bytes=128,
        backup_count=2,
        colored=False,
    )
    try:
        handlers = logger_wrapper.logger.handlers
        assert len(handlers) == 2
        assert type(handlers[0]) is logging.StreamHandler
        assert isinstance(handlers[0].formatter, module.PlainFormatter)
        assert isinstance(handlers[1], RotatingFileHandler)
        assert handlers[1].maxBytes == 128
        assert handlers[1].backupCount == 2
        assert all(handler.level == logging.INFO for handler in handlers)
        logger_wrapper.info("real file message", tag="Init")
        handlers[1].flush()
        assert "[Init] real file message" in log_file.read_text(encoding="utf-8")
    finally:
        _cleanup_logger(logger_wrapper.logger)


def test_logger_singleton_second_initialization_is_a_noop():
    module = _load_isolated_module()
    first_name = _unique_logger_name()
    first = module.Logger(first_name, level=logging.WARNING, colored=False)
    try:
        handler_ids = [id(handler) for handler in first.logger.handlers]
        second = module.Logger(_unique_logger_name(), level=logging.DEBUG, colored=True)
        assert second is first
        assert second.name == first_name
        assert second.logger.level == logging.WARNING
        assert [id(handler) for handler in second.logger.handlers] == handler_ids
        assert second._colored is False
    finally:
        _cleanup_logger(first.logger)


def test_logger_failed_file_setup_keeps_retryable_singleton_state(tmp_path):
    module = _load_isolated_module()
    name = _unique_logger_name()
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    with pytest.raises(OSError):
        module.Logger(name, str(blocked_parent / "prism.log"), colored=False)

    failed = module.Logger._instance
    assert failed is not None
    assert failed._initialized is False
    assert len(failed.logger.handlers) == 1
    retry = module.Logger(name, colored=False)
    try:
        assert retry is failed
        assert retry._initialized is True
        assert len(retry.logger.handlers) == 1
        assert type(retry.logger.handlers[0]) is logging.StreamHandler
    finally:
        _cleanup_logger(retry.logger)
