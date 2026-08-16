# Configuration

The config system uses a five-layer architecture: `Validator` → `SettingEntry` → `SettingsCore` → `AppConfig` → `ConfigManager`.

- **JSON persistence** — Window settings are stored at `~/.prismqml/app.json` by default
- **Atomic writes** — writes to a temp file then replaces, preventing data loss on power failure
- **QML bridging** — exposed as QML Properties via the `ConfigManager` singleton

Theme, Skin, Language, and AccentColor are no longer shared implicitly across
applications. `App()` starts with the Fluent appearance; pass an application-
specific `config_path` to restore and persist that application's appearance:

```python
from prismqml import App

app = App(config_path="APP_CONFIG/app.json")
```

If the host already owns its appearance settings, keep one source of truth:

```python
app = App(
    config_path="APP_CONFIG/prismqml.json",
    persist_appearance=False,
)
```

This mode still restores PrismQML Window settings. Existing on-disk
`Appearance` values are not applied and remain preserved during Window writes.
`PRISMQML_CONFIG_FILE` also counts as an explicit application config path.

## Read & write config

```python
from prismqml.python.config import getConfigManager

config = getConfigManager()
print(config.lazyLoading)   # True
print(config.dpiScale)      # 0 (follow system)

# modify (auto-saved to JSON)
config.setDpiScale(150)
```

## Custom config entries

```python
from typing import ClassVar
from prismqml.python.config import (
    SettingsCore, SettingEntry, EnumEntry, Validator,
)


class MyAppConfig(SettingsCore):
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

Each `SettingEntry` declares group, name, default and validator; a `SettingsCore` subclass auto-persists to JSON and can bridge to QML.

## Custom entry extensions

Override `encode(value)` / `decode(raw)` to customize the persisted form. Both
methods must be pure and must not mutate the entry itself. `SettingsCore`
finishes all conversion and copying before committing disk or memory state, so
a failed save emits no uncommitted signal and a failed load leaves no partial
state.

`SettingEntry` is a `QObject`. A subclass that changes the constructor signature
must also override `clone(parent)` and create the clone through its real
constructor, preserving child objects, signal connections, and Qt ownership.
`dump()` / `load()` are convenience wrappers for direct use outside
`SettingsCore`; they are not transactional persistence hooks.
