# Python API

Top-level API importable via `from prismqml import ...`.

## App & Window

| Name | Description |
|------|-------------|
| `App` | Application entry; auto-handles DPI / register_types / incubation controller |
| `Window` / `WindowCore` | Main window |
| `WindowType` | Window type enum (BAR / SPLIT / FILLED) |
| `NavigationItem` | Navigation item |

```python
from prismqml import App, WindowType
app = App()
window = app.create_window(WindowType.BAR)
```

## Skin & Theme

| Name | Description |
|------|-------------|
| `Skin` | Skin enum (FLUENT / NEOBRUTALISM) |
| `setSkin` / `getSkin` | Switch / get skin |
| `Theme` | Theme enum (LIGHT / DARK / AUTO) |
| `setTheme` / `getTheme` / `isDark` | Theme switch / query |
| `setAccentColor` / `getAccentColor` / `accentQColor` | Accent color |
| `getThemeManager` | ThemeManager singleton |

## State & Config

| Name | Description |
|------|-------------|
| `Store` | Reactive state store |
| `prismqml.python.config` | Config system (AppConfig / getConfigManager / SettingsBase / SettingEntry / Validator) |

## Engine components

| Name | Description |
|------|-------------|
| `Updater` | Auto-update via GitHub Releases |
| `SingleInstance` | Single instance (Named Mutex + IPC) |
| `SystemTrayIcon` | System tray |
| `Icon` / `make_icon` / `make_theme_icon` | Icons |
| `IconProvider` / `register_icon_provider` | Icon provider |
| `ShadowManager` / `getShadowManager` / `installDwmSyncFilter` | Window shadow |

## Logging

| Name | Description |
|------|-------------|
| `Logger` / `getLogger` | Logger |
| `debug` / `info` / `warning` / `error` / `exception` | Log functions |

## Utilities

| Name | Description |
|------|-------------|
| `qml_path` | QML module path |
| `register_types` | Register QML types (called internally by App) |

> Full exports in `prismqml/__init__.py`'s `__all__`.
