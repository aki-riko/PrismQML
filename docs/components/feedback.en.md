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

Attach a tooltip to a control, shown on hover.

## Skeleton

Loading placeholder, supports `shape_rounded` / `shape_rect` / `shape_circle`.

## Skin adaptation

Under neo: progress bar has a white track with black border + orange fill; InfoBar is white with black border, hard shadow + high-saturation status bar; Tooltip gets a black border + hard shadow. Status colors (success green / danger red / warning amber) use high-saturation versions under neo.
