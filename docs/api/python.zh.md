# Python API

`from prismqml import ...` 可直接导入的顶层 API。

## 应用与窗口

| 名称 | 说明 |
|------|------|
| `App` | 应用入口，自动完成 DPI / register_types / 孵化控制器 / Translator 环境初始化 |
| `Window` / `WindowCore` | 主窗口 |
| `WindowType` | 窗口类型枚举（BAR / SPLIT / FILLED） |
| `NavigationItem` | 导航项 |
| `AsyncQmlPage` | 使用引擎标准 LoadingOverlay 和孵化控制器异步创建带 Python backend 的 QML 页面 |

```python
from prismqml import App, WindowType
app = App()
window = app.create_window(WindowType.BAR)
```

`App(allow_qml_file_read=True)` 默认在创建 QML 引擎前启用 Translator 的本地 i18n JSON 读取；传入 `False` 可显式关闭。普通 `import prismqml` 不会修改该环境变量。

`AsyncQmlPage` 供 Python 页面工厂使用。目标 QML 根对象必须声明
`property var backend`；页面管理器会先挂载轻量宿主，再通过异步 `Loader`
分帧创建目标对象树，并在 `page_ready` 之前持续显示窗口自带的标准加载遮罩：

```python
from pathlib import Path

from prismqml import AsyncQmlPage

class LibraryPage(AsyncQmlPage):
    def __init__(self, parent=None):
        super().__init__(Path(__file__).with_name("LibraryPage.qml"), parent)
```

字符串和 `Path` 表示本地文件；其他 URL 应显式传入 `QUrl`。页面工厂本身及其
Python 业务初始化仍同步执行，应保持轻量；该封装异步处理的是目标 QML 对象树。
如果目标根对象内部还有需要分帧完成的首屏容器（例如 `StackView.initialItem`），
可声明 `property bool prismqmlAsyncReady`。引擎会等待该属性首次变为 `true` 后再
发出 `page_ready`；未声明该属性的页面仍以 Loader Ready 作为就绪条件。

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

## 后台任务

业务代码无需继承 `QRunnable`、`QThread` 或手写 worker 对象，只需提交普通
Python callable：

```python
from prismqml import current_task, run_in_pool

def load_library(path):
    task = current_task()
    task.report_progress("scanning")
    task.raise_if_cancelled()
    return scan_library(path)

handle = run_in_pool(load_library, library_path)
handle.progress.connect(update_progress)
handle.succeeded.connect(apply_library)
handle.failed.connect(report_failure)
```

`run_in_pool()` 使用 Qt 全局线程池，适合有界、可并发的后台调用；
`run_in_thread()` 为单次调用创建独立 `QThread`，适合需要独占线程的长阻塞任务。
两者都返回 `TaskHandle`，统一提供 `started`、`progress`、`succeeded`、
`failed`、`cancelled`、`finished` 和 `state_changed` 信号。公开信号在 Qt 应用
线程发出，`result` / `failure` / `state` 可读取最终状态；`TaskFailure` 同时保留
异常对象和格式化堆栈。

`handle.cancel()` 是协作式取消，不会调用不安全的 `terminate()`。长任务应周期性
调用 `current_task().raise_if_cancelled()`；也可读取 `cancel_requested` 自行清理后
返回。`App.exec()` 退出时会调用 `shutdown_tasks()`，先请求取消，再等待执行后端
完全停止，防止仍在运行的 `QThread` 被析构。若只使用裸 `QCoreApplication`，应在
销毁应用前显式调用 `shutdown_tasks()`。Python CPU 密集型代码仍受 GIL 限制，需
真正并行时应使用多进程。`handle.wait(timeout_ms)` 仅适合测试或非 UI 退出流程；
正常界面逻辑应监听信号，避免阻塞 Qt 应用线程。

## 引擎组件

| 名称 | 说明 |
|------|------|
| `Updater` | 基于 GitHub Releases 的自动更新，支持自定义 API 根地址 |
| `SingleInstance` | 单实例（Named Mutex + IPC） |
| `SystemTrayIcon` | 系统托盘 |
| `Icon` / `make_icon` / `make_theme_icon` | 图标 |
| `IconProvider` / `register_icon_provider` | 显式图标路径提供器，仅公开 `getPath(name)` / `isValid(name)`；窗口默认不注入 `Icon` context |
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
