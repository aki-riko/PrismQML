# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TabWidget D3D11 hover-motion probe. TabWidget D3D11 悬浮运动探针。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QPoint, QPointF, QTimer, QtMsgType, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface
from PySide6.QtTest import QTest

import prismqml
from prismqml import (
    Skin,
    Theme,
    configure_qml_environment,
    register_types,
    setSkin,
    setTheme,
)


ARTIFACT_ROOT_ENV = "PRISM_ARTIFACT_ROOT"
FRAME_DELAYS_MS = (0, 16, 32, 64, 120, 220, 420)
QML_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    width: 400
    height: 260
    visible: false
    color: Enums.backgroundColor

    Component {
        id: page
        Rectangle { color: Enums.demoPalette.blue }
    }

    TabWidget {
        id: tabs
        objectName: "tabWidget"
        x: 40
        y: 40
        width: 320
        height: 110
        showAddButton: true
        closable: true
        tabs: [
            { title: "Alpha", icon: "", content: page },
            { title: "Bravo", icon: "", content: page },
            { title: "Charlie", icon: "", content: page }
        ]
    }

    Row {
        x: 40
        y: 180
        spacing: 10

        Button {
            objectName: "hoverButtonSmall"
            width: 70
            text: "Small"
        }

        Button {
            objectName: "hoverButtonMedium"
            width: 100
            text: "Medium"
        }

        Button {
            objectName: "hoverButtonLarge"
            width: 120
            text: "Large"
        }
    }
}
"""
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}


def _parse_args(argv=None):
    default_root = Path(os.environ.get(ARTIFACT_ROOT_ENV, ROOT / ".artifacts"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_root / "python" / "manual" / "tab-widget-shadow-artifact",
    )
    return parser.parse_args(argv)


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visual_descendants(root: QQuickItem):
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.childItems())


def _delegates(tab: QQuickItem) -> list[QQuickItem]:
    delegates = [
        item
        for item in _visual_descendants(tab)
        if item.metaObject().indexOfProperty("visualOffsetX") >= 0
        and item.metaObject().indexOfProperty("selected") >= 0
    ]
    delegates.sort(key=lambda item: item.x())
    return delegates


def _indicator(tab: QQuickItem) -> QQuickItem:
    indicators = [
        item
        for item in _visual_descendants(tab)
        if item.metaObject().indexOfProperty("_currentTabKey") >= 0
    ]
    if len(indicators) != 1:
        raise RuntimeError(f"Expected one sliding indicator, got {len(indicators)}")
    return indicators[0]


def _delegate_background(delegate: QQuickItem) -> QQuickItem:
    backgrounds = [
        child
        for child in delegate.childItems()
        if child.metaObject().indexOfProperty("radius") >= 0
        and child.metaObject().indexOfProperty("color") >= 0
    ]
    if len(backgrounds) != 1:
        raise RuntimeError(
            f"Expected one delegate background, got {len(backgrounds)}"
        )
    return backgrounds[0]


def _color_state(item: QQuickItem) -> dict:
    color = item.property("color")
    return {
        "red": round(color.redF(), 6),
        "green": round(color.greenF(), 6),
        "blue": round(color.blueF(), 6),
        "alpha": round(color.alphaF(), 6),
    }


def _scene_rect(item: QQuickItem | None):
    if item is None:
        return None
    top_left = item.mapToScene(QPointF(0, 0))
    return {
        "x": round(top_left.x(), 3),
        "y": round(top_left.y(), 3),
        "width": round(item.width(), 3),
        "height": round(item.height(), 3),
        "visible": item.isVisible(),
    }


def _state(window: QQuickWindow, elapsed_ms: int):
    tab = window.findChild(QQuickItem, "tabWidget")
    if tab is None:
        raise RuntimeError("TabWidget was not created")
    delegates = _delegates(tab)
    indicator = _indicator(tab)
    layer = window.findChild(QQuickItem, "_neumorphicInsetLayer")
    shader = window.findChild(QQuickItem, "_neumorphicInsetShader")
    return {
        "elapsed_ms": elapsed_ms,
        "current_index": tab.property("currentIndex"),
        "indicator": _scene_rect(indicator),
        "inset_layer": _scene_rect(layer),
        "inset_shader": _scene_rect(shader),
        "delegates": [
            {
                **_scene_rect(item),
                "selected": item.property("selected"),
                "hovered": item.property("hovered"),
                "pressed": item.property("pressed"),
                "background": _color_state(_delegate_background(item)),
            }
            for item in delegates
        ],
    }


def _save_frame(
    window: QQuickWindow, output_dir: Path, sequence: str, elapsed_ms: int
) -> dict:
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError("D3D11 grabWindow returned an empty image")
    path = output_dir / f"{sequence}-{elapsed_ms:03d}.png"
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save D3D11 frame: {path}")
    state = _state(window, elapsed_ms)
    state["image"] = path.name
    return state


def _point(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _capture_hover_exit_sequence(
    window: QQuickWindow,
    output_dir: Path,
    sequence: str,
    inter_move_ms: int,
) -> dict:
    tab = window.findChild(QQuickItem, "tabWidget")
    if tab is None:
        raise RuntimeError("TabWidget was not created")
    delegates = _delegates(tab)
    points = [_point(window, delegate) for delegate in delegates]
    outside = QPoint(20, 20)

    QTest.mouseMove(window, outside)
    _pump(30)
    for _ in range(12):
        for index in (1, 2):
            QTest.mouseMove(window, points[index])
            if inter_move_ms:
                _pump(inter_move_ms)

    active_frame = _save_frame(window, output_dir, f"{sequence}-active", 0)
    if active_frame["current_index"] != 0:
        raise RuntimeError("Hover-only probe changed the current tab")
    if not active_frame["delegates"][2]["hovered"]:
        raise RuntimeError("Rapid mouse movement did not reach the final tab")

    QTest.mouseMove(window, outside)
    exit_frames = [_save_frame(window, output_dir, f"{sequence}-exit", 0)]
    elapsed = 0
    for target_elapsed in FRAME_DELAYS_MS[1:]:
        _pump(target_elapsed - elapsed)
        elapsed = target_elapsed
        exit_frames.append(
            _save_frame(window, output_dir, f"{sequence}-exit", elapsed)
        )

    settled = next(frame for frame in exit_frames if frame["elapsed_ms"] == 32)
    if any(delegate["hovered"] for delegate in settled["delegates"]):
        raise RuntimeError("A delegate retained hover after the pointer exited")
    if any(
        delegate["background"]["alpha"] != 0
        for delegate in settled["delegates"]
    ):
        raise RuntimeError("A hover background remained visible after 32 ms")
    return {"active": active_frame, "exit": exit_frames}


def _capture_button_hover_exit_sequence(
    window: QQuickWindow, output_dir: Path
) -> dict:
    buttons = [
        window.findChild(QQuickItem, name)
        for name in (
            "hoverButtonSmall",
            "hoverButtonMedium",
            "hoverButtonLarge",
        )
    ]
    if any(button is None for button in buttons):
        raise RuntimeError("Hover probe buttons were not created")
    points = [_point(window, button) for button in buttons]
    outside = QPoint(20, 240)

    QTest.mouseMove(window, outside)
    _pump(220)
    baseline = window.grabWindow()
    baseline_path = output_dir / "buttons-baseline.png"
    if baseline.isNull() or not baseline.save(str(baseline_path)):
        raise RuntimeError("Failed to save the button hover baseline")

    for _ in range(12):
        for point in points:
            QTest.mouseMove(window, point)
            _pump(1)
    active = window.grabWindow()
    active_path = output_dir / "buttons-active.png"
    if active.isNull() or not active.save(str(active_path)):
        raise RuntimeError("Failed to save the active button hover frame")

    QTest.mouseMove(window, outside)
    restored_frames = []
    elapsed = 0
    for target_elapsed in (0, 16, 32):
        if target_elapsed > elapsed:
            _pump(target_elapsed - elapsed)
            elapsed = target_elapsed
        restored = window.grabWindow()
        restored_path = output_dir / f"buttons-restored-{elapsed:03d}.png"
        if restored.isNull() or not restored.save(str(restored_path)):
            raise RuntimeError("Failed to save a restored button hover frame")
        restored_frames.append({
            "elapsed_ms": elapsed,
            "image": restored_path.name,
            "equals_baseline": restored == baseline,
        })
    if not restored_frames[-1]["equals_baseline"]:
        raise RuntimeError("Button pixels did not restore after rapid hover exit")
    return {
        "baseline": baseline_path.name,
        "active": active_path.name,
        "exit": restored_frames,
    }


def main(argv=None) -> int:
    args = _parse_args(argv)
    package_path = Path(prismqml.__file__).resolve()
    try:
        package_path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(
            f"Probe imported PrismQML outside checkout: {package_path}"
        ) from error

    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_qml_environment()
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QGuiApplication(sys.argv)
    messages = []
    engine = QQmlApplicationEngine()
    engine.warnings.connect(
        lambda errors: messages.extend(
            (QtMsgType.QtWarningMsg, error.toString()) for error in errors
        )
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    component = QQmlComponent(engine)
    component.setData(
        QML_SOURCE,
        QUrl.fromLocalFile(str(ROOT / "scripts/manual/tab-widget-shadow-probe.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))
    window = component.create(engine.rootContext())
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("TabWidget shadow probe window creation failed")

    window.show()
    window.requestActivate()
    _pump(240)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"TabWidget shadow probe requires Direct3D11; actual={actual_api_name}"
        )

    same_turn_frames = _capture_hover_exit_sequence(
        window, args.output_dir, "same-turn", inter_move_ms=0
    )
    paced_frames = _capture_hover_exit_sequence(
        window, args.output_dir, "paced", inter_move_ms=1
    )
    button_frames = _capture_button_hover_exit_sequence(window, args.output_dir)
    failures = [message for mode, message in messages if mode in QT_FAILURE_TYPES]
    result = {
        "requested_graphics_api": "Direct3D11",
        "actual_graphics_api": actual_api_name,
        "package_path": str(package_path),
        "same_turn": same_turn_frames,
        "paced": paced_frames,
        "buttons": button_frames,
        "qt_failures": failures,
    }
    result_path = args.output_dir / "result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if failures:
        raise RuntimeError("; ".join(failures))

    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
