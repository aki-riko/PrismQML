# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Canned SSE backend for the Gallery AI assistant page. Gallery AI 助手页的固定话术 SSE 后端。

Gallery 需要一个**真实**的流式后端来演示聊天组件的增量渲染，但又不该真的去接一个大模型：
本模块用标准库起一个只监听 127.0.0.1 临时端口的 SSE 服务，把一段固定话术按事件逐块吐出来。

The demo deliberately speaks the wire format a real provider would use, so the QML side exercises
the same incremental parsing and the same "reasoning / delta / done" event split:
演示严格使用真实服务商会上线的线格式，QML 侧因此走的是同一套增量解析与
「推理 / 正文增量 / 结束」事件划分：

    event: reasoning
    data: {"text": "..."}

    event: delta
    data: {"text": "..."}

    event: done
    data: {"finish_reason": "stop"}

🔴 话术放在 Python 而不是 QML：Gallery 的 i18n 门禁会把 QML 里的中文字面量全部登记成待翻译项，
   演示内容不该逼着 20 份语言目录各翻一遍。
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterable, Iterator, Sequence

# 每块之间的间隔：既让"打字机"效果看得见，又不至于让演示等太久。
REASONING_DELAY_SECONDS = 0.18
DELTA_DELAY_SECONDS = 0.05

REASONING_CHUNKS: tuple[str, ...] = (
    "先确认一下问题边界：",
    "气泡的外观不该由每个界面各写一份，",
    "而应该由组件自己按皮肤令牌决定。",
)

# 正文按 markdown 增量下发：标题、列表、行内代码与围栏代码块都要覆盖到，
# 这样 MarkdownView / CodeBlock 的增量重排也能一并演示。
DELTA_CHUNKS: tuple[str, ...] = (
    "## 气泡由谁负责\n",
    "聊天界面只需要提供内容，**外壳**收在引擎里：\n\n",
    "- 表面色、圆角与尖角走皮肤令牌\n",
    "- 描边与阴影层级按角色分流\n",
    "- 换肤、深色模式、主题色一起跟随\n\n",
    "```qml\n",
    "ChatBubbleSurface {\n",
    "    role: \"user\"\n",
    "    tail: true\n",
    "}\n",
    "```\n\n",
    "流式输出本身只追加文本，不动布局高度以外的任何东西。",
)


def sse_frame(event: str, payload: dict[str, object]) -> bytes:
    """Encode one SSE frame. 编码一帧 SSE。

    帧格式按 SSE 规范：`event:` 与 `data:` 各一行，空行结束；JSON 一律压成单行，
    避免 `data:` 被拆成多行后客户端还要自己拼接。
    """
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {body}\n\n".encode("utf-8")


def demo_events() -> Iterator[tuple[float, bytes]]:
    """Yield `(delay, frame)` pairs for one canned answer. 产出一次固定话术的 (间隔, 帧) 序列。"""
    for chunk in REASONING_CHUNKS:
        yield REASONING_DELAY_SECONDS, sse_frame("reasoning", {"text": chunk})
    for chunk in DELTA_CHUNKS:
        yield DELTA_DELAY_SECONDS, sse_frame("delta", {"text": chunk})
    yield 0.0, sse_frame("done", {"finish_reason": "stop"})


class _StreamHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PrismQMLGallerySSE/1.0"

    # 演示服务不需要访问日志，避免污染 Gallery 的启动输出。
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - 基类签名
        return

    def do_GET(self) -> None:  # noqa: N802 - 基类签名
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send_bytes(b"ok", "text/plain; charset=utf-8")
            return
        if path != "/assistant/stream":
            self.send_error(404, "unknown endpoint")
            return
        self._stream_events()

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _stream_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        # 反向代理/中间层不得缓冲：缓冲会把逐块流变成一次性到货，演示就失真了。
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            scale = float(getattr(self.server, "delay_scale", 1.0))  # type: ignore[attr-defined]
            for delay, frame in demo_events():
                if delay:
                    # 用 Event.wait 而不是 sleep：取消时能立刻醒来退出。
                    if self.server.cancel_event.wait(delay * scale):  # type: ignore[attr-defined]
                        break
                self.wfile.write(frame)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # 客户端（或用户）中断了流，属于正常路径。
            return


class AssistantStreamServer:
    """Loopback-only canned SSE server. 仅回环地址的固定话术 SSE 服务。

    `delay_scale` 缩放块间间隔：Gallery 用默认值让"打字机"效果看得见，测试用 0 让整套门禁
    不用等真实节奏（帧序列与线格式完全一致，只是不等）。
    """

    def __init__(self, delay_scale: float = 1.0) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._port = 0
        self._delay_scale = delay_scale

    @property
    def port(self) -> int:
        return self._port

    @property
    def stream_url(self) -> str:
        return f"http://127.0.0.1:{self._port}/assistant/stream"

    def start(self) -> str:
        """Start serving and return the stream URL. 启动服务并返回流地址。"""
        if self._server is not None:
            return self.stream_url
        server = ThreadingHTTPServer(("127.0.0.1", 0), _StreamHandler)
        server.daemon_threads = True
        server.cancel_event = threading.Event()  # type: ignore[attr-defined]
        server.delay_scale = self._delay_scale  # type: ignore[attr-defined]
        self._server = server
        self._port = int(server.server_address[1])
        self._thread = threading.Thread(
            target=server.serve_forever, name="prismqml-gallery-sse", daemon=True
        )
        self._thread.start()
        return self.stream_url

    def cancel_streams(self) -> None:
        """Wake up in-flight streams so they stop at the next chunk. 唤醒在途的流，使其在下一块前停止。"""
        if self._server is not None:
            self._server.cancel_event.set()  # type: ignore[attr-defined]
            self._server.cancel_event.clear()  # type: ignore[attr-defined]

    def stop(self) -> None:
        """Shut the server down. 关闭服务。"""
        server, thread = self._server, self._thread
        self._server = None
        self._thread = None
        self._port = 0
        if server is None:
            return
        server.cancel_event.set()  # type: ignore[attr-defined]
        server.shutdown()
        server.server_close()
        if thread is not None:
            thread.join(timeout=2.0)


def frames_for(events: Iterable[tuple[float, bytes]]) -> Sequence[bytes]:
    """Test helper: strip delays. 测试辅助：只取帧。"""
    return [frame for _delay, frame in events]
