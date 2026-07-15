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
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Property, QUrl
from PySide6.QtWidgets import QApplication


class _UnavailableMicaManager(QObject):
    @Property(bool, constant=True)
    def isMicaSupported(self):
        return False


def _isolated_window_class(window_class, temp_dir, prefix):
    class IsolatedWindow(window_class):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-windows"
        _GENERATED_SPLASH_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-splash"

    return IsolatedWindow


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def _generated_source(window_class):
    files = sorted(window_class._GENERATED_QML_CACHE_DIR.glob("window_*.qml"))
    assert len(files) == 1
    return files[0].read_text(encoding="utf-8")


def _configure_rich_window(window, temp_dir):
    bottom_icon = Path(temp_dir) / "tool.svg"
    window.setSplashEnabled(False)
    window.setWindowTitle('Title "quoted" {brace}\nline')
    window.resize(1111, 777)
    window.setWindowIcon(":/icons/app.svg", colored=False)
    window.setMicaEffectEnabled(False)
    window.addPage(None, "Home", 'Top "one"')
    window.addPage(
        None, str(bottom_icon), "Bottom", position="bottom", selectable=False
    )


def _assert_rich_source(source, temp_dir):
    bottom_icon = QUrl.fromLocalFile(str(Path(temp_dir) / "tool.svg")).toString()
    assert '\nWindowsBar {\n' in source
    assert 'width: 1111\n    height: 777' in source
    assert 'windowTitle: "Title \\"quoted\\" \\u007Bbrace\\u007D\\nline"' in source
    assert 'windowIcon: "qrc:/icons/app.svg"' in source
    assert 'windowIconColored: false' in source
    assert 'micaEnabled: false' in source
    assert '"text": "Top \\"one\\""' in source
    assert '"key": "page_1", "selectable": false' in source
    assert f'"icon": "{bottom_icon}"' in source
    assert "userCard" not in source
    assert "userCardPosition" not in source
    assert source.count('objectName: "page_') == 2


def _assert_rich_root(window):
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
    assert window._pending_props == {}


def _exercise_rich_bar(window_class, temp_dir, window_type):
    window = window_class(window_type=window_type)
    _configure_rich_window(window, temp_dir)
    try:
        window.show()
        QApplication.processEvents()
        _assert_rich_source(_generated_source(window_class), temp_dir)
        _assert_rich_root(window)
    finally:
        _dispose_window(window)


def _exercise_window_type(window, window_class, component):
    window.setSplashEnabled(False)
    window.setMicaEffectEnabled(False)
    window.addPage(None, "Home", "Home")
    try:
        window.show()
        QApplication.processEvents()
        source = _generated_source(window_class)
        assert f"\n{component} {{\n" in source
        assert "micaEnabled: false" in source
        assert component in window._window.metaObject().className()
        assert window._window.property("micaEnabled") is False
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
