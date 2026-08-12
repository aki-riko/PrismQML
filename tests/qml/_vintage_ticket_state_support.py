# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared vintage ticket runtime harness. 复古票据运行时共享夹具。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QJSValue, QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "vintage-ticket-state-matrix.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/data/Chart/_internal" as ChartInternal
import "../../prismqml/PrismQML/controls/inputs/Toggle" as ToggleInternal

Item {
    id: root

    property int buttonStyle: Enums.button.style_default
    property int buttonLevel: Enums.statusLevel.error
    property bool buttonEnabled: true
    property bool buttonLoading: false
    property bool buttonHovered: false
    property bool buttonPressed: false
    property bool buttonChecked: false
    readonly property var buttonStyles: [
        Enums.button.style_default,
        Enums.button.style_primary,
        Enums.button.style_transparent,
        Enums.button.style_filled,
        Enums.button.style_text,
        Enums.button.style_hyperlink,
        Enums.button.style_gradient
    ]
    readonly property var statusLevels: [
        Enums.statusLevel.info,
        Enums.statusLevel.success,
        Enums.statusLevel.warning,
        Enums.statusLevel.error,
        Enums.statusLevel.attention,
        Enums.statusLevel.processing
    ]
    readonly property color buttonBackground: stateButton._styleBgColor
    readonly property color buttonBorder: stateButton._styleBorderColor
    readonly property color buttonText: stateButton._styleTextColor
    readonly property color toggleText: textToggle._textColor
    readonly property color progressCoreTrack: progressCore.trackColor
    readonly property color progressRingTrack: progressRing.trackColor
    readonly property color cropperBackground: cropper._previewBackground
    readonly property color cropperBorder: cropper._previewBorderColor
    readonly property color cropperIcon: cropper._previewIconColor
    readonly property color cropperText: cropper._previewTextColor
    readonly property color ratingFill: rating.fillColor
    readonly property color ratingOutline: rating.outlineColor
    readonly property color sliderHandle: slider.handleColor
    readonly property color inputBackground: stateInput.color
    readonly property color inputBorder: stateInput.border.color
    readonly property color navigationBackground: navigationItem._navItemBackground
    readonly property color navigationBorder: navigationItem._navItemBorderColor
    readonly property color navigationContent: navigationItem._navItemContentColor
    readonly property color chartTooltipBackground: chartTooltip._tooltipBackground
    readonly property color chartTooltipBorder: chartTooltip._tooltipBorderColor
    readonly property color tipBackground: tipPopup._tipBackground
    readonly property color tipBorder: tipPopup._tipBorderColor
    readonly property color loginBackground: login.color
    readonly property color matrixMain: matrixRain.mainColor
    readonly property color matrixHead: matrixRain.headColor
    readonly property color matrixBackground: matrixRain.backgroundColor
    readonly property var confettiPalette: confetti.colors
    readonly property var passwordPalette: passwordStrength.strengthColors

    width: 900
    height: 700

    Button {
        id: stateButton
        objectName: "stateButton"
        style: root.buttonStyle
        level: root.buttonLevel
        enabled: root.buttonEnabled
        loading: root.buttonLoading
        pseudoHovered: root.buttonHovered
        pseudoPressed: root.buttonPressed
        feature: root.buttonChecked ? Enums.button.feature_toggle : Enums.button.feature_none
        checked: root.buttonChecked
        text: "State button"
    }

    Toggle {
        id: textToggle
        objectName: "textToggle"
        text: "Ticket text"
    }

    ToggleInternal.ToggleCheckIndicator { objectName: "checkIndicator" }
    ToggleInternal.ToggleRadioIndicator { objectName: "radioIndicator" }
    ToggleInternal.ToggleSwitchIndicator { objectName: "switchIndicator" }

    ProgressCore { id: progressCore; objectName: "progressCore" }
    ProgressRing { id: progressRing; objectName: "progressRing" }
    Button {
        objectName: "buttonRing"
        feature: Enums.button.feature_indeterminate_ring
        text: "Ring"
    }

    ImageCropper { id: cropper; objectName: "cropper" }
    RatingCore { id: rating; objectName: "rating" }
    Slider { id: slider; objectName: "slider" }
    InputCore { id: stateInput; objectName: "stateInput" }
    NavigationBarItem {
        id: navigationItem
        objectName: "navigationItem"
        text: "Ticket"
    }

    ChartInternal.ChartTooltip {
        id: chartTooltip
        objectName: "chartTooltip"
        label: "Ticket label"
        value: "42"
        isValueString: true
    }
    TipPopup { id: tipPopup; objectName: "tipPopup" }
    LoginWindow { id: login; objectName: "login"; matrixEnabled: true }
    SplashScreen {
        objectName: "splash"
        enableShadow: true
        showTitleBar: false
        showProgress: false
        visible: false
    }
    ChartInternal.BoxplotChartArea {
        width: 360
        height: 240
        boxplotData: [{ label: "Ticket", min: 1, q1: 2, median: 3, q3: 4, max: 5, outliers: [] }]
        animated: false
        showValues: false
        showGrid: false
        isHorizontal: false
        hoveredIndex: 0
    }
    MatrixRain { id: matrixRain; objectName: "matrixRain"; running: false }
    Confetti { id: confetti; objectName: "confetti"; running: false }
    PasswordStrengthIndicator {
        id: passwordStrength
        objectName: "passwordStrength"
        password: "Ticket123!"
    }
}
"""

PALETTES = {
    Theme.LIGHT: {
        "background": "#e9e1d2", "surface": "#f8f3e8", "muted": "#eee6d8",
        "foreground": "#2b211a", "secondary": "#74685b", "disabled": "#a79b8b",
        "border": "#5a4637", "divider": "#b8aa96", "primary": "#5a3d2b",
        "primary_foreground": "#fff9ee", "success": "#267451", "danger": "#a33e36",
        "warning": "#91651f", "info": "#416c73",
    },
    Theme.DARK: {
        "background": "#1d1a17", "surface": "#28231e", "muted": "#342e27",
        "foreground": "#ede3d2", "secondary": "#b9ab98", "disabled": "#766b60",
        "border": "#b4a48e", "divider": "#776a5b", "primary": "#c6a66b",
        "primary_foreground": "#1d1a17", "success": "#68a77c", "danger": "#d37b72",
        "warning": "#c9a45d", "info": "#88a9ae",
    },
}


def _pump(milliseconds: int = 1) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _settle_colors() -> None:
    # Toggle leaves animate color changes; assert the rendered end state, not
    # an in-flight interpolation sample. Toggle 叶组件会做颜色动画；这里等待
    # 动画结束后验证最终渲染态，避免把过渡帧误判为皮肤颜色。
    _pump(350)


def _color(value) -> QColor:
    return QColor(value)


def _lighter(value, factor: int) -> QColor:
    return _color(value).lighter(factor)


def _darker(value, factor: int) -> QColor:
    return _color(value).darker(factor)


def _transparent(value) -> QColor:
    result = _color(value)
    result.setAlpha(0)
    return result


def _alpha(value, alpha: float) -> QColor:
    result = _color(value)
    result.setAlphaF(alpha)
    return result


def _variant_list(value) -> list:
    if isinstance(value, QJSValue):
        value = value.toVariant()
    return list(value)


def _descendants(root: QObject) -> list[QObject]:
    return root.findChildren(QObject)


def _find_type(root: QObject, type_fragment: str) -> QObject:
    matches = [
        child for child in _descendants(root)
        if type_fragment in child.metaObject().className()
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _set_button(root: QObject, style: int, **state) -> None:
    defaults = {
        "buttonStyle": style,
        "buttonLevel": 3,
        "buttonEnabled": True,
        "buttonLoading": False,
        "buttonHovered": False,
        "buttonPressed": False,
        "buttonChecked": False,
    }
    defaults.update(state)
    for name, value in defaults.items():
        assert root.setProperty(name, value)
    _pump()


@pytest.fixture(scope="module")
def ticket_scene(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    warnings: list[str] = []
    setSkin(Skin.VINTAGE_TICKET)
    setTheme(Theme.LIGHT)
    engine = QQmlApplicationEngine()
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(10)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(30)
    try:
        yield root, warnings
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        setTheme(previous_theme)
        setSkin(previous_skin)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
