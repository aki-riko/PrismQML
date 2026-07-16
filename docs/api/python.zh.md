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

版本比较会去除可选的 `v` / `V` 前缀，支持项目使用的可变长度点分数字主版本和点分预发布标识；正式版高于同主版本的预发布版，`+` 后的构建元数据不参与优先级，空白或仅前缀标签视为最小版本。该逻辑用于比较 GitHub tag，不是严格拒绝非标准 tag 的完整 SemVer 校验器。

release 响应必须是严格 UTF-8 JSON 对象，`tag_name` 必须是非空字符串，`body`、`html_url`、`assets` 及 asset 字段会按公开 schema 校验；非法输入只发 `checkFailed`，不会被静默截断或误报为可更新。下载使用进程唯一临时文件，完整写入并 flush/fsync/close 后原子发布；网络、写入、关闭、提交或空文件失败只发一次 `downloadFailed` 并清理残留。同一 Updater 实例已有检查或下载进行时，重复调用会被忽略且不会替换活动 reply。

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
