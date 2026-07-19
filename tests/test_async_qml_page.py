# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AsyncQmlPage runtime regressions. AsyncQmlPage 运行时回归。"""

from PySide6.QtCore import QObject, Property, QEventLoop, QTimer, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine

from prismqml import AsyncQmlPage
from prismqml.python.core.engine import EngineManager
from prismqml.python.core.incubation import install_incubation_controller
from prismqml.python.window import AsyncQmlPage as WindowAsyncQmlPage


class _Backend(QObject):
    completed = Signal()

    @Property(str, constant=True)
    def marker(self):
        return "backend-ready"

    @Slot()
    def markLoaded(self):
        self.completed.emit()


def _pump_until(predicate, timeout_ms=3000):
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    poll.start()
    timeout.start(timeout_ms)
    loop.exec()
    poll.stop()
    return predicate()


def _write_page(path, *, gated=False):
    ready_property = "property bool prismqmlAsyncReady: false" if gated else ""
    ready_timer = (
        "Timer { interval: 100; running: true; "
        "onTriggered: parent.prismqmlAsyncReady = true }"
        if gated
        else ""
    )
    path.write_text(
        f"""
import QtQuick
Item {{
    property var backend: null
    {ready_property}
    property string marker: backend ? backend.marker : ""
    Component.onCompleted: backend.markLoaded()
    {ready_timer}
}}
""",
        encoding="utf-8",
    )


def test_async_qml_page_injects_backend_before_completed(qapp, tmp_path):
    assert WindowAsyncQmlPage is AsyncQmlPage
    page_path = tmp_path / "TargetPage.qml"
    _write_page(page_path)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    backend = _Backend()
    completed = []
    ready = []
    backend.completed.connect(lambda: completed.append(True))

    page = AsyncQmlPage(page_path, backend=backend)
    page.page_ready.connect(lambda: ready.append(True))
    host = page._qml_item
    assert host.property("pageReady") is False

    page.start_loading()
    page.start_loading()

    assert _pump_until(lambda: page.is_ready)
    assert completed == [True]
    assert ready == [True]
    assert host.property("pageReady") is True
    assert page._qml_item is host.property("contentItem")
    assert page._qml_item.property("marker") == "backend-ready"
    assert page.load_error == ""

    controller._timer.stop()
    EngineManager.reset()


def test_async_qml_page_waits_for_optional_target_ready_gate(qapp, tmp_path):
    page_path = tmp_path / "GatedPage.qml"
    _write_page(page_path, gated=True)
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    backend = _Backend()
    completed = []
    backend.completed.connect(lambda: completed.append(True))

    page = AsyncQmlPage(page_path, backend=backend)
    host = page._qml_item
    page.start_loading()

    assert _pump_until(lambda: completed == [True])
    assert page.is_ready is False
    assert host.property("pageReady") is False
    assert _pump_until(lambda: page.is_ready)
    assert host.property("pageReady") is True

    controller._timer.stop()
    EngineManager.reset()


def test_async_qml_page_reports_real_loader_failure(qapp, tmp_path):
    missing_path = tmp_path / "MissingPage.qml"
    engine = QQmlApplicationEngine()
    EngineManager.set_engine(engine)
    controller = install_incubation_controller(engine)
    page = AsyncQmlPage(missing_path)
    failures = []
    page.page_failed.connect(failures.append)

    page.start_loading()

    assert _pump_until(lambda: bool(failures))
    assert page.is_ready is False
    assert missing_path.as_posix() in page.load_error.replace("\\", "/")

    controller._timer.stop()
    EngineManager.reset()
