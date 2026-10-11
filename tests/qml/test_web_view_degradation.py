# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WebView2 lazy creation and degradation contracts. WebView2 延迟创建与降级合同。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "web-view-degradation-scene.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/media"

Item {
    width: 480
    height: 360

    QtObject {
        id: probe
        property int failureCount: 0
        property string failureMessage: ""
    }

    WebView2 {
        id: webView
        objectName: "webView"
    }

    WebView2 {
        id: probeView
        objectName: "probeView"
    }

    Connections {
        function onAvailabilityFailed(message) {
            probe.failureCount += 1
            probe.failureMessage = message
        }

        target: webView
    }
}
"""

MISSING_MODULE_SURFACE = (
    "import QtQuick\n"
    "import QtWebEngineMissingProbe\n"
    "Item { }\n"
)

ASYNC_RECORDING_SURFACE = b"""
import QtQuick

Item {
    required property Item host
    property string loadedHtml: ""

    function requestLoadHtml(html, baseUrl) {
        loadedHtml = html
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 3_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _evaluate(instance: QObject, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def _invoke(instance: QObject, source: str) -> None:
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    expression.evaluate()
    assert not expression.hasError(), expression.error().toString()


def _class_names(root: QQuickItem) -> list[str]:
    return sorted({child.metaObject().className() for child in root.findChildren(QObject)})


def _children_of_class(root: QQuickItem, prefix: str) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if child.metaObject().className().startswith(prefix)
    ]


def _web_engines(root: QQuickItem) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if "WebEngine" in child.metaObject().className()
    ]


def _create_scene():
    engine = QQmlEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root, warnings


def _dispose(engine, component, root) -> None:
    for obj in (root, component, engine):
        if obj is not None:
            obj.deleteLater()
    _pump(1)


def test_web_view_does_not_start_the_engine(qapp):
    """Construction and probing must not start QtWebEngine. 构造与探测不得启动 QtWebEngine。"""
    engine, component, root, warnings = _create_scene()
    try:
        view = root.findChild(QQuickItem, "webView")
        assert view is not None

        assert view.property("active") is False
        assert view.property("surfaceCreated") is False
        assert view.property("loading") is False
        assert view.property("available") is False
        assert view.property("degraded") is False
        assert view.property("availabilityState") == _evaluate(
            view, "Enums.media.availability_unknown"
        )
        assert view.property("pageLoading") is False
        assert view.property("loadProgress") == 0
        assert view.property("title") == ""
        assert view.property("canGoBack") is False
        assert view.property("canGoForward") is False
        assert _web_engines(view) == [], _class_names(view)

        # The availability probe only compiles the surface 可用性探测只编译表面
        _invoke(view, "probeAvailability()")
        assert _wait_for(lambda: view.property("available") is True)
        assert view.property("availabilityState") == _evaluate(
            view, "Enums.media.availability_available"
        )
        assert view.property("surfaceCreated") is False
        assert _web_engines(view) == [], _class_names(view)
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_web_view_degrades_when_engine_module_is_missing(qapp, tmp_path):
    """A missing QtWebEngine module degrades gracefully. QtWebEngine 缺失时优雅降级。"""
    engine, component, root, warnings = _create_scene()
    try:
        view = root.findChild(QQuickItem, "webView")
        assert view is not None
        missing = tmp_path / "missing-web-engine-surface.qml"
        missing.write_text(MISSING_MODULE_SURFACE, encoding="utf-8")
        view.setProperty("surfaceUrl", QUrl.fromLocalFile(str(missing)))

        # The probe reports the missing module instead of crashing
        # 探测上报模块缺失，而不是崩溃
        _invoke(view, "probeAvailability()")
        assert _wait_for(lambda: view.property("degraded") is True)
        assert view.property("available") is False
        assert view.property("availabilityState") == _evaluate(
            view, "Enums.media.availability_unavailable"
        )
        assert "is not installed" in str(view.property("errorString"))
        assert _web_engines(view) == [], _class_names(view)

        # Incubation fails the same way and the fallback surface renders
        # 孵化以同样方式失败，并渲染回退界面
        _invoke(view, "activate()")
        assert _wait_for(lambda: view.property("degraded") is True)
        assert view.property("surfaceCreated") is False
        assert _web_engines(view) == [], _class_names(view)
        assert _evaluate(root, "probe.failureCount") >= 1
        assert "is not installed" in str(_evaluate(root, "probe.failureMessage"))
        assert _wait_for(
            lambda: _children_of_class(view, "QQuickText") != []
        ), _class_names(view)

        # Public navigation commands stay safe while unavailable
        # 不可用状态下导航命令保持安全
        _invoke(view, "reload()")
        _invoke(view, "stop()")
        _invoke(view, "goBack()")
        _invoke(view, "goForward()")
        _invoke(view, "runJavaScript('1 + 1')")
        _invoke(view, "load('file:///nonexistent-page.html')")
        assert view.property("surfaceCreated") is False
        # Only the expected missing-module diagnostic is allowed 仅允许预期的模块缺失诊断
        assert warnings == [
            warning for warning in warnings if "is not installed" in warning
        ]
    finally:
        _dispose(engine, component, root)


def test_web_view_reports_a_missing_surface_file(qapp, tmp_path):
    """A missing surface file degrades gracefully. 表面文件缺失时优雅降级。"""
    engine, component, root, warnings = _create_scene()
    try:
        view = root.findChild(QQuickItem, "probeView")
        assert view is not None
        absent = tmp_path / "absent-web-surface.qml"
        view.setProperty("surfaceUrl", QUrl.fromLocalFile(str(absent)))

        _invoke(view, "probeAvailability()")
        assert _wait_for(lambda: view.property("degraded") is True)
        assert view.property("available") is False
        assert view.property("errorString") != ""
        _invoke(view, "activate()")
        assert _wait_for(lambda: view.property("degraded") is True)
        assert view.property("surfaceCreated") is False
        assert _web_engines(view) == [], _class_names(view)
        assert _wait_for(
            lambda: _children_of_class(view, "QQuickText") != []
        ), _class_names(view)
        # Only the expected missing-file diagnostic is allowed 仅允许预期的文件缺失诊断
        assert warnings == [
            warning for warning in warnings if "No such file or directory" in warning
        ]
    finally:
        _dispose(engine, component, root)


def test_web_view_replays_load_html_after_async_activation(qapp, tmp_path):
    """Inline HTML survives first async activation. 首次异步激活不会丢失内联 HTML。"""
    engine, component, root, warnings = _create_scene()
    try:
        view = root.findChild(QQuickItem, "probeView")
        assert view is not None
        surface = tmp_path / "recording-web-surface.qml"
        surface.write_bytes(ASYNC_RECORDING_SURFACE)
        view.setProperty("surfaceUrl", QUrl.fromLocalFile(str(surface)))

        _invoke(view, "loadHtml('hello from the first call', '')")

        assert _wait_for(lambda: view.property("surfaceCreated"))
        loaded = [
            child.property("loadedHtml")
            for child in view.findChildren(QQuickItem)
            if child.property("loadedHtml") is not None
        ]
        assert loaded == ["hello from the first call"]
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_web_view_scheduler_gate_defers_load_html_until_activation(qapp, tmp_path):
    """Scheduler gating preserves queued inline HTML. 调度门控保留排队的内联 HTML。"""
    engine, component, root, warnings = _create_scene()
    try:
        view = root.findChild(QQuickItem, "probeView")
        assert view is not None
        surface = tmp_path / "scheduler-recording-web-surface.qml"
        surface.write_bytes(ASYNC_RECORDING_SURFACE)
        view.setProperty("surfaceUrl", QUrl.fromLocalFile(str(surface)))
        view.setProperty("schedulerActive", False)

        _invoke(view, "loadHtml('queued by scheduler', '')")
        assert view.property("surfaceCreated") is False

        view.setProperty("schedulerActive", True)
        assert _wait_for(lambda: view.property("surfaceCreated"))
        loaded = [
            child.property("loadedHtml")
            for child in view.findChildren(QQuickItem)
            if child.property("loadedHtml") is not None
        ]
        assert loaded == ["queued by scheduler"]
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_web_view_activation_scheduler_limits_same_group_creation(qapp, tmp_path):
    """Same-group surfaces start one at a time. 同组表面按顺序创建。"""
    engine, component, root, warnings = _create_scene()
    try:
        first = root.findChild(QQuickItem, "webView")
        second = root.findChild(QQuickItem, "probeView")
        surface = tmp_path / "queued-web-surface.qml"
        surface.write_bytes(ASYNC_RECORDING_SURFACE)
        for view in (first, second):
            view.setProperty("surfaceUrl", QUrl.fromLocalFile(str(surface)))

        _invoke(first, "activate()")
        _invoke(second, "activate()")
        _pump(20)
        assert sum(
            bool(view.property("activationInProgress")) for view in (first, second)
        ) <= 1

        assert _wait_for(
            lambda: first.property("surfaceCreated")
            and second.property("surfaceCreated")
        )
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_web_view_sources_contain_no_injected_endpoints():
    """Web QML must not hardcode URLs or credentials. 网页 QML 不得硬编码 URL 或凭据。"""
    media_root = ROOT / "prismqml" / "PrismQML" / "controls" / "media"
    offenders = []
    for path in sorted(media_root.rglob("*.qml")):
        text = path.read_text(encoding="utf-8")
        for token in ("http://", "https://", "apiKey", "api_key", "accessToken"):
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert offenders == []
