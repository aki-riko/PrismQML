# Feedback

Progress, notification, tooltip, and skeleton feedback controls.

## Progress

```qml
import PrismQML as Fluent

Fluent.ProgressBar { value: 65 }      // progress bar
Fluent.ProgressRing { value: 75 }     // progress ring
```

`Progress` supports `type_bar` / `type_bar_filled` / `type_ring`, plus indeterminate, paused, and error states.

## Toast

```python
from prismqml import showDesktopSuccess, showDesktopError

showDesktopSuccess("Done")
showDesktopError("Something went wrong")
```

QML desktop notifications accept atomic creation `options`, so layout and action
content are applied before the notification is positioned:

```qml
Component {
    id: openFolderAction
    Fluent.Button {
        text: "Open folder"
        width: parent ? parent.width : implicitWidth
    }
}

Fluent.Button {
    text: "Show export notification"
    onClicked: Fluent.NotificationManager.desktop.success(
        "Export complete",
        "00:14\nC:/recordings/clip.mp4",
        0,
        Fluent.Enums.notification.posBottomRight,
        {
            "orient": Qt.Vertical,
            "customContent": openFolderAction,
            "closable": true,
            "screen": Window.window.screen
        }
    )
}
```

Shared Toast and InfoBar options are `orient`, `customContent`, `closable`,
`feature`, `progress`, `completeDuration`, `backgroundColorLight`, and
`backgroundColorDark`. Desktop InfoBar also accepts `icon` and `radius`.
Use `screen` to select the target display. The native window is positioned inside
that screen's `availableGeometry`, avoiding taskbars and reflowing after content
or work-area geometry changes.

Desktop notifications support a complete row-major nine-grid:
`posTopLeft` / `posTop` / `posTopRight`, `posLeft` / `posCenter` / `posRight`, and
`posBottomLeft` / `posBottom` / `posBottomRight`. Edge positions keep an 8 logical-pixel
work-area margin, while the middle row and column are centered vertically and horizontally.
Python's `Position` enum uses the same order.

The Python helper accepts the same serializable options, except QML `Component`
values such as `customContent`:

```python
from PySide6.QtCore import Qt
from prismqml import showDesktopSuccess

showDesktopSuccess(
    "Export complete",
    "00:14\nC:/recordings/clip.mp4",
    duration=0,
    options={"orient": Qt.Vertical, "closable": False},
)
```

### Outside the host window

The last optional argument of the InfoBar/Toast manager methods selects the
notification mode. With `Enums.notification.mode_window_outside`, the window
that owns `parent` becomes the host and the notification is created as a
separate window attached to its outside edge:

```qml
Fluent.Button {
    text: "Show a Toast outside the top-left of the window"
    onClicked: Fluent.NotificationManager.toast.info(
        Window.window,
        "Notice",
        "Attached to the host window",
        0,
        Fluent.Enums.notification.posTopLeft,
        Fluent.Enums.notification.mode_window_outside
    )
}
```

`posTopLeft` / `posTopRight` stack downward from the top of the host sides,
`posLeft` / `posRight` stack from the vertical center, and
`posBottomLeft` / `posBottomRight` stack upward from the bottom. `posTop`
starts at the middle of the top edge and stacks upward; `posBottom` starts at
the middle of the bottom edge and stacks downward. `posCenter` has no outside
edge and is rejected. Attachments follow host movement and resizing, close
when the host is hidden or minimized, and account for same-edge outside Drawer
reservations.

## InfoBar

```qml
Fluent.InfoBar {
    severity: "success"     // info / success / warning / error
    title: "Success"
    message: "InfoBar content"
    duration: 0             // 0 = persistent, no auto-dismiss
}
```

## Tooltip

All controls derived from `Widget` can attach hover text with `toolTipText` and
select `Enums.position.top/right/bottom/left` through `toolTipPosition`. Regular
controls default to the top; `HintIcon` defaults to the right of the icon and
uses the shared horizontal and vertical padding.

```qml
Fluent.HintIcon {
    toolTipText: "Additional context"
    // Default; top / bottom / left are also supported
    toolTipPosition: Fluent.Enums.position.right
}
```

## Skeleton

Loading placeholder, supports `shape_rounded` / `shape_rect` / `shape_circle`.

## Skin adaptation

Under neo: progress bar has a white track with black border + orange fill; InfoBar is white with black border, hard shadow + high-saturation status bar; Tooltip gets a black border + hard shadow. Status colors (success green / danger red / warning amber) use high-saturation versions under neo.
