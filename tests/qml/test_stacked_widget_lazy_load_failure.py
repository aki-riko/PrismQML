# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget lazy-load failure regressions. StackedWidget 懒加载失败回归。"""

import time
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlExpression

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 2000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        _pump()
    return predicate()


def _evaluate(item, expression: str):
    result = QQmlExpression(
        QQmlApplicationEngine.contextForObject(item), item, expression
    ).evaluate()
    return result[0] if isinstance(result, tuple) else result


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def test_lazy_load_error_restores_old_page_and_emits_once(qapp, tmp_path):
    """A broken target must fail once and stop loading. 损坏目标须单次失败并停止加载。"""
    configure_qml_environment()
    valid_page = tmp_path / "ValidPage.qml"
    invalid_page = tmp_path / "InvalidPage.qml"
    valid_page.write_text(
        "import QtQuick\nRectangle { objectName: \"validPage\" }\n",
        encoding="utf-8",
    )
    invalid_page.write_text(
        "import QtQuick\nRectangle { this is not valid QML }\n",
        encoding="utf-8",
    )
    valid_url = QUrl.fromLocalFile(str(valid_page)).toString()
    invalid_url = QUrl.fromLocalFile(str(invalid_page)).toString()
    scene = f"""
import QtQuick
import PrismQML

StackedWidget {{
    width: 320
    height: 180
    animationEnabled: false
    lazyLoading: true
    lazyActivationDelay: Enums.duration.dialog
    currentIndex: 0
    pageSources: ["{valid_url}", "{invalid_url}"]
}}
"""

    messages = []
    previous_handler = qInstallMessageHandler(
        lambda _mode, _context, message: messages.append(str(message))
    )
    engine = QQmlApplicationEngine()
    component = None
    stack = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            scene.encode("utf-8"),
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/lazy-load-failure.qml")),
        )
        assert _wait_until(
            lambda: component.status() != QQmlComponent.Status.Loading
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        stack = component.create(engine.rootContext())
        assert stack is not None, [error.toString() for error in component.errors()]
        assert _wait_until(lambda: bool(_evaluate(stack, "_isPageLoaded(0)")))

        failures = []
        assert hasattr(stack, "pageLoadFailed")
        stack.pageLoadFailed.connect(
            lambda index, error: failures.append((index, str(error)))
        )

        stack.setProperty("currentIndex", 1)
        _pump(50)
        assert bool(_evaluate(stack, "_loaders[1].active")) is False
        assert bool(_evaluate(stack, "_loaders[0].visible")) is True
        assert _wait_until(
            lambda: bool(
                _evaluate(stack, "_loaders[1].status === Loader.Error")
            )
        )
        _pump(300)

        assert int(_evaluate(stack, "_displayIndex")) == 0
        assert bool(_evaluate(stack, "_loaders[0].visible")) is True
        assert bool(_evaluate(stack, "_loaders[1].visible")) is False
        overlay = stack.findChild(QObject, "lazyLoadingOverlay")
        assert overlay is not None
        helper = overlay.parent()
        assert helper.property("pendingTargetIndex") == -1
        assert helper.property("isLoadingSwitching") is False
        activation_timer = helper.findChild(QObject, "lazyLoaderActivateTimer")
        assert activation_timer is not None
        assert 0 < activation_timer.property("interval") < stack.property(
            "lazyActivationDelay"
        )
        assert overlay.property("visible") is False
        assert len(failures) == 1
        assert failures[0][0] == 1
        assert "InvalidPage.qml" in failures[0][1]
        assert "Expected" in failures[0][1]
        assert not any(
            "[启动剖析] StackedWidget" in message
            or "[懒加载诊断] StackedWidget #" in message
            for message in messages
        )
    finally:
        qInstallMessageHandler(previous_handler)
        _release(qapp, stack, component, engine)


def test_lazy_load_diagnostics_cover_transition_boundaries(qapp, tmp_path):
    """A successful switch must expose every boundary. 成功切页必须暴露各阶段边界。"""
    configure_qml_environment()
    first_page = tmp_path / "FirstPage.qml"
    second_page = tmp_path / "SecondPage.qml"
    first_page.write_text(
        'import QtQuick\nRectangle { objectName: "firstPage" }\n',
        encoding="utf-8",
    )
    second_page.write_text(
        'import QtQuick\nRectangle { objectName: "secondPage" }\n',
        encoding="utf-8",
    )
    first_url = QUrl.fromLocalFile(str(first_page)).toString()
    second_url = QUrl.fromLocalFile(str(second_page)).toString()
    scene = f"""
import QtQuick
import PrismQML

StackedWidget {{
    width: 320
    height: 180
    animationEnabled: false
    lazyLoading: true
    currentIndex: 0
    pageSources: ["{first_url}", "{second_url}"]
}}
"""
    messages = []
    diagnostic_modes = []

    def record_message(mode, _context, message):
        rendered = str(message)
        messages.append(rendered)
        if "[懒加载诊断] StackedWidget #" in rendered:
            diagnostic_modes.append(mode)

    previous_handler = qInstallMessageHandler(record_message)
    engine = QQmlApplicationEngine()
    component = None
    stack = None
    try:
        register_types(engine)
        engine.rootContext().setContextProperty(
            "PrismQmlStartupProfileVerbose", True
        )
        component = QQmlComponent(engine)
        component.setData(
            scene.encode("utf-8"),
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/lazy-load-diagnostics.qml")),
        )
        assert _wait_until(
            lambda: component.status() != QQmlComponent.Status.Loading
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        stack = component.create(engine.rootContext())
        assert stack is not None, [error.toString() for error in component.errors()]
        assert _wait_until(lambda: bool(_evaluate(stack, "_isPageLoaded(0)")))

        stack.setProperty("currentIndex", 1)
        assert _wait_until(lambda: int(_evaluate(stack, "_displayIndex")) == 1)

        diagnostic_messages = [
            message for message in messages if "[懒加载诊断] StackedWidget #" in message
        ]
        assert diagnostic_modes
        assert set(diagnostic_modes) == {QtMsgType.QtDebugMsg}
        expected_stages = (
            "stage=stacked.current_index_changed",
            "stage=stacked.switch_request",
            "stage=stacked.helper_dispatch.begin",
            "stage=helper.show.begin",
            "stage=helper.loader_activate.begin",
            "stage=stacked.loader_activate.begin",
            "stage=stacked.source_loader.status_changed",
            "stage=helper.loading_complete.emit_begin",
            "stage=stacked.loading_complete.begin",
            "stage=stacked.loading_complete.done",
            "stage=helper.loading_complete.emit_done",
        )
        for stage in expected_stages:
            assert any(stage in message for message in diagnostic_messages), stage

        sequences = [
            int(message.split("StackedWidget #", 1)[1].split(" ", 1)[0])
            for message in diagnostic_messages
        ]
        assert sequences == sorted(sequences)
        assert len(sequences) == len(set(sequences))
        assert all(
            " current=" in message
            and " display=" in message
            and " pending=" in message
            and " targetSource=\"" in message
            and " currentSource=\"" in message
            and (" loader." in message or " loader=" in message)
            for message in diagnostic_messages
        )
        assert any(
            f'targetSource="{second_url}"' in message
            and f'currentSource="{first_url}"' in message
            and 'loader.source="' in message
            and 'loader.itemObjectName="' in message
            for message in diagnostic_messages
        )
    finally:
        qInstallMessageHandler(previous_handler)
        _release(qapp, stack, component, engine)
