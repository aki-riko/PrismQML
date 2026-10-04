# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Bridge a Server-Sent-Events stream into QML signals. 把 SSE 流桥接成 QML 可消费的信号。

QML 的 `XMLHttpRequest` 拿不到增量（它只在请求结束时给出完整正文），所以流式渲染必须由宿主
侧接：本类用 `QNetworkAccessManager` 读 `text/event-stream`，按帧解析后逐块发信号，
QML 只负责把增量追加到自己的文本属性上。

Gallery 用固定话术的本地服务演示这条链路，接口形态与真实服务商一致：
`reasoning`（推理）/ `delta`（正文增量）/ `done`（结束）/ `error`。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class AssistantStreamBridge(QObject):
    """Expose one SSE stream to QML. 向 QML 暴露一条 SSE 流。"""

    reasoningChunk = Signal(str)
    deltaChunk = Signal(str)
    finished = Signal()
    failed = Signal(str)
    streamingChanged = Signal()

    def __init__(self, stream_url: str = "", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._url = stream_url
        self._manager = QNetworkAccessManager(self)
        self._reply: Optional[QNetworkReply] = None
        self._buffer = bytearray()
        self._streaming = False
        self._error = ""
        # 帧计数器：QML 侧用它证明"确实是分多块到的"，而不是一次到齐后假装流式。
        self._frame_count = 0

    # ==================== QML 属性 ====================
    @Property(bool, notify=streamingChanged)
    def streaming(self) -> bool:
        return self._streaming

    @Property(int, notify=streamingChanged)
    def frameCount(self) -> int:
        return self._frame_count

    @Property(str, notify=streamingChanged)
    def lastError(self) -> str:
        return self._error

    @Property(str, notify=streamingChanged)
    def streamUrl(self) -> str:
        return self._url

    @Property(bool, notify=streamingChanged)
    def available(self) -> bool:
        return bool(self._url)

    # ==================== QML 调用 ====================
    @Slot(str)
    def setStreamUrl(self, url: str) -> None:
        """Wire the endpoint before the first start. 在首次 start 之前接上端点。"""
        self._url = url
        self.streamingChanged.emit()

    @Slot()
    def start(self) -> None:
        """Open the stream. 打开流。"""
        if not self._url or self._streaming:
            return
        self._buffer.clear()
        self._error = ""
        self._frame_count = 0
        request = QNetworkRequest(QUrl(self._url))
        request.setRawHeader(b"Accept", b"text/event-stream")
        # 演示流每次都要最新：任何缓存都会让"流式"变成一次性快照。
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.AlwaysNetwork,
        )
        self._reply = self._manager.get(request)
        self._reply.readyRead.connect(self._on_ready_read)
        self._reply.finished.connect(self._on_finished)
        self._set_streaming(True)

    @Slot()
    def cancel(self) -> None:
        """Abort the stream. 中断流。"""
        if self._reply is not None:
            self._reply.abort()

    # ==================== 内部 ====================
    def _set_streaming(self, value: bool) -> None:
        if self._streaming == value:
            return
        self._streaming = value
        self.streamingChanged.emit()

    def _on_ready_read(self) -> None:
        if self._reply is None:
            return
        self._buffer.extend(bytes(self._reply.readAll()))
        self._drain_frames()

    def _drain_frames(self) -> None:
        """Parse complete frames; keep the remainder buffered. 解析完整帧，残帧留在缓冲里。"""
        while True:
            separator = self._buffer.find(b"\n\n")
            if separator < 0:
                return
            raw = bytes(self._buffer[:separator])
            del self._buffer[: separator + 2]
            event, payload = _parse_frame(raw.decode("utf-8", errors="replace"))
            if event is None:
                continue
            self._frame_count += 1
            if event == "reasoning":
                self.reasoningChunk.emit(str(payload.get("text", "")))
            elif event == "delta":
                self.deltaChunk.emit(str(payload.get("text", "")))
            elif event == "done":
                self.finished.emit()
            else:
                # 未知事件按协议要求忽略，但要计数，便于诊断服务端换了契约。
                self.streamingChanged.emit()

    def _on_finished(self) -> None:
        reply, self._reply = self._reply, None
        if reply is not None:
            if reply.error() not in (QNetworkReply.NetworkError.NoError, QNetworkReply.NetworkError.OperationCanceledError):
                self._error = reply.errorString()
                self.failed.emit(self._error)
            reply.deleteLater()
        self._set_streaming(False)
        self.streamingChanged.emit()


def _parse_frame(raw: str) -> tuple[Optional[str], dict]:
    """Parse one SSE frame into `(event, payload)`. 解析一帧 SSE。

    只认 `event:` 与单行 `data:`；注释行（`:` 开头）与其它字段按规范忽略。
    """
    import json

    event: Optional[str] = None
    data_lines: list[str] = []
    for line in raw.splitlines():
        if not line or line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if field == "event":
            event = value
        elif field == "data":
            data_lines.append(value)
    if event is None or not data_lines:
        return None, {}
    try:
        payload = json.loads("\n".join(data_lines))
    except ValueError:
        return None, {}
    return event, payload if isinstance(payload, dict) else {}
