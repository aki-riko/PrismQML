# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Canned SSE demo for the Gallery assistant page. Gallery 助手页的固定话术 SSE 演示。

`start_assistant_demo()` 起一个仅回环地址的 SSE 服务，并把 QML 需要的一切装配成一个上下文属性：

    aiAssistantDemo.available        演示后端是否就绪
    aiAssistantDemo.errorText        起不来时的原因（页面显示降级提示）
    aiAssistantDemo.previewMessages  静态会话（role / content / reasoning / timestamp）
    aiAssistantDemo.surfaceShowcase  气泡壳矩阵（role / tail / elevationOnUser / label）
    aiAssistantDemo.stream           流式桥（streaming / frameCount / start() / cancel()）

起不来时**不抛异常**：Gallery 仍然要能打开这个页面，只是流式那一栏显示"演示后端不可用"。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from examples.ai_demo.demo_script import PREVIEW_MESSAGES, SUGGESTIONS, SURFACE_SHOWCASE
from examples.ai_demo.sse_demo_server import AssistantStreamServer
from examples.ai_demo.sse_stream_bridge import AssistantStreamBridge

__all__ = ["AssistantDemo", "start_assistant_demo"]


class AssistantDemo(QObject):
    """Owns the canned server, the QML bridge and the demo script. 持有固定话术服务、流式桥与演示稿。"""

    stateChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None, delay_scale: float = 1.0) -> None:
        super().__init__(parent)
        self._server = AssistantStreamServer(delay_scale=delay_scale)
        self._bridge = AssistantStreamBridge("", self)
        self._error = ""

    # ==================== QML 属性 ====================
    @Property(QObject, constant=True)
    def stream(self) -> AssistantStreamBridge:
        return self._bridge

    @Property(bool, notify=stateChanged)
    def available(self) -> bool:
        return bool(self._bridge.streamUrl)

    @Property(str, notify=stateChanged)
    def errorText(self) -> str:
        return self._error

    @Property("QVariantList", constant=True)
    def previewMessages(self) -> list:
        return [dict(message) for message in PREVIEW_MESSAGES]

    @Property("QVariantList", constant=True)
    def suggestions(self) -> list:
        return list(SUGGESTIONS)

    @Property("QVariantList", constant=True)
    def surfaceShowcase(self) -> list:
        return [dict(row) for row in SURFACE_SHOWCASE]

    # ==================== 生命周期 ====================
    @Slot()
    def start(self) -> None:
        """Start the loopback SSE server. 启动回环 SSE 服务（失败降级，不抛）。"""
        if self._bridge.streamUrl:
            return
        try:
            url = self._server.start()
        except OSError as error:  # 端口/权限异常：页面显示降级提示
            self._error = str(error)
            self.stateChanged.emit()
            return
        self._bridge.setStreamUrl(url)
        self.stateChanged.emit()

    @Slot()
    def stop(self) -> None:
        self._server.stop()

    # 演示只在 Gallery 进程内使用，退出时随父对象销毁即可；显式 stop 供测试调用。


def start_assistant_demo(
    parent: Optional[QObject] = None, delay_scale: float = 1.0
) -> AssistantDemo:
    """Start the demo backend. 启动演示后端。"""
    demo = AssistantDemo(parent, delay_scale=delay_scale)
    demo.start()
    return demo
