# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""D3D11 stacked page retention benchmark. D3D11 堆叠页面驻留基准。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import time

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prismqml
from prismqml import configure_qml_environment, register_types


QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window
    width: 720
    height: 440
    visible: false
    color: Enums.backgroundColor

    StackedWidget {
        id: stack
        objectName: "retentionStack"
        anchors.fill: parent
        lazyLoading: true
        animationEnabled: false
        pageRetentionRadius: __RADIUS__
        pageSources: [__SOURCES__]
    }
}
"""
QT_FAILURE_TYPES = {QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg}
KNOWN_WARNINGS = ("QFontDatabase: Cannot find font directory",)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radius", type=int, default=0)
    parser.add_argument("--pages", type=int, default=8)
    parser.add_argument("--sample-ms", type=int, default=1000)
    parser.add_argument(
        "--result-file",
        type=Path,
        default=ROOT / ".artifacts" / "python" / "stacked-page-retention.json",
    )
    return parser.parse_args(argv)


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_frame(window, action, timeout_ms=5000):
    frames = []

    def on_frame():
        if not frames:
            frames.append(time.perf_counter())

    window.frameSwapped.connect(on_frame)
    started = time.perf_counter()
    try:
        action()
        elapsed = 0
        while not frames and elapsed < timeout_ms:
            _pump(10)
            elapsed += 10
    finally:
        window.frameSwapped.disconnect(on_frame)
    if not frames:
        raise RuntimeError("D3D11 frame was not presented")
    return (frames[0] - started) * 1000


def _sample_intervals(window, sample_ms):
    stamps = []

    def on_frame():
        stamps.append(time.perf_counter())

    window.frameSwapped.connect(on_frame)
    try:
        _pump(sample_ms)
    finally:
        window.frameSwapped.disconnect(on_frame)
    return [(b - a) * 1000 for a, b in zip(stamps, stamps[1:])]


def _percentile(values, ratio):
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, round((len(values) - 1) * ratio))]


def _objects(window):
    return [window, *window.findChildren(QObject)]


def _resident_count(stack):
    loaders = stack.property("_loaders")
    if hasattr(loaders, "toVariant"):
        loaders = loaders.toVariant()
    return sum(
        loader is not None and loader.property("item") is not None
        for loader in (loaders or [])
    )


def _write_pages(root: Path, count: int):
    urls = []
    for index in range(count):
        page = root / f"retention_bench_{index}.qml"
        page.write_text(
            "import QtQuick\nimport PrismQML\n"
            "Item {\n"
            f"objectName: \"benchPage-{index}\"\n"
            "MatrixRain { anchors.fill: parent; running: true; density: 0.7; schedulerActive: true }\n"
            "}\n",
            encoding="utf-8",
        )
        urls.append(QUrl.fromLocalFile(str(page)).toString())
    return urls


def main(argv=None):
    args = _parse_args(argv)
    if args.pages < 2:
        raise SystemExit("--pages must be at least 2")
    configure_qml_environment()
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QGuiApplication(sys.argv)
    messages = []
    previous = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)

    with tempfile.TemporaryDirectory(prefix="prismqml-retention-") as temp_dir:
        urls = _write_pages(Path(temp_dir), args.pages)
        source = QML_TEMPLATE.replace("__RADIUS__", str(args.radius)).replace(
            "__SOURCES__", ", ".join(f'"{url}"' for url in urls)
        )
        component = QQmlComponent(engine)
        component.setData(
            source.encode("utf-8"),
            QUrl.fromLocalFile(str(ROOT / "tests/qml/stacked-page-retention-bench.qml")),
        )
        while component.status() == QQmlComponent.Status.Loading:
            _pump()
        if component.status() != QQmlComponent.Status.Ready:
            raise RuntimeError("; ".join(error.toString() for error in component.errors()))
        created_at = time.perf_counter()
        window = component.create(engine.rootContext())
        create_ms = (time.perf_counter() - created_at) * 1000
        if not isinstance(window, QQuickWindow):
            raise RuntimeError("retention benchmark window creation failed")
        first_frame_ms = _wait_for_frame(window, window.show)
        api = window.rendererInterface().graphicsApi()
        api_name = getattr(api, "name", str(api))
        actual_api_name = api_name
        if actual_api_name != "Direct3D11":
            raise RuntimeError(f"retention benchmark requires Direct3D11; actual={api_name}")
        stack = window.findChild(QObject, "retentionStack")
        if stack is None:
            raise RuntimeError("retention stack missing")

        ready_started = time.perf_counter()
        for index in range(args.pages):
            stack.setProperty("currentIndex", index)
            elapsed = 0
            while elapsed < 15000:
                _pump(20)
                loaded = _resident_count(stack)
                if loaded > 0:
                    current = stack.property("_displayIndex")
                    if int(current) == index:
                        break
                elapsed += 20
        ready_ms = (time.perf_counter() - ready_started) * 1000
        intervals = _sample_intervals(window, args.sample_ms)
        failures = [
            message for mode, message in messages
            if mode in QT_FAILURE_TYPES and not message.startswith(KNOWN_WARNINGS)
        ]
        if failures:
            raise RuntimeError("; ".join(failures))
        result = {
            "radius": args.radius,
            "pages": args.pages,
            "sample_ms": args.sample_ms,
            "requested_graphics_api": "Direct3D11",
            "actual_graphics_api": api_name,
            "create_ms": round(create_ms, 3),
            "first_frame_ms": round(first_frame_ms, 3),
            "all_pages_ready_ms": round(ready_ms, 3),
            "resident_loaders": _resident_count(stack),
            "object_count": len(_objects(window)),
            "frame_interval_p95_ms": round(_percentile(intervals, 0.95), 3),
            "frame_interval_max_ms": round(max(intervals), 3) if intervals else 0.0,
            "frames_over_20ms": sum(value > 20 for value in intervals),
            "frames_over_33ms": sum(value > 33 for value in intervals),
            "qt_failures": failures,
        }
        args.result_file.parent.mkdir(parents=True, exist_ok=True)
        args.result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        window.close()
        qInstallMessageHandler(previous)
        app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
