# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Calendar range-bar D3D11 benchmark. 日历范围条 D3D11 手工基准。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
MODES = ("single", "range_idle", "range_partial", "range_full", "range_transition")
QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    function activateRanges() {
        for (var i = 0; i < calendars.count; ++i) {
            var calendar = calendars.itemAt(i)
            calendar.rangeStart = new Date(2026, 3, 10)
            calendar.rangeEnd = new Date(2026, 3, 15)
        }
    }

    function clearRanges() {
        for (var i = 0; i < calendars.count; ++i) {
            var calendar = calendars.itemAt(i)
            calendar.rangeStart = null
            calendar.rangeEnd = null
        }
    }

    width: __COLUMNS__ * 264
    height: __ROWS__ * 314
    x: 64
    y: 64
    visible: false
    color: Enums.backgroundColor

    Grid {
        anchors.fill: parent
        columns: __COLUMNS__
        spacing: 8

        Repeater {
            id: calendars
            model: __INSTANCES__

            CalendarPickerCore {
                objectName: "calendar-" + index
                width: 256
                height: 306
                year: 2026
                month: 4
                rangeMode: "__MODE__" !== "single"
                rangeStart: "__MODE__" === "range_partial"
                    ? new Date(2026, 3, 10)
                    : ("__MODE__" === "range_full" ? new Date(2026, 3, 1) : null)
                rangeEnd: "__MODE__" === "range_partial"
                    ? new Date(2026, 3, 15)
                    : ("__MODE__" === "range_full" ? new Date(2026, 3, 30) : null)
            }
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
    parser.add_argument("--mode", choices=MODES, default="single")
    parser.add_argument("--instances", type=int, default=4)
    parser.add_argument("--image-output", type=Path)
    return parser.parse_args(argv)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_frame(window: QQuickWindow, action, timeout_ms: int = 3000) -> float:
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
        raise RuntimeError("D3D11 frame was not presented within 3000 ms")
    return (swapped_at[0] - started_at) * 1000


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        if current.isNull():
            raise RuntimeError("D3D11 grabWindow returned an empty image")
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise RuntimeError("D3D11 calendar frame did not stabilize within 800 ms")


def _wait_for_image_change(
    window: QQuickWindow, reference: QImage, action, timeout_ms: int = 3000
) -> tuple[float, QImage]:
    started_at = time.perf_counter()
    action()
    elapsed = 0
    while elapsed < timeout_ms:
        current = window.grabWindow()
        if current.isNull():
            raise RuntimeError("D3D11 grabWindow returned an empty image")
        if current != reference:
            return (time.perf_counter() - started_at) * 1000, current
        _pump(10)
        elapsed += 10
    raise RuntimeError("D3D11 calendar pixels did not change within 3000 ms")


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


def _owned_objects(window: QQuickWindow, visual_items) -> list[QObject]:
    objects = []
    pending = [window, *visual_items]
    seen = set()
    while pending:
        obj = pending.pop()
        identity = id(obj)
        if identity in seen:
            continue
        seen.add(identity)
        objects.append(obj)
        pending.extend(obj.children())
    return objects


def _invoke_and_update(window: QQuickWindow, method: str) -> None:
    if not QMetaObject.invokeMethod(window, method):
        raise RuntimeError(f"Calendar benchmark method failed: {method}")
    window.update()


def _qml_source(mode: str, instances: int) -> bytes:
    columns = 1 if instances == 1 else 2
    rows = (instances + columns - 1) // columns
    return (
        QML_TEMPLATE.replace("__MODE__", mode)
        .replace("__INSTANCES__", str(instances))
        .replace("__COLUMNS__", str(columns))
        .replace("__ROWS__", str(rows))
        .encode("utf-8")
    )


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.instances < 1:
        raise SystemExit("--instances must be at least 1")

    QQuickWindow.setGraphicsApi(
        QSGRendererInterface.GraphicsApi.Direct3D11
    )
    app = QGuiApplication(sys.argv)
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)

    load_started = time.perf_counter()
    component.setData(
        _qml_source(args.mode, args.instances),
        QUrl.fromLocalFile(str(ROOT / "tests/qml/calendar-range-bars-bench.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    qml_load_ms = (time.perf_counter() - load_started) * 1000
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    create_started = time.perf_counter()
    window = component.create(engine.rootContext())
    construction_ms = (time.perf_counter() - create_started) * 1000
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("Calendar benchmark window creation failed")

    ready_frame_ms = _wait_for_frame(window, window.show)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"Calendar benchmark requires Direct3D11; actual={actual_api_name}"
        )

    initial_image = _stable_window_image(window)
    if args.image_output is not None:
        args.image_output.parent.mkdir(parents=True, exist_ok=True)
        if not initial_image.save(str(args.image_output)):
            raise RuntimeError(f"Failed to save D3D11 image: {args.image_output}")
    visual_items = _visual_items(window)
    result = {
        "mode": args.mode,
        "instances": args.instances,
        "requested_graphics_api": "Direct3D11",
        "actual_graphics_api": actual_api_name,
        "qml_load_ms": round(qml_load_ms, 3),
        "construction_ms": round(construction_ms, 3),
        "ready_frame_ms": round(ready_frame_ms, 3),
        "qquickitem_count": len(visual_items),
        "qobject_count": len(_owned_objects(window, visual_items)),
        "initial_hash": _image_hash(initial_image),
    }

    if args.mode == "range_transition":
        transition_ms, _ = _wait_for_image_change(
            window,
            initial_image,
            lambda: _invoke_and_update(window, "activateRanges"),
        )
        active_image = _stable_window_image(window)
        clear_ms, _ = _wait_for_image_change(
            window,
            active_image,
            lambda: _invoke_and_update(window, "clearRanges"),
        )
        restored_image = _stable_window_image(window)
        repeat_ms, _ = _wait_for_image_change(
            window,
            restored_image,
            lambda: _invoke_and_update(window, "activateRanges"),
        )
        repeated_image = _stable_window_image(window)
        if restored_image != initial_image or repeated_image != active_image:
            raise RuntimeError("Calendar range transition did not restore stable pixels")
        result.update(
            {
                "transition_grab_ms": round(transition_ms, 3),
                "clear_transition_grab_ms": round(clear_ms, 3),
                "repeat_transition_grab_ms": round(repeat_ms, 3),
                "active_hash": _image_hash(active_image),
                "restored_hash": _image_hash(restored_image),
            }
        )
        if args.image_output is not None:
            active_path = args.image_output.with_name(
                f"{args.image_output.stem}-active{args.image_output.suffix}"
            )
            if not active_image.save(str(active_path)):
                raise RuntimeError(f"Failed to save D3D11 image: {active_path}")

    failures = [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]
    result["qt_failures"] = failures
    if failures:
        raise RuntimeError("; ".join(failures))

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    window.close()
    qInstallMessageHandler(previous_handler)
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
