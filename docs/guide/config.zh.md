# 配置系统

配置系统采用五层架构：`Validator` → `SettingEntry` → `SettingsBase` → `AppConfig` → `ConfigManager`。

- **JSON 持久化** — 默认存储于 `~/.prismqml/app.json`
- **原子写入** — 先写临时文件再替换，防止断电数据丢失
- **QML 桥接** — 通过 `ConfigManager` 单例暴露为 QML Property

## 读写配置

```python
from prismqml.python.config import getConfigManager

config = getConfigManager()
print(config.lazyLoading)   # True
print(config.dpiScale)      # 0（跟随系统）

# 修改配置（自动保存到 JSON）
config.setDpiScale(150)
```

## 自定义配置项

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

每个 `SettingEntry` 声明分组、名称、默认值和验证器；`SettingsBase` 子类自动落盘到 JSON，并可桥接到 QML。
