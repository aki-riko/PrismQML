# 状态管理

`Store` 提供线程归属明确的响应式状态存储，支持细粒度 watch、批量更新和 QML 可绑定视图。

## 线程模型

Store 在创建线程拥有状态和通知顺序。`set`、`define`、`watch` 和批处理只能在
该 Qt 线程调用；后台线程必须使用 `post_set`。`post_set` 返回一个
`concurrent.futures.Future`，更新会通过 Qt 的 queued signal 按提交顺序在 Store
线程执行，因此 Python watcher、Qt signal 和 QML binding 不会在 worker 线程运行。

```python
future = store.post_set("count", 10)
future.result()  # 只在后台线程等待；不要让 Store 线程等待自己
```

调用 `future.cancel()` 只取消等待方，不撤销已经排队的状态更新；这样不会让后续
更新丢失，也不会中断 Store 线程的通知队列。

读取 `get` / `values` 可以跨线程进行，但返回的是受锁保护的浅副本；可变值本身
仍应由调用方使用不可变快照或复制品。

## 基本用法

```python
from prismqml import Store

class AppStore(Store):
    def __init__(self):
        super().__init__("app")
        self.define("user", None)
        self.define("count", 0)

store = AppStore()

# 监听变化；返回值可调用，也可以显式 close()
subscription = store.watch("count", lambda new, old: print(f"{old} → {new}"))

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

## QML 绑定

不要让 QML 直接猜测通用 `changed(key, new, old)` 信号来维护绑定。通过
`as_qml()` 暴露门面，并为每个键取得稳定的绑定对象：

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
        // 只处理跨键审计或日志；界面字段使用 binding().value
    }
}
```

`owner` 参数可以把 watcher 绑定到 QObject 生命周期，QObject 销毁时会自动解绑。
Store 关闭后不再接受更新，并解除所有订阅。
