# PrismQML

[简体中文](./README.md) | **English**

A multi-skin UI engine (Fluent + Neobrutalism) built on PySide6 + QML, delivering 120fps+ smooth animations.

## ✨ Features

- **Pure QML rendering**: no frame-rate cap, 120fps+ smooth animations
- **Fluent Design**: Microsoft Fluent Design System components
- **Python integration**: seamless PySide6 integration, business logic stays on the Python side
- **Config system**: JSON persistence + atomic writes + QML Property bridging
- **Reactive state**: fine-grained Store state management with watch / batch modes
- **Window management**: multiple window layouts + lazy loading + Mica effect + system tray
- **Cross-platform**: Windows, macOS, Linux

## 📦 Installation

```bash
pip install prismqml
```

> Note: the PyPI package is named `prismqml` (`prismqml` is taken), but the import name is still `prismqml` (`from prismqml import ...`).

Development install:

```bash
git clone https://github.com/aki-riko/PrismQML.git
cd PrismQML
pip install -e ".[dev]"
```

## 🚀 Quick Start

```python
from prismqml import App, Window, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("My App")
window.resize(1200, 800)

# Add navigation pages
window.addPage(HomePage, "Home", "Home")
window.addPage(SettingsPage, "Settings", "Settings")

window.show()
app.exec()
```

## 🏗️ Architecture

```
prismqml/
├── PrismQML/              # QML components (module name: PrismQML)
│   ├── controls/           # UI controls
│   ├── _internal/          # internal window implementation
│   └── FluentEnums/        # enums & constants
└── python/                 # Python modules
    ├── config/             # configuration management
    ├── core/               # core engine (theme/logging/icons/shadow)
    ├── window/             # window management (lazy load/Mica/tray)
    ├── state/              # reactive state store
    ├── providers/          # feature providers (SVG/QR code/color picker)
    └── models/             # data models (high-performance tables)
```

## 📐 Window Types

| Type | Value | Description |
|------|-------|-------------|
| `WindowType.BAR` | 1 | Compact side navigation (default) |
| `WindowType.SPLIT` | 0 | Expandable side navigation |
| `WindowType.FILLED` | 2 | Filled split window |

```python
from prismqml import App, Window, WindowType

app = App()

# Compact side navigation (default)
window = app.create_window(WindowType.BAR)

# Expandable side navigation
window = app.create_window(WindowType.SPLIT)
```

## 🎨 Theme System

### Switching themes

```python
from prismqml import setTheme, Theme

setTheme(Theme.LIGHT)   # light
setTheme(Theme.DARK)    # dark
setTheme(Theme.AUTO)    # follow system
```

### Custom accent color

```python
from prismqml import setAccentColor, getAccentColor

setAccentColor("#0078d4")
print(getAccentColor())  # "#0078d4"
```

### Using in QML

```qml
import PrismQML as Fluent

// Primary button (style_primary automatically uses the global accent color)
Fluent.Button {
    text: "OK"
    style: Fluent.Enums.button.style_primary
}

// Access ThemeManager properties
Rectangle {
    color: ThemeManager.accentColor
}
```

> Note: `ComboBox` and `Slider` share names with QtQuick.Controls native types, so they are
> not exported from the top-level `PrismQML` module. Import them via their submodule directory,
> e.g. `import "../prismqml/PrismQML/controls/inputs"`.

## ⚙️ Config System

The config system uses a five-layer architecture: `Validator` → `SettingEntry` → `SettingsBase` → `AppConfig` → `ConfigManager`

- **JSON persistence**: stored at `~/.prismqml/app.json` by default
- **Atomic writes**: write to a temp file then replace, preventing data loss on power failure
- **QML bridging**: exposed as QML Properties via the `ConfigManager` singleton

```python
from prismqml.python.config import AppConfig, getConfigManager

# Read config values
config = getConfigManager()
print(config.lazyLoading)   # True
print(config.dpiScale)      # 0 (follow system)

# Update config (auto-saved to JSON)
config.setDpiScale(150)
```

### Custom config items

```python
from typing import ClassVar
from prismqml.python.config import (
    SettingsBase, SettingEntry, EnumEntry,
    Validator,
)


class MyAppConfig(SettingsBase):
    auto_save: ClassVar[SettingEntry] = SettingEntry(
        group="Editor", name="AutoSave",
        default=True, validator=Validator.boolean(),
    )
    font_size: ClassVar[EnumEntry] = EnumEntry(
        group="Editor", name="FontSize",
        default=14,
        validator=Validator.choice([12, 14, 16, 18, 20, 24]),
    )
```

## 📊 State Management

`Store` provides reactive state storage with fine-grained watch and batch updates:

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# Watch changes
store.watch("count", lambda new, old: print(f"{old} → {new}"))

# Set a value
store.set("count", 1)     # prints: 0 → 1

# Batch updates (notifications coalesced)
with store.batch():
    store.set("count", 10)
    store.set("user", "Alice")
# Notified once on exiting the with block

# Dict-style syntax
store["count"] = 20
print(store["count"])      # 20
```

## 🔔 System Tray

```python
from prismqml import SystemTrayIcon, Icon

tray = SystemTrayIcon(icon="AppIcon.png", toolTip="My App")
tray.addAction(text="Show", icon="Visibility", triggered=window.show)
tray.addSeparator()
tray.addAction(text="Quit", icon="Power", triggered=app.quit)
tray.show()
```

## 🧩 UI Components

### Controls
Button · Card · CheckBox · ToggleSwitch · LineEdit · ComboBox · Slider · ProgressBar · SpinBox · TableView · ListView · TreeView

### Navigation
NavigationBar · NavigationView · Pivot · Breadcrumb · Windows

### Effects
Shadow · ShadowedRectangle · ColorOverlay · GaussianBlur

> See each `controls/` subdirectory's `qmldir` for the full component list. Components that share names with QtQuick native types (e.g. `ComboBox`, `Slider`) must be imported via their submodule directory.

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

## 📄 License

PrismQML is licensed under the [MIT License](./LICENSE).

Copyright © 2026 aki-riko.

## 🙏 Credits

- Design inspired by the Microsoft Fluent Design System.
- Icons from [Microsoft Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons) (MIT License).
