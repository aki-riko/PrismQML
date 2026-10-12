# 聊天

聊天组件（`controls/chat/` 模块）。`ChatBubble` 负责单条消息的内容与布局，
`ChatMessageList` 负责消息模型、虚拟化和滚动；`ChatBubbleSurface` 提供可复用的气泡外壳。

## ChatBubbleSurface 气泡外壳

`ChatBubbleSurface` 只绘制气泡表面，不管理消息正文。它统一处理颜色、圆角、尖角、描边和
皮肤相关的阴影，适合被聊天消息、卡片流或其他聊天视图复用。

```qml
import QtQuick
import PrismQML as Fluent

Fluent.ChatBubbleSurface {
    width: 260
    height: 64
    role: "assistant"       // "user" / "assistant" / "system"
    tail: true
    elevationOnUser: false

    Text {
        anchors.centerIn: parent
        text: "消息内容"
    }
}
```

公开属性：

- `role`：`"user"`、`"assistant"` 或 `"system"`，决定消息侧别与表面语义。
- `tail`：是否收紧对应一侧的圆角来表现气泡尖角。
- `chromeless`：设为 `true` 时移除气泡表面，四角变为直角且不绘制边框。
- `elevationOnUser`：是否给用户侧气泡保留阴影；默认值为 `true`。

`ChatBubbleSurface` 的内容通过默认内容属性放入内部表面。通常直接使用 `ChatBubble` 即可；
需要自定义消息内容或复用气泡外壳时，再单独使用此组件。

## ChatBubble 单条消息

`ChatBubble` 接收 `role`、`content`、`reasoning`、`timestamp`、`maxBubbleWidth`、头像和
显示开关等属性。正文使用 Markdown 渲染；助手消息可以显示可折叠的推理内容。

```qml
Fluent.ChatBubble {
    width: parent.width
    role: "assistant"
    content: "已完成 **导出**。"
    timestamp: "12:34"
    showAvatar: true
}
```

## ChatMessageList 消息列表

`ChatMessageList` 使用轻量高度占位和视口附近的消息委托来处理变高消息。通过公开方法追加、
更新、清空消息并控制滚动到底部：`appendMessage()`、`appendReasoningToLast()`、
`updateLastContent()`、`appendToLast()`、`clear()`、`scrollToEnd()` 和 `getLastRole()`。

```qml
Fluent.ChatMessageList {
    anchors.fill: parent

    Component.onCompleted: appendMessage("user", "请生成报告", "12:30")
}
```

`maxBubbleWidth`、`assistantAvatarText`、`assistantAvatarSource`、`showAssistantAvatar`、
`showScrollBar`、`dragScrollEnabled` 和 `scrollBarWidth` 可用于调整列表外观与交互。
