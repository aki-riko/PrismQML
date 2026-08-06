# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ProgressRing visibility D3D11 benchmark. 进度环可见性 D3D11 手工基准。"""

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


QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    property bool ringsVisible: true

    function hideRings() {
        ringsVisible = false
        window.update()
    }

    function showRings() {
        ringsVisible = true
        window.update()
    }

    width: __COLUMNS__ * 48
    height: __ROWS__ * 48
    x: 64
    y: 64
    visible: false
    color: Enums.backgroundColor

    Grid {
        anchors.centerIn: parent
        columns: __COLUMNS__

        Repeater {
            model: __RINGS__

            ProgressRing {
                width: 48
                height: 48
                visible: window.ringsVisible
                indeterminate: true
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
    parser.add_argument("--rings", type=int, default=50)
    parser.add_argument("--sample-ms", type=int, default=500)
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


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _grab(window: QQuickWindow) -> QImage:
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError("D3D11 grabWindow returned an empty image")
    return image


def _visual_items(window: QQuickWindow) -> list[QQuickItem]:
    items = []
    pending = [window.contentItem()]
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


def _arc_count(window: QQuickWindow) -> int:
    return sum(
        item.objectName() == "progressRingIndeterminateArc"
        for item in _visual_items(window)
    )


def _invoke(window: QQuickWindow, method: str) -> None:
    if not QMetaObject.invokeMethod(window, method):
        raise RuntimeError(f"ProgressRing benchmark method failed: {method}")


def _qml_source(rings: int) -> bytes:
    columns = min(10, rings)
    rows = (rings + columns - 1) // columns
    return (
        QML_TEMPLATE.replace("__RINGS__", str(rings))
        .replace("__COLUMNS__", str(columns))
        .replace("__ROWS__", str(rows))
        .encode("utf-8")
    )


def _save_image(image: QImage, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save D3D11 image: {path}")


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.rings < 1:
        raise SystemExit("--rings must be at least 1")
    if args.sample_ms < 100:
        raise SystemExit("--sample-ms must be at least 100")

    package_path = Path(prismqml.__file__).resolve()
    try:
        package_path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(
            f"ProgressRing benchmark imported PrismQML outside checkout: {package_path}"
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
        _qml_source(args.rings),
        QUrl.fromLocalFile(str(ROOT / "tests/qml/progress-ring-visibility-bench.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    window = component.create(engine.rootContext())
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("ProgressRing benchmark window creation failed")

    _wait_for_frame(window, window.show)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"ProgressRing benchmark requires Direct3D11; actual={actual_api_name}"
        )

    _pump(150)
    visible_image = _grab(window)
    visible_frames = _sample_frames(window, args.sample_ms)
    visible_arc_count = _arc_count(window)
    _wait_for_frame(window, lambda: _invoke(window, "hideRings"))
    _pump(100)
    hidden_image = _grab(window)
    hidden_frames = _sample_frames(window, args.sample_ms)
    hidden_arc_count = _arc_count(window)
    _wait_for_frame(window, lambda: _invoke(window, "showRings"))
    _pump(100)
    restored_image = _grab(window)
    restored_frames = _sample_frames(window, args.sample_ms)
    restored_arc_count = _arc_count(window)

    if visible_image == hidden_image or restored_image == hidden_image:
        raise RuntimeError("ProgressRing visibility did not change D3D11 pixels")
    if (
        visible_arc_count != args.rings
        or hidden_arc_count != args.rings
        or restored_arc_count != args.rings
    ):
        raise RuntimeError(
            "ProgressRing visibility changed the active visual branch count: "
            f"visible={visible_arc_count}, hidden={hidden_arc_count}, "
            f"restored={restored_arc_count}, expected={args.rings}"
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
        "rings": args.rings,
        "sample_ms": args.sample_ms,
        "requested_graphics_api": "Direct3D11",
        "actual_graphics_api": actual_api_name,
        "package_path": str(package_path),
        "visible_frames": visible_frames,
        "hidden_frames": hidden_frames,
        "restored_frames": restored_frames,
        "visible_arc_count": visible_arc_count,
        "hidden_arc_count": hidden_arc_count,
        "restored_arc_count": restored_arc_count,
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
