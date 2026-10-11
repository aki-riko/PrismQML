# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Standalone D3D11 heavy-component scheduler benchmark. 独立 D3D11 重型组件调度基准。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from PySide6.QtCore import QEventLoop, QObject, QTimer, QtMsgType, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prismqml
from prismqml import configure_qml_environment, register_types


MODES = ("direct", "scheduled")
QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    width: __WINDOW_WIDTH__
    height: __WINDOW_HEIGHT__
    visible: false
    color: Enums.backgroundColor

    Component.onCompleted: {
        HeavyComponentScheduler.schedulerEnabled = true
        HeavyComponentScheduler.activationBudgetMs = 5
        HeavyComponentScheduler.maxActivationsPerTick = 1
    }

    Grid {
        anchors.centerIn: parent
        columns: __COLUMNS__
        rowSpacing: 10
        columnSpacing: 10

        Repeater {
            model: __INSTANCES__
            delegate: __DELEGATE__
        }
    }
}
"""
DIRECT_DELEGATE = """
MatrixRain {
    objectName: "rain-" + index
    width: __ITEM_WIDTH__
    height: __ITEM_HEIGHT__
    running: true
    density: 0.8
    glowEnabled: false
}
"""
SCHEDULED_DELEGATE = """
HeavyComponentSlot {
    id: slot
    objectName: "slot-" + index
    width: __ITEM_WIDTH__
    height: __ITEM_HEIGHT__
    scheduled: true
    priority: HeavyComponentScheduler.priority_visible
    sourceComponent: Component {
        MatrixRain {
            objectName: "rain-" + index
            anchors.fill: parent
            running: true
            density: 0.8
            glowEnabled: false
            schedulerActive: slot.workActive
        }
    }
}
"""
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--instances", type=int, default=4)
    parser.add_argument("--sample-ms", type=int, default=1000)
    parser.add_argument(
        "--result-file",
        type=Path,
        default=ROOT / ".artifacts" / "python" / "heavy-component-scheduler.json",
    )
    parser.add_argument("--image-output", type=Path)
    return parser.parse_args(argv)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_frame(window: QQuickWindow, action, timeout_ms: int = 5000) -> float:
    swapped_at = []

    def on_frame_swapped():
        if not swapped_at:
            swapped_at.append(time.perf_counter())

    window.frameSwapped.connect(on_frame_swapped)
    started_at = time.perf_counter()
    try:
        action()
        elapsed = 0
        while not swapped_at and elapsed < timeout_ms:
            _pump(10)
            elapsed += 10
    finally:
        window.frameSwapped.disconnect(on_frame_swapped)
    if not swapped_at:
        raise RuntimeError("D3D11 frame was not presented within 5000 ms")
    return (swapped_at[0] - started_at) * 1000


def _sample_frame_intervals(window: QQuickWindow, sample_ms: int) -> list[float]:
    timestamps = []

    def on_frame_swapped():
        timestamps.append(time.perf_counter())

    window.frameSwapped.connect(on_frame_swapped)
    try:
        _pump(sample_ms)
    finally:
        window.frameSwapped.disconnect(on_frame_swapped)
    return [
        (right - left) * 1000
        for left, right in zip(timestamps, timestamps[1:])
    ]


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * ratio))
    return ordered[index]


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _visual_items(window: QQuickWindow) -> list[QQuickItem]:
    items = []
    pending = [window.contentItem()]
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


def _objects(window: QQuickWindow) -> list[QObject]:
    return [window, *window.findChildren(QObject)]


def _ready_count(window: QQuickWindow, mode: str) -> int:
    items = _visual_items(window)
    if mode == "direct":
        return sum(
            item.objectName().startswith("rain-")
            for item in items
        )
    return sum(
        bool(item.property("loaded"))
        for item in items
        if item.objectName().startswith("slot-")
        and item.metaObject().indexOfProperty("loaded") >= 0
    )


def _wait_until_ready(window: QQuickWindow, mode: str, expected: int) -> float:
    started_at = time.perf_counter()
    elapsed = 0
    while _ready_count(window, mode) < expected and elapsed < 15000:
        _pump(20)
        elapsed += 20
    ready_ms = (time.perf_counter() - started_at) * 1000
    if _ready_count(window, mode) != expected:
        raise RuntimeError(
            f"heavy components did not become ready: mode={mode} "
            f"ready={_ready_count(window, mode)} expected={expected}"
        )
    return ready_ms


def _grab(window: QQuickWindow) -> QImage:
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError("D3D11 grabWindow returned an empty image")
    return image


def _qml_source(mode: str, instances: int) -> bytes:
    columns = min(2, instances)
    item_width = 220
    item_height = 160
    delegate = DIRECT_DELEGATE if mode == "direct" else SCHEDULED_DELEGATE
    delegate = delegate.replace("__ITEM_WIDTH__", str(item_width)).replace(
        "__ITEM_HEIGHT__", str(item_height)
    )
    return (
        QML_TEMPLATE.replace("__WINDOW_WIDTH__", str(columns * item_width + 30))
        .replace("__WINDOW_HEIGHT__", str(((instances + columns - 1) // columns) * item_height + 30))
        .replace("__COLUMNS__", str(columns))
        .replace("__INSTANCES__", str(instances))
        .replace("__DELEGATE__", delegate)
        .encode("utf-8")
    )


def _save_image(image: QImage, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save D3D11 image: {path}")


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.instances < 1:
        raise SystemExit("--instances must be at least 1")
    if args.sample_ms < 200:
        raise SystemExit("--sample-ms must be at least 200")

    package_path = Path(prismqml.__file__).resolve()
    package_path.relative_to(ROOT)
    configure_qml_environment()
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QGuiApplication(sys.argv)
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        _qml_source(args.mode, args.instances),
        QUrl.fromLocalFile(str(ROOT / "tests/qml/heavy-component-scheduler-bench.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    create_started_at = time.perf_counter()
    window = component.create(engine.rootContext())
    create_ms = (time.perf_counter() - create_started_at) * 1000
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("Heavy component scheduler benchmark window creation failed")

    first_frame_ms = _wait_for_frame(window, window.show)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"Heavy component scheduler benchmark requires Direct3D11; actual={actual_api_name}"
        )

    ready_ms = _wait_until_ready(window, args.mode, args.instances)
    _pump(200)
    image = _grab(window)
    intervals = _sample_frame_intervals(window, args.sample_ms)
    total_objects = len(_objects(window))
    quick_items = len(_visual_items(window))
    failures = [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]
    if failures:
        raise RuntimeError("; ".join(failures))

    result = {
        "mode": args.mode,
        "instances": args.instances,
        "sample_ms": args.sample_ms,
        "requested_graphics_api": "Direct3D11",
        "actual_graphics_api": actual_api_name,
        "create_ms": round(create_ms, 3),
        "first_frame_ms": round(first_frame_ms, 3),
        "ready_ms_after_first_frame": round(ready_ms, 3),
        "ready_count": _ready_count(window, args.mode),
        "frame_count": len(intervals) + 1 if intervals else 0,
        "frame_interval_mean_ms": round(sum(intervals) / len(intervals), 3) if intervals else 0.0,
        "frame_interval_p95_ms": round(_percentile(intervals, 0.95), 3),
        "frame_interval_max_ms": round(max(intervals), 3) if intervals else 0.0,
        "frames_over_20ms": sum(interval > 20 for interval in intervals),
        "frames_over_33ms": sum(interval > 33 for interval in intervals),
        "object_count": total_objects,
        "quick_item_count": quick_items,
        "image_hash": _image_hash(image),
        "qt_failures": failures,
    }
    args.result_file.parent.mkdir(parents=True, exist_ok=True)
    args.result_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.image_output is not None:
        _save_image(image, args.image_output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    window.close()
    qInstallMessageHandler(previous_handler)
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
