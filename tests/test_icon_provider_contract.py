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
ROOT = Path(__file__).resolve().parents[1]
VALID_ICON = "Add"
INVALID_ICON = "MissingProviderContractIcon"
PROBE_SOURCE = """import QtQuick
QtObject {
    property string validPath: Icon.getPath("Add")
    property bool validIcon: Icon.isValid("Add")
    property bool invalidIcon: Icon.isValid("MissingProviderContractIcon")
}
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


def test_python_provider_matches_minimal_cpp_surface():
    provider = get_icon_provider()
    valid_path = Path(provider.getPath(VALID_ICON))

    assert valid_path.name == "Add.svg"
    assert valid_path.is_file()
    assert provider.isValid(VALID_ICON)
    assert not provider.isValid(INVALID_ICON)
    removed_surface = (
        "get",
        "getAll",
        "getAllNames",
        "count",
        "isCustomIcon",
        "register_custom_icon",
        "register_custom_icons",
    )
    for removed in removed_surface:
        assert not hasattr(provider, removed)
    assert not hasattr(provider, "ADD")


def test_explicit_qml_provider_registration_exposes_minimal_surface(qapp):
    keep = _create_probe()
    probe = keep[-1]

    assert probe is not None
    assert Path(probe.property("validPath")).name == "Add.svg"
    assert probe.property("validIcon") is True
    assert probe.property("invalidIcon") is False


def test_explicit_registration_reuses_process_singleton(qapp):
    first = QQmlEngine()
    second = QQmlEngine()
    register_icon_provider(first)
    register_icon_provider(second)
    provider = get_icon_provider()

    assert first.rootContext().contextProperty("Icon") is provider
    assert second.rootContext().contextProperty("Icon") is provider
