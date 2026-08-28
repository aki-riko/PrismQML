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
| `prepare_windows_icon` | 从单一图片生成 Windows 多尺寸 ICO |
| `nuitka_icon_options` | 从同一源图片生成当前平台的 Nuitka 图标参数 |

```python
from pathlib import Path

from prismqml import App, WindowType

app = App(application_icon=Path(__file__).with_name("app_icon.png"))
window = app.create_window(WindowType.BAR)
```

`splash_subtitle` 是应用级启动页副标题入口；创建 `App` 时传入后，FastSplash、
纯 QML 默认窗口、Python 窗口以及内嵌 Splash 回退会共同使用该值。不传入时使用
引擎默认启动文案和旧版启动时序；窗口级 `splashSubtitle` 或 `showSplash()` 参数
可以显式覆盖。

`App(allow_qml_file_read=True)` 默认在创建 QML 引擎前启用 Translator 的本地 i18n JSON 读取；传入 `False` 可显式关闭。普通 `import prismqml` 不会修改该环境变量。

Windows 下 `App` 还会在首个 `QQuickWindow` 创建前固定选择 D3D11。自行装配
Qt 应用时，必须在创建 `QApplication` 前调用
`prismqml.python.runtime.prepare_application_environment(True)`，并在创建
`QQmlApplicationEngine` 后调用 `register_types(engine)`；跨层 context/provider
注册统一由该公开入口完成。

`application_icon` 是应用级统一入口：Qt 全局图标、当前及后续创建的 PrismQML
窗口、任务栏和默认启动画面都会继承它；运行时也可调用
`app.set_application_icon(path, colored=True)` 更新全部托管窗口。构建阶段可把同一
源图片交给 `nuitka_icon_options(source, output_dir)`；Windows 会生成多尺寸 ICO，
macOS/Linux 则返回 Nuitka 已验证的平台参数。Inno Setup 等外部安装器可直接消费
`prepare_windows_icon()` 返回的 ICO 路径。

使用自定义 QML 宿主时，可将已创建的主窗口交给
`app.attach_startup_window(window)`，接入 App 持有的 FastSplash 生命周期。
标准 `Fluent.Windows` 会自动完成这一步。

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
| `Skin` | 皮肤枚举（FLUENT / NEOBRUTALISM / VINTAGE_TICKET / NEUMORPHISM） |
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

`run_in_pool()` 默认使用 PrismQML 进程级受管线程池，适合有界、可并发的后台调用；
`run_in_thread()` 为单次调用创建独立 `QThread`，适合需要独占线程的长阻塞任务，
但不替代需要持续事件循环的 QObject/QThread 服务。
两者都返回 `TaskHandle`，统一提供 `started`、`progress`、`succeeded`、
`failed`、`cancelled`、`finished` 和 `state_changed` 信号。公开信号在 Qt 应用
线程发出，`result` / `failure` / `state` 可读取最终状态；`TaskFailure` 同时保留
异常对象和格式化堆栈。

自定义线程池、优先级和背压通过独立选项对象传入，不会占用普通 callable 的位置参数：

```python
from prismqml import PoolSubmitPolicy, PoolTaskOptions, TaskThreadPool, run_in_pool

io_pool = TaskThreadPool()
io_pool.setMaxThreadCount(16)
options = PoolTaskOptions(pool=io_pool, priority=10)
handle = run_in_pool(load_library, library_path, task_options=options)

# 繁忙时不排队，直接抛出 TaskRejectedError
immediate = PoolTaskOptions(
    pool=io_pool,
    submit_policy=PoolSubmitPolicy.REQUIRE_AVAILABLE,
)
```

`PoolTaskOptions.pool` 只接受 `TaskThreadPool`。它会在 `clear()` 时结算已排队的
PrismQML 任务；原生 `QThreadPool` 无法通知框架哪些非自动删除任务被外部清掉，
因此不会被接受。

`handle.cancel()` 是协作式取消，不会调用不安全的 `terminate()`。尚未开始的线程池
任务会尽量从队列安全移除；已经运行的任务应周期性调用
`current_task().raise_if_cancelled()`，或读取 `cancel_requested` 完成清理后返回。
一旦 `cancel()` 接受请求，随后正常返回也会结算为 `CANCELLED`，不会误报成功。

`handle.wait(timeout_ms)` 仅适合测试或非 UI 退出流程；返回 `True` 时后端已经停止，
且 `state` / `result` / `failure` 可立即读取。公开信号仍在 Qt 应用线程排队派发，
因此 `wait()` 返回时回调可能尚未执行；正常界面逻辑应监听信号，避免阻塞事件循环。

`shutdown_tasks(timeout_ms)` 先向当前全部任务请求取消，再使用一个共享总截止时间等待，
并返回 `TaskShutdownReport`。`complete` 为 `False` 时，`pending` 保留仍运行的句柄，
调用方可完成业务清理后再次调用。`App(task_shutdown_timeout_ms=...)` 会将同一策略用于
`App.exec()` 退出；超时时抛出 `TaskShutdownTimeoutError` 并保留 Qt 运行时，防止活跃
`QThread` 被析构；调用方完成清理后可调用公开且幂等的 `app.shutdown()` 重试。
默认 `None` 表示为了安全持续等待。若只使用裸
`QCoreApplication`，应在销毁应用前显式调用 `shutdown_tasks()`。Python CPU 密集型
代码仍受 GIL 限制，需要真正并行时应使用多进程。

`shutdown_tasks()` 必须从 Qt 应用线程调用；后台任务调用会立即抛出 `RuntimeError`，
避免任务等待自身结束。

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

release 响应必须是严格 UTF-8 JSON 对象，`tag_name` 必须是非空字符串，`body`、`html_url`、`assets` 及 asset 字段会按公开 schema 校验；默认还要求所选安装资产带有效的 `sha256:<64位十六进制>` `digest`，下载完成后会再次校验摘要。非法输入只发 `checkFailed`，不会被静默截断或误报为可更新。下载使用进程唯一临时文件，完整写入并 flush/fsync/close 后原子发布；网络、写入、关闭、提交、摘要或空文件失败只发一次 `downloadFailed` 并清理残留。同一 Updater 实例已有任意检查或下载事务时，新检查/下载调用会发对应失败信号而不是静默丢弃。`requireArtifactDigest` 是 QML 只读属性；若可信 Python 集成确实需要兼容旧服务，可显式调用 `set_require_artifact_digest()`。

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
