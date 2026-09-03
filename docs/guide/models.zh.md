# 数据模型

PrismQML 提供两个可直接绑定 QML 视图的列表模型。

## TableListModel

内存表格模型：数据整体放在 Python 侧，`QAbstractListModel` 按需供数，适合中等规模的列表/表格数据。

```python
from prismqml import TableListModel

model = TableListModel()
model.setModelData([
    {"name": "商品1", "count": 10, "price": "¥9.99"},
    {"name": "商品2", "count": 5,  "price": "¥3.50"},
])
```

| 成员 | 说明 |
|------|------|
| `setModelData(rows)` | 整体替换数据；QML 角色名自动从第一行的键推断 |
| `appendRow(row)` / `removeRow(row)` | 追加 / 删除一行 |
| `getRow(row)` | 读取一行 `dict` |
| `clear()` | 清空 |
| `count` | 行数属性，随数据变化通知（`countChanged` 信号） |

- 每个字段名就是一个 QML 角色：delegate 中直接 `model.name` 取值
- `modelData` 角色返回整行 `dict`

## SqlListModel

SQLite 分页模型：不一次性取数，`data()` 命中时按页（默认 1000 行）加载进 LRU 缓存（默认 64 页），内存恒定，适合百万行级数据。

```python
from prismqml import SqlListModel

model = SqlListModel("/path/to/db.sqlite")
model.setQuery(
    "SELECT id, date, income FROM records WHERE book_id=:bid ORDER BY date DESC, id",
    "SELECT COUNT(*) FROM records WHERE book_id=:bid",
    params={"bid": 4},
    formatters={"income": lambda v: f"+{v:,}"},
)
```

| 成员 | 说明 |
|------|------|
| `setQuery(sql, count_sql, ...)` | 设置分页查询；可选 `params` / `formatters` / `cursor_columns` 等 |
| `count()` | 总行数 |
| `getRow(row)` | 按行索引返回整行 `dict`（column → value） |
| `refresh()` | 数据被外部改动后重跑当前查询并丢弃缓存 |

- **角色名 = SELECT 字段名**：SQL 里写 `SELECT col AS xxx`，QML 里就用 `model.xxx`
- `formatters` 是「列名 → 回调」字典，新页加载时对原始值转换一次并缓存，渲染时只是查表
- 未传 `cursor_columns` 时按 `LIMIT/OFFSET` 翻页；传入后改走 keyset 谓词，深翻页更快

keyset 有严格合同：`ORDER BY` 必须与 `cursor_columns` 完全一致；最多声明一个可空 cursor 列；末列必须跨分片全局唯一。查询主体只支持简单顶层 `SELECT`。

## DbRouter 跨分片

把 `DbRouter` 子类传给 `SqlListModel` 即可查询多个 shard 文件：

```python
from prismqml import DbRouter, SqlListModel

class ShardRouter(DbRouter):
    def route(self, params):
        return ["shard-2024.db", "shard-2025.db"]

model = SqlListModel(ShardRouter())
```

`route()` 根据查询参数返回需要访问的数据库文件列表：返回 1 个等价单库；返回 N 个时走 fan-out 归并查询——各 shard 独立取页后按 cursor 列归并取 top-N。

## Rust 加速

Rust 扩展 `prismqml_rs` 为 SqlListModel 提供加速路径（`fetch_page` / `count_rows` / `fan_out_fetch_page`），以只读方式打开 SQLite，绕开 GIL 与 Python 对象创建开销。

```python
from prismqml import is_rust_accelerated

is_rust_accelerated()   # True = 已加载 Rust 扩展
```

- 未安装 `prismqml_rs` 时自动回退内置 `sqlite3`，功能完全等价，只是慢一档
- 构建安装见 `pyproject.toml` 注释：`cd rust && maturin build --release && pip install target/wheels/prismqml_rs-*.whl`

## QML 侧使用

两个模型都是标准 `QAbstractListModel`，可直接赋给视图的 `model`：

```qml
import PrismQML as Fluent

Fluent.TableView { model: backend.tableModel }
Fluent.ListWidget { model: backend.listModel }
```

视图控件详见 [数据](../components/data.md)。
