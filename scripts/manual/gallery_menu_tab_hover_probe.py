# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Probe the Gallery MenuPage TabWidget layout with real mouse motion. 使用 Gallery 菜单页布局验证真实鼠标运动。"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from PySide6.QtCore import QEventLoop, QPoint, QPointF, QTimer, QUrl, QtMsgType
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prismqml
from prismqml import Skin, Theme, configure_qml_environment, register_types, setSkin, setTheme

ARTIFACT_ROOT_ENV = "PRISM_ARTIFACT_ROOT"
QML_SOURCE = '''
import QtQuick
import QtQuick.Window
import PrismQML
import "../../examples/pages"

Window {
    id: root
    width: 760
    height: 360
    visible: true
    color: Enums.backgroundColor

    ExampleCard {
        id: exampleCard
        objectName: "galleryExampleCard"
        x: 8
        y: 16
        width: 744
        title: "标签页组件"
        description: "TabWidget"

        Column {
            spacing: Enums.spacing.l
            Row {
                spacing: Enums.spacing.xl
                ComponentCard {
                    label: "TabWidget"
                    TabWidget {
                        id: tabWidget
                        objectName: "galleryTabWidget"
                        width: 320
                        height: 110
                        showAddButton: true
                        closable: true
                        tabs: [
                            { title: "标签1", icon: "", content: tab1Content },
                            { title: "标签2", icon: "", content: tab2Content },
                            { title: "标签3", icon: "", content: tab3Content }
                        ]
                    }
                }
            }
        }

        Component { id: tab1Content; Rectangle { anchors.fill: parent; color: Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: "内容1"; color: Enums.accentForeground } } }
        Component { id: tab2Content; Rectangle { anchors.fill: parent; color: Enums.demoPalette.green; Text { anchors.centerIn: parent; text: "内容2"; color: Enums.accentForeground } } }
        Component { id: tab3Content; Rectangle { anchors.fill: parent; color: Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: "内容3"; color: Enums.accentForeground } } }
    }
}
'''.encode("utf-8")


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _point(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(item.width() / 2, item.height() / 2))
    return QPoint(round(point.x()), round(point.y()))


def _delegates(tab: QQuickItem) -> list[QQuickItem]:
    pending = list(tab.childItems())
    items = []
    while pending:
        child = pending.pop()
        if (child.metaObject().indexOfProperty("visualOffsetX") >= 0
                and child.metaObject().indexOfProperty("selected") >= 0):
            items.append(child)
        pending.extend(child.childItems())
    return sorted(items, key=lambda item: item.x())


def _background(delegate: QQuickItem) -> dict:
    backgrounds = [
        child for child in delegate.childItems()
        if child.metaObject().indexOfProperty("radius") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    if len(backgrounds) != 1:
        raise RuntimeError(f"Expected one Gallery tab background, got {len(backgrounds)}")
    bg = backgrounds[0]
    color = bg.property("color")
    return {
        "red": color.red(),
        "green": color.green(),
        "blue": color.blue(),
        "alpha": color.alpha(),
    }


def _background_alpha(delegate: QQuickItem) -> int:
    backgrounds = [
        child for child in delegate.childItems()
        if child.metaObject().indexOfProperty("radius") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    if len(backgrounds) != 1:
        raise RuntimeError(f"Expected one Gallery tab background, got {len(backgrounds)}")
    return backgrounds[0].property("color").alpha()


def _state(window: QQuickWindow, tab: QQuickItem, elapsed: int) -> dict:
    return {
        "elapsed_ms": elapsed,
        "current_index": tab.property("currentIndex"),
        "delegates": [
            {
                "x": round(item.x(), 3),
                "width": round(item.width(), 3),
                "selected": bool(item.property("selected")),
                "hovered": bool(item.property("hovered")),
                "pressed": bool(item.property("pressed")),
                "background": _background(item),
            }
            for item in _delegates(tab)
        ],
    }


def main() -> int:
    output_dir = Path(os.environ.get(ARTIFACT_ROOT_ENV, ROOT / ".artifacts")) / "python" / "manual" / "gallery-menu-tab-hover"
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_qml_environment()
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QGuiApplication(sys.argv)
    messages = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda errors: messages.extend((QtMsgType.QtWarningMsg, error.toString()) for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl.fromLocalFile(str(ROOT / "scripts" / "manual" / "gallery_menu_tab_hover_probe.qml")))
    while component.status() == QQmlComponent.Status.Loading:
        _pump(10)
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))
    window = component.create(engine.rootContext())
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("Gallery layout window creation failed")
    window.show()
    window.requestActivate()
    _pump(300)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(f"D3D11 required; actual={actual_api_name}")

    tab = window.findChild(QQuickItem, "galleryTabWidget")
    if tab is None:
        raise RuntimeError("Gallery TabWidget was not created")
    delegates = _delegates(tab)
    points = [_point(window, item) for item in delegates]
    outside = QPoint(20, 20)
    QTest.mouseMove(window, outside)
    _pump(80)
    baseline_image = window.grabWindow()
    baseline_image.save(str(output_dir / "baseline.png"))
    QTest.mouseMove(window, points[1])
    _pump(50)
    entry_midpoint = _state(window, tab, 50)
    entry_midpoint_image = window.grabWindow()
    entry_midpoint_image.save(str(output_dir / "entry-midpoint.png"))
    QTest.mouseMove(window, outside)
    _pump(1)
    for _ in range(30):
        for point in points[1:]:
            QTest.mouseMove(window, point)
    active = {"point": [points[-1].x(), points[-1].y()], **_state(window, tab, 0)}
    active_image = window.grabWindow()
    active_image.save(str(output_dir / "active.png"))
    _pump(150)
    settled_active = _state(window, tab, 150)
    settled_image = window.grabWindow()
    settled_image.save(str(output_dir / "settled-active.png"))
    QTest.mouseMove(window, outside)
    exit_states = []
    exit_images = []
    previous = 0
    for elapsed in (0, 1, 16, 32, 64, 120):
        if elapsed > previous:
            _pump(elapsed - previous)
            previous = elapsed
        exit_states.append(_state(window, tab, elapsed))
        image = window.grabWindow()
        image_path = output_dir / f"exit-{elapsed:03d}.png"
        image.save(str(image_path))
        exit_images.append({
            "elapsed_ms": elapsed,
            "equals_baseline": image == baseline_image,
            "path": image_path.name,
        })

    path_states = []
    for name, point in (
        ("content", QPoint(220, 220)),
        ("card", QPoint(700, 220)),
        ("outside", outside),
    ):
        QTest.mouseMove(window, points[1])
        _pump(120)
        QTest.mouseMove(window, point)
        _pump(1)
        path_states.append({"target": name, **_state(window, tab, 1)})

    stress_failures = []
    stress_patterns = (
        (0, 0),
        (1, 0),
        (5, 0),
        (20, 0),
        (50, 0),
        (99, 0),
        (20, 1),
        (50, 1),
        (99, 1),
    )
    for enter_ms, cross_ms in stress_patterns:
        for iteration in range(40):
            QTest.mouseMove(window, outside)
            _pump(1)
            QTest.mouseMove(window, points[1])
            if enter_ms:
                _pump(enter_ms)
            QTest.mouseMove(window, points[2])
            if cross_ms:
                _pump(cross_ms)
            QTest.mouseMove(window, outside)
            alphas = [_background_alpha(item) for item in delegates]
            if any(alphas):
                stress_failures.append({
                    "enter_ms": enter_ms,
                    "cross_ms": cross_ms,
                    "iteration": iteration,
                    "alphas": alphas,
                })
                _pump(120)

    result = {
        "package_path": str(Path(prismqml.__file__).resolve()),
        "actual_graphics_api": actual_api_name,
        "tab_scene_points": [[point.x(), point.y()] for point in points],
        "active": active,
        "entry_midpoint": entry_midpoint,
        "settled_active": settled_active,
        "exit": exit_states,
        "exit_images": exit_images,
        "path_states": path_states,
        "stress_failures": stress_failures,
        "qt_warnings": [message for kind, message in messages if kind != QtMsgType.QtDebugMsg],
    }
    (output_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
