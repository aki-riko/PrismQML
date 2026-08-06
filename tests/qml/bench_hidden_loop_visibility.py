# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Hidden loop D3D11 benchmark. 隐藏循环动画 D3D11 手工基准。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface

import prismqml
from prismqml import configure_qml_environment, register_types


MODES = ("tag", "marquee")
DELEGATES = {
    "tag": """
        Tag {
            objectName: "benchItem-" + index
            width: 64
            height: 28
            visible: window.itemsVisible
            text: "Work"
            status: Enums.statusLevel.processing
        }
    """,
    "marquee": """
        Marquee {
            objectName: "benchItem-" + index
            width: 120
            height: 28
            visible: window.itemsVisible
            text: "Long scrolling text"
            forceScroll: true
            pauseDuration: 0
        }
    """,
}
QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    property bool itemsVisible: true

    function hideItems() {
        itemsVisible = false
        window.update()
    }

    function showItems() {
        itemsVisible = true
        window.update()
    }

    width: __COLUMNS__ * __ITEM_WIDTH__
    height: __ROWS__ * 28
    x: 64
    y: 64
    visible: false
    color: Enums.backgroundColor

    Grid {
        anchors.centerIn: parent
        columns: __COLUMNS__

        Repeater {
            model: __INSTANCES__
            delegate: __DELEGATE__
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
    parser.add_argument("--instances", type=int, default=50)
    parser.add_argument("--sample-ms", type=int, default=500)
    parser.add_argument("--image-output", type=Path)
    return parser.parse_args(argv)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_frame(window: QQuickWindow, action, timeout_ms: int = 3000) -> None:
    swapped = []

    def on_frame_swapped():
        if not swapped:
            swapped.append(True)

    window.frameSwapped.connect(on_frame_swapped)
    try:
        action()
        elapsed = 0
        while not swapped and elapsed < timeout_ms:
            _pump(10)
            elapsed += 10
    finally:
        window.frameSwapped.disconnect(on_frame_swapped)
    if not swapped:
        raise RuntimeError("D3D11 frame was not presented within 3000 ms")


def _sample_frames(window: QQuickWindow, sample_ms: int) -> int:
    frames = []

    def on_frame_swapped():
        frames.append(time.perf_counter())

    window.frameSwapped.connect(on_frame_swapped)
    try:
        _pump(sample_ms)
    finally:
        window.frameSwapped.disconnect(on_frame_swapped)
    return len(frames)


def _grab(window: QQuickWindow) -> QImage:
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError("D3D11 grabWindow returned an empty image")
    return image


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


def _bench_item_count(window: QQuickWindow) -> int:
    return sum(
        item.objectName().startswith("benchItem-")
        for item in _visual_items(window)
    )


def _invoke(window: QQuickWindow, method: str) -> None:
    if not QMetaObject.invokeMethod(window, method):
        raise RuntimeError(f"Hidden-loop benchmark method failed: {method}")


def _qml_source(mode: str, instances: int) -> bytes:
    columns = min(10, instances)
    rows = (instances + columns - 1) // columns
    item_width = 64 if mode == "tag" else 120
    return (
        QML_TEMPLATE.replace("__INSTANCES__", str(instances))
        .replace("__COLUMNS__", str(columns))
        .replace("__ROWS__", str(rows))
        .replace("__ITEM_WIDTH__", str(item_width))
        .replace("__DELEGATE__", DELEGATES[mode])
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
    if args.sample_ms < 100:
        raise SystemExit("--sample-ms must be at least 100")

    package_path = Path(prismqml.__file__).resolve()
    try:
        package_path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(
            f"Hidden-loop benchmark imported PrismQML outside checkout: {package_path}"
        ) from error

    configure_qml_environment()
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
    component.setData(
        _qml_source(args.mode, args.instances),
        QUrl.fromLocalFile(str(ROOT / "tests/qml/hidden-loop-visibility-bench.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    window = component.create(engine.rootContext())
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("Hidden-loop benchmark window creation failed")

    _wait_for_frame(window, window.show)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"Hidden-loop benchmark requires Direct3D11; actual={actual_api_name}"
        )

    _pump(200)
    visible_image = _grab(window)
    visible_frames = _sample_frames(window, args.sample_ms)
    visible_item_count = _bench_item_count(window)
    _wait_for_frame(window, lambda: _invoke(window, "hideItems"))
    _pump(100)
    hidden_image = _grab(window)
    hidden_frames = _sample_frames(window, args.sample_ms)
    hidden_item_count = _bench_item_count(window)
    _wait_for_frame(window, lambda: _invoke(window, "showItems"))
    _pump(150)
    restored_image = _grab(window)
    restored_frames = _sample_frames(window, args.sample_ms)
    restored_item_count = _bench_item_count(window)

    if visible_image == hidden_image or restored_image == hidden_image:
        raise RuntimeError("Hidden-loop visibility did not change D3D11 pixels")
    if (
        visible_item_count != args.instances
        or hidden_item_count != args.instances
        or restored_item_count != args.instances
    ):
        raise RuntimeError(
            "Hidden-loop visibility changed item count: "
            f"visible={visible_item_count}, hidden={hidden_item_count}, "
            f"restored={restored_item_count}, expected={args.instances}"
        )

    if args.image_output is not None:
        _save_image(visible_image, args.image_output)
        _save_image(
            hidden_image,
            args.image_output.with_name(
                f"{args.image_output.stem}-hidden{args.image_output.suffix}"
            ),
        )
        _save_image(
            restored_image,
            args.image_output.with_name(
                f"{args.image_output.stem}-restored{args.image_output.suffix}"
            ),
        )

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
        "package_path": str(package_path),
        "visible_frames": visible_frames,
        "hidden_frames": hidden_frames,
        "restored_frames": restored_frames,
        "visible_item_count": visible_item_count,
        "hidden_item_count": hidden_item_count,
        "restored_item_count": restored_item_count,
        "visible_hash": _image_hash(visible_image),
        "hidden_hash": _image_hash(hidden_image),
        "restored_hash": _image_hash(restored_image),
        "qt_failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    window.close()
    qInstallMessageHandler(previous_handler)
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
