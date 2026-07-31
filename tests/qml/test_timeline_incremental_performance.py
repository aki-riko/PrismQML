# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline incremental paging contracts. Timeline 增量分页合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "timeline-incremental-performance.qml")
)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    // Mirrors the real Gitora 30-to-60 commit boundary: the old tail day grows,
    // then two new day groups are appended. 复现 Gitora 真实分页中的尾日期组增长。
    readonly property var historyBandCounts: [1, 9, 1, 5, 13, 7, 11, 13]
    property var historyItems: makeHistoryPage(30)
    readonly property int historyFlatCount: timeline._flatRows.length
    readonly property string firstAppendedCardText:
        timeline._flatRows.length > 36 ? timeline._flatRows[36].text : ""

    function makeHistoryPage(limit) {
        var result = []
        var commitIndex = 0
        for (var groupIndex = 0;
                groupIndex < historyBandCounts.length && commitIndex < limit;
                groupIndex++) {
            var cards = []
            var groupCount = historyBandCounts[groupIndex]
            for (var cardIndex = 0;
                    cardIndex < groupCount && commitIndex < limit;
                    cardIndex++) {
                cards.push({
                    "text": "Commit " + commitIndex,
                    "commit": "history-" + commitIndex
                })
                commitIndex++
            }
            result.push({
                "title": "History Day " + groupIndex,
                "status": "info",
                "cards": cards
            })
        }
        return result
    }

    function appendFreshHistoryPage() {
        // A fresh object tree matches Gitora's CommitTimelineModel rebuild.
        // 新对象树与 Gitora 的 CommitTimelineModel 重建行为一致。
        historyItems = makeHistoryPage(60)
    }

    width: 720
    height: 640
    visible: true

    TimelineCore {
        id: timeline
        objectName: "historyTimeline"
        anchors.fill: parent
        virtualized: true
        items: root.historyItems
    }
}
""".encode("utf-8")


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


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    timeline = window.findChild(QQuickItem, "historyTimeline")
    assert timeline is not None
    list_view = next(
        item
        for item in timeline.findChildren(QQuickItem)
        if item.objectName() == "timelineVirtualViewport"
    )
    _pump()
    return engine, component, window, timeline, list_view, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_fresh_history_page_only_builds_changed_tail_groups(qapp) -> None:
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, timeline, list_view, warnings = _create_scene()
    try:
        assert _wait_for(lambda: list_view.property("count") == 36)
        assert timeline.property("_lastFlatBuildGroupCount") == 6
        maximum_y = list_view.property("contentHeight") - list_view.height()
        list_view.setProperty("contentY", maximum_y - 5)
        before_y = list_view.property("contentY")

        assert QMetaObject.invokeMethod(window, "appendFreshHistoryPage")
        assert _wait_for(lambda: window.property("historyFlatCount") == 68)
        assert _wait_for(lambda: list_view.property("count") == 68)

        assert window.property("firstAppendedCardText") == "Commit 30"
        assert timeline.property("_lastFlatBuildGroupCount") == 3
        assert list_view.property("contentY") == pytest.approx(before_y)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
