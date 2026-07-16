# Python API

Top-level API importable via `from prismqml import ...`.

## App & Window

| Name | Description |
|------|-------------|
| `App` | Application entry; auto-handles DPI / register_types / incubation controller / Translator environment |
| `Window` / `WindowCore` | Main window |
| `WindowType` | Window type enum (BAR / SPLIT / FILLED) |
| `NavigationItem` | Navigation item |

```python
from prismqml import App, WindowType
app = App()
window = app.create_window(WindowType.BAR)
```

`App(allow_qml_file_read=True)` enables local i18n JSON access for Translator before creating the QML engine; pass `False` to disable it explicitly. A plain `import prismqml` does not change this environment setting.

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
| `prismqml.python.config` | Config system (AppConfig / getConfigManager / SettingsCore / SettingEntry / Validator) |

## Engine components

| Name | Description |
|------|-------------|
| `Updater` | Auto-update via GitHub Releases with a configurable API base URL |
| `SingleInstance` | Single instance (Named Mutex + IPC) |
| `SystemTrayIcon` | System tray |
| `Icon` / `make_icon` / `make_theme_icon` | Icons |
| `IconProvider` / `register_icon_provider` | Icon provider |
| `ShadowManager` / `getShadowManager` / `installDwmSyncFilter` | Window shadow |

For `Updater(..., api_base_url="https://github.example/api/v3")`, the explicit value wins, followed by `PRISMQML_UPDATER_API_BASE_URL`, then the public GitHub API. Whitespace and trailing `/` characters are normalized.

Version comparison strips an optional `v` / `V` prefix and supports the project's variable-length dotted numeric core plus dotted prerelease identifiers. A release outranks a prerelease with the same core, build metadata after `+` does not affect precedence, and blank or prefix-only tags are treated as the minimum version. This compares GitHub tags; it is not a strict validator that rejects every non-standard SemVer tag.

Release responses must be strict UTF-8 JSON objects. `tag_name` must be a non-empty string, while `body`, `html_url`, `assets`, and asset fields are checked against the public schema. Invalid input emits only `checkFailed`; it is never silently truncated or reported as an update. Downloads use process-unique temporary files and are published atomically only after complete write, flush, fsync, and close steps. Network, write, close, commit, or empty-file failures emit `downloadFailed` once and remove partial artifacts. Repeated checks or downloads on the same active Updater instance are ignored without replacing the active reply.

## Logging

| Name | Description |
|------|-------------|
| `Logger` / `getLogger` | Logger |
| `debug` / `info` / `warning` / `error` / `exception` | Log functions |

## Utilities

| Name | Description |
|------|-------------|
| `qml_path` | QML module path |
| `configure_qml_environment` | Explicitly configure local QML XHR for Translator before creating a bare `QQmlApplicationEngine` |
| `register_types` | Register QML types (called internally by App) |

```python
from PySide6.QtQml import QQmlApplicationEngine
from prismqml import configure_qml_environment

configure_qml_environment()
engine = QQmlApplicationEngine()
```

> Full exports in `prismqml/__init__.py`'s `__all__`.
