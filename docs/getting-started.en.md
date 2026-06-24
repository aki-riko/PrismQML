# Getting Started

## Installation

```bash
pip install prismqml
```

PrismQML depends on PySide6 (installed automatically). Distribution name matches import name: after installing, use `from prismqml import ...`.

## Your first window

```python
from prismqml import App, Window, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("My App")
window.resize(1200, 800)

# Add navigation pages (QML component + icon name + title)
window.addPage(HomePage, "Home", "Home")
window.addPage(SettingsPage, "Settings", "Settings")

window.show()
app.exec()
```

`App` handles DPI scaling, message handler installation, `register_types` (registering QML types), the async incubation controller, and more — no manual setup needed.

## Using controls in QML

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "OK"
    style: Fluent.Enums.button.style_primary   // primary auto-uses the global accent color
}
```

!!! note "Importing ComboBox / Slider"
    `ComboBox` and `Slider` share names with QtQuick.Controls native types, so they are not
    exported at the top-level `PrismQML` module. Import them by submodule directory, e.g.
    `import "../prismqml/PrismQML/controls/inputs"`.

## Switch skins in one line

PrismQML's signature capability — the same UI, switched between design languages at runtime:

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)         # Fluent Design
setSkin(Skin.NEOBRUTALISM)   # Neobrutalism
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
    ├── core/              # core engine (theme/skin/log/icon/shadow)
    ├── window/            # window management (lazy load/Mica/tray)
    ├── state/             # reactive state store
    ├── providers/         # feature providers (SVG/QR/eyedropper)
    └── models/            # data models (high-performance table)
```
