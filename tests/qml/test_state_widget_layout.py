# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StateWidget compact layout regressions. StateWidget 紧凑布局回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QPointF, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "state-widget-layout.qml")
)
SCENE_SOURCE = """
import QtQuick
import PrismQML

Item {
    readonly property int expectedResultTitleSize: Enums.typography.displayLarge
    readonly property int expectedStateImageSize: Enums.controlSize.stateImageSize

    width: 736
    height: 240
    Component.onCompleted: Translator.setLanguage(Enums.lang.en)

    StateWidget {
        objectName: "noData"
        x: 0
        width: 160
        height: 180
        stateType: Enums.state.type_no_data
    }

    StateWidget {
        objectName: "success"
        x: 192
        width: 160
        height: 180
        stateType: Enums.state.type_result
        severity: "success"
        title: "提交成功"
    }

    StateWidget {
        objectName: "error"
        x: 384
        width: 160
        height: 180
        stateType: Enums.state.type_result
        severity: "error"
        title: "操作失败"
    }

    StateWidget {
        objectName: "offline"
        x: 576
        width: 160
        height: 200
        stateType: Enums.state.type_no_internet
    }
}
""".encode("utf-8")


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(10)
    return engine, component, root


def _assert_title_stays_inside(widget: QQuickItem) -> QQuickItem:
    title = widget.findChild(QQuickItem, "stateTitle")
    assert title is not None
    position = title.mapToItem(widget, QPointF())
    assert position.x() >= 0
    assert position.x() + title.width() <= widget.width()
    assert position.y() >= 0
    assert position.y() + title.height() <= widget.height()
    return title


def test_compact_state_widget_titles_do_not_overlap(qapp):
    engine, component, root = _create_scene()
    try:
        widgets = {
            name: root.findChild(QQuickItem, name)
            for name in ("noData", "success", "error", "offline")
        }
        assert all(widget is not None for widget in widgets.values())

        titles = {
            name: _assert_title_stays_inside(widget)
            for name, widget in widgets.items()
        }
        expected_title_size = root.property("expectedResultTitleSize")
        assert titles["success"].property("font").pixelSize() == expected_title_size
        assert titles["error"].property("font").pixelSize() == expected_title_size
        assert titles["offline"].height() > titles["noData"].height()
        assert root.property("expectedStateImageSize") == 96
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
