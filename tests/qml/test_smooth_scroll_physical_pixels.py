# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Smooth-scroll physical pixel regressions. 平滑滚动物理像素回归。"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TEST_PROCESS = ROOT / "scripts" / "test_process.py"
PHYSICAL_PIXEL_PROBE = r'''
from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWidgets import QApplication

from prismqml import Skin, register_types, setSkin


root = Path.cwd()
app = QApplication([])
engine = QQmlApplicationEngine()
warnings = []
engine.warnings.connect(
    lambda errors: warnings.extend(error.toString() for error in errors)
)
engine.addImportPath(str(root / "prismqml"))
register_types(engine)
component = QQmlComponent(engine)
component.setData(
    b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "." as Internal

Window {
    id: root

    readonly property real verticalPosition: verticalFlick.contentY
    readonly property real horizontalPosition: horizontalFlick.contentX
    readonly property real verticalMaximum:
        verticalFlick.originY + verticalFlick.contentHeight - verticalFlick.height
    readonly property real horizontalMaximum:
        horizontalFlick.originX + horizontalFlick.contentWidth - horizontalFlick.width

    function resetBoth() {
        verticalFlick.contentY = verticalFlick.originY
        verticalHelper.syncPosition()
        horizontalFlick.contentX = horizontalFlick.originX
        horizontalHelper.syncPosition()
    }

    function scrollBoth() {
        verticalHelper.scrollTo(180)
        horizontalHelper.scrollTo(260)
    }

    function overshootBoth() {
        verticalHelper.scrollToEnd()
        horizontalHelper.scrollToEnd()
        verticalHelper.scrollBy(1000)
        horizontalHelper.scrollBy(1000)
    }

    width: 520
    height: 220
    visible: true

    Flickable {
        id: verticalFlick
        objectName: "verticalFlick"
        x: 20
        y: 20
        width: 180
        height: 160
        contentWidth: width
        contentHeight: 640
        interactive: false
        clip: true

        Rectangle {
            width: verticalFlick.width
            height: verticalFlick.contentHeight
            color: Enums.accentColor
        }
    }

    Internal.SmoothScrollHelper {
        id: verticalHelper
        target: verticalFlick
        orientation: Qt.Vertical
        duration: 160
    }

    Flickable {
        id: horizontalFlick
        objectName: "horizontalFlick"
        x: 240
        y: 20
        width: 240
        height: 160
        contentWidth: 760
        contentHeight: height
        interactive: false
        clip: true

        Rectangle {
            width: horizontalFlick.contentWidth
            height: horizontalFlick.height
            color: Enums.accentColor
        }
    }

    Internal.SmoothScrollHelper {
        id: horizontalHelper
        target: horizontalFlick
        orientation: Qt.Horizontal
        duration: 160
    }
}
""",
    QUrl.fromLocalFile(
        str(
            root
            / "prismqml"
            / "PrismQML"
            / "controls"
            / "containers"
            / "ScrollBar"
            / "physical-pixel-probe.qml"
        )
    ),
)
assert component.status() == QQmlComponent.Status.Ready, [
    error.toString() for error in component.errors()
]
window = component.create(engine.rootContext())
assert isinstance(window, QQuickWindow), [
    error.toString() for error in component.errors()
]
vertical = window.findChild(QQuickItem, "verticalFlick")
horizontal = window.findChild(QQuickItem, "horizontalFlick")
assert vertical is not None
assert horizontal is not None

loop = QEventLoop()


def pump(milliseconds):
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def is_physically_aligned(value, ratio):
    return abs(value * ratio - round(value * ratio)) < 0.000001


pump(100)
ratio = float(window.devicePixelRatio())
assert ratio == 1.5, ratio
vertical_values = []
horizontal_values = []
vertical.contentYChanged.connect(
    lambda: vertical_values.append(float(vertical.property("contentY")))
)
horizontal.contentXChanged.connect(
    lambda: horizontal_values.append(float(horizontal.property("contentX")))
)

for skin in (Skin.FLUENT, Skin.NEOBRUTALISM, Skin.VINTAGE_TICKET):
    setSkin(skin)
    pump(40)
    assert QMetaObject.invokeMethod(window, "resetBoth")
    pump(40)
    vertical_values.clear()
    horizontal_values.clear()
    assert QMetaObject.invokeMethod(window, "scrollBoth")
    pump(320)
    assert len(vertical_values) >= 2, (skin, vertical_values)
    assert len(horizontal_values) >= 2, (skin, horizontal_values)
    assert all(is_physically_aligned(value, ratio) for value in vertical_values), (
        skin,
        vertical_values,
    )
    assert all(is_physically_aligned(value, ratio) for value in horizontal_values), (
        skin,
        horizontal_values,
    )
    assert window.property("verticalPosition") == 180
    assert window.property("horizontalPosition") == 260

vertical_values.clear()
horizontal_values.clear()
assert QMetaObject.invokeMethod(window, "overshootBoth")
pump(900)
assert vertical_values
assert horizontal_values
assert all(is_physically_aligned(value, ratio) for value in vertical_values)
assert all(is_physically_aligned(value, ratio) for value in horizontal_values)
assert window.property("verticalPosition") == window.property("verticalMaximum")
assert window.property("horizontalPosition") == window.property("horizontalMaximum")
assert warnings == [], warnings
print(
    "SMOOTH_SCROLL_PHYSICAL_PIXELS_OK",
    ratio,
    len(vertical_values),
    len(horizontal_values),
)
window.close()
window.deleteLater()
component.deleteLater()
engine.deleteLater()
app.processEvents()
'''


def test_smooth_scroll_publishes_physical_pixels_for_every_skin():
    """Animated positions stay on physical pixels at 150% DPI.

    150% DPI 动画坐标保持物理像素对齐。
    """
    environment = os.environ.copy()
    environment["QT_SCALE_FACTOR"] = "1.5"
    result = subprocess.run(
        [
            sys.executable,
            str(TEST_PROCESS),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "60",
            "--",
            sys.executable,
            "-X",
            "utf8",
            "-c",
            PHYSICAL_PIXEL_PROBE,
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, output
    assert "SMOOTH_SCROLL_PHYSICAL_PIXELS_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
