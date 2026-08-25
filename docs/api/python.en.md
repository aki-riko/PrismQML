# Python API

Top-level API importable via `from prismqml import ...`.

## App & Window

| Name | Description |
|------|-------------|
| `App` | Application entry; auto-handles DPI / register_types / incubation controller / Translator environment |
| `Window` / `WindowCore` | Main window |
| `WindowType` | Window type enum (BAR / SPLIT / FILLED) |
| `NavigationItem` | Navigation item |
| `AsyncQmlPage` | Creates a Python-backed QML page through the engine LoadingOverlay and incubation controller |
| `prepare_windows_icon` | Derives a multi-size Windows ICO from one source image |
| `nuitka_icon_options` | Produces the platform Nuitka icon option from the same source image |

```python
from pathlib import Path

from prismqml import App, WindowType

app = App(application_icon=Path(__file__).with_name("app_icon.png"))
window = app.create_window(WindowType.BAR)
```

Pass `splash_subtitle` to `App` when the fast startup surface must render a
custom subtitle on its first visible frame. Omitting it preserves the default
startup text and legacy startup timing.

`App(allow_qml_file_read=True)` enables local i18n JSON access for Translator before creating the QML engine; pass `False` to disable it explicitly. A plain `import prismqml` does not change this environment setting.

On Windows, `App` also selects D3D11 before the first `QQuickWindow`. For a
manually assembled Qt application, call
`prismqml.python.runtime.prepare_application_environment(True)` before constructing
`QApplication`, then call `register_types(engine)` after constructing
`QQmlApplicationEngine`. The public registry owns cross-layer context and
provider registration.

`application_icon` is the application-level entry point. The shared Qt icon,
all current and future PrismQML windows, the taskbar, and the default splash
inherit it. Call `app.set_application_icon(path, colored=True)` to update all
managed windows at runtime. During packaging, pass the same source image to
`nuitka_icon_options(source, output_dir)`: Windows receives a generated
multi-size ICO, while macOS and Linux receive their verified Nuitka option.
External installers such as Inno Setup can consume the ICO path returned by
`prepare_windows_icon()`.

`AsyncQmlPage` is intended for Python page factories. The target QML root must
declare `property var backend`. The page manager attaches a lightweight host,
incubates the target tree through an asynchronous `Loader`, and keeps the
window's standard loading overlay visible until `page_ready` is emitted:

```python
from pathlib import Path

from prismqml import AsyncQmlPage

class LibraryPage(AsyncQmlPage):
    def __init__(self, parent=None):
        super().__init__(Path(__file__).with_name("LibraryPage.qml"), parent)
```

Strings and `Path` values identify local files; pass `QUrl` explicitly for other
URL schemes. The page factory and its Python business initialization remain
synchronous and should stay lightweight; this wrapper asynchronously creates
the target QML object tree.
If the target root has additional first-frame content that is also incubated
(for example, `StackView.initialItem`), it may declare
`property bool prismqmlAsyncReady`. The engine waits for that property to first
become `true` before emitting `page_ready`. Targets without the property still
use Loader Ready as their readiness condition.

## Skin & Theme

| Name | Description |
|------|-------------|
| `Skin` | Skin enum (FLUENT / NEOBRUTALISM / VINTAGE_TICKET / NEUMORPHISM) |
| `setSkin` / `getSkin` | Switch / get skin |
| `Theme` | Theme enum (LIGHT / DARK / AUTO) |
| `setTheme` / `getTheme` / `isDark` | Theme switch / query |
| `setAccentColor` / `getAccentColor` / `accentQColor` | Accent color |
| `getThemeManager` | ThemeManager singleton |

## State & Config

| Name | Description |
|------|-------------|
| `Store` | Reactive state store |
| `prismqml.python.config` | Config system (AppConfig / getConfigManager / SettingsCore / SettingEntry / Validator) |

## Background tasks

Application code can submit a plain Python callable without subclassing
`QRunnable`, `QThread`, or a worker object:

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

`run_in_pool()` uses PrismQML's process-wide managed pool by default for bounded concurrent
calls. `run_in_thread()` creates one dedicated `QThread` for a long blocking
call, but does not replace QObject/QThread services that require a persistent
event loop.
Both return a `TaskHandle` with the same `started`, `progress`, `succeeded`,
`failed`, `cancelled`, `finished`, and `state_changed` signals. Public signals
are emitted on the Qt application thread; `result`, `failure`, and `state`
expose the final outcome. `TaskFailure` preserves both the exception object and
its formatted traceback.

Custom pools, priority, and backpressure use a separate options object, leaving
ordinary callable positional arguments untouched:

```python
from prismqml import PoolSubmitPolicy, PoolTaskOptions, TaskThreadPool, run_in_pool

io_pool = TaskThreadPool()
io_pool.setMaxThreadCount(16)
options = PoolTaskOptions(pool=io_pool, priority=10)
handle = run_in_pool(load_library, library_path, task_options=options)

# Reject with TaskRejectedError instead of queueing when all workers are busy.
immediate = PoolTaskOptions(
    pool=io_pool,
    submit_policy=PoolSubmitPolicy.REQUIRE_AVAILABLE,
)
```

`PoolTaskOptions.pool` accepts only `TaskThreadPool`. It settles queued PrismQML
tasks when `clear()` is called; a raw `QThreadPool` cannot report which
non-auto-deleting tasks were externally removed, so it is rejected.

`handle.cancel()` is cooperative and never calls the unsafe `terminate()`.
Queued pool work is safely removed when possible. Running work should
periodically call `current_task().raise_if_cancelled()`, or inspect
`cancel_requested`, clean up, and return. Once `cancel()` accepts a request, a
subsequent normal return settles as `CANCELLED` instead of reporting success.

`handle.wait(timeout_ms)` is intended for tests or non-UI teardown paths. A
`True` return guarantees the backend has stopped and `state`, `result`, and
`failure` are immediately readable. Public signals remain queued to the Qt
application thread, so their callbacks may still be pending when `wait()`
returns. Normal UI code should observe signals instead of blocking the event
loop.

`shutdown_tasks(timeout_ms)` requests cancellation for the captured tasks,
waits against one shared deadline, and returns a `TaskShutdownReport`. When
`complete` is false, `pending` retains the live handles so cleanup can finish
before a retry. `App(task_shutdown_timeout_ms=...)` applies the same policy to
`App.exec()` teardown; a deadline raises `TaskShutdownTimeoutError` while
preserving the Qt runtime instead of destroying a live `QThread`. After its
cleanup finishes, the caller can retry through the public, idempotent
`app.shutdown()`. The default `None` waits indefinitely for safety.
Applications using a bare
`QCoreApplication` should call `shutdown_tasks()` before teardown. Python
CPU-bound code is still constrained by the GIL; use multiprocessing for true
CPU parallelism.

`shutdown_tasks()` must be called from the Qt application thread. A background
task call raises `RuntimeError` immediately instead of waiting for itself.

## Engine components

| Name | Description |
|------|-------------|
| `Updater` | Auto-update via GitHub Releases with a configurable API base URL |
| `SingleInstance` | Single instance (Named Mutex + IPC) |
| `SystemTrayIcon` | System tray |
| `Icon` / `make_icon` / `make_theme_icon` | Icons |
| `IconProvider` / `register_icon_provider` | Explicit icon path provider with only `getPath(name)` / `isValid(name)`; windows do not inject the `Icon` context by default |
| `ShadowManager` / `getShadowManager` / `installDwmSyncFilter` | Window shadow |

For `Updater(..., api_base_url="https://github.example/api/v3")`, the explicit value wins, followed by `PRISMQML_UPDATER_API_BASE_URL`, then the public GitHub API. Whitespace and trailing `/` characters are normalized.

Version comparison strips an optional `v` / `V` prefix and supports the project's variable-length dotted numeric core plus dotted prerelease identifiers. A release outranks a prerelease with the same core, build metadata after `+` does not affect precedence, and blank or prefix-only tags are treated as the minimum version. This compares GitHub tags; it is not a strict validator that rejects every non-standard SemVer tag.

Release responses must be strict UTF-8 JSON objects. `tag_name` must be a non-empty string, while `body`, `html_url`, `assets`, and asset fields are checked against the public schema. By default, the selected installer asset must also carry a valid `sha256:<64-hex>` `digest`, which is verified again after download. Invalid input emits only `checkFailed`; it is never silently truncated or reported as an update. Downloads use process-unique temporary files and are published atomically only after complete write, flush, fsync, and close steps. Network, write, close, commit, digest, or empty-file failures emit `downloadFailed` once and remove partial artifacts. When any check or download transaction is already active on the same Updater instance, a new check or download emits its matching failure signal instead of being silently dropped. `requireArtifactDigest` is read-only to QML; trusted Python integrations that must support an older service may explicitly call `set_require_artifact_digest()`.

## Logging

| Name | Description |
|------|-------------|
| `Logger` / `getLogger` | Logger |
| `debug` / `info` / `warning` / `error` / `exception` | Log functions |

## Utilities

| Name | Description |
|------|-------------|
| `qml_path` | QML module path |
| `configure_qml_environment` | Explicitly configure local QML XHR for Translator before creating a bare `QQmlApplicationEngine` |
| `register_types` | Register QML types (called internally by App) |

```python
from PySide6.QtQml import QQmlApplicationEngine
from prismqml import configure_qml_environment

configure_qml_environment()
engine = QQmlApplicationEngine()
```

> Full exports in `prismqml/__init__.py`'s `__all__`.
