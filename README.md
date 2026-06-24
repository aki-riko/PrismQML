# PrismQML

**简体中文** | [English](./README.en.md)

> **一套 QML 控件，多种设计语言一键切换。**
> PrismQML 是基于 PySide6 + QML 的**多皮肤 UI 引擎**：同一套控件，运行时在 **Fluent** 与 **新粗野（Neobrutalism）** 之间自由切换，120fps+ 流畅动画。

<!-- TODO: 此处放 Fluent vs Neobrutalism 同界面并排对比图 (same code, one setSkin() call) -->

```python
from prismqml import setSkin, Skin
setSkin(Skin.NEOBRUTALISM)   # 一行切换整个应用的设计语言
```

## ✨ 特性

- **🎨 多皮肤引擎**：同一套控件，`setSkin()` 一键切换 Fluent / 新粗野，支持 light/dark
- **🧩 token 驱动架构**：颜色、几何、阴影全走 token —— 新增皮肤几乎**零控件改动**
- **⚡ 纯 QML 渲染**：无帧率限制，120fps+ 流畅动画
- **🐍 PySide6 原生**：无缝集成，Python 侧管理业务逻辑，不碰 C++
- **📦 控件齐全**：按钮 / 输入 / 卡片 / 对话框 / 表格 / 图表 / 导航等全套
- **💾 配置系统**：JSON 持久化 + 原子写入 + QML Property 桥接
- **🔄 响应式状态**：细粒度 Store 状态管理，支持 watch / batch 模式
- **🪟 窗口管理**：多种窗口布局 + 懒加载 + 云母效果 + 系统托盘
- **🌍 跨平台**：Windows、macOS、Linux

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
│   └── PrismEnums/        # 枚举与常量
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

## 🎨 皮肤系统（核心）

PrismQML 的招牌能力：**皮肤与明暗正交**。`skin` 控制设计语言，`theme` 控制明暗，两者独立组合。

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)          # Fluent Design：圆角、模糊阴影、蓝主色
setSkin(Skin.NEOBRUTALISM)    # 新粗野：粗黑边、硬阴影、橙撞色
```

QML 侧通过 `Enums.skin` / `Enums.isNeobrutalism` 读取当前皮肤：

```qml
import PrismQML
Rectangle {
    radius: Enums.isNeobrutalism ? 0 : Enums.radius.small
    // 但大多数情况你无需判断——控件已自动适配皮肤
}
```

**架构亮点**：皮肤差异收敛在 token 层（颜色 / 几何 / 阴影），控件本身对皮肤无感知。
新增第三套皮肤只需扩展 token，几乎不动控件代码。

## 🌗 主题系统

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
