// prismqml_rs - PrismQML Rust 加速模块
// 提供 SQLite 分页拉取,绕开 Python sqlite3 + dict 创建的瓶颈
//
// 设计:
// - fetch_page: 一次拿一页(默认 1000 行)行数据,以 list[list[any]] 返回
//   外层 list 是行,内层 list 是列(顺序对应 SELECT 语句的列)
// - count_rows: 单独 SELECT COUNT(*) 接口,供 model.rowCount 调用
// - 所有 SQL 由调用方提供(已 prepared statement,Rust 不拼字符串避免注入)
//
// 性能:
// - rusqlite + bundled SQLite,跟 Python sqlite3 是同一引擎但绕开 GIL/PyObject 创建
// - 列值用 PyObject::None / int / float / str / bytes 直出,无中间 dict
// - 实测 1000 行/页耗时 < 5ms

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict};
use rusqlite::{Connection, OpenFlags, types::ValueRef};

// shard router 模块: 跨分片 fan-out 查询
mod shard;

/// 把单元格 ValueRef 转成 PyObject(无 dict, 无 String 二次分配)
pub fn value_ref_to_py(py: Python, v: ValueRef) -> PyResult<PyObject> {
    Ok(match v {
        ValueRef::Null => py.None(),
        ValueRef::Integer(i) => i.into_py(py),
        ValueRef::Real(f) => f.into_py(py),
        ValueRef::Text(bytes) => {
            // B7 修复: 成功路径直接 borrow &str → into_py (无 alloc),
            // 失败路径才走 lossy String + into_owned (脏数据极少触发)
            match std::str::from_utf8(bytes) {
                Ok(s) => s.into_py(py),
                Err(_) => String::from_utf8_lossy(bytes).into_owned().into_py(py),
            }
        }
        ValueRef::Blob(bytes) => bytes.into_py(py),
    })
}

/// 绑定 SQL 参数: 接受 None / list / tuple,把 Python 值映射到 rusqlite 占位符
fn bind_params<'a>(
    stmt: &'a mut rusqlite::Statement,
    params: Option<&Bound<'_, PyAny>>,
) -> PyResult<rusqlite::Rows<'a>> {
    use rusqlite::types::Value;

    let bound: Vec<Value> = if let Some(p) = params {
        let len = p.len()?;
        let mut v = Vec::with_capacity(len);
        for i in 0..len {
            let item = p.get_item(i)?;
            // 顺序: None / bool / int / float / str / bytes
            if item.is_none() {
                v.push(Value::Null);
            } else if let Ok(b) = item.extract::<bool>() {
                v.push(Value::Integer(if b { 1 } else { 0 }));
            } else if let Ok(i) = item.extract::<i64>() {
                v.push(Value::Integer(i));
            } else if let Ok(f) = item.extract::<f64>() {
                v.push(Value::Real(f));
            } else if let Ok(s) = item.extract::<String>() {
                v.push(Value::Text(s));
            } else if let Ok(bs) = item.extract::<Vec<u8>>() {
                v.push(Value::Blob(bs));
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                    "unsupported sql parameter type at index {}",
                    i
                )));
            }
        }
        v
    } else {
        Vec::new()
    };

    let refs: Vec<&dyn rusqlite::ToSql> = bound.iter().map(|v| v as &dyn rusqlite::ToSql).collect();
    let rows = stmt
        .query(refs.as_slice())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    Ok(rows)
}

/// 打开 SQLite (只读 + WAL 兼容)
fn open_conn(db_path: &str) -> PyResult<Connection> {
    Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

/// 拉取一页数据
///
/// Args:
///     db_path: SQLite 文件路径
///     sql: 已含 ORDER BY 的 SELECT 语句
///         - keyset 模式: 调用方拼好 WHERE 含 (cursor_cols) < (?,?,?) 谓词,
///           cursor_values 跟在 params 之后传进来
///         - OFFSET 模式: sql 不含 cursor 谓词,Rust 末尾追加 LIMIT ? OFFSET ?
///     params: SQL 占位符参数 (list/tuple/None)
///     offset: 偏移行数 (use_keyset=true 时忽略)
///     limit: 拉取行数 (默认 1000)
///     use_keyset: true 时不追加 LIMIT/OFFSET (假设 sql 自己处理), 实际只追加 LIMIT ?
///     extract_cursor_indices: 列下标列表; 若传入,返回 dict 中 last_cursor = 末行这些列的值
///
/// Returns:
///     dict {
///         "columns": [str, ...],
///         "rows": [[v1, v2, ...], ...],
///         "last_cursor": [v1, v2, ...] | None,  # 仅 extract_cursor_indices 传入时有
///     }
#[pyfunction]
#[pyo3(signature = (db_path, sql, params=None, offset=0, limit=1000, use_keyset=false, extract_cursor_indices=None))]
fn fetch_page(
    py: Python,
    db_path: &str,
    sql: &str,
    params: Option<&Bound<'_, PyAny>>,
    offset: i64,
    limit: i64,
    use_keyset: bool,
    extract_cursor_indices: Option<Vec<usize>>,
) -> PyResult<PyObject> {
    // SQL 末尾追加 LIMIT (keyset) 或 LIMIT/OFFSET (offset 模式)
    let final_sql = if use_keyset {
        format!("{} LIMIT ?", sql)
    } else {
        format!("{} LIMIT ? OFFSET ?", sql)
    };
    let conn = open_conn(db_path)?;
    let mut stmt = conn
        .prepare(&final_sql)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let column_count = stmt.column_count();
    let column_names: Vec<String> = (0..column_count)
        .map(|i| stmt.column_name(i).unwrap_or("").to_string())
        .collect();

    // 把分页参数追加到用户 params 后
    use rusqlite::types::Value;
    let mut bound: Vec<Value> = Vec::new();
    if let Some(p) = params {
        let len = p.len()?;
        for i in 0..len {
            let item = p.get_item(i)?;
            if item.is_none() {
                bound.push(Value::Null);
            } else if let Ok(b) = item.extract::<bool>() {
                bound.push(Value::Integer(if b { 1 } else { 0 }));
            } else if let Ok(i) = item.extract::<i64>() {
                bound.push(Value::Integer(i));
            } else if let Ok(f) = item.extract::<f64>() {
                bound.push(Value::Real(f));
            } else if let Ok(s) = item.extract::<String>() {
                bound.push(Value::Text(s));
            } else if let Ok(bs) = item.extract::<Vec<u8>>() {
                bound.push(Value::Blob(bs));
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
                    "unsupported sql parameter type at index {}",
                    i
                )));
            }
        }
    }
    bound.push(Value::Integer(limit));
    if !use_keyset {
        bound.push(Value::Integer(offset));
    }

    let refs: Vec<&dyn rusqlite::ToSql> =
        bound.iter().map(|v| v as &dyn rusqlite::ToSql).collect();
    let mut rows = stmt
        .query(refs.as_slice())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let py_rows = PyList::empty_bound(py);
    // M5: 只在 cursor 列上 clone_ref,非 cursor 列 move 给 py_row 不浪费 PyObject 引用
    // 末行的 cursor 列保留 (覆盖式) 用于输出 last_cursor
    let cursor_idx_list: Option<&Vec<usize>> = extract_cursor_indices.as_ref();
    // B6: 循环外建 sorted_idx + 复用的 last_cursor_by_col HashMap,避免每行 alloc
    let mut sorted_idx: Vec<usize> = cursor_idx_list.cloned().unwrap_or_default();
    sorted_idx.sort_unstable();
    sorted_idx.dedup();
    let mut last_cursor_by_col: std::collections::HashMap<usize, PyObject> =
        std::collections::HashMap::with_capacity(sorted_idx.len());

    while let Some(row) = rows
        .next()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
    {
        let py_row = PyList::empty_bound(py);
        // 每行覆盖式更新 last_cursor_by_col (而非 alloc 新 HashMap)
        if cursor_idx_list.is_some() {
            last_cursor_by_col.clear();
        }
        let mut next_cursor_pos = 0;
        for c in 0..column_count {
            let v = row
                .get_ref(c)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            let py_val = value_ref_to_py(py, v)?;
            if next_cursor_pos < sorted_idx.len() && sorted_idx[next_cursor_pos] == c {
                last_cursor_by_col.insert(c, py_val.clone_ref(py));
                next_cursor_pos += 1;
            }
            py_row.append(py_val)?;
        }
        py_rows.append(py_row)?;
    }

    let result = PyDict::new_bound(py);
    result.set_item("columns", column_names)?;
    result.set_item("rows", py_rows)?;
    // M5: 按用户原 extract_cursor_indices 顺序输出 cursor 值
    if let Some(indices) = cursor_idx_list {
        let cursor_list = PyList::empty_bound(py);
        if !last_cursor_by_col.is_empty() {
            for &idx in indices {
                if let Some(v) = last_cursor_by_col.get(&idx) {
                    cursor_list.append(v.clone_ref(py))?;
                } else {
                    cursor_list.append(py.None())?;
                }
            }
            result.set_item("last_cursor", cursor_list)?;
        } else {
            result.set_item("last_cursor", py.None())?;
        }
    } else {
        result.set_item("last_cursor", py.None())?;
    }
    Ok(result.into())
}

/// 统计行数
///
/// Args:
///     db_path: SQLite 文件
///     sql_count: 完整 SELECT COUNT(*) ... 语句
///     params: 占位符参数
///
/// Returns:
///     int 行数
///
/// 注意: 当 sql_count 是返回 0 行的标量查询时 (例如读 count 缓存表
/// `SELECT total FROM counts WHERE id=?` 而该行尚未建立),返回 0 而非抛异常。
/// 这与 Python fallback 路径 (`row = cur.fetchone(); int(row[0]) if row else 0`)
/// 语义一致 —— "count 查询无匹配行" 即计数 0,两路径行为对齐,避免下游因
/// 缓存行缺失而崩溃 (count query returned no rows)。
#[pyfunction]
#[pyo3(signature = (db_path, sql_count, params=None))]
fn count_rows(
    db_path: &str,
    sql_count: &str,
    params: Option<&Bound<'_, PyAny>>,
) -> PyResult<i64> {
    let conn = open_conn(db_path)?;
    let mut stmt = conn
        .prepare(sql_count)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let mut rows = bind_params(&mut stmt, params)?;
    // 标量查询返回 0 行 → 计数 0 (对齐 Python fallback 的 `if row else 0`),不抛异常。
    match rows
        .next()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
    {
        Some(row) => row
            .get::<_, i64>(0)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string())),
        None => Ok(0),
    }
}

/// 模块定义
#[pymodule]
fn prismqml_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fetch_page, m)?)?;
    m.add_function(wrap_pyfunction!(count_rows, m)?)?;
    m.add_function(wrap_pyfunction!(shard::fan_out_fetch_page, m)?)?;
    m.add_function(wrap_pyfunction!(verify_agg_monthly, m)?)?;
    m.add("__version__", "0.3.1")?;
    Ok(())
}

/// 校验 agg_monthly 与主表 bookkeeping_records 的一致性
///
/// 跑 GROUP BY 重算每个 (book_id, year_month, type) 的真实 count/sum,
/// 与 agg_monthly 表对照,返回不一致行的列表。Python 端可用此结果决定是否修复。
///
/// Args:
///     db_path: SQLite 文件路径 (单 shard 文件或主库)
///
/// Returns:
///     list of dict: [{'book_id', 'year_month', 'type', 'agg_count', 'real_count',
///                     'agg_sum', 'real_sum'}, ...]
///     空列表表示完全一致。
#[pyfunction]
fn verify_agg_monthly(py: Python, db_path: &str) -> PyResult<PyObject> {
    let conn = open_conn(db_path)?;
    // 左 join 让 agg 缺失或主表多余都能检测
    let sql = "
        WITH real_agg AS (
            SELECT book_id, substr(date, 1, 7) AS ym, COALESCE(type, '') AS t,
                   COUNT(*) AS rc, SUM(COALESCE(amount, 0)) AS rs
            FROM bookkeeping_records
            GROUP BY book_id, ym, t
        )
        SELECT COALESCE(a.book_id, r.book_id),
               COALESCE(a.year_month, r.ym),
               COALESCE(a.type, r.t),
               COALESCE(a.count, 0),
               COALESCE(r.rc, 0),
               COALESCE(a.amount_sum, 0),
               COALESCE(r.rs, 0)
        FROM bookkeeping_agg_monthly a
        FULL OUTER JOIN real_agg r
          ON a.book_id = r.book_id AND a.year_month = r.ym AND a.type = r.t
        WHERE COALESCE(a.count, 0) != COALESCE(r.rc, 0)
           OR ABS(COALESCE(a.amount_sum, 0) - COALESCE(r.rs, 0)) > 0.01
    ";
    // SQLite 不支持 FULL OUTER JOIN(<3.39 之前),fallback 到 UNION ALL
    let sql_compat = "
        SELECT a.book_id, a.year_month, a.type, a.count, COALESCE(r.rc, 0),
               a.amount_sum, COALESCE(r.rs, 0)
        FROM bookkeeping_agg_monthly a
        LEFT JOIN (
            SELECT book_id, substr(date, 1, 7) AS ym, COALESCE(type, '') AS t,
                   COUNT(*) AS rc, SUM(COALESCE(amount, 0)) AS rs
            FROM bookkeeping_records
            GROUP BY book_id, ym, t
        ) r ON a.book_id = r.book_id AND a.year_month = r.ym AND a.type = r.t
        WHERE a.count != COALESCE(r.rc, 0)
           OR ABS(a.amount_sum - COALESCE(r.rs, 0)) > 0.01

        UNION ALL

        SELECT r.book_id, r.ym, r.t, 0, r.rc, 0, r.rs
        FROM (
            SELECT book_id, substr(date, 1, 7) AS ym, COALESCE(type, '') AS t,
                   COUNT(*) AS rc, SUM(COALESCE(amount, 0)) AS rs
            FROM bookkeeping_records
            GROUP BY book_id, ym, t
        ) r
        LEFT JOIN bookkeeping_agg_monthly a
          ON a.book_id = r.book_id AND a.year_month = r.ym AND a.type = r.t
        WHERE a.book_id IS NULL
    ";
    // 优先 FULL OUTER JOIN; 失败再 fallback
    let mut stmt = conn.prepare(sql).or_else(|_| conn.prepare(sql_compat))
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
    let mut rows = stmt
        .query([])
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let result = PyList::empty_bound(py);
    while let Some(row) = rows
        .next()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?
    {
        let item = PyDict::new_bound(py);
        item.set_item("book_id", row.get::<_, i64>(0).unwrap_or(0))?;
        item.set_item("year_month", row.get::<_, String>(1).unwrap_or_default())?;
        item.set_item("type", row.get::<_, String>(2).unwrap_or_default())?;
        item.set_item("agg_count", row.get::<_, i64>(3).unwrap_or(0))?;
        item.set_item("real_count", row.get::<_, i64>(4).unwrap_or(0))?;
        item.set_item("agg_sum", row.get::<_, f64>(5).unwrap_or(0.0))?;
        item.set_item("real_sum", row.get::<_, f64>(6).unwrap_or(0.0))?;
        result.append(item)?;
    }
    Ok(result.into())
}
