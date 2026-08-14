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
        assert overlay.findChild(QObject, "qmlPageExitLoader") is None
        assert len(failures) == 1
        assert failures[0][0] == 1
        assert "InvalidPage.qml" in failures[0][1]
        assert "Expected" in failures[0][1]
        assert not any(
            "[启动剖析] StackedWidget" in message
            or "[懒加载诊断] StackedWidget #" in message
            for message in messages
        )
        assert not any(
            "Cannot assign to non-existent property" in message
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


def test_unsafe_incubation_runtime_loads_real_navigation_page_synchronously(qapp):
    """Qt 6.11.1 fallback must not strand the real Gallery page in Loading.

    Qt 6.11.1 回退不得让真实 Gallery 导航页永久停在 Loading。
    """
    configure_qml_environment()
    first_url = QUrl.fromLocalFile(
        str(_ROOT / "examples/pages/ButtonPage.qml")
    ).toString()
    navigation_url = QUrl.fromLocalFile(
        str(_ROOT / "examples/pages/NavigationPage.qml")
    ).toString()
    scene = f"""
import QtQuick
import PrismQML

StackedWidget {{
    width: 1200
    height: 800
    animationEnabled: false
    lazyLoading: true
    currentIndex: 0
    pageSources: ["{first_url}", "{navigation_url}"]
}}
"""
    engine = QQmlApplicationEngine()
    component = None
    stack = None
    try:
        register_types(engine)
        engine.rootContext().setContextProperty(
            "PrismQmlAsynchronousPageLoaderEnabled", False
        )
        component = QQmlComponent(engine)
        component.setData(
            scene.encode("utf-8"),
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/navigation-page-fallback.qml")),
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
        assert bool(_evaluate(stack, "_loaders[1].asynchronous")) is False
        assert _wait_until(
            lambda: bool(_evaluate(stack, "_isPageLoaded(1)")),
            timeout_ms=3000,
        )
        assert _wait_until(
            lambda: int(_evaluate(stack, "_displayIndex")) == 1,
            timeout_ms=1000,
        )
        overlay = stack.findChild(QObject, "lazyLoadingOverlay")
        assert overlay is not None
        assert _wait_until(lambda: overlay.property("visible") is False)
        assert overlay.findChild(QObject, "qmlPageExitLoader") is None
    finally:
        _release(qapp, stack, component, engine)


def test_runtime_eager_switch_stages_real_gallery_pages(qapp):
    """Disabling lazy loading must stage and retain every Gallery page once.

    运行时关闭懒加载须分片激活 Gallery 页面，且每页只加载一次。
    """
    configure_qml_environment()
    page_urls = [
        QUrl.fromLocalFile(str(_ROOT / "examples/pages/ButtonPage.qml")).toString(),
        QUrl.fromLocalFile(str(_ROOT / "examples/pages/InputPage.qml")).toString(),
        QUrl.fromLocalFile(str(_ROOT / "examples/pages/NavigationPage.qml")).toString(),
    ]
    scene = f"""
import QtQuick
import PrismQML

StackedWidget {{
    width: 1200
    height: 800
    animationEnabled: false
    lazyLoading: true
    currentIndex: 0
    pageSources: ["{page_urls[0]}", "{page_urls[1]}", "{page_urls[2]}"]
}}
"""
    engine = QQmlApplicationEngine()
    component = None
    stack = None
    try:
        register_types(engine)
        engine.rootContext().setContextProperty(
            "PrismQmlAsynchronousPageLoaderEnabled", False
        )
        component = QQmlComponent(engine)
        component.setData(
            scene.encode("utf-8"),
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/gallery-eager-switch.qml")),
        )
        assert _wait_until(
            lambda: component.status() != QQmlComponent.Status.Loading
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        stack = component.create(engine.rootContext())
        assert stack is not None, [error.toString() for error in component.errors()]
        eager_helper = stack.findChild(QObject, "eagerActivationHelper")
        assert eager_helper is not None
        assert _wait_until(lambda: bool(_evaluate(stack, "_isPageLoaded(0)")))
        loaded_indexes = []
        stack.pageLoaded.connect(lambda index: loaded_indexes.append(index))

        stack.setProperty("lazyLoading", False)
        assert eager_helper.property("ready") is False
        assert _evaluate(
            stack,
            "_loaders.filter(function(loader) { return loader.active }).length",
        ) == 1

        stack.setProperty("currentIndex", 2)
        assert _wait_until(
            lambda: int(_evaluate(stack, "_displayIndex")) == 2,
            timeout_ms=5000,
        )
        assert _wait_until(
            lambda: bool(eager_helper.property("ready"))
            and all(
                bool(_evaluate(stack, f"_isPageLoaded({index})"))
                for index in range(len(page_urls))
            ),
            timeout_ms=5000,
        )
        _pump(100)
        assert {1, 2}.issubset(loaded_indexes)
        assert len(loaded_indexes) == len(set(loaded_indexes))
    finally:
        _release(qapp, stack, component, engine)


def test_lazy_helper_respects_unsafe_incubation_fallback():
    """The helper Loader must share the page Loader safety gate. 辅助 Loader 必须共用页面安全门禁。"""
    source = (
        _ROOT
        / "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    ).read_text(encoding="utf-8")

    assert "asynchronous: control._asynchronousPageLoaderEnabled" in source
