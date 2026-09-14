# State Management

`Store` provides thread-confined reactive state with fine-grained watchers, batch
updates, and bindable QML views.

## Thread model

The Qt thread that creates a Store owns its state and notification order. `set`,
`define`, `watch`, and batches must run on that Qt thread. Worker threads must use
`post_set`, which returns a `concurrent.futures.Future`; queued updates execute in
submission order on the Store thread, so Python watchers, Qt signals, and QML
bindings never run on a worker thread.

```python
future = store.post_set("count", 10)
future.result()  # Wait from a worker only; never block the Store thread.
```

Calling `future.cancel()` cancels only the waiter's completion notification; it does
not roll back an update that has already been queued. Later updates remain ordered and
continue to drain normally.

`get` and `values` may be read from another thread and are protected by a lock.
They return shallow snapshots, so mutable values should still be copied by callers.

## Basic usage

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# watch changes; the handle is callable and also has close()
subscription = store.watch("count", lambda new, old: print(f"{old} → {new}"))

# set a value
store.set("count", 1)     # prints: 0 → 1
```

## Batch updates

```python
# batch update (coalesced notification, avoids triggering watch multiple times)
with store.batch():
    store.set("count", 10)
    store.set("user", "Alice")
# notifies once on exiting the with block
```

## Dict syntax

```python
store["count"] = 20
print(store["count"])      # 20
```

## QML bindings

Expose the facade with `as_qml()` and use a stable per-key binding object instead of
rebuilding bindings from the generic `changed(key, new, old)` signal:

```python
qml_store = store.as_qml()
engine.rootContext().setContextProperty("appStore", qml_store)
```

```qml
Text {
    text: appStore.binding("count").value
}

Connections {
    target: appStore
    function onChanged(key, newValue, oldValue) {
        // Use this for cross-key auditing; fields use binding().value.
    }
}
```

Pass `owner=` to `watch` or `watch_all` to disconnect automatically when a QObject is
destroyed. `close()` rejects future updates and detaches every subscription.
