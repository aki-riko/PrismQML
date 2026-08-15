# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Regression: pure QML Fluent.Windows must show after create()."""

import sys
import time
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from prismqml import register_types  # noqa: E402


def pump(ms: int):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def wait_until(predicate, timeout_ms: int) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        pump(10)
    return bool(predicate())


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    register_types(engine)

    qml = """
import QtQuick
import PrismQML as Fluent

Fluent.Windows {
    width: 640
    height: 420
    windowTitle: "visible regression"
    lazyLoading: true
    navigationItems: []
    bottomNavigationItems: []
}
"""

    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
    for _ in range(60):
        if comp.status() != QQmlComponent.Status.Loading:
            break
        pump(50)

    if comp.isError():
        for err in comp.errors():
            print(err.toString(), file=sys.stderr)
        return 1

    win = comp.create()
    if win is None:
        for err in comp.errors():
            print(err.toString(), file=sys.stderr)
        return 1

    wait_until(
        lambda: bool(win.property("visible"))
        and float(win.property("opacity")) >= 0.99,
        1000,
    )
    visible = bool(win.property("visible"))
    opacity = float(win.property("opacity"))
    win.close()
    app.processEvents()

    if not visible:
        print("Fluent.Windows created from QML should be visible by default", file=sys.stderr)
        return 1
    if opacity < 0.99:
        print(f"Fluent.Windows should restore opacity, got {opacity}", file=sys.stderr)
        return 1

    print("WINDOW_DEFAULT_VISIBLE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
