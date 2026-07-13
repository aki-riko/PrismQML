# 配置系统

配置系统采用五层架构：`Validator` → `SettingEntry` → `SettingsCore` → `AppConfig` → `ConfigManager`。

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

每个 `SettingEntry` 声明分组、名称、默认值和验证器；`SettingsCore` 子类自动落盘到 JSON，并可桥接到 QML。

## 自定义条目扩展

自定义持久化格式时覆写 `encode(value)` / `decode(raw)`；两者必须是纯函数，
不得修改条目自身状态。`SettingsCore` 会在磁盘或内存提交前完成全部转换与复制，
因此保存失败不会发出未提交信号，加载失败也不会留下部分状态。

`SettingEntry` 是 `QObject`。若子类改变了构造器签名，必须同时覆写
`clone(parent)`，并通过真实构造器创建新实例，以保留子对象、信号连接和 Qt
所有权。`dump()` / `load()` 仅是脱离 `SettingsCore` 时操作当前值的便利包装，
不再作为事务持久化 hook。
