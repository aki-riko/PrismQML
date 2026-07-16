# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public generated icon behavior contracts. 生成图标的公开行为合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import getThemeManager
from prismqml.python.core.icons import Icon


ROOT = Path(__file__).resolve().parents[1]


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_icon_probe() -> tuple[QQmlEngine, QQmlComponent, object]:
    source = """import QtQuick
import PrismQML
QtObject {
    property string addValue: Enums.icon.add
    property string addPath: Enums.icon.path(Enums.icon.add)
    property string addMapped: Enums.icon.iconList.ADD
    property int iconCount: Object.keys(Enums.icon.iconList).length
}
"""
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    engine.rootContext().setContextProperty("ThemeManager", getThemeManager())
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl("inline:icon-contract.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert not component.isError(), [error.toString() for error in component.errors()]
    return engine, component, component.create()


def test_python_icon_enum_keeps_public_helpers(qapp):
    assert str(Icon.ADD) == "Add"
    assert Icon.get_all() == [icon.value for icon in Icon]
    assert Icon.get_all_enum_names() == [icon.name for icon in Icon]
    assert Path(Icon.ADD.path()).is_file()
    assert not Icon.ADD.to_qicon().isNull()
    assert not Icon.ADD.to_qicon("#123456").isNull()


def test_qml_icon_singleton_matches_python_registry(qapp):
    keep = _create_icon_probe()
    probe = keep[-1]
    assert probe is not None
    assert probe.property("addValue") == "Add"
    assert probe.property("addPath") == "fluent/Add.svg"
    assert probe.property("addMapped") == "Add"
    assert probe.property("iconCount") == len(Icon)
