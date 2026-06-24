# 快速开始

## 安装

```bash
pip install prismqml
```

PrismQML 依赖 PySide6（自动安装）。分发名与导入名一致：装好后 `from prismqml import ...`。

## 第一个窗口

```python
from prismqml import App, Window, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("我的应用")
window.resize(1200, 800)

# 添加导航页面（QML 组件 + 图标名 + 标题）
window.addPage(HomePage, "Home", "首页")
window.addPage(SettingsPage, "Settings", "设置")

window.show()
app.exec()
```

`App` 自动完成 DPI 适配、消息处理器安装、`register_types`（注册 QML 类型）、异步孵化控制器等初始化——你无需手动配置。

## 在 QML 中使用控件

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "确定"
    style: Fluent.Enums.button.style_primary   // primary 自动用全局主题色
}
```

!!! note "ComboBox / Slider 的导入"
    `ComboBox`、`Slider` 因与 QtQuick.Controls 原生类型同名，未在顶层 `PrismQML` 模块导出，
    需按子模块目录导入，例如 `import "../prismqml/PrismQML/controls/inputs"`。

## 一键切换皮肤

PrismQML 的招牌能力——同一套界面，运行时切换设计语言：

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)         # Fluent Design
setSkin(Skin.NEOBRUTALISM)   # 新粗野
```

详见 [皮肤系统](guide/skins.md)。

## 项目结构

```
prismqml/
├── PrismQML/              # QML 组件（模块名 PrismQML）
│   ├── controls/          # UI 控件
│   ├── _internal/         # 内部窗口实现
│   └── PrismEnums/        # 枚举与常量
└── python/                # Python 模块
    ├── config/            # 配置管理系统
    ├── core/              # 核心引擎（主题/皮肤/日志/图标/阴影）
    ├── window/            # 窗口管理（懒加载/云母/托盘）
    ├── state/             # 响应式状态存储
    ├── providers/         # 功能提供者（SVG/二维码/取色器）
    └── models/            # 数据模型（高性能表格）
```
