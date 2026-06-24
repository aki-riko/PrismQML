# 状态管理

`Store` 提供响应式状态存储，支持细粒度 watch 和批量更新。

## 基本用法

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# 监听变化
store.watch("count", lambda new, old: print(f"{old} → {new}"))

# 设置值
store.set("count", 1)     # 输出: 0 → 1
```

## 批量更新

```python
# 批量更新（合并通知，避免多次触发 watch）
with store.batch():
    store.set("count", 10)
    store.set("user", "Alice")
# 退出 with 时统一通知一次
```

## 字典语法

```python
store["count"] = 20
print(store["count"])      # 20
```

适合管理跨页面共享的应用状态，配合 QML 绑定实现响应式 UI。
