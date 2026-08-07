# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SystemTray data-backed submenu regression. 系统托盘数据子菜单回归。"""

from __future__ import annotations

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression

from prismqml.python.core.engine import EngineManager
from prismqml.python.core.utils import register_types
from prismqml.python.window.system_tray import SystemTrayIcon


def _pump(milliseconds=30):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(engine, scope, source):
    expression = QQmlExpression(engine.rootContext(), scope, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return result


def test_data_submenu_opens_and_routes_child_action(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    EngineManager.set_engine(engine)
    triggered = []
    tray = SystemTrayIcon()
    tray.addMenu(
        "Drives",
        actions=[
            {
                "text": "NAS",
                "actionId": "drive_nas",
                "triggered": lambda: triggered.append("drive_nas"),
            }
        ],
    )
    tray._showQmlMenu()
    _pump()
    menu = tray._qml_menu
    component = tray._component
    assert menu is not None
    assert component.parent() is engine
    assert menu.parent() is engine
    assert menu.property("_nativeWindowRequested") is True
    assert menu.property("_popupWindow") is not None

    try:
        assert _evaluate(
            engine,
            menu,
            '(function() { var action = getAction("_submenu_Drives"); '
            'return action !== null && action.hasSubmenu; })()',
        )
        _evaluate(
            engine,
            menu,
            '(function() { getAction("_submenu_Drives").submenuRequested(); '
            'return true; })()',
        )
        _pump()
        assert _evaluate(
            engine,
            menu,
            '(function() { var submenu = _openSubmenu; '
            'if (submenu === null) return false; '
            'var child = submenu.getAction("drive_nas"); '
            'if (child === null) return false; '
            'var observed = ""; actionTriggered.connect(function(id) { observed = id; }); '
            'child.triggered(); return observed === "drive_nas"; })()',
        )
        assert triggered == ["drive_nas"]
    finally:
        EngineManager.reset()
        assert tray._qml_menu is None
        assert tray._component is None
        assert shiboken6.isValid(menu)
        assert shiboken6.isValid(component)
        assert menu.property("isOpen") is False
        assert menu.property("_openSubmenu") is None
        assert menu.property("_nativeWindowRequested") is False
        assert menu.property("_popupWindow") is None
        assert _evaluate(
            engine,
            menu,
            'getAction("_submenu_Drives") !== null',
        )
        tray.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert not shiboken6.isValid(menu)
        assert not shiboken6.isValid(component)
        assert not shiboken6.isValid(engine)
