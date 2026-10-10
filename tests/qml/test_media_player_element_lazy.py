# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MediaPlayerElement lazy creation contracts. MediaPlayerElement 延迟创建合同。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "media-player-element-scene.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/media"

Item {
    width: 400
    height: 300

    QtObject {
        id: probe
        property int failureCount: 0
        property string failureMessage: ""
    }

    MediaPlayerElement {
        id: lazyPlayer
        objectName: "lazyPlayer"
    }

    MediaPlayerElement {
        id: activePlayer
        objectName: "activePlayer"
        volume: 0.5
        muted: true
    }

    Connections {
        function onAvailabilityFailed(message) {
            probe.failureCount += 1
            probe.failureMessage = message
        }

        target: lazyPlayer
    }
}
"""

BROKEN_SURFACE_SOURCE = (
    "import QtQuick\n"
    "import QtMultimediaUnavailableProbe\n"
    "Item { }\n"
)


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


def _media_players(root: QQuickItem) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if "MediaPlayer" in child.metaObject().className()
    ]


def _loaded_surface(control: QQuickItem) -> QQuickItem:
    """Return the incubated surface item of one control. 返回控件已孵化的表面对象。"""
    items = [
        loader.property("item")
        for loader in control.childItems()
        if loader.metaObject().className().startswith("QQuickLoader")
    ]
    loaded = [item for item in items if isinstance(item, QQuickItem)]
    assert len(loaded) == 1, _class_names(control)
    return loaded[0]


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


def test_media_player_element_does_not_create_the_backend(qapp):
    """Construction must not create the media backend. 构造期不得创建媒体后端。"""
    engine, component, root, warnings = _create_scene()
    try:
        lazy = root.findChild(QQuickItem, "lazyPlayer")
        assert lazy is not None

        assert lazy.property("active") is False
        assert lazy.property("surfaceCreated") is False
        assert lazy.property("loading") is False
        assert lazy.property("degraded") is False
        assert lazy.property("availabilityState") == _evaluate(
            lazy, "Enums.media.availability_unknown"
        )
        assert lazy.property("playbackState") == _evaluate(
            lazy, "Enums.media.playback_stopped"
        )
        assert lazy.property("position") == 0
        assert lazy.property("duration") == 0
        assert lazy.property("progress") == 0
        assert lazy.property("hasVideo") is False
        assert _media_players(lazy) == [], _class_names(lazy)

        # Availability probing compiles the surface without creating it
        # 可用性探测只编译表面，不创建实例
        _invoke(lazy, "probeAvailability()")
        assert _wait_for(lambda: lazy.property("available") is True)
        assert lazy.property("availabilityState") == _evaluate(
            lazy, "Enums.media.availability_available"
        )
        assert lazy.property("surfaceCreated") is False
        assert _media_players(lazy) == [], _class_names(lazy)
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_media_player_element_activates_on_demand(qapp):
    """activate() incubates the surface and public commands are safe. activate() 按需孵化且命令安全。"""
    engine, component, root, warnings = _create_scene()
    try:
        active = root.findChild(QQuickItem, "activePlayer")
        assert active is not None
        assert active.property("surfaceCreated") is False

        _invoke(active, "activate()")
        assert _wait_for(lambda: active.property("surfaceCreated") is True), _class_names(
            active
        )
        assert active.property("active") is True
        assert active.property("available") is True
        assert active.property("degraded") is False
        assert _media_players(active) != [], _class_names(active)
        surface = _loaded_surface(active)
        assert _evaluate(surface, "player !== undefined") is True
        assert _evaluate(surface, "host === activePlayer") is True

        # Public commands stay safe without a real media source 无真实媒体源时命令安全
        _invoke(active, "seek(1500)")
        _invoke(active, "pause()")
        _invoke(active, "togglePlayPause()")
        _invoke(active, "stop()")
        assert active.property("playbackState") == _evaluate(
            active, "Enums.media.playback_stopped"
        )
        assert active.property("position") == 0

        # Volume clamping 音量限幅
        _invoke(active, "setVolume(2.5)")
        assert abs(float(active.property("volume")) - 1.0) < 0.001
        _invoke(active, "setVolume(-3)")
        assert abs(float(active.property("volume"))) < 0.001

        # Source injection 媒体源注入
        _invoke(active, "setSource('file:///nonexistent-media-sample.mp4')")
        source = active.property("source")
        source_text = source.toString() if hasattr(source, "toString") else str(source)
        assert source_text.endswith("nonexistent-media-sample.mp4")
        _invoke(active, "setMuted(true)")
        assert active.property("muted") is True

        # Repeated activation is idempotent 重复激活幂等
        _invoke(active, "activate()")
        assert _wait_for(lambda: active.property("surfaceCreated") is True)
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_media_player_element_degrades_on_broken_surface(qapp, tmp_path):
    """A broken surface degrades instead of crashing. 表面损坏时优雅降级。"""
    engine, component, root, warnings = _create_scene()
    try:
        lazy = root.findChild(QQuickItem, "lazyPlayer")
        assert lazy is not None
        broken = tmp_path / "broken-media-surface.qml"
        broken.write_text(BROKEN_SURFACE_SOURCE, encoding="utf-8")
        lazy.setProperty("surfaceUrl", QUrl.fromLocalFile(str(broken)))

        # The probe reports the missing module instead of crashing
        # 探测上报模块缺失，而不是崩溃
        _invoke(lazy, "probeAvailability()")
        assert _wait_for(lambda: lazy.property("degraded") is True)
        assert lazy.property("available") is False
        assert lazy.property("availabilityState") == _evaluate(
            lazy, "Enums.media.availability_unavailable"
        )
        assert "is not installed" in str(lazy.property("errorString"))

        _invoke(lazy, "activate()")
        assert _wait_for(lambda: lazy.property("degraded") is True)
        assert lazy.property("surfaceCreated") is False
        assert _media_players(lazy) == [], _class_names(lazy)
        assert _evaluate(root, "probe.failureCount") >= 1
        assert "is not installed" in str(_evaluate(root, "probe.failureMessage"))
        # The fallback surface renders readable content 回退界面渲染可读内容
        assert _wait_for(
            lambda: _children_of_class(lazy, "QQuickText") != []
        ), _class_names(lazy)
        # Only the expected missing-module diagnostic is allowed 仅允许预期的模块缺失诊断
        assert warnings == [
            warning for warning in warnings if "is not installed" in warning
        ]
    finally:
        _dispose(engine, component, root)


def test_media_sources_contain_no_injected_endpoints():
    """Media QML must not hardcode URLs or credentials. 媒体 QML 不得硬编码 URL 或凭据。"""
    media_root = ROOT / "prismqml" / "PrismQML" / "controls" / "media"
    offenders = []
    for path in sorted(media_root.rglob("*.qml")):
        text = path.read_text(encoding="utf-8")
        for token in ("http://", "https://", "apiKey", "api_key", "accessToken"):
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert offenders == []