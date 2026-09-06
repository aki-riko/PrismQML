# Getting Started

Complete the [installation](install.md) first, then bring up your first window in a few lines of code.

Runtime requirements: Python 3.9+ and PySide6 6.9+ (Qt 6.9+).

## Your first window

```python
from prismqml import App, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("My App")
window.resize(1200, 800)

window.show()
app.exec()
```

Add application page classes, factories, or instances with
`window.addPage(PageClass, icon, text)`. Use `AsyncQmlPage` when the QML object
tree should be incubated asynchronously. See the [window guide](guide/windows.md)
for complete navigation examples.

`App` handles DPI scaling, message handler installation, `register_types`
(registering QML types), the async incubation controller, and explicitly enables
the local QML XHR access required by Translator before engine creation. A plain
`import prismqml` does not modify the process environment. Use
`App(allow_qml_file_read=False)` when local translation loading is not needed.

When creating `QApplication` and `QQmlApplicationEngine` yourself, call
`prismqml.python.runtime.prepare_application_environment(allow_qml_file_read=True)`
before constructing the application object, then call `register_types(engine)`
after constructing the engine. `configure_qml_environment()` alone does not
configure DPI, the message handler, or the Windows graphics backend.

On Windows, the complete application setup selects D3D11 before the first
`QQuickWindow`; application code does not need to and should not switch to
OpenGL. macOS and Linux retain Qt's platform-default graphics backend.

## Using controls in QML

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "OK"
    style: Fluent.Enums.button.style_primary   // primary auto-uses the global accent color
}
```

!!! note "ComboBox / Slider"
    `ComboBox` and `Slider` are registered by the top-level `PrismQML` module. Use
    `Fluent.ComboBox` / `Fluent.Slider` through the module alias; do not import
    QtQuick.Controls or internal directories.

## Switch skins in one line

PrismQML's signature capability — the same UI, switched between design languages at runtime:

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)         # Fluent Design
setSkin(Skin.NEOBRUTALISM)   # Neobrutalism
setSkin(Skin.VINTAGE_TICKET) # Vintage Ticket
setSkin(Skin.NEUMORPHISM)    # Neumorphism
```

See [Skins](guide/skins.md).

## Project layout

```
prismqml/
├── PrismQML/              # QML components (module name: PrismQML)
│   ├── controls/          # UI controls
│   ├── _internal/         # internal window implementation
│   └── PrismEnums/        # enums & constants
└── python/                # Python modules
    ├── config/            # configuration system
    ├── core/              # low-level services (theme/logging/icons/window helpers)
    ├── runtime/           # runtime composition (registration/appearance persistence)
    ├── window/            # window management (lazy load/Mica/tray)
    ├── state/             # reactive state store
    ├── providers/         # feature providers (SVG/QR/eyedropper)
    └── models/            # data models (high-performance table)
```
