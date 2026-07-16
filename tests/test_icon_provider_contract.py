# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""IconProvider before contracts. IconProvider 收窄前行为合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml.python.core.icon_provider import (
    get_icon_provider,
    register_icon_provider,
)
from prismqml.python.core.icons import Icon


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_NAME = "ContractCustom"
CUSTOM_PATH = "qrc:/contract/custom.svg"
PROBE_SOURCE = f"""import QtQuick
QtObject {{
    property string enumValue: Icon.get("ADD")
    property string customPath: Icon.getPath("{CUSTOM_NAME}")
    property bool customValid: Icon.isCustomIcon("{CUSTOM_NAME}")
    property int iconCount: Icon.count()
}}
"""


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_probe() -> tuple[QQmlEngine, QQmlComponent, object]:
    engine = QQmlEngine()
    register_icon_provider(engine)
    component = QQmlComponent(engine)
    component.setData(PROBE_SOURCE.encode("utf-8"), QUrl("inline:icon-provider.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert not component.isError(), [error.toString() for error in component.errors()]
    return engine, component, component.create()


def test_python_provider_exposes_enum_and_custom_icon_surfaces():
    provider = get_icon_provider()
    provider._custom_paths.clear()
    provider.register_custom_icon(CUSTOM_NAME, CUSTOM_PATH)

    assert provider.get("ADD") == "Add"
    assert provider.get("add") == "Add"
    assert provider.getAll() == [icon.value for icon in Icon]
    assert provider.getAllNames() == [icon.name for icon in Icon]
    assert provider.count() == len(Icon)
    assert provider.getPath(CUSTOM_NAME) == CUSTOM_PATH
    assert provider.isCustomIcon(CUSTOM_NAME)


def test_explicit_qml_provider_registration_exposes_current_surface(qapp):
    provider = get_icon_provider()
    provider._custom_paths.clear()
    provider.register_custom_icon(CUSTOM_NAME, CUSTOM_PATH)
    keep = _create_probe()
    probe = keep[-1]

    assert probe is not None
    assert probe.property("enumValue") == "Add"
    assert probe.property("customPath") == CUSTOM_PATH
    assert probe.property("customValid") is True
    assert probe.property("iconCount") == len(Icon)
