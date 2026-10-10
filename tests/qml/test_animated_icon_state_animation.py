# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AnimatedIcon state driven animation contracts. AnimatedIcon 状态驱动动画合同。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "animated-icon-state-scene.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/icons"

Item {
    width: 240
    height: 240

    QtObject {
        id: probe
        property int mappedFinishedCount: 0
    }

    AnimatedIcon {
        id: mappedIcon
        objectName: "mappedIcon"
        icon: Enums.icon.play
        iconSize: 32
        duration: Enums.duration.fast
        stateIcons: ({ "1": Enums.icon.pause, "2": Enums.icon.stop })
    }

    AnimatedIcon {
        id: instantIcon
        objectName: "instantIcon"
        icon: Enums.icon.play
        iconSize: 32
        playing: false
        stateIcons: ({ "2": Enums.icon.stop })
    }

    AnimatedIcon {
        id: fallbackIcon
        objectName: "fallbackIcon"
        fallbackIcon: Enums.icon.alert
        iconSize: 32
    }

    AnimatedIcon {
        id: emptyIcon
        objectName: "emptyIcon"
        iconSize: 32
    }

    Connections {
        function onTransitionFinished() { probe.mappedFinishedCount += 1 }

        target: mappedIcon
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
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


def _descendants(root: QQuickItem) -> list[QQuickItem]:
    items = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


def _image_sources(item: QQuickItem) -> list[str]:
    sources = []
    for child in _descendants(item):
        if child.metaObject().className() != "QQuickImage":
            continue
        source = child.property("source")
        sources.append(source.toString() if hasattr(source, "toString") else str(source))
    return sources


def _renderer_item(icon: QQuickItem) -> QQuickItem:
    """Return the internal renderer item of one AnimatedIcon. 返回动效图标的内部渲染器。"""
    matches = [
        item
        for item in _descendants(icon)
        if item.metaObject().className().startswith("AnimatedIconRenderer")
    ]
    assert len(matches) == 1, [
        item.metaObject().className() for item in _descendants(icon)
    ]
    return matches[0]


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


def test_animated_icon_state_icons_and_tokens(qapp):
    """State icons, fallback artwork and state tokens. 状态图标、回退图形与状态 token。"""
    engine, component, root, warnings = _create_scene()
    try:
        mapped = root.findChild(QQuickItem, "mappedIcon")
        fallback = root.findChild(QQuickItem, "fallbackIcon")
        empty = root.findChild(QQuickItem, "emptyIcon")
        assert mapped is not None and fallback is not None and empty is not None

        normal = _evaluate(mapped, "Enums.media.animated_state_normal")
        pointer_over = _evaluate(mapped, "Enums.media.animated_state_pointer_over")
        pressed = _evaluate(mapped, "Enums.media.animated_state_pressed")
        disabled = _evaluate(mapped, "Enums.media.animated_state_disabled")
        assert normal == 0 and pressed == 2
        assert len({normal, pointer_over, pressed, disabled}) == 4

        assert mapped.property("state") == normal
        assert mapped.property("currentIcon") == "Play"
        assert mapped.property("hasVisual") is True
        assert empty.property("hasVisual") is False

        assert _evaluate(mapped, "stateIconFor(Enums.media.animated_state_pressed)") == "Stop"
        assert _evaluate(mapped, "stateIconFor(Enums.media.animated_state_disabled)") == "Play"
        _invoke(mapped, "setState(Enums.media.animated_state_pressed)")
        assert mapped.property("currentIcon") == "Stop"

        assert fallback.property("currentIcon") == "Alert"
        assert fallback.property("hasVisual") is True

        assert _evaluate(mapped, "stateScale") == _evaluate(
            mapped, "Enums.media.animated_scale_pressed"
        )
        assert _evaluate(mapped, "stateOpacity") == _evaluate(
            mapped, "Enums.opacityLevel.visible"
        )
        _invoke(mapped, "setState(Enums.media.animated_state_disabled)")
        assert _evaluate(mapped, "stateScale") == _evaluate(
            mapped, "Enums.media.animated_scale_disabled"
        )
        assert _evaluate(mapped, "stateOpacity") == _evaluate(
            mapped, "Enums.opacityLevel.disabled"
        )
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_animated_icon_cross_fades_state_artwork(qapp):
    """Artwork changes cross fade and report completion. 图形变化交叉淡入并上报完成。"""
    engine, component, root, warnings = _create_scene()
    try:
        mapped = root.findChild(QQuickItem, "mappedIcon")
        assert mapped is not None
        assert _wait_for(
            lambda: any(source.endswith("Play.svg") for source in _image_sources(mapped))
        ), _image_sources(mapped)
        assert mapped.property("transitioning") is False
        assert _evaluate(root, "probe.mappedFinishedCount") == 0

        _invoke(mapped, "setState(Enums.media.animated_state_pressed)")
        assert mapped.property("currentIcon") == "Stop"
        assert mapped.property("transitioning") is True
        # The state transform animates instead of snapping 状态变换是动画而非瞬跳
        assert abs(float(_renderer_item(mapped).property("scale")) - 1.0) < 0.001
        assert _wait_for(lambda: mapped.property("transitioning") is False)
        assert _evaluate(root, "probe.mappedFinishedCount") == 1
        assert abs(
            float(_renderer_item(mapped).property("scale"))
            - float(_evaluate(mapped, "Enums.media.animated_scale_pressed"))
        ) < 0.001
        assert _wait_for(
            lambda: any(source.endswith("Stop.svg") for source in _image_sources(mapped))
        ), _image_sources(mapped)

        # stop() snaps the running transition 停止立即结束过渡
        _invoke(mapped, "setState(Enums.media.animated_state_normal)")
        assert mapped.property("transitioning") is True
        _invoke(mapped, "stop()")
        assert mapped.property("transitioning") is False
        assert mapped.property("playing") is False

        # reset() returns to the initial state 重置回到初始状态
        _invoke(mapped, "play()")
        _invoke(mapped, "reset()")
        assert mapped.property("state") == _evaluate(
            mapped, "Enums.media.animated_state_normal"
        )
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_animated_icon_frozen_state_changes_are_instant(qapp):
    """playing=false applies state changes without animation. playing=false 时状态瞬变。"""
    engine, component, root, warnings = _create_scene()
    try:
        instant = root.findChild(QQuickItem, "instantIcon")
        assert instant is not None
        assert instant.property("playing") is False

        _invoke(instant, "setState(Enums.media.animated_state_pressed)")
        assert instant.property("currentIcon") == "Stop"
        assert instant.property("transitioning") is False
        assert abs(
            float(_renderer_item(instant).property("scale"))
            - float(_evaluate(instant, "Enums.media.animated_scale_pressed"))
        ) < 0.001
        assert _wait_for(
            lambda: any(source.endswith("Stop.svg") for source in _image_sources(instant))
        ), _image_sources(instant)
        assert warnings == []
    finally:
        _dispose(engine, component, root)
