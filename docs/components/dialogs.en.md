# Dialogs

Dialogs, flyouts, and popup windows.

## Dialog

```qml
import PrismQML as Fluent

Fluent.Dialog {
    title: "Confirm"
    // content + action buttons
}
```

## Variants

| Control | Description |
|---------|-------------|
| `OverlayDialogCore` | Full-screen mask base without a built-in body; advanced overlays can declare custom content directly inside it |
| `DialogBox` | Standard dialog (title + content + action area) |
| `MaskedDialog` | Modal dialog with a mask |
| `FlyoutSheet` | Flyout panel |
| `ProgressDialog` | Progress dialog |
| `ConfirmDialog` | Confirm dialog (supports messageAlignment) |
| `PopupWindow` | Generic popup (backing for menus/dropdowns/tooltips) |

`OverlayDialogCore` owns the mask, event blocking, open/close animation state, and overlay-target reparenting. Derived controls should only restore their layout through the internal `_prepareOpen()` hook instead of duplicating the `open()` lifecycle.

## Desktop notifications

```python
from prismqml import showDesktopNotification
showDesktopNotification(title="Reminder", message="You have a new message")
```

## Skin adaptation

Under neo: all popups get thick black borders + hard shadows (NeoShadow, tracking the open/close animation's opacity/scale); dialogs are white with black borders.
