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
use pyo3::types::{PyDict, PyList};
use rusqlite::{
    types::{Value, ValueRef},
    Connection, OpenFlags,
};
use std::collections::HashMap;

// shard router 模块: 跨分片 fan-out 查询
mod shard;

struct PageRequest<'a, 'py> {
    db_path: &'a str,
    sql: &'a str,
    params: Option<&'a Bound<'py, PyAny>>,
    offset: i64,
    limit: i64,
    use_keyset: bool,
    cursor_indices: Option<&'a [usize]>,
}

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

fn py_value_to_sql(item: &Bound<'_, PyAny>, index: usize) -> PyResult<Value> {
    if item.is_none() {
        Ok(Value::Null)
    } else if let Ok(value) = item.extract::<bool>() {
        Ok(Value::Integer(if value { 1 } else { 0 }))
    } else if let Ok(value) = item.extract::<i64>() {
        Ok(Value::Integer(value))
    } else if let Ok(value) = item.extract::<f64>() {
        Ok(Value::Real(value))
    } else if let Ok(value) = item.extract::<String>() {
        Ok(Value::Text(value))
    } else if let Ok(value) = item.extract::<Vec<u8>>() {
        Ok(Value::Blob(value))
    } else {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
            "unsupported sql parameter type at index {index}"
        )))
    }
}

fn extract_params(params: Option<&Bound<'_, PyAny>>) -> PyResult<Vec<Value>> {
    let Some(params) = params else {
        return Ok(Vec::new());
    };
    let mut values = Vec::with_capacity(params.len()?);
    for index in 0..params.len()? {
        values.push(py_value_to_sql(&params.get_item(index)?, index)?);
    }
    Ok(values)
}

fn sql_refs(values: &[Value]) -> Vec<&dyn rusqlite::ToSql> {
    values
        .iter()
        .map(|value| value as &dyn rusqlite::ToSql)
        .collect()
}

fn page_sql(sql: &str, use_keyset: bool) -> String {
    let suffix = if use_keyset {
        " LIMIT ?"
    } else {
        " LIMIT ? OFFSET ?"
    };
    format!("{sql}{suffix}")
}

fn validate_page_request(offset: i64, limit: i64) -> Result<(), &'static str> {
    if limit <= 0 {
        return Err("limit must be greater than zero");
    }
    if offset < 0 {
        return Err("offset must not be negative");
    }
    Ok(())
}

fn query_count(conn: &Connection, sql: &str, params: &[Value]) -> rusqlite::Result<i64> {
    let mut stmt = conn.prepare(sql)?;
    let refs = sql_refs(params);
    let mut rows = stmt.query(refs.as_slice())?;
    match rows.next()? {
        Some(row) => row.get::<_, i64>(0),
        None => Ok(0),
    }
}

fn runtime_error(error: impl ToString) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(error.to_string())
}

fn value_error(error: impl ToString) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyValueError, _>(error.to_string())
}

fn statement_column_names(stmt: &rusqlite::Statement<'_>) -> Vec<String> {
    (0..stmt.column_count())
        .map(|index| stmt.column_name(index).unwrap_or("").to_string())
        .collect()
}

fn page_bindings(
    params: Option<&Bound<'_, PyAny>>,
    limit: i64,
    offset: i64,
    use_keyset: bool,
) -> PyResult<Vec<Value>> {
    let mut bound = extract_params(params)?;
    bound.push(Value::Integer(limit));
    if !use_keyset {
        bound.push(Value::Integer(offset));
    }
    Ok(bound)
}

fn normalized_cursor_indices(cursor_indices: Option<&[usize]>) -> Vec<usize> {
    let mut indices = cursor_indices.map(<[usize]>::to_vec).unwrap_or_default();
    indices.sort_unstable();
    indices.dedup();
    indices
}

fn convert_page_row<'py>(
    py: Python<'py>,
    row: &rusqlite::Row<'_>,
    column_count: usize,
    sorted_indices: &[usize],
    last_cursor_by_col: &mut HashMap<usize, PyObject>,
) -> PyResult<Bound<'py, PyList>> {
    let py_row = PyList::empty_bound(py);
    let mut next_cursor_pos = 0;
    for index in 0..column_count {
        let value = value_ref_to_py(py, row.get_ref(index).map_err(runtime_error)?)?;
        if sorted_indices.get(next_cursor_pos) == Some(&index) {
            last_cursor_by_col.insert(index, value.clone_ref(py));
            next_cursor_pos += 1;
        }
        py_row.append(value)?;
    }
    Ok(py_row)
}

fn collect_page_rows<'py>(
    py: Python<'py>,
    rows: &mut rusqlite::Rows<'_>,
    column_count: usize,
    cursor_indices: Option<&[usize]>,
) -> PyResult<(Bound<'py, PyList>, HashMap<usize, PyObject>)> {
    let py_rows = PyList::empty_bound(py);
    let sorted_indices = normalized_cursor_indices(cursor_indices);
    let mut last_cursor_by_col = HashMap::with_capacity(sorted_indices.len());
    while let Some(row) = rows.next().map_err(runtime_error)? {
        if cursor_indices.is_some() {
            last_cursor_by_col.clear();
        }
        let py_row = convert_page_row(
            py,
            row,
            column_count,
            &sorted_indices,
            &mut last_cursor_by_col,
        )?;
        py_rows.append(py_row)?;
    }
    Ok((py_rows, last_cursor_by_col))
}

fn set_page_cursor(
    py: Python<'_>,
    result: &Bound<'_, PyDict>,
    cursor_indices: Option<&[usize]>,
    last_cursor_by_col: &HashMap<usize, PyObject>,
) -> PyResult<()> {
    let Some(indices) = cursor_indices else {
        return result.set_item("last_cursor", py.None());
    };
    if last_cursor_by_col.is_empty() {
        return result.set_item("last_cursor", py.None());
    }
    let cursor_list = PyList::empty_bound(py);
    for index in indices {
        match last_cursor_by_col.get(index) {
            Some(value) => cursor_list.append(value.clone_ref(py))?,
            None => cursor_list.append(py.None())?,
        }
    }
    result.set_item("last_cursor", cursor_list)
}

fn build_page_result(
    py: Python<'_>,
    column_names: Vec<String>,
    py_rows: Bound<'_, PyList>,
    cursor_indices: Option<&[usize]>,
    last_cursor_by_col: &HashMap<usize, PyObject>,
) -> PyResult<PyObject> {
    let result = PyDict::new_bound(py);
    result.set_item("columns", column_names)?;
    result.set_item("rows", py_rows)?;
    set_page_cursor(py, &result, cursor_indices, last_cursor_by_col)?;
    Ok(result.into())
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
fn fetch_page_impl(py: Python<'_>, request: PageRequest<'_, '_>) -> PyResult<PyObject> {
    validate_page_request(request.offset, request.limit).map_err(value_error)?;
    let final_sql = page_sql(request.sql, request.use_keyset);
    let conn = open_conn(request.db_path)?;
    let mut stmt = conn.prepare(&final_sql).map_err(runtime_error)?;
    let column_names = statement_column_names(&stmt);
    let bound = page_bindings(
        request.params,
        request.limit,
        request.offset,
        request.use_keyset,
    )?;
    let refs = sql_refs(&bound);
    let mut rows = stmt.query(refs.as_slice()).map_err(runtime_error)?;
    let (py_rows, last_cursor_by_col) =
        collect_page_rows(py, &mut rows, column_names.len(), request.cursor_indices)?;
    build_page_result(
        py,
        column_names,
        py_rows,
        request.cursor_indices,
        &last_cursor_by_col,
    )
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
fn count_rows_impl(
    db_path: &str,
    sql_count: &str,
    params: Option<&Bound<'_, PyAny>>,
) -> PyResult<i64> {
    let conn = open_conn(db_path)?;
    let bound = extract_params(params)?;
    query_count(&conn, sql_count, &bound).map_err(runtime_error)
}

#[allow(clippy::useless_conversion)]
mod python_api {
    use super::{count_rows_impl, fetch_page_impl, PageRequest};
    use pyo3::prelude::*;

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
    #[allow(clippy::too_many_arguments)]
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
        fetch_page_impl(
            py,
            PageRequest {
                db_path,
                sql,
                params,
                offset,
                limit,
                use_keyset,
                cursor_indices: extract_cursor_indices.as_deref(),
            },
        )
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
        count_rows_impl(db_path, sql_count, params)
    }

    pub(super) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(fetch_page, m)?)?;
        m.add_function(wrap_pyfunction!(count_rows, m)?)?;
        Ok(())
    }
}

/// 模块定义
#[pymodule]
fn prismqml_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    python_api::register(m)?;
    shard::register(m)?;
    m.add("__version__", "0.3.1")?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{page_sql, query_count, validate_page_request, Connection, Value};

    #[test]
    fn pagination_sql_and_bounds_are_explicit() {
        assert_eq!(
            page_sql("SELECT id FROM items", true),
            "SELECT id FROM items LIMIT ?"
        );
        assert_eq!(
            page_sql("SELECT id FROM items", false),
            "SELECT id FROM items LIMIT ? OFFSET ?"
        );
        assert!(validate_page_request(0, 1).is_ok());
        assert_eq!(
            validate_page_request(0, 0),
            Err("limit must be greater than zero")
        );
        assert_eq!(
            validate_page_request(-1, 1),
            Err("offset must not be negative")
        );
    }

    #[test]
    fn count_query_handles_filters_and_missing_scalar_rows() {
        let conn = Connection::open_in_memory().expect("open test database");
        conn.execute_batch(
            "CREATE TABLE items(kind TEXT); INSERT INTO items VALUES ('a'), ('a'), ('b');",
        )
        .expect("seed items");
        let count = query_count(
            &conn,
            "SELECT COUNT(*) FROM items WHERE kind = ?",
            &[Value::Text("a".to_string())],
        )
        .expect("count filtered rows");
        assert_eq!(count, 2);

        conn.execute_batch("CREATE TABLE cached_counts(id INTEGER, total INTEGER);")
            .expect("create count cache");
        let missing = query_count(
            &conn,
            "SELECT total FROM cached_counts WHERE id = ?",
            &[Value::Integer(7)],
        )
        .expect("missing scalar row maps to zero");
        assert_eq!(missing, 0);
    }
}
