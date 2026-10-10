# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""ButtonCore accessible metadata wiring. 按钮核心的无障碍元数据接线。

VERIFICATION LIMIT 验证限制: Qt 6 does not let a test read `Accessible.role` /
`Accessible.name` back on an offscreen item -- a minimal Qt-only scene that
declaratively sets `Accessible.role: Accessible.Button` also reads back None.
That was measured, not assumed. These cases therefore pin what *is* observable:
the helper chain resolves, the components construct, and the metadata properties
are accepted without error. Effectiveness for a real screen reader still requires
a run with an active platform accessibility bridge.
Qt 6 不允许离屏测试读回 Accessible 附加属性：一个仅声明式设置
`Accessible.role: Accessible.Button` 的最小 Qt 场景读回同样是 None（已实测）。
因此本测试只锁定可观测的部分：helper 链可解析、组件可构造、元数据属性被接受。
真实读屏器下的有效性仍需在启用平台无障碍桥的环境验证。
"""

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types

SCENE = b"""import QtQuick
import PrismQML
Item {
    width: 400
    height: 200

    Button {
        objectName: "plain"
        text: "Save"
    }

    Button {
        objectName: "toggle"
        text: "Bold"
        feature: Enums.button.feature_toggle
        checked: true
    }

    Button {
        objectName: "iconOnly"
        toolTipText: "Copy"
    }
}
"""


def _scene(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    root = component.create()
    assert isinstance(root, QQuickItem), errors
    return engine, component, root


def test_button_variants_construct_with_a11y_helper_wired(qapp) -> None:
    """The helper chain must resolve and construct for every button shape."""
    engine, component, root = _scene(qapp)
    try:
        for name in ("plain", "toggle", "iconOnly"):
            item = root.findChild(QObject, name)
            assert item is not None, f"button {name} was not created"

        # The helper resolves its role through the shared AccessibilityHelper, so a
        # wrong token would surface as an enum error rather than a silent no-op.
        # helper 经 AccessibilityHelper 解析角色；令牌错误会表现为枚举错误而非静默无效。
        plain = root.findChild(QObject, "plain")
        assert plain.property("text") == "Save"
        toggle = root.findChild(QObject, "toggle")
        assert toggle.property("checked") is True
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
