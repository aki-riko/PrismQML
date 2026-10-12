# Chat

Chat components (`controls/chat/`). `ChatBubble` handles one message's content and layout,
`ChatMessageList` owns the model, virtualization, and scrolling, and `ChatBubbleSurface`
provides reusable bubble chrome.

## ChatBubbleSurface

`ChatBubbleSurface` draws only the bubble shell. It keeps color, radius, tail, border, and
skin-specific elevation in one place so message views and card flows can share the same chrome.

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
        text: "Message content"
    }
}
```

Public properties:

- `role`: `"user"`, `"assistant"`, or `"system"`; controls the side and surface semantics.
- `tail`: tightens the edge corner to form the asymmetric bubble tail.
- `chromeless`: removes the bubble shell; corners become square and no border is drawn.
- `elevationOnUser`: keeps elevation on user bubbles when `true` (the default).

Content is supplied through the component's default content property. Use `ChatBubble` for the
standard message presentation; use this component directly when the message content is custom.

## ChatBubble

`ChatBubble` accepts `role`, `content`, `reasoning`, `timestamp`, `maxBubbleWidth`, avatar
properties, and display switches. The message body is rendered as Markdown, and assistant
reasoning can be shown in a collapsible block.

```qml
Fluent.ChatBubble {
    width: parent.width
    role: "assistant"
    content: "Export is **complete**."
    timestamp: "12:34"
    showAvatar: true
}
```

## ChatMessageList

`ChatMessageList` combines lightweight height slots with viewport-near message delegates for
variable-height transcripts. Its public methods append, update, clear, and scroll the transcript:
`appendMessage()`, `appendReasoningToLast()`, `updateLastContent()`, `appendToLast()`, `clear()`,
`scrollToEnd()`, and `getLastRole()`.

```qml
Fluent.ChatMessageList {
    anchors.fill: parent
    // Call appendMessage() from the host after construction.
}
```

Use `maxBubbleWidth`, `assistantAvatarText`, `assistantAvatarSource`, `showAssistantAvatar`,
`showScrollBar`, `dragScrollEnabled`, and `scrollBarWidth` to tune the list's presentation and
interaction.
