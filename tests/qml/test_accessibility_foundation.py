# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Accessibility foundation: tokens, focus ring and role mapping.

无障碍基础：令牌、焦点环与角色映射。

这些是全库无障碍改造的共享底座：Enums.qml 的 accessibility 分类别名、
FocusVisual 与 AccessibilityHelper 两个新公开类型。焦点环粗细刻意复用既有
Enums.border 描边令牌，因此 Metrics.qml 无需新增任何度量（保持在体积门禁内）。
"""

from PySide6.QtQml import QQmlApplicationEngine

from prismqml import (
    Skin,
    getAccentColor,
    getSkin,
    register_types,
    setAccentColor,
    setSkin,
)


def _create(engine, source: bytes, expect_window: bool = False):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtQuick import QQuickItem, QQuickWindow

    component = QQmlComponent(engine)
    component.setData(source, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    instance = component.create()
    expected = QQuickWindow if expect_window else QQuickItem
    assert isinstance(instance, expected), errors
    return component, instance


def test_accessibility_tokens_are_exposed_on_enums(qapp):
    """Enums exposes role/state/live tokens, focus ring and hit target."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    property var roles: [
        Enums.accessibility.role_none,
        Enums.accessibility.role_button,
        Enums.accessibility.role_checkbox,
        Enums.accessibility.role_dialog,
        Enums.accessibility.role_statictext
    ]
    property var states: [
        Enums.accessibility.state_none,
        Enums.accessibility.state_expanded,
        Enums.accessibility.state_selected,
        Enums.accessibility.state_invalid
    ]
    property real focusRingWidth: Enums.border.normal
}
""",
    )
    try:
        roles = instance.property("roles")
        if hasattr(roles, "toVariant"):
            roles = roles.toVariant()
        assert list(roles) == [0, 1, 2, 14, 20]

        states = instance.property("states")
        if hasattr(states, "toVariant"):
            states = states.toVariant()
        assert list(states) == [0, 1, 3, 5]

        # The focus outline reuses the shared border width token.
        # 焦点轮廓复用全局描边粗细令牌。
        assert instance.property("focusRingWidth") > 0
    finally:
        instance.deleteLater()


def test_focus_visual_tracks_active_focus_and_defers_drawing(qapp):
    """The ring appears for active focus and is created lazily.

    焦点环跟随 activeFocus 出现，且绘制是惰性创建的。

    Note 说明: FocusVisual follows activeFocus only; keyboard reachability and
    input modality remain contracts of the focus owner.
    FocusVisual 只跟随 activeFocus；键盘可达性和输入方式仍由焦点宿主负责。
    """
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Window {
    width: 200
    height: 40
    visible: true
    FocusScope {
        id: scope
        anchors.fill: parent
        focus: true
        TextInput {
            id: firstTarget
            width: 80
            height: parent.height
            focus: true
            activeFocusOnTab: true
        }
        TextInput {
            id: focusArea
            x: 100
            width: 80
            height: parent.height
            activeFocusOnTab: true
            color: Enums.cardColor
        }
        FocusVisual {
            id: ring
            x: focusArea.x
            width: focusArea.width
            height: focusArea.height
            radius: Enums.radius.small
            focusSource: focusArea
        }
    }
    property var ringItem: ring
    property var areaItem: focusArea
    property bool drawn: ring.ringItem !== null
    property real drawnStrokeWidth: drawn ? ring.ringItem.children[0].border.width : -1
    property int drawnStrokeCount: drawn ? ring.ringItem.children.length : 0
    property color themeAccentColor: Enums.accentColor
    property color focusRingColor: ring.ringColor
    property color drawnRingColor: drawn
        ? ring.ringItem.children[0].border.color : Enums.transparent
}
""",
        expect_window=True,
    )
    previous_skin = getSkin()
    previous_accent = getAccentColor()
    try:
        setSkin(Skin.FLUENT)
        ring = instance.property("ringItem")
        area = instance.property("areaItem")
        # Before active focus the ring is dormant: nothing is drawn yet.
        # activeFocus 到来前焦点环处于休眠：尚未绘制任何内容。
        assert ring.property("enabled") is False
        assert instance.property("drawn") is False
        assert ring.property("focused") is False

        from PySide6.QtCore import QCoreApplication, Qt
        from PySide6.QtTest import QTest

        instance.requestActivate()
        for _ in range(10):
            QCoreApplication.processEvents()
        assert instance.activeFocusItem() is not area
        QTest.keyClick(instance, Qt.Key.Key_Tab)
        for _ in range(4):
            QCoreApplication.processEvents()
        assert area.property("activeFocus") is True
        assert ring.property("focused") is True
        assert instance.property("drawn") is True

        setAccentColor("#fb923c")
        for _ in range(4):
            QCoreApplication.processEvents()
        assert instance.property("themeAccentColor").name() == "#fb923c"
        expected_accent = instance.property("themeAccentColor")
        assert instance.property("focusRingColor") == expected_accent
        assert instance.property("drawnRingColor") == expected_accent
        assert instance.property("drawnStrokeCount") == 1
        assert instance.property("drawnStrokeWidth") == ring.property("ringWidth")
    finally:
        from PySide6.QtCore import QCoreApplication, QEvent

        setAccentColor(previous_accent)
        setSkin(previous_skin)
        instance.close()
        instance.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_accessibility_helper_maps_roles_and_builds_names(qapp):
    """The helper maps Enums tokens to Qt roles and normalises names."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    property int buttonRole: AccessibilityHelper.roleValue(Enums.accessibility.role_button)
    property int unknownRole: AccessibilityHelper.roleValue(9999)
    property int checkboxRole: AccessibilityHelper.roleValue(Enums.accessibility.role_checkbox)
    property string explicitName: AccessibilityHelper.resolveName("Save", "ignored", "tip")
    property string visibleName: AccessibilityHelper.resolveName("", "Open", "tip")
    property string tipName: AccessibilityHelper.resolveName("", "", "tip")
    property string emptyName: AccessibilityHelper.resolveName("", "", "")
    property string description: AccessibilityHelper.describe(["First", null, "  ", "Second"])
    property string emptyDescription: AccessibilityHelper.describe([])
}
""",
    )
    try:
        # Accessible.Button / CheckBox are Qt enum values; assert they differ and
        # that an unknown token degrades to NoRole.
        # 断言两者不同，且未知令牌退化为 NoRole。
        button_role = instance.property("buttonRole")
        checkbox_role = instance.property("checkboxRole")
        assert button_role > 0 and checkbox_role > 0
        assert button_role != checkbox_role
        assert instance.property("unknownRole") == 0

        assert instance.property("explicitName") == "Save"
        assert instance.property("visibleName") == "Open"
        assert instance.property("tipName") == "tip"
        assert instance.property("emptyName") == ""
        assert instance.property("description") == "First. Second"
        assert instance.property("emptyDescription") == ""
    finally:
        instance.deleteLater()
