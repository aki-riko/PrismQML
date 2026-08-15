# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery WindowType runtime selection baseline. Gallery 窗口类型运行时选择基线。"""

from __future__ import annotations

from pathlib import Path
import re

import pytest
from PySide6.QtCore import Property, QObject, QUrl, Signal
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
import prismqml.python.config as config_module


ROOT = Path(__file__).resolve().parents[2]
GALLERY_QML = ROOT / "examples" / "main.qml"
WINDOW_TYPES = (
    (0, "WindowsSplit"),
    (1, "WindowsBar"),
    (2, "WindowsFilled"),
)


class _GalleryConfig(QObject):
    windowTypeChanged = Signal()

    def __init__(self, window_type: int) -> None:
        super().__init__()
        self._window_type = window_type

    def _bind_appearance_runtime(self, _callback) -> None:
        pass

    @Property(int, notify=windowTypeChanged)
    def windowType(self) -> int:
        return self._window_type

    @Property(bool, constant=True)
    def dwmShadow(self) -> bool:
        return False

    @Property(bool, constant=True)
    def micaEnabled(self) -> bool:
        return False

    @Property(bool, constant=True)
    def lazyLoading(self) -> bool:
        return True


def _normalized_type(obj: QObject) -> str:
    name = obj.metaObject().className()
    name = re.sub(r"_QMLTYPE_\d+", "", name)
    return re.sub(r"_QML_\d+", "", name)


def _create_gallery():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(GALLERY_QML)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root


def _destroy_gallery(engine, component, root, qapp) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    qapp.processEvents()


@pytest.mark.parametrize(("window_type", "expected_type"), WINDOW_TYPES)
def test_gallery_creates_only_configured_window_type(
    qapp, monkeypatch, window_type: int, expected_type: str
) -> None:
    manager = _GalleryConfig(window_type)
    monkeypatch.setattr(config_module, "getConfigManager", lambda: manager)
    engine, component, root = _create_gallery()
    try:
        window = root.property("windowInstance")
        assert window is not None
        assert _normalized_type(window) == expected_type
        assert window.property("lazyLoading") is True
        assert window.property("micaEnabled") is False
    finally:
        _destroy_gallery(engine, component, root, qapp)
