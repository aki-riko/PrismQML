# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public register_types context contracts. 公开注册入口上下文合同。"""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QEventLoop,
    QTimer,
    QUrl,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml.python.config.config_manager import ConfigManager
from prismqml.python.core.shadow import getShadowManager
from prismqml.python.core.theme import getThemeManager
from prismqml.python.core.utils import qml_path, register_types
from prismqml.python.core.window_helper import get_window_helper
from prismqml.python.providers import clipboard as clipboard_module
from prismqml.python.providers.lazy_context import (
    LazyQRCodeGenerator,
    LazyScreenEyedropperManager,
)
from prismqml.python.window import (
    get_acrylic_helper,
    get_mica_manager,
    get_native_window_hook,
)


_PROBE_QML = b"""
import QtQuick
import PrismQML

QtObject {
    property int dpiFromSingleton: DpiManager.userDpiScale
    property int dpiDirect: ConfigManager.dpiScale
    property string clipboardName: ClipboardHelper.objectName
}
"""
_MISSING_CONTEXT_MARKERS = (
    "ReferenceError: ConfigManager is not defined",
    "ReferenceError: ClipboardHelper is not defined",
)
_QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
_OFFSCREEN_FONT_WARNING = "QFontDatabase: Cannot find font directory"


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_component(component):
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def _create_probe(engine):
    component = QQmlComponent(engine)
    component.setData(_PROBE_QML, QUrl("inline:register-types-context.qml"))
    _wait_component(component)
    probe = component.create(engine.rootContext())
    assert probe is not None, [error.toString() for error in component.errors()]
    return component, probe


def _prepare_context_dependencies(tmp_path):
    original_config = ConfigManager._instance
    original_clipboard = clipboard_module._clipboard_helper
    ConfigManager._instance = None
    clipboard_module._clipboard_helper = None
    manager = ConfigManager(str(tmp_path / "app.json"))
    manager.setDpiScale(125)
    clipboard = clipboard_module.get_clipboard_helper()
    return original_config, original_clipboard, manager, clipboard


def _expected_singletons(manager, clipboard):
    return {
        "ThemeManager": getThemeManager(),
        "ConfigManager": manager,
        "MicaManager": get_mica_manager(),
        "AcrylicHelper": get_acrylic_helper(),
        "NativeWindow": get_native_window_hook(),
        "ClipboardHelper": clipboard,
        "ShadowManager": getShadowManager(),
        "WindowHelper": get_window_helper(),
    }


def _dispose_registration(qapp, engines, components, probes):
    for probe in probes:
        if shiboken6.isValid(probe):
            probe.deleteLater()
    for component in components:
        if shiboken6.isValid(component):
            component.deleteLater()
    for engine in engines:
        engine.deleteLater()
    qapp.processEvents()


@pytest.fixture
def registered_context(qapp, tmp_path):
    state = _prepare_context_dependencies(tmp_path)
    original_config, original_clipboard, manager, clipboard = state
    engines = [QQmlApplicationEngine(), QQmlApplicationEngine()]
    components = []
    probes = []
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    try:
        for engine in engines:
            register_types(engine)
        component, probe = _create_probe(engines[0])
        components.append(component)
        probes.append(probe)
        yield manager, clipboard, engines, probe, messages
    finally:
        qInstallMessageHandler(previous_handler)
        _dispose_registration(qapp, engines, components, probes)
        assert shiboken6.isValid(manager)
        assert shiboken6.isValid(clipboard)
        ConfigManager._instance = original_config
        clipboard_module._clipboard_helper = original_clipboard


def test_register_types_injects_public_context_without_qml_warnings(
    registered_context,
):
    manager, clipboard, engines, probe, messages = registered_context
    for engine in engines:
        context = engine.rootContext()
        assert context.contextProperty("ConfigManager") is manager
        assert context.contextProperty("ClipboardHelper") is clipboard
    assert probe.property("dpiFromSingleton") == 125
    assert probe.property("dpiDirect") == 125
    assert probe.property("clipboardName") == ""
    failures = [
        message
        for mode, message in messages
        if mode in _QT_FAILURE_TYPES and _OFFSCREEN_FONT_WARNING not in message
    ]
    assert failures == []
    assert all(
        not any(marker in message for marker in _MISSING_CONTEXT_MARKERS)
        for _mode, message in messages
    )


def test_register_types_preserves_complete_engine_registration(registered_context):
    """Keep every public binding and lazy engine reference. 保留全部公开绑定与延迟引用。"""
    manager, clipboard, engines, _probe, _messages = registered_context
    expected_singletons = _expected_singletons(manager, clipboard)
    expected_import_path = qml_path().parent.resolve()

    for engine in engines:
        context = engine.rootContext()
        for name, expected in expected_singletons.items():
            assert context.contextProperty(name) is expected

        lazy_objects = engine._prismqml_lazy_context_objects
        assert len(lazy_objects) == 2
        qrcode_generator, eyedropper_manager = lazy_objects
        assert isinstance(qrcode_generator, LazyQRCodeGenerator)
        assert isinstance(eyedropper_manager, LazyScreenEyedropperManager)
        assert qrcode_generator._engine is engine
        assert context.contextProperty("QRCodeGenerator") is qrcode_generator
        assert context.contextProperty("ScreenEyedropperManager") is eyedropper_manager
        assert engine.imageProvider("acrylic") is not None
        assert expected_import_path in map(Path, engine.importPathList())
