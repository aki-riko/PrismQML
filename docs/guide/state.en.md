# State Management

`Store` provides reactive state storage with fine-grained watch and batch updates.

## Basic usage

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# watch changes
store.watch("count", lambda new, old: print(f"{old} → {new}"))

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

Ideal for managing app state shared across pages, combined with QML bindings for reactive UI.
