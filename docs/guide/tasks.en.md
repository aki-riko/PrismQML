# Background Tasks

PrismQML abstracts background work as "submit a callable → get a
`TaskHandle`", with no `QRunnable` / `QThread` subclassing or hand-written
worker objects. For the full API reference see
[Python API](../api/python.md).

## Choosing an execution channel

| | `run_in_pool` | `run_in_thread` |
|---|---------------|-----------------|
| Runs on | Process-managed thread pool | A dedicated `QThread` per call |
| Best for | Bounded, concurrency-friendly short tasks | Long blocking work that needs its own thread |
| Backpressure | Configurable (see below) | None |

```python
from prismqml import App, run_in_pool, run_in_thread

app = App([])

handle = run_in_pool(parse_file, path)          # pooled execution
handle = run_in_thread(sync_worker, timeout=30) # dedicated thread
```

Tasks must be started from the Qt application thread (inside the `App` event
loop), otherwise a `RuntimeError` is raised.

## Reading results

`TaskHandle` exposes a uniform set of lifecycle signals, all emitted on the
Qt application thread:

| Signal | Description |
|--------|-------------|
| `started` / `finished` | Start / end of the task |
| `progress(value)` | Values reported via `report_progress()` inside the task |
| `succeeded(result)` / `failed(failure)` | Success payload / structured failure (`TaskFailure` with `exception` and `traceback`) |
| `cancelled` | Cooperative cancellation |
| `state_changed(state)` | State transitions (`TaskState`) |

```python
handle = run_in_pool(load_library, path)
handle.progress.connect(update_progress)
handle.succeeded.connect(apply_library)
handle.failed.connect(lambda f: report(f.exception))
```

`handle.state` / `handle.result` / `handle.failure` read the final outcome at
any time; `wait(timeout_ms)` blocks until the backend stops and is intended
for tests or non-UI shutdown paths only.

## Progress and cooperative cancellation

Inside a task, `current_task()` returns the `TaskContext`:

```python
from prismqml import current_task

def scan(path):
    task = current_task()
    for done, item in enumerate(items):
        task.report_progress(done)      # → handle.progress
        task.raise_if_cancelled()       # raises TaskCancelledError on cancel
    return results
```

`current_task()` is only available inside the task function. `handle.cancel()`
is cooperative and never calls `terminate()`: pool tasks that have not started
are removed from the queue when possible, while running tasks must check
periodically via `raise_if_cancelled()` or `cancel_requested`. Once a cancel
request is accepted, a task that later returns normally still settles as
`CANCELLED`.

## Pool options and backpressure

```python
from prismqml import PoolSubmitPolicy, PoolTaskOptions, TaskThreadPool, run_in_pool

io_pool = TaskThreadPool()
io_pool.setMaxThreadCount(16)

handle = run_in_pool(
    load_library, path,
    task_options=PoolTaskOptions(pool=io_pool, priority=10),
)
```

| Option | Description |
|--------|-------------|
| `pool` | Accepts `TaskThreadPool` only; defaults to the process-wide global pool |
| `priority` | QThreadPool priority (int) |
| `submit_policy` | Submission policy when the pool is busy |

| `PoolSubmitPolicy` | Behavior when the pool is saturated |
|--------------------|-------------------------------------|
| `QUEUE` (default) | The task waits in the queue for a free thread |
| `REQUIRE_AVAILABLE` | Rejects immediately with `TaskRejectedError` |

## Graceful shutdown

```python
from prismqml import TaskShutdownReport, shutdown_tasks

report = shutdown_tasks(3000)   # cancel all active tasks under one shared deadline
if not report.complete:
    print(f"{report.pending_count} task(s) still running")
```

- `shutdown_tasks(timeout_ms)` first requests cancellation of every active
  task, then waits under one shared deadline and returns a
  `TaskShutdownReport` (`requested_count` / `stopped_count` / `pending`)
- It must be called from the Qt application thread; calling it inside a
  background task raises `RuntimeError` immediately
- `App(task_shutdown_timeout_ms=...)` applies the same policy when
  `App.exec()` exits, raising `TaskShutdownTimeoutError` on timeout; retry the
  idempotent `app.shutdown()` after cleanup
