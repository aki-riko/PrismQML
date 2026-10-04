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


def test_gallery_entry_point_wires_the_assistant_demo_to_a_qobject_parent(qapp):
    """端到端接线：`examples/main.py` 的装配函数必须能真的跑起来。

    🔴 这条是启动崩溃的回归护栏：装配曾把 `prismqml.App` 当 QObject parent 传进去——App 只是
    持有 QApplication 与 QML 引擎的 Python 包装、并不是 QObject，于是 `python examples/main.py`
    启动即 TypeError。冷启动 bench 只 `import examples.main`（模块级不执行 main()），漏掉了它。
    """
    from examples.main import wire_assistant_demo

    # 调用点也要钉住：真正崩的是 main() 里那一行，而不是装配函数本身。
    entry_source = (ROOT / "examples" / "main.py").read_text(encoding="utf-8")
    assert "wire_assistant_demo(engine)" in entry_source
    assert "start_assistant_demo(app)" not in entry_source

    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    demo = wire_assistant_demo(engine)
    try:
        assert demo.available, demo.errorText
        assert engine.rootContext().contextProperty("aiAssistantDemo") is demo
        assert demo.parent() is engine, "演示后端必须挂在 QObject（引擎）上，随引擎释放"
        # 页面对上下文属性的依赖是运行期解析的，顺带确认 QML 真的能读到它。
        component = QQmlComponent(engine)
        component.setData(
            b"import QtQuick\nQtObject { property bool ready: aiAssistantDemo.available }",
            QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "gallery-assistant-binding.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        holder = component.create()
        assert holder is not None and holder.property("ready") is True
        holder.deleteLater()
    finally:
        demo.stop()
        engine.collectGarbage()


def test_gallery_assistant_page_sends_a_prompt_and_streams_the_answer(qapp):
    """QML 端到端：用户在输入条里提问 → 助手气泡按增量吐答案。

    ⚠️ 离屏环境不孵化气泡委托（ChatMessageList 只在真正渲染视口附近才把轻量占位换成 ChatBubble），
    所以这里断言可观测链路：空态 → 发送后列表条数、帧序、累积正文、视口高度与零告警；
    气泡渲染本身由聊天组件用例覆盖。
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
    window.resize(1000, 760)
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
    page.setHeight(760)
    # 不 show()：本用例只验可观测链路（帧序 / 累积文本 / 列表布局），不需要真渲染；
    # 一旦显示窗口，就会污染同进程后续用例的 topLevelWindows 快照。
    _pump(200)

    try:
        chat_list = page.findChild(QObject, "galleryAssistantChatList")
        composer = page.findChild(QObject, "galleryAssistantComposer")
        send_button = page.findChild(QObject, "galleryAssistantSendButton")
        empty_state = page.findChild(QObject, "galleryAssistantEmptyState")
        assert None not in (chat_list, composer, send_button, empty_state)

        # 初始是空对话：只有引导与建议，没有消息。
        assert chat_list.property("messageCount") == 0
        assert empty_state.property("visible") is True
        assert len(demo.suggestions) >= 1

        # 用户在输入条里提问（走页面的发送入口，和按钮点击同一条路径）。
        prompt = "气泡的外壳到底是谁画的？"
        composer.setProperty("text", prompt)
        assert _wait_for(lambda: send_button.property("enabled") is True), "有内容后发送键应当可用"
        # 经 QML 表达式调用：QML 函数的形参是 QVariant，用 Q_ARG 直传字符串会静默不匹配。
        _evaluate(page, "sendPrompt(composer.text)")

        # 用户那句 + 空的助手气泡，随后增量往上长。
        assert _wait_for(lambda: chat_list.property("messageCount") == 2), "发送后应当是两条消息"
        assert _wait_for(lambda: demo.stream.streaming), "流没有开始"
        assert _wait_for(lambda: len(delta_chunks) >= 4), "增量没有逐块到达"
        assert _wait_for(lambda: bool(finished)), "流没有结束"
        assert _wait_for(lambda: not demo.stream.streaming)
        # 发过消息之后空态退场。
        assert empty_state.property("visible") is False

        assert demo.stream.frameCount == EXPECTED_FRAMES
        assert frame_snapshots == sorted(frame_snapshots), "帧计数必须单调递增"
        assert "".join(reasoning_chunks) == "".join(REASONING_CHUNKS)
        assert "".join(delta_chunks) == "".join(DELTA_CHUNKS)
        # 内容真的进了布局：列表视口因这条流式消息长高了（内容被吞掉时这里会是 0）。
        content_height = _evaluate(chat_list, "messageViewport.contentHeight")
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
