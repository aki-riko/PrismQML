# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Measure real Windows Gallery startup milestones. 测量真实 Windows Gallery 启动里程碑。"""

from __future__ import annotations

import json
import re
import time


STARTED_NS = time.perf_counter_ns()

import examples.main as gallery
from PySide6.QtCore import QObject, QTimer
from PySide6.QtQuick import QQuickWindow


RESULT_PREFIX = "PRISMQML_GALLERY_PROBE="
POLL_INTERVAL_MS = 1
TIMEOUT_MS = 15_000
EXPECTED_CAPTION_BUTTON_COUNT = 3

METRICS: dict[str, object] = {}
STATE: dict[str, object] = {}
ORIGINAL_APPLICATION = gallery.QApplication
ORIGINAL_ENGINE = gallery.QQmlApplicationEngine
ORIGINAL_LOG_TIME = gallery.log_time
EVENT_NAMES = {
    "QApplication创建完成": "app_created_ms",
    "QML引擎创建完成": "engine_created_ms",
    "上下文属性注册完成": "context_ready_ms",
    "开始加载QML": "qml_start_ms",
    "QML加载完成": "qml_end_ms",
    "窗口准备就绪，进入事件循环": "event_loop_ready_ms",
}


def elapsed_ms() -> float:
    """Return elapsed process-probe time. 返回探针进程已耗时。"""
    return (time.perf_counter_ns() - STARTED_NS) / 1_000_000


def create_engine():
    """Retain the Gallery engine for readiness inspection. 保留 Gallery 引擎供就绪检查。"""
    engine = ORIGINAL_ENGINE()
    STATE["engine"] = engine
    return engine


def capture_log_time(message: str) -> None:
    """Capture existing Gallery timing markers. 捕获 Gallery 现有计时标记。"""
    metric_name = EVENT_NAMES.get(message)
    if metric_name is not None:
        METRICS[metric_name] = elapsed_ms()
    ORIGINAL_LOG_TIME(message)


def normalized_type(obj: QObject) -> str:
    """Strip generated QML suffixes from a meta-object type. 去除 QML 生成类型后缀。"""
    name = obj.metaObject().className()
    name = re.sub(r"_QMLTYPE_\d+", "", name)
    return re.sub(r"_QML_\d+", "", name)


def current_page_ready(stack: QObject) -> bool:
    """Require the current lazy page instance, not only its Loader. 要求当前懒加载页面实例存在。"""
    current_widget = stack.property("currentWidget")
    if current_widget is None:
        return False
    if bool(stack.property("_useSourceMode")):
        return current_widget.property("item") is not None
    return True


def enum_name(value: object) -> str:
    """Normalize a PySide enum name for JSON. 统一 PySide 枚举名称供 JSON 输出。"""
    name = getattr(value, "name", None)
    return str(name if name is not None else value)


class BenchmarkApplication(ORIGINAL_APPLICATION):
    """Run Gallery until the complete home scene reaches a D3D frame. 运行至完整主页进入 D3D 帧。"""

    def exec(self) -> int:
        METRICS["qml_load_return_ms"] = elapsed_ms()
        METRICS["requested_graphics_api"] = enum_name(QQuickWindow.graphicsApi())
        root = STATE["engine"].rootObjects()[0]
        window = root.property("windowInstance")
        METRICS["window_visible_at_load_return"] = bool(window.isVisible())
        METRICS["window_type"] = normalized_type(window)
        state = {
            "caption_count": None,
            "navigation": None,
            "quit_scheduled": False,
            "ready_frame_armed": False,
            "stack": None,
        }

        def schedule_quit() -> None:
            if "ready_frame_ms" not in METRICS or state["quit_scheduled"]:
                return
            state["quit_scheduled"] = True
            QTimer.singleShot(0, self.quit)

        def on_frame_swapped() -> None:
            METRICS["frame_count"] = int(METRICS.get("frame_count", 0)) + 1
            now_ms = elapsed_ms()
            if "first_frame_ms" not in METRICS:
                METRICS["first_frame_ms"] = now_ms
                METRICS["renderer_graphics_api"] = enum_name(
                    window.rendererInterface().graphicsApi()
                )
            if state["ready_frame_armed"] and "ready_frame_ms" not in METRICS:
                METRICS["ready_frame_ms"] = now_ms
                schedule_quit()

        def cache_shell_objects() -> None:
            if state["navigation"] is None:
                state["navigation"] = window.property("navigationView")
            if state["stack"] is None:
                state["stack"] = window.property("stackedWidget")
            if state["caption_count"] != EXPECTED_CAPTION_BUTTON_COUNT:
                state["caption_count"] = sum(
                    normalized_type(obj) == "CaptionButton"
                    for obj in window.findChildren(QObject)
                )
                METRICS["caption_button_count"] = state["caption_count"]

        def poll_ready() -> None:
            cache_shell_objects()
            stack = state["stack"]
            page_ready = stack is not None and current_page_ready(stack)
            dismiss_requested = bool(window.property("_splashDismissRequested"))
            if page_ready and dismiss_requested:
                METRICS.setdefault("home_ready_ms", elapsed_ms())

            dismiss_started = bool(window.property("_splashDismissed"))
            if dismiss_started:
                METRICS.setdefault("splash_dismiss_started_ms", elapsed_ms())
            splash = window.property("_splashInstance")
            splash_finished = splash is None or not bool(splash.property("visible"))
            if dismiss_started and splash_finished:
                METRICS.setdefault("splash_finished_ms", elapsed_ms())

            ready = (
                state["navigation"] is not None
                and stack is not None
                and state["caption_count"] == EXPECTED_CAPTION_BUTTON_COUNT
                and page_ready
                and dismiss_requested
                and splash_finished
                and bool(window.property("_showAnimationStarted"))
                and bool(window.property("_dwmInitializationDone"))
            )
            if not ready or "shell_ready_ms" in METRICS:
                return
            METRICS["shell_ready_ms"] = elapsed_ms()
            METRICS["lazy_loading"] = bool(window.property("lazyLoading"))
            METRICS["mica_enabled"] = bool(window.property("micaEnabled"))
            METRICS["mica_active"] = bool(window.property("_micaActive"))
            METRICS["shadow_mode"] = int(window.property("shadowMode"))
            METRICS["dwm_initialization_done"] = bool(
                window.property("_dwmInitializationDone")
            )
            METRICS["show_animation_started"] = bool(
                window.property("_showAnimationStarted")
            )
            METRICS["splash_visible"] = bool(
                splash is not None and splash.property("visible")
            )
            state["ready_frame_armed"] = True
            window.requestUpdate()

        window.frameSwapped.connect(on_frame_swapped)
        poll_timer = QTimer(self)
        poll_timer.setInterval(POLL_INTERVAL_MS)
        poll_timer.timeout.connect(poll_ready)
        poll_timer.start()
        timeout = QTimer(self)
        timeout.setSingleShot(True)
        timeout.setInterval(TIMEOUT_MS)
        timeout.timeout.connect(self.quit)
        timeout.start()
        STATE["poll_timer"] = poll_timer
        STATE["timeout"] = timeout
        result = super().exec()
        METRICS["timed_out"] = "ready_frame_ms" not in METRICS
        return result


gallery.QApplication = BenchmarkApplication
gallery.QQmlApplicationEngine = create_engine
gallery.log_time = capture_log_time
EXIT_CODE = gallery.main()
METRICS["exit_code"] = EXIT_CODE
print(RESULT_PREFIX + json.dumps(METRICS, ensure_ascii=False, sort_keys=True), flush=True)
