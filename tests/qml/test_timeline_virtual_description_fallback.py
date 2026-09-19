# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under the MIT License.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline virtual description fallback regression. 虚拟时间线副标题回退回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
VIRTUAL_ROW_DIR = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "_internal"
).as_uri()
COMMIT_MESSAGE = "fix-binsi-platform-import-review"
COMMIT_DESCRIPTION = "5546a4c2 · aki-riko"
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent
import \"{VIRTUAL_ROW_DIR}\" as TimelineInternal

Window {{
    width: 480
    height: 300
    visible: true

    QtObject {{
        id: timelineControl
        property bool _graphMode: true
        property real _graphWidth: Fluent.Enums.spacing.timelineGraphPadding * 2
            + Fluent.Enums.spacing.timelineGraphLane
        property var graphPalette: Fluent.Enums.chartColors.extendedPalette
        property var selectedKey: undefined
        property string selectedRole: "hash"
        property real _visualOvershootOffset: 0
        property real _pulseOpacity: 1
        function _getTimeColor(period) {{
            return period === "PM"
                ? Fluent.Enums.statusLevel.getColor("warning")
                : Fluent.Enums.accentColor
        }}
        function _getStatusColor(status) {{ return Fluent.Enums.accentColor }}
        signal cardClicked(int groupIndex, int cardIndex, string text)
        signal cardClickedData(int groupIndex, int cardIndex, var cardData)
        signal cardActionClicked(int groupIndex, int cardIndex, var cardData)
    }}

    ListModel {{ id: rows }}

    Component.onCompleted: rows.append({{
        "kind": "card",
        "groupIndex": 0,
        "cardIndex": 0,
        "groupStatus": "info",
        "text": "{COMMIT_MESSAGE}",
        "description": "",
        "time": "17:31",
        "timePeriod": "PM",
        "status": "info",
        "strikeOut": false,
        "graphData": {{"nodeLane": 0, "nodeColorIndex": 0, "segments": []}},
        "isLastCard": true,
        "cardData": {{
            "text": "{COMMIT_MESSAGE}",
            "description": "{COMMIT_DESCRIPTION}",
            "time": "17:31",
            "timePeriod": "PM",
            "hash": "5546a4c2cb9e43fb64a95f87dbced8377d6610c0",
            "labels": [
                {{"text": "HEAD", "status": Fluent.Enums.statusLevel.processing}},
                {{"text": "master", "status": Fluent.Enums.statusLevel.info}}
            ],
            "graph": {{"nodeLane": 0, "nodeColorIndex": 0, "segments": []}}
        }}
    }})

    ListView {{
        property var timelineControl: timelineControl
        anchors.fill: parent
        model: rows
        delegate: TimelineInternal.TimelineVirtualRow {{}}
    }}
}}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _find_description(root: QQuickWindow) -> QQuickItem | None:
    for item in _visual_descendants(root.contentItem()):
        if item.property("text") == COMMIT_DESCRIPTION:
            return item
    return None


def test_virtual_row_falls_back_to_real_card_description(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), QUrl("inline"))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]

    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    try:
        assert _wait_for(lambda: _find_description(window) is not None)
        description = _find_description(window)
        assert description is not None
        assert description.isVisible()
        assert description.height() > 0
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
