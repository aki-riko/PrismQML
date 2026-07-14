# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design icons, effects, and utility skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _alpha(qcolor):
    return round(qcolor.alphaF(), 2)


def _assert_icons(icon, chevron, check, close, color, accent):
    assert _rgb(icon.property("color")) == color
    assert _rgb(chevron.property("color")) == color
    assert _rgb(close.property("color")) == color
    assert _rgb(check.property("color")) == accent


def _assert_shadowed_rectangle(item, card, shadow_alpha):
    assert item.property("_rectangleRadius") == 14
    assert item.property("_defaultShadowBlur") == 8
    assert item.property("_defaultShadowOffset") == 2
    assert _rgb(item.property("_rectangleColor")) == card
    assert _alpha(item.property("_defaultShadowColor")) == shadow_alpha
    assert _alpha(item.property("shadowColor")) == shadow_alpha


def _assert_popup(item, background, border, shadow_alpha):
    assert item.property("popupRadius") == 18
    assert item.property("_popupBorderWidth") == 1
    assert item.property("_popupShadowBlur") == 16
    assert item.property("_popupShadowOffset") == 4
    assert _rgb(item.property("_popupBackground")) == background
    assert _rgb(item.property("_popupBorderColor")) == border
    assert _alpha(item.property("_popupShadowColor")) == shadow_alpha


def _assert_remaining_effects_utils(item, background, shadow_alpha):
    assert item.property("skinValue") == "prism_design"
    assert item.property("isPrismDesign") is True
    assert item.property("radiusControl") == 10
    assert _rgb(item.property("prismBackground")) == background
    assert item.property("dpiBase") == 96
    assert item.property("dpiSpacing8") >= 8
    assert item.property("translatorHasAuto") is True
    assert item.property("translatorMissing") == "__prism_missing__"
    assert item.property("notificationPositionMatch") is True
    assert item.property("notificationHasToast") is True
    assert item.property("notificationHasInfoBar") is True
    assert item.property("popupFound") is True
    assert item.property("dragThreshold") == 4
    assert item.property("dragHoverEnabled") is False
    assert item.property("horizontalScrollDuration") == 750
    assert item.property("horizontalScrollStep") == 72
    assert item.property("horizontalScrollActive") is True
    assert item.property("horizontalBarWidth") == 6
    assert item.property("viewportInViewport") is True
    assert item.property("cullingInViewport") is True
    assert round(item.property("gaussianBlurValue"), 2) == 0.25
    assert item.property("gaussianSamples") == 17
    assert item.property("opacityMaskEnabled") is True
    assert item.property("opacityMaskThreshold") == 0
    assert item.property("opacityMaskSpread") == 1
    assert round(item.property("shadowBlur"), 2) == 0.15
    assert item.property("shadowOffset") == 2
    assert _alpha(item.property("shadowColor")) == shadow_alpha
    assert item.property("matrixRunning") is False
    assert item.property("matrixFontSize") == 14
    assert item.property("matrixDirection") == "down"
    assert item.property("matrixBinaryCharset") == "01"
    assert item.property("matrixThemeCount") >= 17
    assert item.property("matrixDirectionCount") == 4
    assert item.property("toggleDuration") == 200
    assert item.property("toggleTargetSet") is True


_REMAINING_EFFECTS_UTILS_QML = b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool isPrismDesign: Enums.isPrismDesign
    property int radiusControl: Enums.prismDesign.radiusControl
    property color prismBackground: Enums.backgroundColor
    property int dpiBase: DpiManager.baseDpi
    property int dpiSpacing8: DpiManager.spacing8
    property bool translatorHasAuto: Translator.supportedLanguages[0].code === "auto"
    property string translatorMissing: Translator.tr("__prism_missing__")
    property bool notificationPositionMatch: NotificationManager.posTopRight === Enums.notification.posTopRight
    property bool notificationHasToast: NotificationManager.toast !== null
    property bool notificationHasInfoBar: NotificationManager.infoBar !== null
    property bool popupFound: PopupUtils.findChildByName(searchRoot, "needle") === targetChild
    property int dragThreshold: dragHandle.dragThreshold
    property bool dragHoverEnabled: dragHandle.hoverEnabled
    property int horizontalScrollDuration: hMixin.scrollDuration
    property real horizontalScrollStep: hMixin.scrollStep
    property bool horizontalScrollActive: hMixin.active
    property int horizontalBarWidth: hMixin.barWidth
    property bool viewportInViewport: viewport.isInViewport
    property bool cullingInViewport: culling.inViewport
    property real gaussianBlurValue: blur.blur
    property int gaussianSamples: blur.samples
    property bool opacityMaskEnabled: mask.maskEnabled
    property real opacityMaskThreshold: mask.maskThresholdMin
    property real opacityMaskSpread: mask.maskSpreadAtMin
    property real shadowBlur: shadow.blur
    property real shadowOffset: shadow.verticalOffset
    property color shadowColor: shadow.color
    property bool matrixRunning: matrix.running
    property int matrixFontSize: matrix.fontSize
    property string matrixDirection: matrix.direction
    property string matrixBinaryCharset: matrix._activeCharset
    property int matrixThemeCount: matrix.getAvailableThemes().length
    property int matrixDirectionCount: matrix.getAvailableDirections().length
    property int toggleDuration: toggle.duration
    property bool toggleTargetSet: toggle.target === animTarget

    width: 520
    height: 360

    Item {
        id: searchRoot
        objectName: "root"
        Item {
            id: targetChild
            objectName: "needle"
        }
    }

    Flickable {
        id: flick
        width: 160
        height: 80
        contentWidth: 320
        contentHeight: 160
        clip: true

        Item {
            id: viewportTarget
            width: 40
            height: 40

            ViewportCulling {
                id: culling
            }
        }
    }

    HorizontalScrollMixin {
        id: hMixin
        target: flick
    }

    ViewportMixin {
        id: viewport
        target: viewportTarget
    }

    WindowDragHandle {
        id: dragHandle
    }

    Rectangle {
        id: maskItem
        width: 16
        height: 16
    }

    GaussianBlur {
        id: blur
    }

    OpacityMask {
        id: mask
        mask: maskItem
    }

    Shadow {
        id: shadow
    }

    MatrixRain {
        id: matrix
        width: 80
        height: 80
        running: false
        charsetPreset: "binary"
    }

    Item {
        id: animTarget
        ToggleAnimation {
            id: toggle
            target: animTarget
        }
    }
}
"""


def test_prism_design_icons_effects_utils_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Icon {
    icon: "Settings"
}
"""))
        icon = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
ChevronIcon {}
"""))
        chevron = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CheckIcon {}
"""))
        check = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CloseIcon {}
"""))
        close = keep[-1][1]
        _assert_icons(
            icon,
            chevron,
            check,
            close,
            color=(18, 34, 38),
            accent=(11, 127, 137),
        )

        keep.append(_build(engine, b"""
import PrismQML
ColorOverlay {}
"""))
        overlay = keep[-1][1]
        assert _rgb(overlay.property("color")) == (18, 34, 38)

        keep.append(_build(engine, b"""
import PrismQML
ShadowedRectangle {
    width: 120
    height: 64
}
"""))
        _assert_shadowed_rectangle(keep[-1][1], card=(252, 254, 255), shadow_alpha=0.14)

        keep.append(_build(engine, b"""
import PrismQML
PopupWindowCore {
    popupWidth: 180
    popupHeight: 120
}
"""))
        _assert_popup(
            keep[-1][1],
            background=(247, 252, 254),
            border=(185, 204, 209),
            shadow_alpha=0.22,
        )

        keep.append(_build(engine, _REMAINING_EFFECTS_UTILS_QML))
        utility_effects = keep[-1][1]
        _assert_remaining_effects_utils(
            utility_effects,
            background=(238, 245, 247),
            shadow_alpha=0.14,
        )

        setTheme(Theme.DARK)

        keep.append(_build(engine, b"""
import PrismQML
Icon {
    icon: "Settings"
}
"""))
        dark_icon = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
ChevronIcon {}
"""))
        dark_chevron = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CheckIcon {}
"""))
        dark_check = keep[-1][1]

        keep.append(_build(engine, b"""
import PrismQML
CloseIcon {}
"""))
        dark_close = keep[-1][1]
        _assert_icons(
            dark_icon,
            dark_chevron,
            dark_check,
            dark_close,
            color=(238, 247, 248),
            accent=(109, 235, 242),
        )

        keep.append(_build(engine, b"""
import PrismQML
ColorOverlay {}
"""))
        dark_overlay = keep[-1][1]
        assert _rgb(dark_overlay.property("color")) == (238, 247, 248)

        keep.append(_build(engine, b"""
import PrismQML
ShadowedRectangle {
    width: 120
    height: 64
}
"""))
        _assert_shadowed_rectangle(keep[-1][1], card=(26, 37, 41), shadow_alpha=0.6)

        keep.append(_build(engine, b"""
import PrismQML
PopupWindowCore {
    popupWidth: 180
    popupHeight: 120
}
"""))
        _assert_popup(
            keep[-1][1],
            background=(34, 48, 54),
            border=(50, 72, 79),
            shadow_alpha=0.7,
        )

        keep.append(_build(engine, _REMAINING_EFFECTS_UTILS_QML))
        dark_utility_effects = keep[-1][1]
        _assert_remaining_effects_utils(
            dark_utility_effects,
            background=(9, 14, 16),
            shadow_alpha=0.6,
        )
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
