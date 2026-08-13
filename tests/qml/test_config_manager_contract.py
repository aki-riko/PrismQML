# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""真实 QML 元对象边界下的 ConfigManager 离散值合同。"""

import json

import pytest

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

from prismqml.python.config.config_manager import ConfigManager


_BRIDGE_QML = b"""
import QtQml
QtObject {
    function setDpi(value) { ConfigManager.setDpiScale(value) }
    function setWindow(value) { ConfigManager.setWindowType(value) }
}
"""


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


@pytest.fixture
def qml_config_bridge(qapp, tmp_path):
    original = ConfigManager._instance
    ConfigManager._instance = None
    manager = ConfigManager(str(tmp_path / "app.json"))
    engine = QQmlEngine()
    bridge = None
    try:
        engine.rootContext().setContextProperty("ConfigManager", manager)
        component = QQmlComponent(engine)
        component.setData(_BRIDGE_QML, QUrl("inline:config-manager-contract.qml"))
        for _ in range(50):
            if component.status() != QQmlComponent.Status.Loading:
                break
            _pump()
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        bridge = component.create()
        assert bridge is not None, [error.toString() for error in component.errors()]
        yield manager, bridge, tmp_path / "app.json"
    finally:
        if bridge is not None:
            bridge.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
        ConfigManager._instance = original


def _evaluate(bridge, source):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(bridge), bridge, source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        if is_undefined:
            return None
    return result.toVariant() if hasattr(result, "toVariant") else result


def _spy_persistence(manager, monkeypatch):
    calls = []
    original = manager.cfg._write_mapping_file

    def persist(file_path, mapping):
        calls.append(mapping)
        return original(file_path, mapping)

    monkeypatch.setattr(manager.cfg, "_write_mapping_file", persist)
    return calls


def _wait_persistence(manager):
    assert manager.waitForPersistence(5000)


def test_qml_reads_exact_runtime_options(qml_config_bridge):
    _manager, bridge, _path = qml_config_bridge

    assert _evaluate(bridge, "ConfigManager.dpiScaleOptions") == [
        0,
        100,
        125,
        150,
        175,
        200,
    ]
    assert _evaluate(bridge, "ConfigManager.windowTypeOptions") == [0, 1, 2]


@pytest.mark.parametrize(
    "expression",
    [
        "setDpi(true)",
        "setDpi(125.75)",
        "setDpi(String(100))",
        "setDpi([175])",
        "setDpi(NaN)",
        "setDpi(Infinity)",
    ],
)
def test_qml_dpi_setter_rejects_values_before_numeric_conversion(
    qml_config_bridge, monkeypatch, expression
):
    manager, bridge, path = qml_config_bridge
    manager.setDpiScale(150)
    _wait_persistence(manager)
    baseline = path.read_bytes()
    persist_calls = _spy_persistence(manager, monkeypatch)
    dpi_changes = []
    config_changes = []
    manager.dpiScaleChanged.connect(lambda: dpi_changes.append(True))
    manager.configChanged.connect(lambda: config_changes.append(True))

    _evaluate(bridge, expression)

    assert manager.dpiScale == 150
    assert path.read_bytes() == baseline
    assert persist_calls == []
    assert dpi_changes == []
    assert config_changes == []


@pytest.mark.parametrize(
    "expression",
    [
        "setWindow(true)",
        "setWindow(1.75)",
        "setWindow(String(0))",
        "setWindow([1])",
        "setWindow(3)",
        "setWindow(NaN)",
        "setWindow(Infinity)",
    ],
)
def test_qml_window_type_setter_rejects_non_contract_values(
    qml_config_bridge, monkeypatch, expression
):
    manager, bridge, path = qml_config_bridge
    manager.setWindowType(2)
    _wait_persistence(manager)
    baseline = path.read_bytes()
    persist_calls = _spy_persistence(manager, monkeypatch)
    window_changes = []
    config_changes = []
    manager.windowTypeChanged.connect(lambda: window_changes.append(True))
    manager.configChanged.connect(lambda: config_changes.append(True))

    _evaluate(bridge, expression)

    assert manager.windowType == 2
    assert path.read_bytes() == baseline
    assert persist_calls == []
    assert window_changes == []
    assert config_changes == []


@pytest.mark.parametrize("scale", [0, 100, 125, 150, 175, 200])
def test_qml_legal_dpi_candidates_commit_once(qml_config_bridge, scale):
    manager, bridge, path = qml_config_bridge
    baseline = 100 if scale != 100 else 125
    manager.setDpiScale(baseline)
    _wait_persistence(manager)
    dpi_changes = []
    config_changes = []
    manager.dpiScaleChanged.connect(lambda: dpi_changes.append(True))
    manager.configChanged.connect(lambda: config_changes.append(True))

    _evaluate(bridge, f"setDpi({scale})")
    _wait_persistence(manager)

    assert manager.dpiScale == scale
    assert json.loads(path.read_text(encoding="utf-8"))["Window"]["DpiScale"] == scale
    assert dpi_changes == [True]
    assert config_changes == [True]


@pytest.mark.parametrize("window_type", [0, 1, 2])
def test_qml_legal_window_types_commit_once(qml_config_bridge, window_type):
    manager, bridge, path = qml_config_bridge
    baseline = (window_type + 1) % 3
    manager.setWindowType(baseline)
    _wait_persistence(manager)
    window_changes = []
    config_changes = []
    manager.windowTypeChanged.connect(lambda: window_changes.append(True))
    manager.configChanged.connect(lambda: config_changes.append(True))

    _evaluate(bridge, f"setWindow({window_type})")
    _wait_persistence(manager)

    assert manager.windowType == window_type
    assert json.loads(path.read_text(encoding="utf-8"))["Window"][
        "WindowType"
    ] == window_type
    assert window_changes == [True]
    assert config_changes == [True]
