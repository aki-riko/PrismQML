# Configuration

The config system uses a five-layer architecture: `Validator` → `SettingEntry` → `SettingsBase` → `AppConfig` → `ConfigManager`.

- **JSON persistence** — stored at `~/.prismqml/app.json` by default
- **Atomic writes** — writes to a temp file then replaces, preventing data loss on power failure
- **QML bridging** — exposed as QML Properties via the `ConfigManager` singleton

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
    SettingsBase, SettingEntry, EnumEntry, Validator,
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

Each `SettingEntry` declares group, name, default and validator; a `SettingsBase` subclass auto-persists to JSON and can bridge to QML.
