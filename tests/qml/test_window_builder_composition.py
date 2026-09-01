# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real generated-window composition regressions. 真实生成窗口组合回归。"""

import sys
import tempfile
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    Property,
    QTimer,
    QUrl,
)
from PySide6.QtWidgets import QApplication


class _UnavailableMicaManager(QObject):
    @Property(bool, constant=True)
    def isMicaSupported(self):
        return False


def _isolated_window_class(window_class, temp_dir, prefix):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-windows"

    return IsolatedWindow


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms=2400):
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _assert_static_root_used(window_class):
    files = sorted(window_class._GENERATED_QML_CACHE_DIR.glob("window_*.qml"))
    assert files == []


def _configure_rich_window(window, temp_dir):
    bottom_icon = Path(temp_dir) / "tool.svg"
    window.setSplashEnabled(False)
    window.setWindowTitle('Title "quoted" {brace}\nline')
    window.resize(1111, 777)
    window.setWindowIcon(":/icons/app.svg", colored=False)
    window.setMicaEffectEnabled(False)
    window.addPage(None, "Home", 'Top "one"')
    window.addPage(
        None, str(bottom_icon), "Bottom", position="bottom", selectable=True
    )


def _to_variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _visual_descendants(item):
    for child in item.childItems():
        yield child
        yield from _visual_descendants(child)


def _navigation_item_text(item):
    for property_name in ("text", "itemText"):
        if item.metaObject().indexOfProperty(property_name) >= 0:
            return item.property(property_name)
    return None


def _assert_rich_models(root, temp_dir):
    bottom_icon = QUrl.fromLocalFile(str(Path(temp_dir) / "tool.svg")).toString()
    navigation_items = _to_variant(root.property("navigationItems"))
    bottom_items = _to_variant(root.property("bottomNavigationItems"))
    assert len(navigation_items) == 1
    assert navigation_items[0]["text"] == 'Top "one"'
    assert navigation_items[0]["icon"].endswith("/Home.svg")
    assert navigation_items[0]["visible"] is True
    assert bottom_items == [
        {
            "text": "Bottom",
            "icon": bottom_icon,
            "key": "page_1",
            "selectable": True,
            "visible": True,
        }
    ]


def _assert_programmatic_bottom_navigation(window):
    root = window._window
    navigation = root.property("navigationView")
    assert navigation is not None

    window.setCurrentIndex(1)
    assert _wait_for(lambda: root.property("currentIndex") == 1)

    bottom_page_map = _to_variant(navigation.property("_bottomPageIndexMap"))
    assert bottom_page_map["page_1"] == 1
    if navigation.metaObject().indexOfProperty("_currentKey") >= 0:
        assert navigation.property("_currentKey") == "page_1"
    else:
        assert navigation.metaObject().indexOfProperty("_bottomItemActive") >= 0
        assert navigation.property("_bottomItemActive") is True

    bottom_delegates = [
        item
        for item in _visual_descendants(navigation)
        if item.metaObject().indexOfProperty("selected") >= 0
        and _navigation_item_text(item) == "Bottom"
    ]
    assert len(bottom_delegates) == 1
    assert bottom_delegates[0].property("selected") is True


def _assert_rich_root(window, temp_dir):
    root = window._window
    assert "WindowsBar" in root.metaObject().className()
    assert int(root.width()) == 1111
    assert int(root.height()) == 777
    assert root.property("windowTitle") == 'Title "quoted" {brace}\nline'
    assert root.property("windowIcon") == "qrc:/icons/app.svg"
    assert root.property("windowIconColored") is False
    assert root.property("micaEnabled") is False
    assert root.findChild(QObject, "page_0") is not None
    assert root.findChild(QObject, "page_1") is not None
    _assert_rich_models(root, temp_dir)
    assert window._pending_props == {}


def _assert_page_containers_attached(window, count):
    root = window._window
    assert _wait_for(lambda: root.property("stackedWidget") is not None)
    stack = root.property("stackedWidget")
    container = stack.property("containerItem")
    assert _wait_for(lambda: stack.property("count") == count)
    for index in range(count):
        page = root.findChild(QObject, f"page_{index}")
        assert page is not None
        assert page.parentItem() is container


def _exercise_rich_bar(window_class, temp_dir, window_type):
    window = window_class(window_type=window_type)
    _configure_rich_window(window, temp_dir)
    try:
        window.show()
        QApplication.processEvents()
        _assert_static_root_used(window_class)
        _assert_rich_root(window, temp_dir)
        _assert_page_containers_attached(window, 2)
        _assert_programmatic_bottom_navigation(window)
    finally:
        _dispose_window(window)


def _exercise_window_type(window, window_class, component):
    window.setSplashEnabled(False)
    window.setMicaEffectEnabled(False)
    window.addPage(None, "Home", "Home")
    window.addPage(None, "Settings", "Bottom", position="bottom", selectable=True)
    try:
        window.show()
        QApplication.processEvents()
        _assert_static_root_used(window_class)
        assert component in window._window.metaObject().className()
        assert window._window.property("micaEnabled") is False
        _assert_page_containers_attached(window, 2)
        _assert_programmatic_bottom_navigation(window)
    finally:
        _dispose_window(window)


def main():
    from prismqml import Window, WindowType
    from prismqml.python.window import mica_window

    app = QApplication.instance() or QApplication(sys.argv)
    mica_manager = _UnavailableMicaManager()
    mica_window.get_mica_manager = lambda: mica_manager
    with tempfile.TemporaryDirectory() as temp_dir:
        bar_class = _isolated_window_class(Window, temp_dir, "bar")
        _exercise_rich_bar(bar_class, temp_dir, WindowType.BAR)
        for prefix, window_type, component in (
            ("split", WindowType.SPLIT, "WindowsSplit"),
            ("filled", WindowType.FILLED, "WindowsFilled"),
        ):
            window_class = _isolated_window_class(Window, temp_dir, prefix)
            _exercise_window_type(window_class(window_type), window_class, component)
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
