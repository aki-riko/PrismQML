# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PaintedRow runtime performance regressions. PaintedRow 运行时性能回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Table"
    / "PaintedRow.qml"
)
DATA_CONTROLS_URL = QUrl.fromLocalFile(
    str(ROOT / "prismqml" / "PrismQML" / "controls" / "data")
).toString()
SCENE_SOURCE = f"""import QtQuick
import QtQuick.Window
import PrismQML
import "{DATA_CONTROLS_URL}" as DataControls

Window {{
    id: root

    property int extraDrawCalls: 0
    property int extraColumnCount: -1
    property int extraValue: -1
    property real extraWidth: -1
    property real extraHeight: -1

    width: 320
    height: 80
    visible: true

    DataControls.PaintedRow {{
        id: row

        objectName: "row"
        x: 10
        y: 10
        width: 300
        height: 40
        columns: [
            {{ key: "name", width: 0.5, align: "left" }},
            null,
            {{ key: "value", width: 100, align: "right" }}
        ]
        rowData: ({{ name: "Alpha", value: 42 }})
        rowIndex: 7
        extraDraw: function(ctx, columns, data, width, height) {{
            root.extraDrawCalls += 1
            root.extraColumnCount = columns.length
            root.extraValue = data.value
            root.extraWidth = width
            root.extraHeight = height
        }}
    }}
}}
""".encode("utf-8")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "painted-row-performance.qml")),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    row = window.findChild(QQuickItem, "row")
    assert row is not None
    canvases = [
        child
        for child in row.findChildren(QObject)
        if "Canvas" in child.metaObject().className()
    ]
    assert len(canvases) == 1
    assert _wait_for(lambda: canvases[0].property("available"))
    return engine, component, window, row, canvases[0], warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_painted_row_offscreen_paint_preserves_extra_draw_contract(qapp):
    engine, component, window, _row, canvas, warnings = _create_scene()
    try:
        calls_before = window.property("extraDrawCalls")
        assert QMetaObject.invokeMethod(canvas, "requestPaint") is True
        assert _wait_for(lambda: window.property("extraDrawCalls") > calls_before)
        assert window.property("extraColumnCount") == 3
        assert window.property("extraValue") == 42
        assert window.property("extraWidth") == 300
        assert window.property("extraHeight") == 40
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_painted_row_hover_preserves_column_and_row_indices(qapp):
    engine, component, window, row, _canvas, warnings = _create_scene()
    hovered: list[tuple[int, int]] = []
    row.cellHovered.connect(lambda column, row_index: hovered.append((column, row_index)))
    try:
        for column, local_x in ((0, 50), (1, 170), (2, 220)):
            point = row.mapToScene(QPointF(local_x, row.height() / 2)).toPoint()
            QTest.mouseMove(window, point)
            assert _wait_for(lambda: hovered[-1:] == [(column, 7)])

        QTest.mouseMove(window, QPoint(319, 79))
        assert _wait_for(lambda: hovered[-1:] == [(-1, -1)])
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_painted_row_hot_loop_uses_frame_snapshot():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    paint_section = source.split("onPaint: {", 1)[1].split(
        "// Draw business-specific additions", 1
    )[0]
    loop_marker = "for (var i = 0; i < columns.length; i++) {"
    assert loop_marker in paint_section
    hot_loop = paint_section.split(loop_marker, 1)[1]
    assert "root." not in hot_loop


def test_painted_row_hover_loop_uses_event_snapshot():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    hover_section = source.split("onPositionChanged: function(mouse) {", 1)[1].split(
        "onExited:", 1
    )[0]
    loop_marker = "for (var i = 0; i < columns.length; i++) {"
    assert loop_marker in hover_section
    hot_loop = hover_section.split(loop_marker, 1)[1]
    assert "root._safeColumns" not in hot_loop
    assert "root.width" not in hot_loop
    assert "root.rowIndex" not in hot_loop
