# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Explicit pytest Qt-import canary. pytest 显式 Qt 导入哨兵。"""

import importlib
import json
import os
import sys
from pathlib import Path

from scripts.test_process import automated_test_boundary_is_active


SENTINEL_ENV = "PRISMQML_PYTEST_QT_CANARY_SENTINEL"
sentinel_path = os.environ.get(SENTINEL_ENV)
if not sentinel_path:
    raise RuntimeError(f"{SENTINEL_ENV} is required")

payload = {
    "boundary_active": automated_test_boundary_is_active(),
    "pyside_preloaded": "PySide6" in sys.modules,
    "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
}
Path(sentinel_path).write_text(json.dumps(payload), encoding="utf-8")
qt_core = importlib.import_module("PySide6.QtCore")
if not qt_core.qVersion():
    raise RuntimeError("PySide6.QtCore did not report a Qt version")
