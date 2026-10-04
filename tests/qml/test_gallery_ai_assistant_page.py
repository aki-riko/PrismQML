# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Gallery AI assistant page and canned SSE backend contracts. Gallery AI 助手页与固定话术 SSE 后端合同。

三件事各有用例：
  1. 服务端编码的帧能被客户端的解析器原样还原（纯函数往返，不碰网络）；
  2. 真的经回环 HTTP 把 `text/event-stream` 拉一遍，帧序与正文都对得上；
  3. QML 页面在流式过程中把增量追加进 ChatMessageList，而不是等流结束后一次成型。
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow

from examples.ai_demo import AssistantDemo
from examples.ai_demo.sse_demo_server import (
    DELTA_CHUNKS,
    REASONING_CHUNKS,
    AssistantStreamServer,
    demo_events,
)
from examples.ai_demo.sse_stream_bridge import _parse_frame
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PAGE_PATH = ROOT / "examples" / "pages" / "AIAssistantPage.qml"
EXPECTED_FRAMES = len(REASONING_CHUNKS) + len(DELTA_CHUNKS) + 1


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 8000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(25)
        elapsed += 25
    return predicate()


def _evaluate(instance: QObject, expression_source: str):
    """Read an internal QML expression. 读取内部 QML 表达式（实例属性拿不到的路径）。"""
    expression = QQmlExpression(
        QQmlEngine.contextForObject(instance), instance, expression_source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return result[0] if isinstance(result, tuple) else result


def test_canned_events_round_trip_through_the_client_parser():
    """服务端编码 ↔ 客户端解析必须逐帧一致（纯函数，不碰网络）。"""
    events: list[tuple[str, dict]] = []
    for _delay, frame in demo_events():
        event, payload = _parse_frame(frame.decode("utf-8").strip())
        assert event is not None, frame
        events.append((event, payload))

    assert [event for event, _payload in events] == (
        ["reasoning"] * len(REASONING_CHUNKS)
        + ["delta"] * len(DELTA_CHUNKS)
        + ["done"]
    )
    reasoning = "".join(payload["text"] for event, payload in events if event == "reasoning")
    content = "".join(payload["text"] for event, payload in events if event == "delta")
    assert reasoning == "".join(REASONING_CHUNKS)
    assert content == "".join(DELTA_CHUNKS)
    assert "```qml" in content and content.rstrip().endswith("流式输出本身只追加文本，不动布局高度以外的任何东西。")
    assert events[-1][1] == {"finish_reason": "stop"}


def test_canned_stream_is_served_over_http_as_event_stream():
    """真拉一遍回环 HTTP：头部、帧数、正文与结束事件都要对。"""
    server = AssistantStreamServer(delay_scale=0.0)
    try:
        url = server.start()
        with urllib.request.urlopen(url, timeout=10) as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/event-stream")
            # 逐块读：真实流式下这里会拿到多次，测试只要求拿到完整字节序列。
            body = b""
            while True:
                chunk = response.read(256)
                if not chunk:
                    break
                body += chunk
    finally:
        server.stop()

    frames = [frame for frame in body.split(b"\n\n") if frame.strip()]
    assert len(frames) == EXPECTED_FRAMES

    parsed = [_parse_frame(frame.decode("utf-8")) for frame in frames]
    assert [event for event, _payload in parsed] == (
        ["reasoning"] * len(REASONING_CHUNKS)
        + ["delta"] * len(DELTA_CHUNKS)
        + ["done"]
    )
    delta_text = "".join(payload["text"] for event, payload in parsed if event == "delta")
    assert delta_text == "".join(DELTA_CHUNKS)
    # `data:` 必须是单行 JSON，客户端才不用拼多行数据。
    assert all(frame.count(b"\ndata:") == 1 for frame in frames)


def test_assistant_demo_reports_unavailable_instead_of_raising(qapp):
    """演示后端起不来时只降级，页面仍要能打开。"""
    demo = AssistantDemo(delay_scale=0.0)
    try:
        assert demo.available is False
        assert demo.errorText == ""
        # 指向一个没人监听的端口：必须走 failed 信号而不是抛异常。
        demo.stream.setStreamUrl("http://127.0.0.1:1/assistant/stream")
        failures: list[str] = []
        demo.stream.failed.connect(failures.append)
        demo.stream.start()
        assert _wait_for(lambda: bool(failures)), "连不上时必须给出失败信号"
        assert _wait_for(lambda: not demo.stream.streaming)
    finally:
        demo.stop()


def test_gallery_assistant_page_streams_into_the_message_list(qapp):
    """QML 端到端：开始流之后，增量要逐块进 ChatMessageList，而不是最后一次性写入。

    ⚠️ 离屏环境不孵化气泡委托（ChatMessageList 只在真正渲染视口附近才把轻量占位换成 ChatBubble），
    所以这里断言可观测链路：帧序、累积正文、列表条数与零告警；气泡渲染本身由聊天组件用例覆盖。
    """
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))

    demo = AssistantDemo(delay_scale=0.0)
    demo.start()
    assert demo.available, demo.errorText

    # 逐块累积：证明内容是分多次到达的，而不是一次性成型。
    reasoning_chunks: list[str] = []
    delta_chunks: list[str] = []
    frame_snapshots: list[int] = []
    finished: list[bool] = []
    demo.stream.reasoningChunk.connect(reasoning_chunks.append)

    def _collect_delta(text: str) -> None:
        delta_chunks.append(text)
        frame_snapshots.append(demo.stream.frameCount)

    demo.stream.deltaChunk.connect(_collect_delta)
    demo.stream.finished.connect(lambda: finished.append(True))
    engine.rootContext().setContextProperty("aiAssistantDemo", demo)

    window = QQuickWindow()
    # 页面比窗口高得多：三个 ExampleCard 都要落在视口内，滚动区域才会真正布局。
    window.resize(1000, 2600)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(PAGE_PATH)))
    if component.isLoading():
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    page = component.create(engine.rootContext())
    assert isinstance(page, QQuickItem)
    page.setParentItem(window.contentItem())
    page.setWidth(1000)
    page.setHeight(2600)
    # 不 show()：本用例只验可观测链路（帧序 / 累积文本 / 列表布局），不需要真渲染；
    # 一旦显示窗口，就会污染同进程后续用例的 topLevelWindows 快照。
    _pump(200)

    try:
        stream_list = page.findChild(QObject, "galleryStreamMessageList")
        preview_list = page.findChild(QObject, "galleryPreviewMessageList")
        start_button = page.findChild(QObject, "galleryAssistantStartButton")
        assert stream_list is not None and preview_list is not None and start_button is not None
        # 静态会话按演示稿逐条铺开（含推理那条）。
        assert preview_list.property("messageCount") == len(demo.previewMessages)

        page.metaObject().invokeMethod(page, "startStream")
        assert _wait_for(lambda: demo.stream.streaming), "流没有开始"
        # 流式期间就应当已经落进列表：不是等结束后再一次性写入。
        assert _wait_for(lambda: stream_list.property("messageCount") == 1)
        assert _wait_for(lambda: len(delta_chunks) >= 4), "增量没有逐块到达"
        assert _wait_for(lambda: bool(finished)), "流没有结束"
        assert _wait_for(lambda: not demo.stream.streaming)

        assert demo.stream.frameCount == EXPECTED_FRAMES
        assert frame_snapshots == sorted(frame_snapshots), "帧计数必须单调递增"
        assert "".join(reasoning_chunks) == "".join(REASONING_CHUNKS)
        assert "".join(delta_chunks) == "".join(DELTA_CHUNKS)
        # 内容真的进了布局：列表视口因这条流式消息长高了（内容被吞掉时这里会是 0）。
        content_height = _evaluate(stream_list, "messageViewport.contentHeight")
        assert float(content_height) > 40.0, content_height
        assert warnings == [], warnings
    finally:
        demo.stop()
        page.setParentItem(None)
        window.close()
        window.deleteLater()
        component.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        engine.collectGarbage()
