# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphism engine skin and reusable surface regressions. 新拟态引擎皮肤回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
INSET_LAYER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "effects"
    / "_internal"
    / "NeumorphicInsetLayer.qml"
)
INSET_SHADER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "shaders" / "neumorphic_inset.frag"
)
INSET_SHADER_BINARY_PATH = INSET_SHADER_PATH.with_suffix(".frag.qsb")
QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string skinName: Enums.skin
    readonly property bool neumorphismActive: Enums.isNeumorphism
    readonly property bool outlined: Enums.hasOutlinedSurfaces
    readonly property bool softElevation: Enums.usesSoftElevation
    readonly property bool neumorphicElevation: Enums.usesNeumorphicElevation
    readonly property bool micaAllowed: Enums.allowsMica
    readonly property int surfaceRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property real surfaceBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color backgroundToken: Enums.backgroundColor
    readonly property color surfaceToken: Enums.cardColor
    readonly property color foregroundToken: Enums.foregroundColor
    readonly property color darkShadowToken: Enums.neumorphism.shadowDark
    readonly property color lightShadowToken: Enums.neumorphism.shadowLight
    readonly property real shadowOffsetToken: Enums.neumorphism.shadowOffset
    readonly property real shadowSpreadToken: Enums.neumorphism.shadowSpread
    readonly property real popupShadowOffsetToken: Enums.neumorphism.popupShadowOffset
    readonly property real popupShadowBlurToken: Enums.neumorphism.popupShadowBlur
    readonly property real popupShadowSpreadToken: Enums.neumorphism.popupShadowSpread
    readonly property real popupShadowMarginToken: Enums.neumorphism.popupShadowMargin
    readonly property real insetEdgeToken: Enums.neumorphism.insetEdgeSize
    readonly property real insetSoftnessToken: Enums.neumorphism.insetSoftness
    readonly property real insetDarkOpacityToken: Enums.neumorphism.insetDarkOpacity
    readonly property real insetLightOpacityToken: Enums.neumorphism.insetLightOpacity
    readonly property color successToken: Enums.statusLevel.getColorByLevel(Enums.statusLevel.success)

    width: 320
    height: 180

    Button {
        objectName: "button"
        text: "Action"
    }

    InputCore {
        objectName: "input"
        x: 120
    }

    Card {
        objectName: "card"
        x: 120
        y: 72
        width: 160
        height: 80
    }

    PopupWindowCore {
        objectName: "popup"
        popupWidth: 180
        popupHeight: 120
    }
}
"""

NESTED_TARGET_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 320
    height: 180

    Item {
        id: outerContainer
        objectName: "outerContainer"
        x: 24
        y: 18

        Item {
            id: innerContainer
            objectName: "innerContainer"
            x: 13
            y: 9

            Rectangle {
                id: nestedTarget
                objectName: "nestedTarget"
                x: 7
                y: 5
                width: 96
                height: 42
                radius: Enums.radius.large
            }
        }
    }

    NeumorphicShadow {
        objectName: "nestedShadow"
        target: nestedTarget
        visible: Enums.isNeumorphism
    }
}
"""

EXTENDED_SURFACES_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 1200
    height: 900

    ShadowedRectangle {
        objectName: "shadowedRectangle"
        width: 180
        height: 90
    }

    PinInput {
        objectName: "pinInput"
        x: 220
        length: 4
    }

    ChatBubble {
        objectName: "chatBubble"
        y: 140
        width: 360
        role: "assistant"
        content: "Surface"
        showAvatar: false
    }

    Expander {
        objectName: "expander"
        x: 400
        y: 140
        width: 320
        title: "Surface"
    }

    InfoBarCore {
        objectName: "infoBar"
        y: 320
        width: 360
        title: "Surface"
        desktopMode: true
    }

    Toast {
        objectName: "toast"
        x: 400
        y: 320
        width: 320
        title: "Surface"
        duration: 0
        desktopMode: true
    }

    DesktopNotification {
        objectName: "desktopNotification"
        x: 760
        y: 320
        title: "Surface"
        duration: 0
    }

    DataWidgetCore {
        objectName: "dataWidget"
        y: 500
        width: 320
        height: 180
    }

    TreeWidget {
        objectName: "treeWidget"
        x: 360
        y: 500
        width: 320
        height: 180
    }

    Carousel {
        objectName: "carousel"
        x: 720
        y: 500
        width: 320
        height: 180
        model: ["Surface"]
        shadowLevel: Enums.shadow.level4
        itemDelegate: Rectangle { color: Enums.cardColor }
    }

    BeforeAfterSlider {
        objectName: "beforeAfterSlider"
        x: 760
        width: 320
        height: 220
    }
}
"""

TOGGLE_SURFACE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property color mutedToken: Enums.neumorphism.muted
    readonly property real switchShadowOffset: Enums.neumorphism.switchShadowOffset
    readonly property real switchShadowBlur: Enums.neumorphism.switchShadowBlur
    readonly property real switchShadowSpread: Enums.neumorphism.switchShadowSpread

    width: 180
    height: 80

    ToggleSwitch {
        objectName: "offToggle"
        checked: false
    }

    ToggleSwitch {
        objectName: "onToggle"
        x: 80
        checked: true
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene() -> tuple[QQmlApplicationEngine, QQmlComponent, QObject, list[str]]:
    return _create_scene_from_source(QML_SOURCE, "inline:neumorphism-skin.qml")


def _create_scene_from_source(
    source: bytes, source_url: str
) -> tuple[QQmlApplicationEngine, QQmlComponent, QObject, list[str]]:
    engine = QQmlApplicationEngine()
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.setData(source, QUrl(source_url))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root, warnings


def _assert_color(root: QObject, name: str, expected: str) -> None:
    assert root.property(name) == QColor(expected)


def _owned(root: QObject, type_fragment: str) -> list[QObject]:
    owned = [
        child
        for child in root.findChildren(QObject)
        if type_fragment in child.metaObject().className()
    ]
    seen = {id(child) for child in owned}
    if isinstance(root, QQuickWindow):
        pending = [root.contentItem()]
    elif isinstance(root, QQuickItem):
        pending = list(root.childItems())
    else:
        pending = []
    while pending:
        child = pending.pop()
        if id(child) not in seen and type_fragment in child.metaObject().className():
            owned.append(child)
            seen.add(id(child))
        pending.extend(child.childItems())
    return owned


def test_neumorphism_runtime_tokens_and_surfaces(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene()
    try:
        assert root.property("skinName") == "neumorphism"
        assert root.property("neumorphismActive") is True
        assert root.property("outlined") is False
        assert root.property("softElevation") is False
        assert root.property("neumorphicElevation") is True
        assert root.property("micaAllowed") is False
        assert root.property("surfaceRadius") == 14
        assert root.property("surfaceBorderWidth") == 0
        _assert_color(root, "backgroundToken", "#e4ebf3")
        _assert_color(root, "surfaceToken", "#e4ebf3")
        _assert_color(root, "foregroundToken", "#27364a")
        _assert_color(root, "darkShadowToken", "#b7c2d0")
        _assert_color(root, "lightShadowToken", "#ffffff")
        assert root.property("shadowOffsetToken") == 7
        assert root.property("shadowSpreadToken") == -7
        assert root.property("popupShadowOffsetToken") == 4
        assert root.property("popupShadowBlurToken") == 14
        assert root.property("popupShadowSpreadToken") == -4
        assert root.property("popupShadowMarginToken") == 16
        assert root.property("popupShadowMarginToken") >= (
            root.property("popupShadowBlurToken")
            + abs(root.property("popupShadowOffsetToken"))
            + root.property("popupShadowSpreadToken")
        )
        assert root.property("insetEdgeToken") == 4
        assert root.property("insetSoftnessToken") == 6
        assert root.property("insetDarkOpacityToken") == 0.5
        assert root.property("insetLightOpacityToken") == 0.6
        _assert_color(root, "successToken", "#238b64")

        for object_name in ("button", "input", "card"):
            surface = root.findChild(QObject, object_name)
            assert surface is not None
            assert any(
                "NeumorphicShadow" in child.metaObject().className()
                for child in surface.findChildren(QObject)
            )

        popup = root.findChild(QObject, "popup")
        popup_shadow = root.findChild(QObject, "_popupNeumorphicShadow")
        assert popup is not None
        assert popup_shadow is not None
        assert popup.property("_panelOffset") == root.property(
            "popupShadowMarginToken"
        )
        assert popup.property("_outerWidth") == 212
        assert popup.property("_outerHeight") == 152
        assert popup_shadow.property("offset") == root.property(
            "popupShadowOffsetToken"
        )
        assert popup_shadow.property("blur") == root.property(
            "popupShadowBlurToken"
        )
        assert popup_shadow.property("spread") == root.property(
            "popupShadowSpreadToken"
        )

        setTheme(Theme.DARK)
        _pump()
        _assert_color(root, "backgroundToken", "#252b35")
        _assert_color(root, "surfaceToken", "#252b35")
        _assert_color(root, "foregroundToken", "#e8eef7")
        _assert_color(root, "darkShadowToken", "#171c24")
        _assert_color(root, "lightShadowToken", "#3e4a5b")

        setSkin(Skin.FLUENT)
        _pump()
        assert popup.property("_panelOffset") == 8
        assert popup.property("_outerWidth") == 196
        assert popup.property("_outerHeight") == 136
        assert warnings == []
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphic_shadow_maps_nested_target_geometry(qapp):
    previous_skin = getSkin()
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene_from_source(
        NESTED_TARGET_SOURCE, "inline:neumorphism-nested-target.qml"
    )
    try:
        outer = root.findChild(QObject, "outerContainer")
        inner = root.findChild(QObject, "innerContainer")
        target = root.findChild(QObject, "nestedTarget")
        shadow = root.findChild(QObject, "nestedShadow")
        assert outer is not None
        assert inner is not None
        assert target is not None
        assert shadow is not None

        assert shadow.property("x") == 44
        assert shadow.property("y") == 32
        assert shadow.property("width") == 96
        assert shadow.property("height") == 42

        outer.setProperty("x", 38)
        inner.setProperty("y", 21)
        _pump()
        assert shadow.property("x") == 58
        assert shadow.property("y") == 44
        assert warnings == []
    finally:
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphic_shadow_loads_only_the_active_state(qapp):
    previous_skin = getSkin()
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene_from_source(
        NESTED_TARGET_SOURCE, "inline:neumorphism-shadow-lifecycle.qml"
    )
    try:
        shadow = root.findChild(QObject, "nestedShadow")
        assert shadow is not None

        outer_shadows = _owned(shadow, "RectangularShadow")
        assert len(outer_shadows) == 2
        assert all(bool(item.property("visible")) for item in outer_shadows)
        assert all(
            item.property("spread") == shadow.property("spread")
            for item in outer_shadows
        )
        assert shadow.property("spread") == -shadow.property("offset")
        assert not _owned(shadow, "_neumorphicInsetLayer")

        shadow.setProperty("pressed", True)
        _pump()
        assert not _owned(shadow, "RectangularShadow")
        inset_layer = root.findChild(QObject, "_neumorphicInsetLayer")
        inset_shader = root.findChild(QObject, "_neumorphicInsetShader")
        assert inset_layer is not None
        assert inset_shader is not None
        assert bool(inset_shader.property("visible"))
        assert inset_shader.property("darkOpacity") == shadow.property("insetDarkOpacity")
        assert inset_shader.property("lightOpacity") == shadow.property("insetLightOpacity")
        assert inset_shader.property("shadowDepth") == shadow.property("_edgeSize")

        setSkin(Skin.FLUENT)
        _pump()
        assert not bool(shadow.property("visible"))
        assert not _owned(shadow, "RectangularShadow")
        assert root.findChild(QObject, "_neumorphicInsetLayer") is None
        assert warnings == []
    finally:
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphism_extended_surfaces_use_engine_shadow(qapp):
    previous_skin = getSkin()
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene_from_source(
        EXTENDED_SURFACES_SOURCE, "inline:neumorphism-extended-surfaces.qml"
    )
    try:
        for object_name in (
            "shadowedRectangle",
            "pinInput",
            "chatBubble",
            "expander",
            "infoBar",
            "toast",
            "desktopNotification",
            "dataWidget",
            "treeWidget",
            "carousel",
            "beforeAfterSlider",
        ):
            surface = root.findChild(QObject, object_name)
            assert surface is not None, object_name
            assert _owned(surface, "NeumorphicShadow"), object_name
            assert all(
                not bool(shadow.property("visible"))
                for shadow in _owned(surface, "NeoShadow")
            ), object_name
            assert all(
                not bool(shadow.property("visible"))
                for shadow in _owned(surface, "RectangularShadow")
                if not shadow.objectName().startswith("_neumorphic")
            ), object_name
        assert warnings == []
    finally:
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphic_toggle_uses_recessed_track_and_raised_thumb(qapp):
    previous_skin = getSkin()
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene_from_source(
        TOGGLE_SURFACE_SOURCE, "inline:neumorphism-toggle-surface.qml"
    )
    try:
        for object_name, checked in (("offToggle", False), ("onToggle", True)):
            toggle = root.findChild(QObject, object_name)
            assert toggle is not None
            indicators = _owned(toggle, "ToggleSwitchIndicator")
            assert len(indicators) == 1
            indicator = indicators[0]
            shadows = _owned(indicator, "NeumorphicShadow")
            assert len(shadows) == 2
            assert all(bool(shadow.property("visible")) for shadow in shadows)
            assert all(
                shadow.property("offset") == root.property("switchShadowOffset")
                for shadow in shadows
            )
            assert all(
                shadow.property("blur") == root.property("switchShadowBlur")
                for shadow in shadows
            )
            assert all(
                shadow.property("spread") == root.property("switchShadowSpread")
                for shadow in shadows
            )
            assert sum(bool(shadow.property("inset")) for shadow in shadows) == (
                0 if checked else 1
            )
            if not checked:
                assert indicator.property("_trackColor") == root.property("mutedToken")
        assert warnings == []
    finally:
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()


def test_neumorphism_python_skin_round_trip():
    from prismqml.python.core.theme import ThemeManager

    manager = ThemeManager()
    previous_skin = manager.getSkin()
    try:
        manager.setSkinFromQml("neumorphism")
        assert manager.getSkin() is Skin.NEUMORPHISM
        assert manager.skin == "neumorphism"
    finally:
        manager.setSkin(previous_skin)


def test_neumorphism_is_registered_without_gallery_dependency():
    effect_qmldir = (ROOT / "prismqml" / "PrismQML" / "effects" / "qmldir").read_text(
        encoding="utf-8"
    )
    root_qmldir = (ROOT / "prismqml" / "PrismQML" / "qmldir").read_text(
        encoding="utf-8"
    )
    assert "NeumorphicShadow NeumorphicShadow.qml" in effect_qmldir
    assert "NeumorphicShadow effects/NeumorphicShadow.qml" in root_qmldir


def test_neumorphic_inset_uses_precompiled_rounded_sdf_shader():
    layer_source = INSET_LAYER_PATH.read_text(encoding="utf-8")
    shader_source = INSET_SHADER_PATH.read_text(encoding="utf-8")
    assert 'fragmentShader: Qt.resolvedUrl("../../shaders/neumorphic_inset.frag.qsb")' in layer_source
    assert "ShaderEffect {" in layer_source
    assert "roundedBoxSDF" in shader_source
    assert "gradientLength < 0.001" in shader_source
    assert INSET_SHADER_BINARY_PATH.is_file()
    assert INSET_SHADER_BINARY_PATH.stat().st_size > 0
