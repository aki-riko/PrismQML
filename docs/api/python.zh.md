# Python API

`from prismqml import ...` 可直接导入的顶层 API。

## 应用与窗口

| 名称 | 说明 |
|------|------|
| `App` | 应用入口，自动完成 DPI / register_types / 孵化控制器 / Translator 环境初始化 |
| `Window` / `WindowCore` | 主窗口 |
| `WindowType` | 窗口类型枚举（BAR / SPLIT / FILLED） |
| `NavigationItem` | 导航项 |

```python
from prismqml import App, WindowType
app = App()
window = app.create_window(WindowType.BAR)
```

`App(allow_qml_file_read=True)` 默认在创建 QML 引擎前启用 Translator 的本地 i18n JSON 读取；传入 `False` 可显式关闭。普通 `import prismqml` 不会修改该环境变量。

## 皮肤与主题

| 名称 | 说明 |
|------|------|
| `Skin` | 皮肤枚举（FLUENT / NEOBRUTALISM / PRISM_DESIGN） |
| `setSkin` / `getSkin` | 切换 / 获取皮肤 |
| `Theme` | 主题枚举（LIGHT / DARK / AUTO） |
| `setTheme` / `getTheme` / `isDark` | 主题切换 / 查询 |
| `setAccentColor` / `getAccentColor` / `accentQColor` | 主题色 |
| `getThemeManager` | ThemeManager 单例 |

## 状态与配置

| 名称 | 说明 |
|------|------|
| `Store` | 响应式状态存储 |
| `prismqml.python.config` | 配置系统（AppConfig / getConfigManager / SettingsCore / SettingEntry / Validator） |

## 引擎组件

| 名称 | 说明 |
|------|------|
| `Updater` | 基于 GitHub Releases 的自动更新，支持自定义 API 根地址 |
| `SingleInstance` | 单实例（Named Mutex + IPC） |
| `SystemTrayIcon` | 系统托盘 |
| `Icon` / `make_icon` / `make_theme_icon` | 图标 |
| `IconProvider` / `register_icon_provider` | 图标提供器 |
| `ShadowManager` / `getShadowManager` / `installDwmSyncFilter` | 窗口阴影 |

`Updater(..., api_base_url="https://github.example/api/v3")` 的显式地址优先，其次读取 `PRISMQML_UPDATER_API_BASE_URL`，最后使用 GitHub 公共 API；空白和尾部 `/` 会被归一化。

## 日志

| 名称 | 说明 |
|------|------|
| `Logger` / `getLogger` | 日志器 |
| `debug` / `info` / `warning` / `error` / `exception` | 日志函数 |

## 工具

| 名称 | 说明 |
|------|------|
| `qml_path` | QML 模块路径 |
| `configure_qml_environment` | 在裸 `QQmlApplicationEngine` 创建前显式配置 Translator 所需的本地 QML XHR |
| `register_types` | 注册 QML 类型（App 内部已调用） |

```python
from PySide6.QtQml import QQmlApplicationEngine
from prismqml import configure_qml_environment

configure_qml_environment()
engine = QQmlApplicationEngine()
```

> 完整导出见 `prismqml/__init__.py` 的 `__all__`。
