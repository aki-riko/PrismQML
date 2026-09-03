# 后台任务

PrismQML 把后台执行抽象为「提交 callable → 返回 `TaskHandle`」，无需继承
`QRunnable` / `QThread` 或手写 worker 对象。完整 API 说明见
[Python API](../api/python.md)。

## 选择执行通道

| | `run_in_pool` | `run_in_thread` |
|---|---------------|-----------------|
| 运行位置 | 进程级受管线程池 | 每次调用独占一条 `QThread` |
| 适用场景 | 有界、可并发的短任务 | 长阻塞、需要独占线程的任务 |
| 背压 | 可配置（见下文） | 无 |

```python
from prismqml import App, run_in_pool, run_in_thread

app = App([])

handle = run_in_pool(parse_file, path)          # 池化执行
handle = run_in_thread(sync_worker, timeout=30) # 独占线程
```

任务必须从 Qt 应用线程（`App` 事件循环内）启动，否则抛 `RuntimeError`。

## 读取结果

`TaskHandle` 统一提供生命周期信号，全部在 Qt 应用线程发出：

| 信号 | 说明 |
|------|------|
| `started` / `finished` | 开始 / 结束 |
| `progress(value)` | 任务内 `report_progress()` 上报的值 |
| `succeeded(result)` / `failed(failure)` | 成功结果 / 结构化失败（`TaskFailure` 含 `exception` 与 `traceback`） |
| `cancelled` | 协作取消 |
| `state_changed(state)` | 状态迁移（`TaskState`） |

```python
handle = run_in_pool(load_library, path)
handle.progress.connect(update_progress)
handle.succeeded.connect(apply_library)
handle.failed.connect(lambda f: report(f.exception))
```

`handle.state` / `handle.result` / `handle.failure` 可随时读取最终状态；
`wait(timeout_ms)` 会阻塞到后端停止，仅适合测试或非 UI 退出流程。

## 进度上报与协作取消

任务内部通过 `current_task()` 获取 `TaskContext`：

```python
from prismqml import current_task

def scan(path):
    task = current_task()
    for done, item in enumerate(items):
        task.report_progress(done)      # → handle.progress
        task.raise_if_cancelled()       # 收到取消请求时抛 TaskCancelledError
    return results
```

`current_task()` 只能在任务函数内部调用。`handle.cancel()` 是协作式取消，
不会调用 `terminate()`：尚未开始的池任务会尽量从队列安全移除，已运行的任务
需要周期性调用 `raise_if_cancelled()` 或读取 `cancel_requested`。取消请求被
接受后，任务随后正常返回也会结算为 `CANCELLED`。

## 线程池选项与背压

```python
from prismqml import PoolSubmitPolicy, PoolTaskOptions, TaskThreadPool, run_in_pool

io_pool = TaskThreadPool()
io_pool.setMaxThreadCount(16)

handle = run_in_pool(
    load_library, path,
    task_options=PoolTaskOptions(pool=io_pool, priority=10),
)
```

| 选项 | 说明 |
|------|------|
| `pool` | 只接受 `TaskThreadPool`；缺省使用进程级全局池 |
| `priority` | QThreadPool 优先级（int） |
| `submit_policy` | 满载时的提交策略 |

| `PoolSubmitPolicy` | 池满时行为 |
|--------------------|-----------|
| `QUEUE`（默认） | 任务排队等待空闲线程 |
| `REQUIRE_AVAILABLE` | 不排队，直接抛 `TaskRejectedError` |

## 优雅停机

```python
from prismqml import TaskShutdownReport, shutdown_tasks

report = shutdown_tasks(3000)   # 取消全部活动任务，共享一个总截止时间
if not report.complete:
    print(f"{report.pending_count} 个任务仍在运行")
```

- `shutdown_tasks(timeout_ms)` 先向全部活动任务请求取消，再用统一 deadline
  等待，返回 `TaskShutdownReport`（`requested_count` / `stopped_count` / `pending`）
- 必须从 Qt 应用线程调用；后台任务内调用会立即抛 `RuntimeError`
- `App(task_shutdown_timeout_ms=...)` 会在 `App.exec()` 退出时应用同一策略，
  超时抛 `TaskShutdownTimeoutError`，完成清理后可重试 `app.shutdown()`
