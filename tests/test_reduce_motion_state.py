# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Reduced-motion state contracts. 减少动态效果状态合同。

覆盖环境变量解析（含非法值告警回退）、运行时切换、QML Slot 入口、runtime 门面
与根包导出，以及单例构造时的默认值来源。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

import prismqml
from prismqml import register_types
from prismqml.python.core import theme as theme_module
from prismqml.python.core.theme import (
    REDUCE_MOTION_ENV,
    ThemeManager,
    is_reduce_motion,
    read_reduce_motion_env,
    set_reduce_motion,
)
from prismqml.python.runtime import appearance

ROOT = Path(__file__).resolve().parents[1]

SLOT_SCENE = """
import QtQuick
import PrismQML

Item {
    property bool flag: Enums.reduceMotion
    function enable() { ThemeManager.setReduceMotionFromQml(true) }
    function disable() { ThemeManager.setReduceMotionFromQml(false) }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


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



@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "Yes", "on", " ON "])
def test_reduce_motion_env_truthy_values_enable(raw):
    assert read_reduce_motion_env(raw) is True


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "off", " off "])
def test_reduce_motion_env_falsy_values_disable(raw):
    assert read_reduce_motion_env(raw) is False


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_reduce_motion_env_empty_uses_default(monkeypatch, raw):
    monkeypatch.delenv(REDUCE_MOTION_ENV, raising=False)
    assert read_reduce_motion_env(raw) is False


@pytest.mark.parametrize("raw", ["maybe", "2", "enabled", "dark"])
def test_reduce_motion_env_invalid_value_warns_and_falls_back(raw, monkeypatch):
    warnings = []
    monkeypatch.setattr(theme_module, "warning", warnings.append)

    assert read_reduce_motion_env(raw) is False
    assert len(warnings) == 1
    assert REDUCE_MOTION_ENV in warnings[0]
    assert repr(raw) in warnings[0]


def test_reduce_motion_env_default_is_read_at_construction(monkeypatch):
    monkeypatch.setenv(REDUCE_MOTION_ENV, "yes")
    original = ThemeManager._instance
    ThemeManager._instance = None
    try:
        manager = ThemeManager()
        assert manager.reduceMotion is True
        assert manager.property("reduceMotion") is True
    finally:
        ThemeManager._instance = original
    if original is not None:
        assert ThemeManager().reduceMotion is False


def test_reduce_motion_env_invalid_value_keeps_singleton_usable(monkeypatch):
    warnings = []
    monkeypatch.setattr(theme_module, "warning", warnings.append)
    monkeypatch.setenv(REDUCE_MOTION_ENV, "nonsense")
    original = ThemeManager._instance
    ThemeManager._instance = None
    try:
        manager = ThemeManager()
        assert manager.reduceMotion is False
        assert warnings
    finally:
        ThemeManager._instance = original


def test_runtime_toggle_emits_only_real_changes(qapp):
    del qapp
    manager = ThemeManager()
    set_reduce_motion(False)
    observed = []

    def record(value):
        observed.append(value)

    manager.reduceMotionChanged.connect(record)
    try:
        set_reduce_motion(True)
        set_reduce_motion(True)
        set_reduce_motion(False)
        assert observed == [True, False]
        assert is_reduce_motion() is False
        assert manager.get_reduce_motion() is False
    finally:
        manager.reduceMotionChanged.disconnect(record)
        set_reduce_motion(False)


def test_qml_slot_toggles_reduce_motion(qapp):
    del qapp
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    set_reduce_motion(False)
    try:
        component, instance = _create(engine, SLOT_SCENE, "w5-reduce-motion-slot")
        _pump()
        assert instance.property("flag") is False

        assert QMetaObject.invokeMethod(instance, "enable")
        _pump()
        assert ThemeManager().reduceMotion is True
        assert instance.property("flag") is True

        assert QMetaObject.invokeMethod(instance, "disable")
        _pump()
        assert ThemeManager().reduceMotion is False
        assert instance.property("flag") is False
    finally:
        set_reduce_motion(False)
        _dispose(engine, component, instance)


def test_public_facades_route_through_runtime_appearance():
    assert prismqml.set_reduce_motion is appearance.set_reduce_motion
    assert prismqml.is_reduce_motion is appearance.is_reduce_motion
    assert prismqml.get_accent_scale is appearance.get_accent_scale


def test_root_package_toggle_reaches_the_singleton(qapp):
    del qapp
    set_reduce_motion(False)
    try:
        prismqml.set_reduce_motion(True)
        assert prismqml.is_reduce_motion() is True
        assert ThemeManager().reduceMotion is True
    finally:
        prismqml.set_reduce_motion(False)
    assert prismqml.is_reduce_motion() is False
