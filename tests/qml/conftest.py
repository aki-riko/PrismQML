# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared QML test fixtures. QML 测试共享 fixture。"""

import pytest


@pytest.fixture(scope="module")
def qml_engine(qapp):
    """Reuse QML type registration and import caches within one test module."""
    from pathlib import Path

    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtQml import QQmlApplicationEngine

    from prismqml import register_types

    root = Path(__file__).resolve().parents[2]
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(root / "prismqml"))
    register_types(engine)
    yield engine
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
