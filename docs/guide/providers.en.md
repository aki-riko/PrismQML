# System Services

PrismQML bundles a set of system-level service objects. On the Python side
they are obtained through `get_xxx()` singletons; when using `App` or
`register_types()`, identically named context properties are injected into
QML and can be referenced directly.

## Clipboard — ClipboardHelper

| Method | Description |
|--------|-------------|
| `copy(text)` | Copy text to the clipboard |
| `paste()` | Read clipboard text; returns `""` when empty |

```python
from prismqml import get_clipboard_helper

get_clipboard_helper().copy("copied text")
```

```qml
Fluent.Button {
    text: "Copy"
    onClicked: ClipboardHelper.copy("text")
}
```

## QR Code — QRCodeGenerator

Depends on the optional `qrcode` package; `available` is `False` when it is
not installed:

```python
from prismqml import get_qrcode_generator

gen = get_qrcode_generator()
if gen.available:
    url = gen.getImageSource("https://example.com", 256, "#000000", "#ffffff", "M")
```

| Member | Description |
|--------|-------------|
| `available` | Whether the `qrcode` library is usable |
| `getImageSource(content, size, fgColor, bgColor, errorLevel)` | Returns an `image://qrcode/...` URL for a QML `Image` |

`size` accepts 32–1024 (default 128); `errorLevel` is `L` / `M` / `Q` / `H`.
QML can use the ready-made component instead:

```qml
Fluent.QRCode { content: "https://example.com" }
```

See [Data](../components/data.md) for the component details.

## SVG Rendering — SvgImageProvider

The `image://svg` image provider is registered automatically at `App`
startup and renders SVG files at high quality through `QSvgRenderer`;
`sourceSize` optionally selects the render size:

```qml
Image {
    source: "image://svg/path/to/icon.svg"
    sourceSize: Qt.size(128, 128)   // optional
}
```

Everything after `image://svg/` is one QML URL component: reserved characters
are percent-decoded exactly once, then file / qrc sources are resolved with
Qt URL semantics.

## Screen Eyedropper — ScreenEyedropperManager

| Member | Description |
|--------|-------------|
| `startPicking(is_dark)` | Show a cursor-following magnifier and start picking |
| `stopPicking()` | Stop picking |
| `colorPicked(QColor)` | Signal: a color was confirmed |
| `pickingStarted` / `pickingFinished` / `pickingCancelled` | Signals: picking lifecycle |

```python
from prismqml import get_screen_eyedropper_manager

picker = get_screen_eyedropper_manager()
picker.colorPicked.connect(lambda color: print(color.name()))
picker.startPicking(True)   # True = dark magnifier appearance
```

Left click or Enter confirms; right click, `Esc`, or losing focus cancels.
The QML `ColorPicker` component already integrates this entry point.

## Single Instance — SingleInstance

```python
from prismqml import SingleInstance

instance = SingleInstance("com.example.myapp")
instance.activateRequested.connect(raise_main_window)
if not instance.try_lock():
    return  # another instance is running; this process sent the activate message
app.exec()
instance.unlock()
```

- Windows locks through a named mutex (`Local\\{app_id}`); other platforms use
  `QSharedMemory`
- When `try_lock()` fails, the second instance sends an activate message to
  the primary instance and returns `False`; the primary emits the
  `activateRequested` signal, which can raise the main window to the front
- If the primary instance is unresponsive (a stale lock), the second instance
  takes over startup automatically
- Prefer a reverse-domain `app_id`; a `with SingleInstance("...") as instance:`
  context manager is also supported
