# Data Models

PrismQML ships two list models that bind directly to QML views.

## TableListModel

In-memory table model: data lives entirely on the Python side while
`QAbstractListModel` supplies rows on demand — a good fit for medium-sized
list/table data.

```python
from prismqml import TableListModel

model = TableListModel()
model.setModelData([
    {"name": "Item 1", "count": 10, "price": "$9.99"},
    {"name": "Item 2", "count": 5,  "price": "$3.50"},
])
```

| Member | Description |
|--------|-------------|
| `setModelData(rows)` | Replace all data; QML role names are inferred from the first row's keys |
| `appendRow(row)` / `removeRow(row)` | Append / remove one row |
| `getRow(row)` | Read one row as a `dict` |
| `clear()` | Clear all rows |
| `count` | Row-count property, notified via the `countChanged` signal |

- Every field name becomes a QML role: read values in delegates as `model.name`
- The `modelData` role returns the whole row `dict`

## SqlListModel

Paged SQLite model: nothing is fetched up front. When `data()` is hit, pages
(1,000 rows by default) load into an LRU cache (64 pages by default), keeping
memory constant — designed for million-row datasets.

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

| Member | Description |
|--------|-------------|
| `setQuery(sql, count_sql, ...)` | Set the paged query; optional `params` / `formatters` / `cursor_columns` and more |
| `count()` | Total row count |
| `getRow(row)` | Return one row as a `dict` (column → value) |
| `refresh()` | Re-run the current query and drop caches after external data changes |

- **Role names = SELECT column names**: write `SELECT col AS xxx` in SQL, then
  reference `model.xxx` in QML
- `formatters` maps column name → callable; raw values are converted once when
  a page loads and cached, so rendering is a pure lookup
- Without `cursor_columns`, pages use `LIMIT/OFFSET`; with them, keyset
  predicates are used instead, making deep paging faster

Keyset paging follows a strict contract: `ORDER BY` must match
`cursor_columns` exactly; at most one nullable cursor column may be declared;
the last cursor column must be globally unique across shards. Query bodies
support only simple top-level `SELECT` statements.

## DbRouter Sharding

Pass a `DbRouter` subclass to `SqlListModel` to query multiple shard files:

```python
from prismqml import DbRouter, SqlListModel

class ShardRouter(DbRouter):
    def route(self, params):
        return ["shard-2024.db", "shard-2025.db"]

model = SqlListModel(ShardRouter())
```

`route()` returns the database files to visit for the current query
parameters: one path behaves like a single database; N paths trigger a
fan-out merge query — each shard fetches its own page, then results are
merged by the cursor columns into a top-N list.

## Rust Acceleration

The Rust extension `prismqml_rs` provides the accelerated path for
SqlListModel (`fetch_page` / `count_rows` / `fan_out_fetch_page`), opening
SQLite read-only and bypassing the GIL and Python object creation overhead.

```python
from prismqml import is_rust_accelerated

is_rust_accelerated()   # True = the Rust extension is loaded
```

- Without `prismqml_rs` installed, the model falls back to the built-in
  `sqlite3` module — functionally identical, just one tier slower
- Build and install instructions live in the `pyproject.toml` comments:
  `cd rust && maturin build --release && pip install target/wheels/prismqml_rs-*.whl`

## QML Usage

Both models are standard `QAbstractListModel` instances and can be assigned
to a view's `model` directly:

```qml
import PrismQML as Fluent

Fluent.TableView { model: backend.tableModel }
Fluent.ListWidget { model: backend.listModel }
```

See [Data](../components/data.md) for the view components.
