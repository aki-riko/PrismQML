# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery WindowType runtime selection baseline. Gallery 窗口类型运行时选择基线。"""

from __future__ import annotations

from pathlib import Path
import re

import pytest
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
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
    lazyLoadingStyleChanged = Signal()

    def __init__(self, window_type: int, lazy_loading_style: int = 0) -> None:
        super().__init__()
        self._window_type = window_type
        self._lazy_loading_style = lazy_loading_style

    def _bind_appearance_runtime(
        self, _callback, *, apply_persisted: bool = True
    ) -> None:
        pass

    @Property(bool, constant=True)
    def appearancePersistenceEnabled(self) -> bool:
        return True

    @Property(int, notify=windowTypeChanged)
    def windowType(self) -> int:
        return self._window_type

    @Property(int, notify=lazyLoadingStyleChanged)
    def lazyLoadingStyle(self) -> int:
        return self._lazy_loading_style

    @Slot(int)
    def setLazyLoadingStyle(self, value: int) -> None:
        if value == self._lazy_loading_style:
            return
        self._lazy_loading_style = value
        self.lazyLoadingStyleChanged.emit()


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


def _create_gallery(config_path: Path):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(
        engine,
        config_path=config_path,
        persist_appearance=True,
    )
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
    qapp, monkeypatch, tmp_path, window_type: int, expected_type: str
) -> None:
    manager = _GalleryConfig(window_type)
    monkeypatch.setattr(
        config_module, "getConfigManager", lambda *_args, **_kwargs: manager
    )
    engine, component, root = _create_gallery(tmp_path / "gallery.json")
    try:
        window = root.property("windowInstance")
        assert window is not None
        assert _normalized_type(window) == expected_type
        assert window.property("lazyLoading") is True
        assert window.property("micaEnabled") is False
    finally:
        _destroy_gallery(engine, component, root, qapp)


@pytest.mark.parametrize("style", (0, 1))
def test_gallery_forwards_configured_lazy_loading_style_to_the_window(
    qapp, monkeypatch, tmp_path, style: int
) -> None:
    """The settings page value must reach the window and its page stack.

    设置页的取值必须到达窗口及其页面栈。

    LazyLoadingStyle was configurable and persisted while the Gallery window
    silently kept the ring default, because nothing forwarded it from the root
    to the window shells. This locks the whole forwarding chain: root ->
    window -> StackedWidget.
    展示形式此前可配置且已落盘, 但 Gallery 窗口一直静默保持环形默认值, 因为没有任何
    地方把它从根转发到窗口外壳。这里锁住整条转发链: 根 -> 窗口 -> StackedWidget。
    """
    manager = _GalleryConfig(1, lazy_loading_style=style)
    monkeypatch.setattr(
        config_module, "getConfigManager", lambda *_args, **_kwargs: manager
    )
    engine, component, root = _create_gallery(tmp_path / f"gallery-style-{style}.json")
    try:
        window = root.property("windowInstance")
        assert window is not None
        assert window.property("lazyLoadingStyle") == style

        # Non-zero styles must survive the second hop as well; the ring default
        # would hide a break in the page-stack binding.
        # 非零取值必须同样走通第二跳; 环形默认值会掩盖页面栈绑定的断裂。
        stack = None
        for _ in range(300):
            stack = window.property("stackedWidget")
            if stack is not None:
                break
            qapp.processEvents()
        assert stack is not None
        for _ in range(200):
            if stack.property("lazyLoadingStyle") == style:
                break
            qapp.processEvents()
        assert stack.property("lazyLoadingStyle") == style
    finally:
        _destroy_gallery(engine, component, root, qapp)


def test_gallery_applies_a_runtime_lazy_loading_style_switch(
    qapp, monkeypatch, tmp_path
) -> None:
    """Picking a style in the settings page must take effect without a restart.

    在设置页选择展示形式必须无需重启即可生效。

    The Gallery bound lazyLoadingStyle to a startup snapshot, so a runtime switch
    changed the config and nothing else. The binding must stay live.
    Gallery 曾把 lazyLoadingStyle 绑定到启动快照, 因此运行时切换只改了配置, 别处不动。
    该绑定必须保持实时。
    """
    manager = _GalleryConfig(1, lazy_loading_style=0)
    monkeypatch.setattr(
        config_module, "getConfigManager", lambda *_args, **_kwargs: manager
    )
    engine, component, root = _create_gallery(tmp_path / "gallery-runtime-style.json")
    try:
        window = root.property("windowInstance")
        assert window.property("lazyLoadingStyle") == 0

        manager.setLazyLoadingStyle(1)
        for _ in range(200):
            if window.property("lazyLoadingStyle") == 1:
                break
            qapp.processEvents()

        assert window.property("lazyLoadingStyle") == 1

        # The window shell exposes its page stack asynchronously.
        # 窗口外壳异步暴露其页面栈。
        stack = None
        for _ in range(300):
            stack = window.property("stackedWidget")
            if stack is not None:
                break
            qapp.processEvents()
        assert stack is not None
        for _ in range(200):
            if stack.property("lazyLoadingStyle") == 1:
                break
            qapp.processEvents()
        assert stack.property("lazyLoadingStyle") == 1
    finally:
        _destroy_gallery(engine, component, root, qapp)
