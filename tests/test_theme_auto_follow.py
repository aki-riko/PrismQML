# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Theme.AUTO live system-follow contracts. Theme.AUTO 实时跟随系统配色合同。

真实运行时证据链：QStyleHints.colorSchemeChanged（真实 Qt 信号）→ ThemeManager
延迟重新通知 → isDark 真实变化 → Enums.isDark QML 绑定刷新。

触发方式按平台能力选择：
- 平台报告已知配色方案（Windows 平台插件，含 --qt-platform windows 运行）时，
  使用真实的 QStyleHints.setColorScheme() 覆盖，必须生效；
- offscreen 平台插件不支持配色覆盖（colorScheme() 恒为 Unknown），此时改用 AUTO
  既有的判定源（应用调色板）+ 真实 colorSchemeChanged 信号复现同一链路。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.core.theme import Theme, ThemeManager

ROOT = Path(__file__).resolve().parents[1]

DARK_WINDOW = "#1e1e1e"
LIGHT_WINDOW = "#f3f3f3"

ENUMS_SCENE = """
import QtQuick
import PrismQML

Item {
    property bool isDark: Enums.isDark
    property string theme: Enums.theme
    property bool reduceFlag: Enums.reduceMotion
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 10
    return predicate()


def _create(engine: QQmlApplicationEngine, source: str, name: str):
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl(f"inline:{name}.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _dispose(engine, component, instance) -> None:
    if instance is not None:
        instance.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _platform_override(hints, scheme) -> bool:
    """Apply a real platform color-scheme override. 应用真实平台配色覆盖。"""
    hints.setColorScheme(scheme)
    QCoreApplication.processEvents()
    return hints.colorScheme() == scheme


class _SchemeDriver:
    """Drive the real colorSchemeChanged signal on the current platform.

    在当前平台上驱动真实的 colorSchemeChanged 信号。
    """

    def __init__(self, app):
        self.app = app
        self.hints = QGuiApplication.styleHints()
        self.original_palette = app.palette()
        self.original_scheme = self.hints.colorScheme()
        self.platform_supported = self.original_scheme != Qt.ColorScheme.Unknown
        self.used_platform_override = False

    def _palette(self, window_color: str) -> QPalette:
        palette = QPalette(self.original_palette)
        palette.setColor(QPalette.ColorRole.Window, QColor(window_color))
        return palette

    def apply_dark(self) -> bool:
        """Return True when the real platform override was used. 返回是否走平台覆盖。"""
        if self.platform_supported:
            self.used_platform_override = True
            assert _platform_override(self.hints, Qt.ColorScheme.Dark), (
                "平台报告已知配色方案时必须支持真实覆盖"
            )
            return True
        self.app.setPalette(self._palette(DARK_WINDOW))
        self.hints.colorSchemeChanged.emit(Qt.ColorScheme.Dark)
        return False

    def apply_light(self) -> None:
        if self.used_platform_override:
            assert _platform_override(self.hints, Qt.ColorScheme.Light)
            return
        self.app.setPalette(self._palette(LIGHT_WINDOW))
        self.hints.colorSchemeChanged.emit(Qt.ColorScheme.Light)

    def restore(self) -> None:
        self.app.setPalette(self.original_palette)
        if self.used_platform_override:
            self.hints.setColorScheme(self.original_scheme)
            QCoreApplication.processEvents()


@pytest.fixture()
def scheme_driver(qapp):
    driver = _SchemeDriver(qapp)
    yield driver
    driver.restore()


@pytest.fixture()
def auto_theme(qapp):
    del qapp
    manager = ThemeManager()
    previous = manager.theme
    manager._apply_theme(Theme.AUTO)
    yield manager
    manager._apply_theme(Theme(previous))


def test_auto_tracks_system_color_scheme_change(auto_theme, scheme_driver):
    manager = auto_theme
    assert manager.theme == "auto"
    assert manager.bind_system_theme_watch() is True

    notifications = []

    def record(value):
        notifications.append(value)

    manager.themeChanged.connect(record)
    try:
        scheme_driver.apply_dark()
        assert _wait_for(lambda: manager.isDark is True), "系统转深色后 isDark 必须为真"
        assert _wait_for(lambda: bool(notifications)), "AUTO 下必须通过真实信号重新通知 QML"
        assert notifications[-1] == "auto"
        assert manager.theme == "auto"

        notifications.clear()
        scheme_driver.apply_light()
        assert _wait_for(lambda: manager.isDark is False), "系统转浅色后 isDark 必须为假"
        assert _wait_for(lambda: bool(notifications))
    finally:
        manager.themeChanged.disconnect(record)


def test_enums_is_dark_binding_refreshes_on_system_change(auto_theme, scheme_driver, qapp):
    del qapp
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        component, instance = _create(engine, ENUMS_SCENE, "w5-auto-follow")
        _pump()
        assert auto_theme.bind_system_theme_watch() is True

        scheme_driver.apply_dark()
        assert _wait_for(lambda: instance.property("isDark") is True), (
            "Enums.isDark QML 绑定必须随系统配色刷新"
        )
        assert instance.property("theme") == "auto"

        scheme_driver.apply_light()
        assert _wait_for(lambda: instance.property("isDark") is False)
        assert instance.property("theme") == "auto"
    finally:
        _dispose(engine, component, instance)


def test_explicit_light_ignores_system_color_scheme(auto_theme, scheme_driver):
    manager = auto_theme
    assert manager.bind_system_theme_watch() is True
    manager._apply_theme(Theme.LIGHT)
    assert manager.isDark is False

    notifications = []

    def record(value):
        notifications.append(value)

    manager.themeChanged.connect(record)
    try:
        scheme_driver.apply_dark()
        _pump(30)
        assert notifications == [], "显式 LIGHT 不得因系统配色变化而重新通知"
        assert manager.isDark is False
        assert manager.theme == "light"
    finally:
        manager.themeChanged.disconnect(record)


def test_explicit_dark_ignores_system_color_scheme(auto_theme, scheme_driver):
    manager = auto_theme
    assert manager.bind_system_theme_watch() is True
    manager._apply_theme(Theme.DARK)
    assert manager.isDark is True

    notifications = []

    def record(value):
        notifications.append(value)

    manager.themeChanged.connect(record)
    try:
        scheme_driver.apply_light()
        _pump(30)
        assert notifications == [], "显式 DARK 不得因系统配色变化而重新通知"
        assert manager.isDark is True
        assert manager.theme == "dark"
    finally:
        manager.themeChanged.disconnect(record)


def test_switching_back_to_auto_resumes_following(auto_theme, scheme_driver):
    manager = auto_theme
    assert manager.bind_system_theme_watch() is True
    manager._apply_theme(Theme.LIGHT)
    assert manager.isDark is False

    manager._apply_theme(Theme.AUTO)
    scheme_driver.apply_dark()
    assert _wait_for(lambda: manager.isDark is True)

    manager._apply_theme(Theme.LIGHT)
    assert manager.isDark is False


def test_watch_binding_is_idempotent(auto_theme, qapp):
    del qapp
    manager = auto_theme
    assert manager.bind_system_theme_watch() is True
    assert manager.bind_system_theme_watch() is True
    assert manager._system_color_scheme_bound is True
