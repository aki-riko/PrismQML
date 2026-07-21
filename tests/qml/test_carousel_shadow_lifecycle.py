# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Carousel shadow fallback lifecycle regressions. 轮播阴影兜底生命周期回归。"""

import re
import subprocess
import sys
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_TEST_PROCESS_RUNNER = _ROOT / "scripts/test_process.py"
_PROCESS_EXIT_PROBE = r"""
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent

from prismqml import App


app = App([])
component = QQmlComponent(app._engine)
component.setData(
    b'''import QtQuick
import PrismQML

Item {
    Carousel {
        objectName: "carousel"
        width: 320
        height: 180
        model: []
        shadowLevel: Enums.shadow.level8
        showIndicator: false
        showNavButtons: false
    }
}
''',
    QUrl("carousel-level8-process-exit.qml"),
)
assert component.status() == QQmlComponent.Status.Ready, [
    error.toString() for error in component.errors()
]
root = component.create(app._engine.rootContext())
assert root is not None, [error.toString() for error in component.errors()]
carousel = root.findChild(QObject, "carousel")
assert carousel is not None
shadows = [
    item
    for item in carousel.findChildren(QObject)
    if item.parent() is carousel
    if "RectangularShadow" in item.metaObject().className()
]
assert len(shadows) == 1, [item.metaObject().className() for item in shadows]
assert QColor(shadows[0].property("color")).alpha() > 0
"""


def test_carousel_level8_shadow_process_exit_has_no_teardown_warning():
    """Natural exit must not read an expired shadow token. 正常退出不得读取失效阴影 token。"""
    result = subprocess.run(
        [
            sys.executable,
            str(_TEST_PROCESS_RUNNER),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "60",
            "--",
            sys.executable,
            "-X",
            "utf8",
            "-c",
            _PROCESS_EXIT_PROBE,
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, output
    assert "Unable to assign [undefined] to QColor" not in output
    assert not re.search(
        r"Carousel\.qml:\d+:\d+:\s+\[QtContext\]",
        output,
    ), output
