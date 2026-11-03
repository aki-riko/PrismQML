# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared QML test fixtures. QML 测试共享 fixture。"""

import pytest


@pytest.fixture(autouse=True)
def _drain_deferred_delete_between_tests():
    """Drain DeferredDelete before and after every QML test. 每个 QML 用例前后排空延迟删除。

    ``processEvents()`` never delivers DeferredDelete events, so a test that only calls
    ``deleteLater()`` leaves its widget/window reachable: ``topLevelWindows()`` still
    returns a Python wrapper whose C++ object is already gone. Fixtures that snapshot
    ``windows_before`` then capture that zombie as their baseline, and the teardown
    comparison fails with a diff full of
    ``libshiboken: Internal C++ object (QQuickWindow) already deleted``. Real CI shards
    hit exactly that as ``ERROR at teardown of
    test_flow_layout_modes_preserve_current_geometry``.
    ``processEvents()`` 从不派发 DeferredDelete, 因此只调用 ``deleteLater()`` 的用例会留下
    仍可达的窗口: ``topLevelWindows()`` 继续返回 C++ 对象已销毁的 Python 包装。快照
    ``windows_before`` 的 fixture 于是把僵尸当成基线, teardown 比较就失败, 差异里满是
    ``libshiboken: Internal C++ object (QQuickWindow) already deleted``。真实 CI 分片正是
    以 ``ERROR at teardown of test_flow_layout_modes_preserve_current_geometry`` 命中这个形态。

    Draining at both edges keeps every test's baseline honest without touching the ~290
    fixtures that sample ``topLevelWindows()`` without flushing first.
    在两侧都排空, 可以让每个用例的基线保持真实, 而无需改动那约 290 个未先冲刷就采样的
    fixture。
    """
    from PySide6.QtCore import QCoreApplication, QEvent

    if QCoreApplication.instance() is None:
        yield
        return

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    yield
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


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
