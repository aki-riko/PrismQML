# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Physical-pixel border regressions. 物理像素描边回归。"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TEST_PROCESS = ROOT / "scripts" / "test_process.py"
PHYSICAL_BORDER_PROBE = r'''
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QApplication

from examples.resources import register_gallery_resources
from prismqml import Skin, Theme, register_types, setSkin, setTheme


root = Path.cwd()
app = QApplication([])
setTheme(Theme.LIGHT)
setSkin(Skin.VINTAGE_TICKET)
assert register_gallery_resources()
engine = QQmlApplicationEngine()
engine.addImportPath(str(root / "prismqml"))
register_types(engine)
warnings = []
engine.warnings.connect(
    lambda errors: warnings.extend(error.toString() for error in errors)
)
component = QQmlComponent(
    engine,
    QUrl.fromLocalFile(str(root / "examples" / "pages" / "InputPage.qml")),
)
assert component.status() == QQmlComponent.Status.Ready, [
    error.toString() for error in component.errors()
]
page = component.create(engine.rootContext())
assert isinstance(page, QQuickItem), [error.toString() for error in component.errors()]
page.setWidth(1132)
page.setHeight(800)

loop = QEventLoop()


def pump(milliseconds=30):
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def physically_integral(value, ratio):
    physical = float(value) * ratio
    return abs(physical - round(physical)) < 0.000001


pump(500)
ratio = float(app.primaryScreen().devicePixelRatio())
assert ratio == 1.5, ratio

separators = [
    item
    for item in page.findChildren(QQuickItem)
    if item.metaObject().className().startswith("Separator_QMLTYPE")
]
line_edits = [
    item
    for item in page.findChildren(QQuickItem)
    if item.metaObject().className().startswith("LineEditCore_QMLTYPE")
]
assert separators
assert line_edits

for skin in (Skin.FLUENT, Skin.NEOBRUTALISM, Skin.VINTAGE_TICKET):
    setSkin(skin)
    pump(50)
    separator_widths = [float(item.property("lineWidth")) for item in separators]
    line_edit_widths = [
        float(QQmlProperty(item, "border.width", engine).read())
        for item in line_edits
    ]
    assert all(physically_integral(width, ratio) for width in separator_widths), (
        skin,
        ratio,
        separator_widths,
    )
    assert all(physically_integral(width, ratio) for width in line_edit_widths), (
        skin,
        ratio,
        line_edit_widths,
    )
assert warnings == [], warnings
print(
    "PHYSICAL_BORDER_PIXELS_OK",
    ratio,
    len(separators),
    len(line_edits),
)
page.deleteLater()
component.deleteLater()
engine.deleteLater()
app.processEvents()
'''


def test_input_gallery_borders_use_integer_physical_pixels_at_150_percent():
    """Existing InputPage borders avoid fractional physical widths at 150%.

    现有 InputPage 描边在 150% 缩放下不得使用分数物理像素。
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
            PHYSICAL_BORDER_PROBE,
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
    assert "PHYSICAL_BORDER_PIXELS_OK" in output
    if sys.platform == "win32":
        assert "visible_windows=0 / job_active_processes=0" in output
