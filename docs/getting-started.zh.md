# 快速开始

先完成[安装](install.md)，然后几行代码跑起第一个窗口。

## 第一个窗口

```python
from prismqml import App, WindowType

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("我的应用")
window.resize(1200, 800)

window.show()
app.exec()
```

通过 `window.addPage(PageClass, icon, text)` 可继续添加应用自己的页面类、页面
工厂或页面实例；需要异步孵化 QML 对象树时使用 `AsyncQmlPage`。完整导航用法见
[窗口指南](guide/windows.md)。

`App` 自动完成 DPI 适配、消息处理器安装、`register_types`（注册 QML 类型）、
异步孵化控制器等初始化，并在创建引擎前显式启用 Translator 读取本地 i18n JSON
所需的 QML XHR。普通 `import prismqml` 不会修改进程环境；不需要本地翻译读取时
可使用 `App(allow_qml_file_read=False)`。

若自行创建 `QApplication` 与 `QQmlApplicationEngine`，必须在创建应用对象前调用
`prismqml.python.runtime.prepare_application_environment(allow_qml_file_read=True)`，
并在创建引擎后调用 `register_types(engine)`。只调用
`configure_qml_environment()` 不会配置 DPI、消息处理器或 Windows 图形后端。

Windows 下完整装配入口会在创建首个 `QQuickWindow` 前固定选择 D3D11；无需也
不应由应用代码切换到 OpenGL。macOS 与 Linux 保留 Qt 的平台默认图形后端。

## 在 QML 中使用控件

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "确定"
    style: Fluent.Enums.button.style_primary   // primary 自动用全局主题色
}
```

!!! note "ComboBox / Slider"
    `ComboBox`、`Slider` 已在顶层 `PrismQML` 模块注册。通过模块别名直接使用
    `Fluent.ComboBox` / `Fluent.Slider`，无需导入 QtQuick.Controls 或内部目录。

## 一键切换皮肤

PrismQML 的招牌能力——同一套界面，运行时切换设计语言：

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)         # Fluent Design
setSkin(Skin.NEOBRUTALISM)   # 新粗野
setSkin(Skin.VINTAGE_TICKET) # 复古票据
setSkin(Skin.NEUMORPHISM)    # 新拟态
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
    ├── core/              # 底层能力（主题/日志/图标/窗口辅助）
    ├── runtime/           # 运行时装配（注册/外观持久化边界）
    ├── window/            # 窗口管理（懒加载/云母/托盘）
    ├── state/             # 响应式状态存储
    ├── providers/         # 功能提供者（SVG/二维码/取色器）
    └── models/            # 数据模型（高性能表格）
```
