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
