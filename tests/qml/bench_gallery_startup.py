# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Measure the real Windows Gallery startup path. 测量真实 Windows Gallery 启动路径。

This benchmark is intentionally excluded from the automated suite because it
creates a real Direct3D 11 window. Run it on the active Windows desktop; an
isolated desktop cannot provide the real swap-chain path. Use
``--move-offscreen`` to keep the window outside the visible work area.
本基准会创建真实 Direct3D 11 窗口，因此不进入自动测试集；必须在 Windows
活动桌面运行，私有桌面无法提供真实交换链。可用 ``--move-offscreen`` 将窗口
移出可见工作区。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path


RESULT_PREFIX = "PRISMQML_GALLERY_STARTUP="
WINDOW_TYPE_NAMES = {0: "split", 1: "bar", 2: "filled"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--window-type", type=int, choices=sorted(WINDOW_TYPE_NAMES), required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--snapshot-dir", type=Path)
    parser.add_argument(
        "--lazy-loading",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep page loading lazy; use --no-lazy-loading for eager startup.",
    )
    parser.add_argument(
        "--move-offscreen",
        action="store_true",
        help="Move the real window off the active desktop before the event loop starts.",
    )
    parser.add_argument(
        "--profile-objects",
        action="store_true",
        help="Record one visual QQuickItem class histogram after the ready landmark.",
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


def _write_config(path: Path, window_type: int, lazy_loading: bool) -> None:
    payload = {
        "Window": {
            "LazyLoading": lazy_loading,
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
    from PySide6.QtGui import QGuiApplication, QImage
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickItem

    import prismqml.python.config.config_manager as config_manager_module

    temporary_config = tempfile.TemporaryDirectory(prefix="prismqml-gallery-startup-")
    config_path = Path(temporary_config.name) / "app.json"
    _write_config(config_path, args.window_type, args.lazy_loading)
    config_manager_module.DEFAULT_APP_CONFIG = config_path
    config_manager_module.ConfigManager._instance = None

    import examples.main as gallery

    output: dict[str, object] = {
        "repo": str(repo),
        "window_type": args.window_type,
        "window_type_name": WINDOW_TYPE_NAMES[args.window_type],
        "lazy_loading": args.lazy_loading,
        "requested_graphics_api": "direct3d11",
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
            self.captions: list[QObject] = []
            self.stack = None
            self.first_page_item: QQuickItem | None = None
            self.first_page_loaded = False
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
            output["observed_lazy_loading"] = bool(window.property("lazyLoading"))
            if args.move_offscreen:
                window.setPosition(-32000, -32000)
                output["window_moved_offscreen"] = True
            window.frameSwapped.connect(self._frame_swapped)

        def _frame_swapped(self) -> None:
            self.frame_count += 1
            if self.first_frame_at is None:
                self.first_frame_at = time.perf_counter()
                output["first_frame_ms"] = elapsed_ms(self.first_frame_at)

        def _record_startup_presentation(self, window) -> None:
            if output.get("startup_presentation_ready_ms") is not None:
                return
            if bool(window.property("_startupPresentationReady")):
                output["startup_presentation_ready_ms"] = elapsed_ms(
                    time.perf_counter()
                )

        @staticmethod
        def _qml_class_name(obj: QObject) -> str:
            return obj.metaObject().className().split("_QMLTYPE_", 1)[0]

        @staticmethod
        def _current_page_item(stack) -> QQuickItem | None:
            if stack is None or int(stack.property("currentIndex")) != 0:
                return None
            current = stack.property("currentWidget")
            if current is None:
                return None
            item_index = current.metaObject().indexOfProperty("item")
            item = current if item_index < 0 else current.property("item")
            return item if isinstance(item, QQuickItem) else None

        def _mark_first_page_loaded(self, item: QQuickItem, source: str) -> None:
            if self.first_page_loaded:
                return
            class_name = self._qml_class_name(item)
            if class_name != "ButtonPage":
                output["error"] = (
                    "First Gallery page must be ButtonPage; "
                    f"got {class_name}"
                )
                self.timer.stop()
                publish(6)
                return
            self.first_page_item = item
            self.first_page_loaded = True
            output["first_page_class"] = class_name
            output["first_page_ready_source"] = source
            output["first_page_ready_ms"] = elapsed_ms(time.perf_counter())

        def _page_loaded(self, index: int) -> None:
            if int(index) != 0 or self.stack is None:
                return
            item = self._current_page_item(self.stack)
            if item is not None:
                self._mark_first_page_loaded(item, "pageLoaded")

        def _observe_stack(self, stack) -> None:
            if stack is None or stack is self.stack:
                return
            self.stack = stack
            stack.pageLoaded.connect(self._page_loaded)
            output["stacked_widget_ms"] = elapsed_ms(time.perf_counter())
            item = self._current_page_item(stack)
            if item is not None:
                self._mark_first_page_loaded(item, "loaderReadyBeforeSignalAttach")

        @staticmethod
        def _visual_items(window) -> list[QQuickItem]:
            content_item = window.contentItem()
            if content_item is None:
                return []
            result: list[QQuickItem] = []
            pending = [content_item]
            while pending:
                item = pending.pop()
                result.append(item)
                pending.extend(item.childItems())
            return result

        def _snapshot(self):
            roots = self.engine.rootObjects()
            root = roots[0] if roots else None
            window = root.property("windowInstance") if root is not None else None
            stack = window.property("stackedWidget") if window is not None else None
            navigation = window.property("navigationView") if window is not None else None
            self._observe_stack(stack)
            page_ready = self.first_page_loaded
            if window is not None and len(self.captions) != 3:
                self.captions = [
                    child for child in window.findChildren(QObject)
                    if "CaptionButton" in child.metaObject().className()
                ]
            splash = window.property("_splashInstance") if window is not None else None
            return root, window, stack, navigation, page_ready, self.captions, splash

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
            actual_api_name = getattr(
                actual_api, "name", str(_enum_value(actual_api))
            )
            output["actual_graphics_api"] = actual_api_name
            if actual_api_name != "Direct3D11":
                output["error"] = (
                    "Gallery startup benchmark requires Direct3D11; "
                    f"got {actual_api_name}"
                )
                self.timer.stop()
                publish(5)
                return
            output["dwm_initialization_done"] = bool(
                window.property("_dwmInitializationDone")
            )
            output["native_hook_ready"] = bool(window.property("_nativeHookReady"))
            output["show_animation_start_count"] = int(
                window.property("_showAnimationStartCount") or 0
            )
            output["splash_dismissed"] = bool(window.property("_splashDismissed"))
            output["ready_frame_ms"] = elapsed_ms(time.perf_counter())
            if args.profile_objects:
                visual_items = self._visual_items(window)
                class_counts = Counter(
                    self._qml_class_name(item) for item in visual_items
                )
                output["visual_item_count"] = len(visual_items)
                output["visual_item_class_counts"] = dict(class_counts.most_common())
            self._capture("ready")
            self.timer.stop()
            publish(0)

        def _poll(self) -> None:
            now = time.perf_counter()
            root, window, stack, navigation, page_ready, captions, splash = self._snapshot()
            if window is not None:
                self._record_startup_presentation(window)
            if window is not None and self.window is None:
                self.window = window
                output["window_instance_ms"] = elapsed_ms(now)
                if args.move_offscreen:
                    window.setPosition(-32000, -32000)
                    output["window_moved_offscreen"] = True
                window.frameSwapped.connect(self._frame_swapped)
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
                if window is not None:
                    application_state = QGuiApplication.applicationState()
                    output["application_state"] = getattr(
                        application_state,
                        "name",
                        str(_enum_value(application_state)),
                    )
                    output["window_visible"] = bool(window.isVisible())
                    output["window_exposed"] = bool(window.isExposed())
                    output["window_active"] = bool(window.isActive())
                    output["window_opacity"] = float(window.opacity())
                    output["dwm_initialization_done"] = bool(
                        window.property("_dwmInitializationDone")
                    )
                    output["native_hook_ready"] = bool(
                        window.property("_nativeHookReady")
                    )
                    output["show_animation_started"] = bool(
                        window.property("_showAnimationStarted")
                    )
                    output["show_animation_start_count"] = int(
                        window.property("_showAnimationStartCount") or 0
                    )
                    if args.profile_objects:
                        visual_items = self._visual_items(window)
                        class_counts = Counter(
                            self._qml_class_name(item) for item in visual_items
                        )
                        output["timeout_visual_item_count"] = len(visual_items)
                        output["timeout_visual_item_class_counts"] = dict(
                            class_counts.most_common()
                        )
                        timer_states = []
                        for child in window.findChildren(QObject):
                            meta = child.metaObject()
                            if (
                                meta.indexOfProperty("interval") < 0
                                or meta.indexOfProperty("running") < 0
                            ):
                                continue
                            timer_states.append(
                                {
                                    "class": self._qml_class_name(child),
                                    "object_name": child.objectName(),
                                    "interval": int(child.property("interval") or 0),
                                    "running": bool(child.property("running")),
                                    "repeat": bool(child.property("repeat")),
                                }
                            )
                        output["timeout_timer_states"] = timer_states
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
