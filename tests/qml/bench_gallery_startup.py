# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Measure the real Windows Gallery startup path. 测量真实 Windows Gallery 启动路径。

This benchmark is intentionally excluded from the automated suite because it
creates a real Direct3D 11 window. Run it through ``scripts/test_process.py``
with the Windows platform so the window stays on the isolated test desktop.
本基准会创建真实 Direct3D 11 窗口，因此不进入自动测试集；运行时必须通过
``scripts/test_process.py`` 的 Windows 私有桌面边界。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path


RESULT_PREFIX = "PRISMQML_GALLERY_STARTUP="
WINDOW_TYPE_NAMES = {0: "split", 1: "bar", 2: "filled"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--window-type", type=int, choices=sorted(WINDOW_TYPE_NAMES), required=True)
    parser.add_argument(
        "--graphics-api",
        choices=("main", "direct3d11"),
        default="main",
        help="Use the Gallery entrypoint backend or explicitly request Direct3D 11.",
    )
    parser.add_argument("--result", type=Path)
    parser.add_argument("--snapshot-dir", type=Path)
    parser.add_argument(
        "--move-offscreen",
        action="store_true",
        help="Move the real window off the active desktop before the event loop starts.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser.parse_args()


def _enum_value(value) -> int:
    enum_value = getattr(value, "value", value)
    return int(enum_value)


def _image_payload(image) -> tuple[str, bytes]:
    from PySide6.QtGui import QImage

    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    pixels = bytes(converted.bits()[: converted.sizeInBytes()])
    return hashlib.sha256(pixels).hexdigest(), pixels


def _write_config(path: Path, window_type: int) -> None:
    payload = {
        "Window": {
            "LazyLoading": True,
            "DwmShadow": True,
            "MicaEnabled": True,
            "DpiScale": 0,
            "WindowType": window_type,
        }
    }
    path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def _run(args: argparse.Namespace) -> int:
    process_start = time.perf_counter()
    repo = args.repo.resolve()
    qml_path = repo / "examples" / "main.qml"
    if not qml_path.is_file():
        raise FileNotFoundError(f"Gallery QML not found: {qml_path}")

    sys.path.insert(0, str(repo))
    os.chdir(repo)

    from PySide6.QtCore import QCoreApplication, QObject, QTimer
    from PySide6.QtGui import QImage
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

    if args.graphics_api == "direct3d11":
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)

    import prismqml.python.config.config_manager as config_manager_module

    temporary_config = tempfile.TemporaryDirectory(prefix="prismqml-gallery-startup-")
    config_path = Path(temporary_config.name) / "app.json"
    _write_config(config_path, args.window_type)
    config_manager_module.DEFAULT_APP_CONFIG = config_path
    config_manager_module.ConfigManager._instance = None

    import examples.main as gallery

    output: dict[str, object] = {
        "repo": str(repo),
        "window_type": args.window_type,
        "window_type_name": WINDOW_TYPE_NAMES[args.window_type],
        "requested_graphics_api": args.graphics_api,
    }
    probes: list[object] = []

    def elapsed_ms(moment: float) -> float:
        return round((moment - process_start) * 1000.0, 4)

    def publish(exit_code: int) -> None:
        serialized = json.dumps(output, ensure_ascii=False, sort_keys=True)
        if args.result:
            args.result.parent.mkdir(parents=True, exist_ok=True)
            args.result.write_text(serialized, encoding="utf-8")
        print(f"{RESULT_PREFIX}{serialized}", flush=True)
        QCoreApplication.exit(exit_code)

    class _StartupProbe(QObject):
        def __init__(self, engine, load_start: float, load_end: float) -> None:
            super().__init__(engine)
            self.engine = engine
            self.load_start = load_start
            self.load_end = load_end
            self.window = None
            self.frame_count = 0
            self.first_frame_at: float | None = None
            self.splash_captured = False
            self.ready_landmark_at: float | None = None
            self.ready_landmark_frame = -1
            self.timer = QTimer(self)
            self.timer.setInterval(5)
            self.timer.timeout.connect(self.poll)
            self.timer.start()
            output["qml_load_ms"] = round((load_end - load_start) * 1000.0, 4)
            output["qml_load_end_ms"] = elapsed_ms(load_end)
            self._attach_loaded_window()

        def _attach_loaded_window(self) -> None:
            roots = self.engine.rootObjects()
            root = roots[0] if roots else None
            window = root.property("windowInstance") if root is not None else None
            if window is None:
                return
            self.window = window
            output["window_instance_ms"] = elapsed_ms(time.perf_counter())
            if args.move_offscreen:
                window.setPosition(-32000, -32000)
                output["window_moved_offscreen"] = True
            window.frameSwapped.connect(self._frame_swapped)

        def _frame_swapped(self) -> None:
            self.frame_count += 1
            if self.first_frame_at is None:
                self.first_frame_at = time.perf_counter()
                output["first_frame_ms"] = elapsed_ms(self.first_frame_at)

        def _snapshot(self):
            roots = self.engine.rootObjects()
            root = roots[0] if roots else None
            window = root.property("windowInstance") if root is not None else None
            stack = window.property("stackedWidget") if window is not None else None
            navigation = window.property("navigationView") if window is not None else None
            current = stack.property("currentWidget") if stack is not None else None
            page_ready = False
            if current is not None:
                item_index = current.metaObject().indexOfProperty("item")
                page_ready = item_index < 0 or current.property("item") is not None
            children = window.findChildren(QObject) if window is not None else []
            captions = [
                child for child in children
                if "CaptionButton" in child.metaObject().className()
            ]
            splash = window.property("_splashInstance") if window is not None else None
            return root, window, stack, navigation, page_ready, captions, splash

        def _capture(self, label: str) -> bool:
            image = self.window.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
            if image.isNull():
                return False
            digest, _pixels = _image_payload(image)
            output[f"{label}_rgba_sha256"] = digest
            output[f"{label}_image_size"] = [image.width(), image.height()]
            if args.snapshot_dir:
                args.snapshot_dir.mkdir(parents=True, exist_ok=True)
                path = args.snapshot_dir / (
                    f"{WINDOW_TYPE_NAMES[args.window_type]}-{label}.png"
                )
                if not image.save(str(path), "PNG"):
                    raise RuntimeError(f"Failed to save benchmark snapshot: {path}")
                output[f"{label}_snapshot"] = str(path.resolve())
            return True

        def _finish_success(self, window, captions) -> None:
            output["frame_count"] = self.frame_count
            output["caption_count"] = len(captions)
            output["window_class"] = window.metaObject().className()
            actual_api = window.rendererInterface().graphicsApi()
            output["actual_graphics_api"] = getattr(
                actual_api, "name", str(_enum_value(actual_api))
            )
            output["dwm_initialization_done"] = bool(
                window.property("_dwmInitializationDone")
            )
            output["native_hook_ready"] = bool(window.property("_nativeHookReady"))
            output["show_animation_start_count"] = int(
                window.property("_showAnimationStartCount") or 0
            )
            output["splash_dismissed"] = bool(window.property("_splashDismissed"))
            output["ready_frame_ms"] = elapsed_ms(time.perf_counter())
            self._capture("ready")
            self.timer.stop()
            publish(0)

        def _poll(self) -> None:
            now = time.perf_counter()
            root, window, stack, navigation, page_ready, captions, splash = self._snapshot()
            if window is not None and self.window is None:
                self.window = window
                output["window_instance_ms"] = elapsed_ms(now)
                if args.move_offscreen:
                    window.setPosition(-32000, -32000)
                    output["window_moved_offscreen"] = True
                window.frameSwapped.connect(self._frame_swapped)
            if stack is not None and "stacked_widget_ms" not in output:
                output["stacked_widget_ms"] = elapsed_ms(now)
            if page_ready and "first_page_ready_ms" not in output:
                output["first_page_ready_ms"] = elapsed_ms(now)

            if (
                self.window is not None
                and self.first_frame_at is not None
                and splash is not None
                and bool(splash.property("visible"))
                and float(window.property("_animOpacity") or 0.0) >= 0.999
                and not self.splash_captured
            ):
                self.splash_captured = self._capture("splash")

            show_complete = (
                window is not None
                and bool(window.property("_showAnimationStarted"))
                and float(window.property("_animOpacity") or 0.0) >= 0.999
                and float(window.property("_animScale") or 0.0) >= 0.999
            )
            splash_complete = (
                splash is None or not bool(splash.property("visible"))
            )
            shell_ready = (
                root is not None
                and window is not None
                and stack is not None
                and navigation is not None
                and page_ready
                and len(captions) == 3
                and bool(window.property("_dwmInitializationDone"))
                and bool(window.property("_nativeHookReady"))
                and show_complete
                and splash_complete
            )
            if shell_ready and self.ready_landmark_at is None:
                self.ready_landmark_at = now
                self.ready_landmark_frame = self.frame_count
                output["shell_ready_ms"] = elapsed_ms(now)
                window.requestUpdate()
                return
            if (
                self.ready_landmark_at is not None
                and self.frame_count > self.ready_landmark_frame
            ):
                self._finish_success(window, captions)
                return

            if now - process_start > args.timeout:
                output.update(
                    {
                        "error": "timeout",
                        "frame_count": self.frame_count,
                        "has_root": root is not None,
                        "has_window": window is not None,
                        "has_stack": stack is not None,
                        "has_navigation": navigation is not None,
                        "page_ready": page_ready,
                        "caption_count": len(captions),
                        "splash_complete": splash_complete,
                        "show_complete": show_complete,
                    }
                )
                self.timer.stop()
                publish(3)

        def poll(self) -> None:
            try:
                self._poll()
            except (OSError, RuntimeError, TypeError, ValueError) as error:
                output["error"] = f"probe {type(error).__name__}: {error}"
                self.timer.stop()
                publish(4)

    class _BenchEngine(QQmlApplicationEngine):
        def load(self, url) -> None:
            load_start = time.perf_counter()
            super().load(url)
            load_end = time.perf_counter()
            probe = _StartupProbe(self, load_start, load_end)
            probes.append(probe)

    if args.graphics_api == "direct3d11":
        class _GraphicsApiGuard:
            @staticmethod
            def setGraphicsApi(_api) -> None:
                """Keep the selected D3D backend. 保留基准选择的 D3D 后端。"""

        gallery.QQuickWindow = _GraphicsApiGuard
    gallery.QQmlApplicationEngine = _BenchEngine
    try:
        return int(gallery.main())
    finally:
        temporary_config.cleanup()


def main() -> int:
    args = _parse_args()
    try:
        return _run(args)
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        payload = {"error": f"{type(error).__name__}: {error}"}
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if args.result:
            args.result.parent.mkdir(parents=True, exist_ok=True)
            args.result.write_text(serialized, encoding="utf-8")
        print(f"{RESULT_PREFIX}{serialized}", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
