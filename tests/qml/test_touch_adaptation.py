# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Touch adaptation regressions. 触摸适配回归。

桌面不变式: 无 PlatformInfo 时 Enums.controlSize 交互 token 与其字面量完全一致。
触摸语义: 注入 isTouch=true 的 PlatformInfo 后, 交互 token 抬到 >=48 且 hover 视觉
只在按压时生效。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Property, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PROBE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "touch-adaptation-probe.qml")
)
TOOLTIP_PROBE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "touch-adaptation-tooltip-probe.qml")
)

# Decision: touch shows no tooltip. 决策: 触摸端不显示任何提示。
TOOLTIP_PROBE_SOURCE = """
import QtQuick
import PrismQML

Item {
    TooltipCore {
        id: tip
        text: "tip"
    }

    readonly property bool windowRequested: tip._windowRequested
    readonly property bool pendingShow: tip._pendingShow
    readonly property bool probeTouch: Touch.isTouch
    readonly property int probeMinTarget: Touch.minTargetSize

    function trigger() { tip.show() }
}
"""

PROBE_SOURCE = """
import QtQuick
import PrismQML

QtObject {
    // Interactive tokens 交互 token
    readonly property int inputHeight: Enums.controlSize.inputHeight
    readonly property int inputHeightCompact: Enums.controlSize.inputHeightCompact
    readonly property int inputHeightLarge: Enums.controlSize.inputHeightLarge
    readonly property int pickerRow: Enums.controlSize.pickerRow
    readonly property int tabBarHeight: Enums.controlSize.tabBarHeight
    readonly property int segmentedHeight: Enums.controlSize.segmentedHeight
    readonly property int segmentedToolSize: Enums.controlSize.segmentedToolSize
    readonly property int commandBarButtonSize: Enums.controlSize.commandBarButtonSize
    readonly property int toolButtonWidth: Enums.controlSize.toolButtonWidth
    readonly property int listItemHeight: Enums.controlSize.listItemHeight
    readonly property int tableHeaderHeight: Enums.controlSize.tableHeaderHeight
    readonly property int calendarCell: Enums.controlSize.calendarCell
    readonly property int calendarCellHeight: Enums.controlSize.calendarCellHeight
    readonly property int buttonHeight: Enums.controlSize.buttonHeight
    readonly property int closeButton: Enums.controlSize.closeButton
    readonly property int closeButtonSize: Enums.controlSize.closeButtonSize
    readonly property int dialogButtonHeight: Enums.controlSize.dialogButtonHeight
    readonly property int topNavItemHeight: Enums.controlSize.topNavItemHeight
    readonly property int navItemHeight: Enums.controlSize.navItemHeight
    readonly property int flipViewNavButton: Enums.controlSize.flipViewNavButton
    readonly property int emptyStateButtonHeight: Enums.controlSize.emptyStateButtonHeight

    // Non-interactive tokens must stay untouched 非交互 token 必须保持不变
    readonly property int radioOuter: Enums.controlSize.radioOuter
    readonly property int checkboxOuter: Enums.controlSize.checkboxOuter
    readonly property int switchHeight: Enums.controlSize.switchHeight
    readonly property int statusBarHeight: Enums.controlSize.statusBarHeight
    readonly property int tooltipHeight: Enums.controlSize.tooltipHeight
    readonly property int navBarHeight: Enums.controlSize.navBarHeight
    readonly property int bottomTabBarHeight: Enums.controlSize.bottomTabBarHeight

    // Capability resolution 能力解析
    readonly property bool touch: Touch.isTouch
    readonly property int minTargetSize: Touch.minTargetSize
    readonly property int targetRaised: Touch.target(32)
    readonly property int targetKept: Touch.target(56)

    // Feedback mapping 反馈映射
    readonly property bool feedbackHover: Touch.feedback(true, false)
    readonly property bool feedbackPress: Touch.feedback(false, true)
    readonly property bool feedbackBoth: Touch.feedback(true, true)
    readonly property bool feedbackNone: Touch.feedback(false, false)

    // Hover-revealed affordances 依赖 hover 揭示的控件
    readonly property bool revealHovered: Touch.reveal(true)
    readonly property bool revealIdle: Touch.reveal(false)

    // Nested mapping must be idempotent: several controls feed an already mapped
    // state into another Touch.feedback (Toggle -> indicator, ListWidget ->
    // ListWidgetItem, ComboBoxCore -> ComboBoxCoreContent).
    // 嵌套映射必须幂等: 多个控件把已映射的状态再喂给下一层 Touch.feedback。
    readonly property bool nestedA: Touch.feedback(Touch.feedback(true, false), false)
        === Touch.feedback(true, false)
    readonly property bool nestedB: Touch.feedback(Touch.feedback(false, true), true)
        === Touch.feedback(false, true)
    readonly property bool nestedC: Touch.feedback(Touch.feedback(true, true), true)
        === Touch.feedback(true, true)
}
"""

INTERACTIVE_TOKENS = (
    "inputHeight",
    "inputHeightCompact",
    "inputHeightLarge",
    "pickerRow",
    "tabBarHeight",
    "segmentedHeight",
    "segmentedToolSize",
    "commandBarButtonSize",
    "toolButtonWidth",
    "listItemHeight",
    "tableHeaderHeight",
    "calendarCell",
    "calendarCellHeight",
    "buttonHeight",
    "closeButton",
    "closeButtonSize",
    "dialogButtonHeight",
    "topNavItemHeight",
    "navItemHeight",
    "flipViewNavButton",
    "emptyStateButtonHeight",
)

DESKTOP_TOKENS = {
    "inputHeight": 32,
    "inputHeightCompact": 28,
    "inputHeightLarge": 40,
    "pickerRow": 36,
    "tabBarHeight": 40,
    "segmentedHeight": 36,
    "segmentedToolSize": 36,
    "commandBarButtonSize": 36,
    "toolButtonWidth": 36,
    "listItemHeight": 36,
    "tableHeaderHeight": 44,
    "calendarCell": 32,
    "calendarCellHeight": 36,
    "buttonHeight": 32,
    "closeButton": 32,
    "closeButtonSize": 28,
    "dialogButtonHeight": 32,
    "topNavItemHeight": 36,
    "navItemHeight": 40,
    "flipViewNavButton": 28,
    "emptyStateButtonHeight": 32,
}

UNTOUCHED_TOKENS = {
    "radioOuter": 20,
    "checkboxOuter": 18,
    "switchHeight": 24,
    "statusBarHeight": 24,
    "tooltipHeight": 28,
    "navBarHeight": 48,
    "bottomTabBarHeight": 56,
}


class _PlatformInfo(QObject):
    """Synthetic host PlatformInfo. 合成宿主 PlatformInfo。"""

    def __init__(self, touch: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._touch = touch

    def _is_touch(self) -> bool:
        return self._touch

    def _target_size(self) -> int:
        return 48 if self._touch else 32

    def _platform_name(self) -> str:
        return "android" if self._touch else "windows"

    isTouch = Property(bool, _is_touch, constant=True)
    isMobile = Property(bool, _is_touch, constant=True)
    isCompact = Property(bool, lambda self: False, constant=True)
    touchTargetSize = Property(int, _target_size, constant=True)
    platformName = Property(str, _platform_name, constant=True)


def _create_probe(platform_info: _PlatformInfo | None, source: str = PROBE_SOURCE,
                  url: QUrl = PROBE_URL):
    engine = QQmlEngine()
    assert engine.rootContext() is not None
    if platform_info is not None:
        engine.rootContext().setContextProperty("PlatformInfo", platform_info)
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), url)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    obj = component.create(engine.rootContext())
    assert obj is not None, [error.toString() for error in component.errors()]
    return engine, component, obj


def _dispose(engine, component, obj) -> None:
    obj.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()


def _read(obj, name):
    return obj.property(name)


def test_desktop_metrics_and_feedback_are_unchanged(qapp):
    engine, component, obj = _create_probe(None)
    try:
        assert _read(obj, "touch") is False
        assert _read(obj, "minTargetSize") == 0
        for token, expected in DESKTOP_TOKENS.items():
            assert _read(obj, token) == expected, token
        for token, expected in UNTOUCHED_TOKENS.items():
            assert _read(obj, token) == expected, token

        assert _read(obj, "targetRaised") == 32
        assert _read(obj, "targetKept") == 56

        # Desktop feedback stays hover-driven 桌面反馈依旧由 hover 驱动
        assert _read(obj, "feedbackHover") is True
        assert _read(obj, "feedbackPress") is False
        assert _read(obj, "feedbackBoth") is True
        assert _read(obj, "feedbackNone") is False
        assert _read(obj, "revealHovered") is True
        assert _read(obj, "revealIdle") is False
        assert _read(obj, "nestedA") is True
        assert _read(obj, "nestedB") is True
        assert _read(obj, "nestedC") is True
    finally:
        _dispose(engine, component, obj)


def test_touch_metrics_are_raised_and_feedback_follows_press(qapp):
    platform_info = _PlatformInfo(True)
    engine, component, obj = _create_probe(platform_info)
    try:
        assert _read(obj, "touch") is True
        assert _read(obj, "minTargetSize") == 48
        for token in INTERACTIVE_TOKENS:
            value = _read(obj, token)
            assert value >= 48, (token, value)
        for token, expected in UNTOUCHED_TOKENS.items():
            assert _read(obj, token) == expected, token

        assert _read(obj, "targetRaised") == 48
        assert _read(obj, "targetKept") == 56

        # Touch has no hover preview: the hover treatment follows the press
        # 触摸没有 hover 预览: hover 视觉跟随按压
        assert _read(obj, "feedbackHover") is False
        assert _read(obj, "feedbackPress") is True
        assert _read(obj, "feedbackBoth") is True
        assert _read(obj, "feedbackNone") is False
        # Hover-revealed affordances stay visible on touch 依赖 hover 揭示的控件在触摸端常显
        assert _read(obj, "revealHovered") is True
        assert _read(obj, "revealIdle") is True
        # Nested mapping stays idempotent on touch too 触摸端嵌套映射同样幂等
        assert _read(obj, "nestedA") is True
        assert _read(obj, "nestedB") is True
        assert _read(obj, "nestedC") is True
    finally:
        _dispose(engine, component, obj)


def test_tooltip_stays_shut_on_touch_and_opens_on_desktop(qapp):
    """Decision: touch shows no tooltip. 决策: 触摸端不显示提示。"""
    engine, component, obj = _create_probe(None, TOOLTIP_PROBE_SOURCE, TOOLTIP_PROBE_URL)
    try:
        assert _read(obj, "probeTouch") is False
        assert QMetaObject.invokeMethod(obj, "trigger")
        assert _read(obj, "windowRequested") is True
        assert _read(obj, "pendingShow") is True
    finally:
        _dispose(engine, component, obj)

    # Hold a strong reference: an inline temporary would be collected by Python and
    # PlatformInfo would silently degrade to non-touch.
    # 必须持有强引用: 内联临时对象会被回收, PlatformInfo 会静默退化为非触摸。
    touch_info = _PlatformInfo(True)
    engine, component, obj = _create_probe(
        touch_info, TOOLTIP_PROBE_SOURCE, TOOLTIP_PROBE_URL
    )
    try:
        assert _read(obj, "probeTouch") is True
        assert QMetaObject.invokeMethod(obj, "trigger")
        assert _read(obj, "windowRequested") is False
        assert _read(obj, "pendingShow") is False
    finally:
        _dispose(engine, component, obj)
