# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Feedback style token runtime regressions. 反馈组件样式令牌运行时回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
TOAST_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Notification"
    / "Toast.qml"
)
TOAST_CONTENT_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Notification"
    / "_internal"
    / "ToastContent.qml"
)
SPLASH_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "SplashScreen"
    / "SplashScreen.qml"
)
LAZY_PAGE_CIRCLE_TRANSITION_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "_internal"
    / "LazyPageCircleTransition.qml"
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "feedback-style.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property int spacingM: Enums.spacing.m
    readonly property int spacingL: Enums.spacing.l
    readonly property int cardElevate: Enums.spacing.cardElevate
    readonly property real radiusLarge: Enums.radius.large
    readonly property real radiusTiny: Enums.radius.tiny
    readonly property int borderNormal: Enums.border.normal
    readonly property int spacingMicro: Enums.spacing.micro
    readonly property int iconXl: Enums.iconSize.xl
    readonly property int splashBreatheDuration: Enums.duration.splashBreathe
    readonly property int splashProgressSpinDuration: Enums.duration.splashProgressSpin
    readonly property int closeRippleDuration: Enums.windowCloseMetrics.rippleDuration
    readonly property int splashRevealDuration: Enums.lazyLoadingTransitionMetrics.splashRevealDuration
    readonly property int splashProgressStyle: Enums.progress.indeterminate_style_orbit_dot
    readonly property int splashProgressDotSize: Enums.splashScreenMetrics.progressDotSize
    readonly property int splashProgressDotRadius: Enums.splashScreenMetrics.progressDotRadius
    readonly property int splashProgressDotTopMargin: Enums.splashScreenMetrics.progressDotTopMargin
    readonly property var splashHomeIcon: Enums.icon.home
    readonly property real splashShadowBlur: Enums.shadow.splashIcon.blurNormalized
    readonly property real splashShadowOffset: Enums.shadow.splashIcon.offset
    readonly property int splashIconSize: splash.iconSize

    width: 640
    height: 480

    Rectangle {
        objectName: "splashUnderlyingPage"
        anchors.fill: parent
        color: "#ff00ff"
    }

    Toast {
        objectName: "toast"
        desktopMode: true
        duration: 0
        closable: false
        visible: true
    }

    SplashScreen {
        id: splash
        objectName: "splash"
        enableShadow: false
        showTitleBar: false
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    window = QQuickWindow()
    root.setParentItem(window.contentItem())
    window.show()
    root.destroyed.connect(lambda: (window.close(), window.deleteLater()))
    _pump(1)
    return engine, component, root


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.childItems()))


def _read(item: QQuickItem, name: str):
    prop = QQmlProperty(item, name)
    assert prop.isValid(), (item.metaObject().className(), name)
    return prop.read()


def _find_unique(items, predicate, label: str) -> QQuickItem:
    matches = [item for item in items if predicate(item)]
    assert len(matches) == 1, (
        label,
        [
            (
                item.metaObject().className(),
                item.x(),
                item.y(),
                item.width(),
                item.height(),
            )
            for item in matches
        ],
    )
    return matches[0]


def _toast_targets(
    toast: QQuickItem, spacing_l: int, radius_large: float
) -> tuple[QQuickItem, QQuickItem]:
    color_bar = _find_unique(
        list(_walk_visual_tree(toast)),
        lambda item: item.metaObject().className() == "QQuickRectangle"
        and item.height() == pytest.approx(spacing_l)
        and item.property("radius") == pytest.approx(radius_large),
        "toast color bar",
    )
    container = color_bar.parentItem()
    assert isinstance(container, QQuickItem)
    return container, color_bar


def _splash_progress_ring(splash: QQuickItem) -> QQuickItem:
    progress_ring = splash.findChild(QQuickItem, "splashProgressRing")
    assert progress_ring is not None
    assert progress_ring.metaObject().className().startswith("ProgressRing_")
    return progress_ring


def _splash_effect_component(splash: QQuickItem, icon_size: int) -> QQmlComponent:
    matches = []
    for item in _walk_visual_tree(splash):
        effect_prop = QQmlProperty(item, "layer.effect")
        enabled_prop = QQmlProperty(item, "layer.enabled")
        if not effect_prop.isValid() or not enabled_prop.isValid():
            continue
        effect_component = effect_prop.read()
        if (
            isinstance(effect_component, QQmlComponent)
            and item.width() == pytest.approx(icon_size)
            and item.height() == pytest.approx(icon_size)
            and enabled_prop.read() is False
        ):
            matches.append(effect_component)
    assert len(matches) == 1, [str(component.status()) for component in matches]
    return matches[0]


def _animation_objects(splash: QQuickItem) -> list[QObject]:
    return [
        obj
        for obj in splash.findChildren(QObject)
        if obj.metaObject().indexOfProperty("duration") >= 0
    ]


def _style_metrics(root: QQuickItem) -> dict[str, float]:
    metrics = {
        "spacing_m": root.property("spacingM"),
        "spacing_l": root.property("spacingL"),
        "card_elevate": root.property("cardElevate"),
        "radius_large": root.property("radiusLarge"),
        "border_normal": root.property("borderNormal"),
        "icon_xl": root.property("iconXl"),
    }
    assert tuple(metrics.values()) == (8, 12, 3, 8, 2, 20)
    return metrics


def _assert_toast_geometry(toast: QQuickItem, metrics: dict[str, float]) -> None:
    container, color_bar = _toast_targets(
        toast, metrics["spacing_l"], metrics["radius_large"]
    )
    expected_top = metrics["spacing_m"] + metrics["card_elevate"]
    assert _read(container, "anchors.topMargin") == expected_top
    assert container.x() == pytest.approx(metrics["spacing_m"])
    assert container.y() == pytest.approx(expected_top)
    assert _read(color_bar, "anchors.topMargin") == -metrics["card_elevate"]
    assert color_bar.y() == pytest.approx(-metrics["card_elevate"])
    assert container.y() + color_bar.y() == pytest.approx(metrics["spacing_m"])


def _assert_splash_geometry(splash: QQuickItem, metrics: dict[str, float]) -> None:
    progress_ring = _splash_progress_ring(splash)
    assert progress_ring.width() == pytest.approx(metrics["icon_xl"])
    assert progress_ring.height() == pytest.approx(metrics["icon_xl"])
    assert progress_ring.property("strokeWidth") == metrics["border_normal"]
    assert progress_ring.property("indeterminate") is True
    assert progress_ring.property("indeterminateStyle") == splash.property(
        "parent"
    ).property("splashProgressStyle")
    assert progress_ring.property("indeterminateDotSize") == splash.property(
        "parent"
    ).property("splashProgressDotSize")
    assert progress_ring.property("indeterminateDotRadius") == splash.property(
        "parent"
    ).property("splashProgressDotRadius")
    assert progress_ring.property("indeterminateDotTopMargin") == splash.property(
        "parent"
    ).property("splashProgressDotTopMargin")


def test_feedback_metrics_preserve_runtime_geometry(qapp):
    engine, component, root = _create_scene()
    try:
        metrics = _style_metrics(root)
        toast = root.findChild(QQuickItem, "toast")
        splash = root.findChild(QQuickItem, "splash")
        assert toast is not None and splash is not None
        _assert_toast_geometry(toast, metrics)
        _assert_splash_geometry(splash, metrics)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_splash_instantiates_only_selected_icon_renderer(qapp):
    engine, component, root = _create_scene()
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None

        assert splash.findChild(QObject, "splashFluentIconDisplay") is None
        assert splash.findChild(QObject, "splashImageDisplay") is None

        splash.setProperty("icon", root.property("splashHomeIcon"))
        _pump(1)
        assert splash.findChild(QObject, "splashFluentIconDisplay") is not None
        assert splash.findChild(QObject, "splashImageDisplay") is None

        splash.setProperty("iconSource", "qrc:/icons/splash.svg")
        _pump(1)
        assert splash.findChild(QObject, "splashFluentIconDisplay") is None
        assert splash.findChild(QObject, "splashImageDisplay") is not None

        splash.setProperty("iconSource", "")
        _pump(1)
        assert splash.findChild(QObject, "splashFluentIconDisplay") is not None
        assert splash.findChild(QObject, "splashImageDisplay") is None
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_splash_animation_and_shadow_tokens_preserve_runtime_values(qapp):
    engine, component, root = _create_scene()
    effect = None
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None
        breathe_duration = root.property("splashBreatheDuration")
        spin_duration = root.property("splashProgressSpinDuration")
        close_ripple_duration = root.property("closeRippleDuration")
        shadow_blur = root.property("splashShadowBlur")
        shadow_offset = root.property("splashShadowOffset")
        assert (
            breathe_duration,
            spin_duration,
            close_ripple_duration,
            shadow_blur,
            shadow_offset,
        ) == (
            1200,
            1000,
            500,
            0.8,
            6,
        )

        animations = _animation_objects(splash)
        scale_animations = [
            animation
            for animation in animations
            if animation.property("property") == "scale"
            and animation.property("duration") == breathe_duration
        ]
        assert len(scale_animations) == 2
        assert {
            animation.property("to") for animation in scale_animations
        } == {0.9, 1.1}
        assert {animation.property("duration") for animation in scale_animations} == {
            breathe_duration
        }

        progress_ring = _splash_progress_ring(splash)
        assert progress_ring.property("spinDuration") == spin_duration

        effect_component = _splash_effect_component(
            splash, root.property("splashIconSize")
        )
        effect = effect_component.create(effect_component.creationContext())
        assert isinstance(effect, QQuickItem), [
            error.toString() for error in effect_component.errors()
        ]
        assert effect.property("shadowEnabled") is True
        assert effect.property("shadowBlur") == pytest.approx(shadow_blur)
        assert effect.property("shadowVerticalOffset") == pytest.approx(shadow_offset)
    finally:
        if effect is not None:
            effect.deleteLater()
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_splash_finish_exits_without_waiting_for_an_intro(qapp):
    engine, component, root = _create_scene()
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None
        assert QMetaObject.invokeMethod(splash, "finish")

        _pump(80)
        assert splash.property("visible") is True
        assert splash.property("opacity") > 0.1

        _pump(root.property("splashRevealDuration") + 50)
        assert splash.property("visible") is False
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_splash_first_frame_shows_complete_content(qapp):
    engine, component, root = _create_scene()
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None
        content = splash.findChild(QQuickItem, "splashContent")
        assert content is not None
        icon_container = splash.findChild(QQuickItem, "splashIconContainer")
        assert icon_container is not None
        solid_background = splash.findChild(QQuickItem, "splashSolidBackground")
        lazy_loader = splash.findChild(QQuickItem, "splashLazyTransitionLoader")
        assert solid_background is not None
        assert lazy_loader is not None

        # The very first visible frame must already be the complete splash.
        # A background-only frame is a user-visible white flash.
        assert splash.property("visible") is True
        assert splash.property("opacity") == pytest.approx(1.0)
        assert content.property("opacity") == pytest.approx(1.0)
        assert content.property("scale") == pytest.approx(1.0)
        assert icon_container.property("scale") == pytest.approx(1.0, abs=0.005)
        assert solid_background.property("visible") is True
        assert lazy_loader.property("active") is False
        assert QQmlProperty(splash, "layer.enabled").read() is False
        assert splash.findChild(QObject, "splashLazyPageCircleTransition") is None

        _pump(80)
        assert splash.property("opacity") == pytest.approx(1.0)
        assert content.property("opacity") == pytest.approx(1.0)
        assert content.property("scale") == pytest.approx(1.0)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_splash_finish_uses_shared_lazy_switch_transition(qapp):
    engine, component, root = _create_scene()
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None
        content = splash.findChild(QQuickItem, "splashContent")
        solid_background = splash.findChild(QQuickItem, "splashSolidBackground")
        underlying_page = root.findChild(QQuickItem, "splashUnderlyingPage")
        assert content is not None
        assert solid_background is not None
        assert underlying_page is not None
        lazy_loader = splash.findChild(QQuickItem, "splashLazyTransitionLoader")
        assert lazy_loader is not None
        assert lazy_loader.property("active") is False

        assert QMetaObject.invokeMethod(splash, "finish")
        visual_items = {item.objectName(): item for item in _walk_visual_tree(splash)}
        transition = visual_items.get("splashLazyPageCircleTransition")
        assert transition is not None
        assert lazy_loader.property("active") is True
        assert transition.property("collapsing") is False
        assert transition.property("revealDuration") == root.property(
            "splashRevealDuration"
        )
        assert transition.property("revealTarget") is True
        assert QQmlProperty(splash, "layer.enabled").read() is True
        assert QQmlProperty(splash, "layer.effect").read() is not None
        assert solid_background.property("visible") is True

        _pump(80)

        assert splash.property("visible") is True
        assert 0 < transition.property("progress") < 1
        assert content.property("opacity") == pytest.approx(1.0)
        frame = root.window().grabWindow()
        assert not frame.isNull()
        underlying_color = QColor(underlying_page.property("color"))
        assert frame.pixelColor(frame.width() // 2, frame.height() // 2) == underlying_color
        assert frame.pixelColor(8, frame.height() - 8) != underlying_color

        _pump(root.property("splashRevealDuration") + 50)
        assert splash.property("visible") is False
        assert QQmlProperty(splash, "layer.enabled").read() is False
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_feedback_sources_use_shared_style_tokens():
    toast_source = TOAST_SOURCE.read_text(encoding="utf-8")
    toast_content_source = TOAST_CONTENT_SOURCE.read_text(encoding="utf-8")
    splash_source = SPLASH_SOURCE.read_text(encoding="utf-8")

    assert 'import "../../icons"' not in splash_source
    assert 'import "../../data"' not in splash_source
    assert (
        "anchors.topMargin: Enums.spacing.m + Enums.spacing.cardElevate"
        in toast_content_source
    )
    assert "anchors.topMargin: -Enums.spacing.cardElevate" in toast_content_source
    assert "Enums.spacing.m + 3" not in toast_source
    assert "anchors.topMargin: -3" not in toast_source

    assert (
        "readonly property real _progressRingBorderWidth: "
        "Enums.splashScreenMetrics.progressRingBorderWidth" in splash_source
    )
    assert "ProgressRing {" in splash_source
    assert "strokeWidth: control._progressRingBorderWidth" in splash_source
    assert (
        "indeterminateStyle: Enums.progress.indeterminate_style_orbit_dot"
        in splash_source
    )
    assert "duration: Enums.duration.splashBreathe" in splash_source
    lazy_transition_source = LAZY_PAGE_CIRCLE_TRANSITION_SOURCE.read_text(
        encoding="utf-8"
    )
    assert 'objectName: "splashLazyTransitionLoader"' in splash_source
    assert "sourceComponent: NavigationInternal.LazyPageCircleTransition" in splash_source
    assert 'objectName: "splashLazyPageCircleTransition"' in splash_source
    assert "lazyExitLoader.item.expand(control)" in splash_source
    assert "revealDuration: Enums.lazyLoadingTransitionMetrics.splashRevealDuration" in splash_source
    assert "revealTarget: true" in splash_source
    assert lazy_transition_source.count(
        "revealTarget: transition.revealTarget"
    ) == 2
    assert "CloseRipple" not in splash_source
    assert "signal collapseFinished()" in lazy_transition_source
    assert "FeedbackInternal.QMLPageCircleFrame" in lazy_transition_source
    assert "Repeater {" not in splash_source
    assert "border.width:" not in splash_source
    assert "border.color:" not in splash_source
    assert "target: leftCurtain" not in splash_source
    assert "target: rightCurtain" not in splash_source
    assert "target: exitFlip" not in splash_source
    assert "spinDuration: Enums.duration.splashProgressSpin" in splash_source
    assert "shadowBlur: Enums.shadow.splashIcon.blurNormalized" in splash_source
    assert "shadowVerticalOffset: Enums.shadow.splashIcon.offset" in splash_source
    assert "border.width: 2" not in splash_source
    assert "RotationAnimation on rotation" not in splash_source
    assert "Canvas {" not in splash_source
    assert "duration: 1200" not in splash_source
    assert "duration: 1000" not in splash_source
    assert "shadowBlur: 0.8" not in splash_source
    assert "shadowVerticalOffset: 6" not in splash_source
