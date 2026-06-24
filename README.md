# PrismQML

**简体中文** | [English](./README.en.md)

基于 PySide6 + QML 的多皮肤 UI 引擎（Fluent + 新粗野），提供 120fps+ 流畅动画体验。

## ✨ 特性

- **纯 QML 渲染**：无帧率限制，120fps+ 流畅动画
- **Fluent Design**：微软 Fluent Design System 组件
- **Python 集成**：PySide6 无缝集成，Python 侧管理业务逻辑
- **配置系统**：JSON 持久化 + 原子写入 + QML Property 桥接
- **响应式状态**：细粒度 Store 状态管理，支持 watch / batch 模式
- **窗口管理**：多种窗口布局 + 懒加载 + 云母效果 + 系统托盘
- **跨平台**：Windows、macOS、Linux

## 📦 安装

```bash
pip install prismqml
```

> 分发名与导入名一致：`pip install prismqml` 后 `from prismqml import ...`。

开发模式安装：

```bash
git clone https://github.com/aki-riko/PrismQML.git
cd PrismQML
pip install -e ".[dev]"
```

## 🚀 快速开始

```python
from prismqml import App, Window, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("我的应用")
window.resize(1200, 800)

# 添加导航页面
window.addPage(HomePage, "Home", "首页")
window.addPage(SettingsPage, "Settings", "设置")

window.show()
app.exec()
```

## 🏗️ 架构

```
prismqml/
├── PrismQML/              # QML 组件（模块名 PrismQML）
│   ├── controls/           # UI 控件
│   ├── _internal/          # 内部窗口实现
│   └── FluentEnums/        # 枚举与常量
└── python/                 # Python 模块
    ├── config/             # 配置管理系统
    ├── core/               # 核心引擎（主题/日志/图标/阴影）
    ├── window/             # 窗口管理（懒加载/云母/托盘）
    ├── state/              # 响应式状态存储
    ├── providers/          # 功能提供者（SVG/二维码/取色器）
    └── models/             # 数据模型（高性能表格）
```

## 📐 窗口类型

| 类型 | 枚举值 | 说明 |
|------|--------|------|
| `WindowType.BAR` | 1 | 紧凑侧边导航（默认） |
| `WindowType.SPLIT` | 0 | 展开式侧边导航 |
| `WindowType.FILLED` | 2 | 填充式分割窗口 |

```python
from prismqml import App, Window, WindowType

app = App()

# 紧凑侧边导航（默认）
window = app.create_window(WindowType.BAR)

# 展开式侧边导航
window = app.create_window(WindowType.SPLIT)
```

## 🎨 主题系统

### 切换主题

```python
from prismqml import setTheme, Theme

setTheme(Theme.LIGHT)   # 浅色
setTheme(Theme.DARK)    # 深色
setTheme(Theme.AUTO)    # 跟随系统
```

### 自定义主题色

```python
from prismqml import setAccentColor, getAccentColor

setAccentColor("#0078d4")
print(getAccentColor())  # "#0078d4"
```

### QML 中使用

```qml
import PrismQML as Fluent

// Primary 按钮（style_primary 自动使用全局主题色）
Fluent.Button {
    text: "确定"
    style: Fluent.Enums.button.style_primary
}

// 访问 ThemeManager 属性
Rectangle {
    color: ThemeManager.accentColor
}
```

> 说明：`ComboBox`、`Slider` 因与 QtQuick.Controls 原生类型同名，未在顶层 `PrismQML` 模块导出，
> 需按子模块目录导入后使用，例如 `import "../prismqml/PrismQML/controls/inputs"`。

## ⚙️ 配置系统

配置系统采用五层架构：`Validator` → `SettingEntry` → `SettingsBase` → `AppConfig` → `ConfigManager`

- **JSON 持久化**：默认存储于 `~/.prismqml/app.json`
- **原子写入**：先写临时文件再替换，防止断电数据丢失
- **QML 桥接**：通过 `ConfigManager` 单例暴露为 QML Property

```python
from prismqml.python.config import AppConfig, getConfigManager

# 获取配置值
config = getConfigManager()
print(config.lazyLoading)   # True
print(config.dpiScale)      # 0（跟随系统）

# 修改配置（自动保存到 JSON）
config.setDpiScale(150)
```

### 自定义配置项

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

## 📊 状态管理

`Store` 提供响应式状态存储，支持细粒度 watch 和批量更新：

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# 监听变化
store.watch("count", lambda new, old: print(f"{old} → {new}"))

# 设置值
store.set("count", 1)     # 输出: 0 → 1

# 批量更新（合并通知）
with store.batch():
    store.set("count", 10)
    store.set("user", "Alice")
# 退出 with 时统一通知

# 字典语法
store["count"] = 20
print(store["count"])      # 20
```

## 🔔 系统托盘

```python
from prismqml import SystemTrayIcon, Icon

tray = SystemTrayIcon(icon="AppIcon.png", toolTip="我的应用")
tray.addAction(text="显示", icon="Visibility", triggered=window.show)
tray.addSeparator()
tray.addAction(text="退出", icon="Power", triggered=app.quit)
tray.show()
```

## 🧩 UI 组件

### 控件
Button · Card · CheckBox · ToggleSwitch · LineEdit · ComboBox · Slider · ProgressBar · SpinBox · TableView · ListView · TreeView

### 导航
NavigationBar · NavigationView · Pivot · Breadcrumb · Windows

### 特效
Shadow · ShadowedRectangle · ColorOverlay · GaussianBlur

> 完整组件清单见各 `controls/` 子目录的 `qmldir`。`ComboBox`、`Slider` 等与 QtQuick 原生同名的组件需经子模块目录导入。

## 🧪 测试

```bash
python -m pytest tests/ -v
```

## 📄 License

PrismQML is licensed under the [MIT License](./LICENSE).

Copyright © 2026 aki-riko.

## 🙏 Credits

- Design inspired by the Microsoft Fluent Design System.
- Icons from [Microsoft Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons) (MIT License).
