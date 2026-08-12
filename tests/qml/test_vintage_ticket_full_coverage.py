# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket full component coverage gate. 复古票据全组件覆盖门禁。"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
QMLDIR = ROOT / "prismqml" / "PrismQML" / "qmldir"
RUNNER = ROOT / "scripts" / "test_process.py"
PROBE = ROOT / "tests" / "qml" / "probe_all_components.py"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "vintage-ticket-global-contract.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/effects" as Effects

Item {
    id: root

    readonly property real radiusMicro: Enums.radius.micro
    readonly property real radiusTiny: Enums.radius.tiny
    readonly property real radiusSmall: Enums.radius.small
    readonly property real radiusCard: Enums.radius.card
    readonly property real radiusMedium: Enums.radius.medium
    readonly property real radiusLarge: Enums.radius.large
    readonly property real radiusDialog: Enums.radius.dialog
    readonly property real radiusXLarge: Enums.radius.xlarge
    readonly property bool softShadowVisible: softSurface.shadowItem.visible
    readonly property bool effectShadowEnabled: softEffect.shadowEnabled
    readonly property bool neoShadowVisible: neoShadow.visible
    readonly property color scrollTrackColor: Enums.stateColor.scrollTrack
    readonly property color scrollThumbColor: Enums.stateColor.scrollThumb
    readonly property color listHoverColor: Enums.stateColor.listItemHover
    readonly property color segmentedBorderColor: Enums.stateColor.segmentedBorder
    readonly property color skeletonBaseColor: Enums.stateColor.skeletonBase
    readonly property color codeBlockBackground: Enums.codeBlockColors.background
    readonly property color chartGridColor: Enums.chartColors.gridLine
    readonly property color calendarRangeColor: Enums.isDark
        ? Enums.calendarColors.rangeBarDark : Enums.calendarColors.rangeBarLight

    Rectangle { id: target; width: 100; height: 60 }

    ShadowedRectangle {
        id: softSurface
        width: 100
        height: 60
        shadowVisible: true
    }

    Shadow { id: softEffect }
    Effects.NeoShadow { id: neoShadow; target: target }
}
"""


def _registered_type_count() -> int:
    pattern = re.compile(r"^(?:singleton\s+)?[A-Z]\w*\s+\S+\.qml$")
    return sum(
        bool(pattern.match(line.strip()))
        for line in QMLDIR.read_text(encoding="utf-8").splitlines()
    )


def _pump() -> None:
    loop = QEventLoop()
    QTimer.singleShot(0, loop.quit)
    loop.exec()


def _wait_for_component(component: QQmlComponent) -> None:
    if component.status() != QQmlComponent.Status.Loading:
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    component.statusChanged.connect(loop.quit)
    timer.start(10_000)
    while component.status() == QQmlComponent.Status.Loading and timer.isActive():
        loop.exec()


def _assert_color(root, property_name: str, expected: str) -> None:
    assert root.property(property_name) == QColor(expected)


@pytest.mark.parametrize("theme_name", ("light", "dark"))
def test_every_registered_component_creates_in_ticket_skin(theme_name):
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "180",
            "--",
            sys.executable,
            str(PROBE),
            "--skin",
            "vintage_ticket",
            "--theme",
            theme_name,
            "--full-required",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=210,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    summary = re.search(
        r"组件加载 probe 结果:\s+(\d+) OK / (\d+) 错误 / "
        r"(\d+) 跳过 .*\(共 (\d+)\)",
        output,
    )
    assert summary is not None, output
    ok, errors, skipped, total = map(int, summary.groups())
    registered = _registered_type_count()
    assert (ok, errors, skipped, total) == (registered, 0, 0, registered)


def test_ticket_global_surface_contract_preserves_other_skins(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    _wait_for_component(component)

    try:
        setSkin(Skin.VINTAGE_TICKET)
        setTheme(Theme.LIGHT)
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump()

        for property_name in (
            "radiusMicro",
            "radiusTiny",
            "radiusSmall",
            "radiusCard",
            "radiusMedium",
            "radiusLarge",
            "radiusDialog",
            "radiusXLarge",
        ):
            assert root.property(property_name) == pytest.approx(0)
        assert root.property("softShadowVisible") is False
        assert root.property("effectShadowEnabled") is False
        assert root.property("neoShadowVisible") is True
        _assert_color(root, "scrollTrackColor", "#eee6d8")
        _assert_color(root, "scrollThumbColor", "#b8aa96")
        _assert_color(root, "listHoverColor", "#eee6d8")
        _assert_color(root, "segmentedBorderColor", "#5a4637")
        _assert_color(root, "skeletonBaseColor", "#eee6d8")
        _assert_color(root, "codeBlockBackground", "#eee6d8")
        _assert_color(root, "chartGridColor", "#b8aa96")
        _assert_color(root, "calendarRangeColor", "#eee6d8")

        setTheme(Theme.DARK)
        _pump()
        _assert_color(root, "scrollTrackColor", "#342e27")
        _assert_color(root, "scrollThumbColor", "#776a5b")
        _assert_color(root, "listHoverColor", "#342e27")
        _assert_color(root, "segmentedBorderColor", "#b4a48e")
        _assert_color(root, "skeletonBaseColor", "#342e27")
        _assert_color(root, "codeBlockBackground", "#342e27")
        _assert_color(root, "chartGridColor", "#776a5b")
        _assert_color(root, "calendarRangeColor", "#342e27")

        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        _pump()
        assert root.property("radiusSmall") == pytest.approx(4)
        assert root.property("radiusLarge") == pytest.approx(8)
        assert root.property("softShadowVisible") is True
        assert root.property("effectShadowEnabled") is True
        assert root.property("neoShadowVisible") is True

        setSkin(Skin.NEOBRUTALISM)
        _pump()
        assert root.property("radiusSmall") == pytest.approx(4)
        assert root.property("radiusLarge") == pytest.approx(8)
        assert root.property("softShadowVisible") is True
        assert root.property("effectShadowEnabled") is True
        assert root.property("neoShadowVisible") is True
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        if "root" in locals() and root is not None:
            root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()
