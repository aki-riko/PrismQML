# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window close-animation prewarm regressions. 窗口关闭动画预热回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QEventLoop, QMetaObject, QObject, Qt, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
ANIMATION_HELPER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
)
DISSOLVE_EFFECT_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowCloseDissolve.qml"
)
RIPPLE_SHADER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "shaders" / "window_close_ripple.frag"
)
RIPPLE_SHADER_BINARY_PATH = RIPPLE_SHADER_PATH.with_suffix(".frag.qsb")
CAPTION_BUTTON_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "CaptionButton.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "window-close-animation-prewarm.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/_internal" as Internal

Window {
    id: window
    property int closeCallbacks: 0
    property int hoverPrewarmCalls: 0
    property int closeRippleDuration: Enums.windowCloseMetrics.rippleDuration

    width: 320
    height: 200
    visible: false

    QtObject {
        id: hoverTarget
        function prewarmCloseAnimation() { window.hoverPrewarmCalls += 1 }
    }

    Rectangle {
        id: frame
        anchors.fill: parent
        color: Enums.cardColor
        radius: Enums.radius.large
    }

    Internal.WindowAnimationHelper {
        id: animationHelper
        objectName: "animationHelper"
        targetWindow: window
        targetItem: frame
        closeCornerRadius: frame.radius
        onCloseCallback: function() { window.closeCallbacks += 1 }
    }

    Internal.CaptionButton {
        objectName: "closeCaptionButton"
        targetWindow: hoverTarget
        iconType: "close"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _class_count(root: QObject, prefix: str) -> int:
    return sum(
        child.metaObject().className().startswith(prefix)
        for child in root.findChildren(QObject)
    )


def _visual_items(root: QQuickItem):
    for child in root.childItems():
        yield child
        yield from _visual_items(child)


def _visual_class_count(root: QQuickItem, prefix: str) -> int:
    return sum(
        child.metaObject().className().startswith(prefix)
        for child in _visual_items(root)
    )


@pytest.fixture
def close_animation_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    try:
        yield window, warnings
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()


def test_close_animation_is_absent_at_startup_and_programmatic_close_loads_it(
    close_animation_scene,
):
    window, warnings = close_animation_scene
    assert window.property("closeRippleDuration") == 700
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None
    window.show()
    assert _wait_for(lambda: helper.width() == pytest.approx(window.width()))
    assert _class_count(helper, "QQuickSequentialAnimation") == 0

    window.setOpacity(1)
    helper.setProperty("animScale", 1)
    helper.setProperty("animOpacity", 1)
    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _class_count(helper, "QQuickSequentialAnimation") > 1
    dissolve = helper.findChild(QQuickItem, "windowCloseDissolve")
    assert dissolve is not None
    overlay = dissolve.findChild(QQuickWindow, "windowCloseOverlayWindow")
    assert overlay is not None
    frozen_frame = overlay.findChild(QQuickItem, "windowCloseFrozenFrame")
    assert frozen_frame is not None
    ripple_frame = overlay.findChild(QQuickItem, "windowCloseRippleFrame")
    assert ripple_frame is not None
    assert _visual_class_count(overlay.contentItem(), "QQuickImage") == 1
    assert _visual_class_count(overlay.contentItem(), "QQuickShaderEffect") == 1
    assert _visual_class_count(overlay.contentItem(), "QQuickShaderEffectSource") == 0
    assert ripple_frame.width() == pytest.approx(overlay.width())
    assert ripple_frame.height() == pytest.approx(overlay.height())
    assert _wait_for(lambda: helper.property("animOpacity") == 0)
    assert overlay.isVisible()
    assert window.opacity() == pytest.approx(0)
    assert frozen_frame.isVisible()
    assert frozen_frame.opacity() == pytest.approx(0)
    _pump(120)
    assert frozen_frame.opacity() == pytest.approx(0)
    assert frozen_frame.scale() == pytest.approx(1)
    assert 0 < dissolve.property("_dissolveProgress") < 1
    assert ripple_frame.property("progress") == pytest.approx(
        dissolve.property("_dissolveProgress")
    )
    assert ripple_frame.property("aspectRatio") > 0
    assert ripple_frame.property("tailLength") > 0
    assert ripple_frame.property("waveFrequency") > 0
    assert ripple_frame.property("waveDispersion") > 0
    assert ripple_frame.property("waveDamping") > 0
    assert ripple_frame.property("waveAmplitude") > 0
    assert ripple_frame.property("frontRefractionWidth") > 0
    assert ripple_frame.property("crestSharpness") > 1
    assert 0 < ripple_frame.property("rippleOpacity") < 1
    assert 0 < ripple_frame.property("finishFadeStart") < 1
    assert window.property("closeCallbacks") == 0
    assert _wait_for(lambda: window.property("closeCallbacks") == 1)
    assert window.opacity() == pytest.approx(0)
    assert not overlay.isVisible()
    assert helper.property("animScale") == pytest.approx(1)
    assert helper.property("animOpacity") == pytest.approx(0)
    assert warnings == []


def test_close_dissolve_can_be_cancelled_and_restarted(close_animation_scene):
    window, warnings = close_animation_scene
    helper = window.findChild(QQuickItem, "animationHelper")
    assert helper is not None
    window.show()
    assert _wait_for(lambda: helper.width() == pytest.approx(window.width()))
    window.setOpacity(1)
    helper.setProperty("animScale", 1)
    helper.setProperty("animOpacity", 1)

    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(lambda: helper.property("animOpacity") == 0)
    assert QMetaObject.invokeMethod(
        helper, "restoreVisibleState", Qt.ConnectionType.DirectConnection
    )
    assert window.property("closeCallbacks") == 0
    assert window.opacity() == pytest.approx(1)
    assert helper.property("animScale") == pytest.approx(1)
    assert helper.property("animOpacity") == pytest.approx(1)
    dissolve = helper.findChild(QQuickItem, "windowCloseDissolve")
    overlay = dissolve.findChild(QQuickWindow, "windowCloseOverlayWindow")
    assert not overlay.isVisible()

    assert QMetaObject.invokeMethod(
        helper, "animatedClose", Qt.ConnectionType.DirectConnection
    )
    assert _wait_for(lambda: window.property("closeCallbacks") == 1)
    assert window.opacity() == pytest.approx(0)
    assert warnings == []


def test_close_caption_entered_prewarms_without_clicking(close_animation_scene):
    window, warnings = close_animation_scene
    caption = window.findChild(QQuickItem, "closeCaptionButton")
    assert caption is not None
    mouse_areas = [
        child
        for child in caption.findChildren(QObject)
        if child.metaObject().className().startswith("QQuickMouseArea")
    ]
    assert len(mouse_areas) == 1
    assert window.property("hoverPrewarmCalls") == 0
    assert QMetaObject.invokeMethod(
        mouse_areas[0], "entered", Qt.ConnectionType.DirectConnection
    )
    assert window.property("hoverPrewarmCalls") == 1
    assert window.property("closeCallbacks") == 0
    assert warnings == []


def test_close_animation_source_uses_water_ripple_shader():
    animation_source = ANIMATION_HELPER_PATH.read_text(encoding="utf-8")
    dissolve_source = DISSOLVE_EFFECT_PATH.read_text(encoding="utf-8")
    ripple_shader_source = RIPPLE_SHADER_PATH.read_text(encoding="utf-8")
    caption_source = CAPTION_BUTTON_PATH.read_text(encoding="utf-8")
    assert "active: false" in animation_source
    assert "sourceComponent: WindowCloseDissolve" in animation_source
    assert "targetItem: helper.targetItem" in animation_source
    assert "cornerRadius: helper.closeCornerRadius" in animation_source
    assert "helper.animOpacity = Enums.opacityLevel.invisible" in animation_source
    assert 'objectName: "windowCloseOverlayWindow"' in dissolve_source
    assert "transientParent: null" in dissolve_source
    assert "overlayWindow.requestUpdate()" in dissolve_source
    assert "AcrylicHelper.grabWindowFrame" in dissolve_source
    assert "targetItem.grabToImage" in dissolve_source
    assert "ShaderEffect {" in dissolve_source
    assert 'objectName: "windowCloseRippleFrame"' in dissolve_source
    assert 'property variant source: frozenFrame' in dissolve_source
    assert 'fragmentShader: Qt.resolvedUrl("../shaders/window_close_ripple.frag.qsb")' in dissolve_source
    assert "import QtQuick.Shapes" not in dissolve_source
    assert "MultiEffect {" not in dissolve_source
    assert "Shape {" not in dissolve_source
    assert "Repeater {" not in dissolve_source
    assert "ShaderEffectSource {" not in dissolve_source
    assert "maskInverted" not in dissolve_source
    assert 'objectName: "windowCloseFrozenFrame"' in dissolve_source
    assert "sourceClipRect:" not in dissolve_source
    assert "color: Enums.transparent" in dissolve_source
    assert "targetWindow.opacity = Enums.opacityLevel.invisible" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleDuration" in dissolve_source
    assert "Enums.duration.splashExitDissolve" not in dissolve_source
    assert "Enums.windowCloseMetrics.rippleTailLength" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleWaveFrequency" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleWaveDispersion" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleWaveDamping" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleWaveAmplitude" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleHighlightStrength" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleFrontSoftness" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleFrontRefractionWidth" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleCrestSharpness" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleOpacity" in dissolve_source
    assert "Enums.windowCloseMetrics.rippleFinishFadeStart" in dissolve_source
    assert dissolve_source.count("Image {") == 1
    assert "Easing.OutQuad" in dissolve_source
    assert RIPPLE_SHADER_BINARY_PATH.is_file()
    assert RIPPLE_SHADER_BINARY_PATH.stat().st_size > 0
    assert "float exteriorAlpha" in ripple_shader_source
    assert "float rippleAlpha" in ripple_shader_source
    assert "float clearRippleAlpha" in ripple_shader_source
    assert "float distortionEnvelope" in ripple_shader_source
    assert "float frontSlope" in ripple_shader_source
    assert "float surfaceSlope" in ripple_shader_source
    assert "float rippleCrest" in ripple_shader_source
    assert "sin(wavePhase)" in ripple_shader_source
    assert "cos(wavePhase)" in ripple_shader_source
    assert "pow(abs(waveHeight), crestSharpness)" in ripple_shader_source
    assert "waveDispersion * tailRatio" in ripple_shader_source
    assert "exp(-rippleDistance * waveDamping)" in ripple_shader_source
    assert "signedFrontDistance" in ripple_shader_source
    assert "vec3 rippleColor" in ripple_shader_source
    assert "sourceColor.rgb * exteriorAlpha" in ripple_shader_source
    assert "texture(source, sampleUv)" in ripple_shader_source
    assert "onCloseCallback()" in dissolve_source
    assert (
        "if (captionBtn.isClose) "
        "captionBtn.targetWindow.prewarmCloseAnimation()"
    ) in caption_source
