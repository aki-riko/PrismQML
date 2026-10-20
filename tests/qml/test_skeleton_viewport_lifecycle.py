# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Skeleton viewport and callback lifecycle regressions. 骨架屏视口生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
    QQmlProperty,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[2]
SKELETON_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "State"
    / "Skeleton.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "skeleton-viewport-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    property int skeletonCount: 4

    function clearSkeletons() { skeletonCount = 0 }
    function refillSkeletons() { skeletonCount = 4 }

    width: 420
    height: 260
    visible: true

    Flickable {
        id: viewport
        objectName: "viewport"
        x: 20
        y: 20
        width: 220
        height: 100
        contentWidth: width
        contentHeight: 520
        clip: true

        Item {
            width: viewport.width
            height: viewport.contentHeight

            Repeater {
                model: root.skeletonCount

                Skeleton {
                    objectName: "skeleton_" + index
                    x: 10
                    y: index === 0 ? 0 : (index === 1 ? 130 : index * 130)
                    width: 180
                    height: 20
                }
            }
        }
    }

    Skeleton {
        objectName: "outsideSkeleton"
        x: 270
        y: 20
        width: 120
        height: 20
    }

    // A circular placeholder is the only shape that still needs the mask layer, so
    // the viewport gating of that layer is exercised through it.
    // Circular placeholder: the only shape that still needs the mask layer, so the
    // viewport gating of that layer is exercised through it.
    Skeleton {
        objectName: "circleSkeleton"
        x: 10
        y: 40
        width: 40
        height: 40
        shape: Enums.skeleton.shape_circle
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


@pytest.fixture
def skeleton_scene(qapp):
    scene = _create_scene()
    try:
        yield scene
    finally:
        _dispose_scene(*scene[:3])


@pytest.fixture
def vintage_ticket_skeleton_scene(qapp):
    previous_skin = getSkin()
    setSkin(Skin.VINTAGE_TICKET)
    scene = _create_scene()
    try:
        yield scene
    finally:
        _dispose_scene(*scene[:3])
        setSkin(previous_skin)
        _pump(20)


def _skeleton(window: QQuickWindow, name: str) -> QQuickItem:
    pending = list(window.contentItem().childItems())
    while pending:
        item = pending.pop()
        if item.objectName() == name:
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"Skeleton not found: {name}")


def _shimmer_animation(skeleton: QQuickItem) -> QObject:
    animations = [
        child
        for child in skeleton.findChildren(QObject)
        if child.metaObject().className() == "QQuickSequentialAnimation"
    ]
    assert len(animations) == 1
    return animations[0]


def _assert_animation_semantics(skeleton: QQuickItem) -> None:
    expected = bool(
        skeleton.property("loading")
        and skeleton.isVisible()
        and skeleton.property("_isInViewport")
    )
    assert bool(_shimmer_animation(skeleton).property("running")) is expected


def _enabled_layer_count(skeleton: QQuickItem) -> int:
    """Number of enabled `layer` groups inside one skeleton. 一个骨架内已启用的图层数。"""
    pending = list(skeleton.childItems())
    enabled = 0
    while pending:
        item = pending.pop()
        pending.extend(item.childItems())
        layer_enabled = QQmlProperty(item, "layer.enabled")
        if layer_enabled.isValid() and layer_enabled.read() is True:
            enabled += 1
    return enabled


def _is_circle(skeleton: QQuickItem) -> bool:
    """Whether this placeholder uses the circular shape. 该占位块是否为圆形。

    Read through the item's own QML context, so the test does not need a Python
    mirror of the enum value.
    经该项自身的 QML 上下文读取, 因此测试不需要在 Python 侧镜像枚举值。
    """
    expression = QQmlExpression(
        QQmlEngine.contextForObject(skeleton), skeleton,
        "shape === Enums.skeleton.shape_circle")
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return bool(value)


def _assert_layer_semantics(skeleton: QQuickItem) -> None:
    """The mask layer is only ever on where it earns its offscreen pass.

    遮罩图层只在值得付出离屏渲染代价时才开启。

    Two guarantees, both about cost rather than looks: a placeholder outside the
    viewport must never hold a layer, and a rounded rectangle must never hold one at
    all, because its background already carries its own radius. Whether a circle
    ends up with one also depends on the viewport mixin, so that direction is
    asserted separately.
    两条保证都关于开销而非外观: 视口外的占位块绝不得持有图层; 圆角矩形根本不得持有
    图层, 因为它的背景本身已带圆角。圆形是否持有还取决于视口混入, 因此那一方向单独断言。
    """
    enabled_layers = _enabled_layer_count(skeleton)
    needs_mask = _is_circle(skeleton)
    in_viewport = bool(skeleton.property("_isInViewport"))
    if not needs_mask:
        assert enabled_layers == 0, (enabled_layers, needs_mask, in_viewport)
    if not in_viewport:
        assert enabled_layers == 0, (enabled_layers, needs_mask, in_viewport)
    assert enabled_layers <= 2, enabled_layers


def test_viewport_scroll_visibility_position_height_and_loading(skeleton_scene):
    _engine, _component, window, warnings = skeleton_scene
    viewport = window.findChild(QQuickItem, "viewport")
    assert viewport is not None
    inside = _skeleton(window, "skeleton_0")
    near_outside = _skeleton(window, "skeleton_1")
    far_outside = _skeleton(window, "skeleton_2")
    outside = _skeleton(window, "outsideSkeleton")
    circle = _skeleton(window, "circleSkeleton")

    assert inside.property("_isInViewport")
    assert not near_outside.property("_isInViewport")
    assert not far_outside.property("_isInViewport")
    assert outside.property("_isInViewport")
    assert circle.property("_isInViewport")
    for skeleton in (inside, near_outside, far_outside, outside, circle):
        _assert_animation_semantics(skeleton)
        _assert_layer_semantics(skeleton)
    # A rounded placeholder never carries the mask layer; only a circle may, and
    # only while it is in the viewport.
    # 圆角占位块从不带遮罩图层; 只有圆形可能带, 且仅在视口内时。
    assert _is_circle(circle)
    assert _enabled_layer_count(inside) == 0
    assert _enabled_layer_count(outside) == 0

    viewport.setProperty("contentY", 120)
    _pump(30)
    assert not inside.property("_isInViewport")
    assert near_outside.property("_isInViewport")

    viewport.setVisible(False)
    _pump(20)
    assert not near_outside.property("_isInViewport")
    viewport.setVisible(True)
    _pump(20)
    assert near_outside.property("_isInViewport")

    viewport.setProperty("contentY", 0)
    near_outside.setHeight(40)
    _pump(30)
    assert near_outside.property("_isInViewport")

    far_outside.setY(40)
    _pump(30)
    assert far_outside.property("_isInViewport")
    far_outside.setProperty("loading", False)
    _pump(20)
    assert not far_outside.property("_isInViewport")
    far_outside.setProperty("loading", True)
    _pump(20)
    assert far_outside.property("_isInViewport")

    for skeleton in (inside, near_outside, far_outside, outside):
        _assert_animation_semantics(skeleton)
        _assert_layer_semantics(skeleton)
    assert warnings == []


def test_vintage_ticket_skeleton_shimmer_moves(vintage_ticket_skeleton_scene):
    _engine, _component, window, warnings = vintage_ticket_skeleton_scene
    skeleton = _skeleton(window, "outsideSkeleton")
    animation = _shimmer_animation(skeleton)

    assert skeleton.property("loading") is True
    assert skeleton.property("_isInViewport") is True
    assert animation.property("running") is True

    shimmer = skeleton.findChild(QQuickItem, "skeletonShimmer")
    assert shimmer is not None
    start_x = shimmer.x()
    _pump(120)
    assert shimmer.x() != pytest.approx(start_x)
    assert warnings == []


def test_destroyed_skeleton_callbacks_do_not_write_global_properties(skeleton_scene):
    engine, _component, window, warnings = skeleton_scene
    viewport = window.findChild(QQuickItem, "viewport")
    assert viewport is not None
    assert QMetaObject.invokeMethod(window, "clearSkeletons")
    _pump(40)
    engine.collectGarbage()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)

    viewport.setProperty("contentY", 80)
    viewport.setHeight(120)
    _pump(30)

    assert not any(
        "Invalid write to global property \"_isInViewport\"" in warning
        for warning in warnings
    ), warnings
    assert warnings == []


def test_repeated_bulk_destroy_leaves_no_stale_viewport_callbacks(skeleton_scene):
    engine, _component, window, warnings = skeleton_scene
    viewport = window.findChild(QQuickItem, "viewport")
    assert viewport is not None

    for cycle in range(3):
        window.setProperty("skeletonCount", 64)
        _pump(30)
        window.setProperty("skeletonCount", 0)
        _pump(30)
        engine.collectGarbage()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        viewport.setProperty("contentY", 40 * (cycle + 1))
        viewport.setHeight(110 + cycle * 10)
        _pump(20)

    assert not any(
        "Invalid write to global property \"_isInViewport\"" in warning
        for warning in warnings
    ), warnings
    assert warnings == []


def test_queued_geometry_updates_are_safe_when_delegate_is_destroyed(skeleton_scene):
    _engine, _component, window, warnings = skeleton_scene
    skeleton = _skeleton(window, "skeleton_1")

    skeleton.setY(40)
    skeleton.setHeight(60)
    window.setProperty("skeletonCount", 0)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(30)

    assert warnings == []


def test_skeleton_delegates_viewport_detection_to_mixin():
    """Skeleton 只允许委托 ViewportMixin, 不得自持视口算法副本。

    The viewport algorithm moved to ViewportMixin, so Skeleton must keep only the
    observable ``_isInViewport`` binding. The comment-swallow protection this gate
    used to provide now comes from the repo-wide QML014 rule, which CI runs over
    changed files as a blocking check.
    """
    source = SKELETON_PATH.read_text(encoding="utf-8")

    assert "ViewportMixin {" in source
    assert "target: control" in source
    assert "readonly property bool _isInViewport: viewport.isInViewport" in source

    # No second copy of the algorithm may reappear here. 不得在此处再现算法副本。
    assert "function _updateViewport()" not in source
    assert "function _findFlickable()" not in source
    assert "instanceof Flickable" not in source
