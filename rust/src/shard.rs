// shard.rs - 跨分片 fan-out 查询 + 归并排序
//
// 设计:
// - fan_out_fetch_page(db_paths, sql, params, limit, cursor_indices, sort_directions):
//   每个 shard 独立 fetch_page (LIMIT N),把所有 shard 结果按 cursor 列做归并排序,
//   取 top-N 返回。供 FluentSqlListModel 跨片场景使用。
//
// - 关键不变量:
//   1. 所有 shard 使用同一 SQL 模板 (含同 ORDER BY 子句)
//   2. cursor_columns 在所有 shard 都是 ORDER BY 前缀
//   3. sort_directions 与 cursor_columns 同长度,每列 'DESC'/'ASC' (统一所有 shard)
//
// - 性能:
//   N shard 各拉 limit 行 → 归并 N*limit 行取 top-limit。N=10, limit=1000 时
//   归并 10000 行 ~1ms (Rust),fetch 并发 ~5ms (rusqlite 多连接), total <10ms。

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rusqlite::{
    types::{Value, ValueRef},
    Connection, OpenFlags,
};
use std::cmp::Ordering;

use crate::{
    extract_params, page_sql, runtime_error, sql_refs, statement_column_names, value_error,
    value_ref_to_py,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Direction {
    Asc,
    Desc,
}

#[derive(Debug, Clone, PartialEq)]
enum SortValue {
    Null,
    Integer(i64),
    Real(f64),
    Text(Vec<u8>),
    Blob(Vec<u8>),
}

/// 一个 shard 取出的一行,带源 shard 索引(用于堆稳定性 / 调试)
struct CandidateRow<T> {
    cells: T,
    cursor_values: Vec<SortValue>,
    _shard_idx: usize,
}

struct ShardRows {
    column_names: Vec<String>,
    candidates: Vec<CandidateRow<Vec<PyObject>>>,
}

struct FanOutInput<'a, 'py> {
    db_paths: Vec<String>,
    sql: &'a str,
    params: Option<&'a Bound<'py, PyAny>>,
    limit: i64,
    cursor_indices: Option<Vec<usize>>,
    sort_directions: Option<Vec<String>>,
}

fn open_conn(db_path: &str) -> PyResult<Connection> {
    Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

fn sort_value(value: ValueRef<'_>) -> SortValue {
    match value {
        ValueRef::Null => SortValue::Null,
        ValueRef::Integer(value) => SortValue::Integer(value),
        ValueRef::Real(value) if value.is_nan() => SortValue::Null,
        ValueRef::Real(value) => SortValue::Real(value),
        ValueRef::Text(value) => SortValue::Text(value.to_vec()),
        ValueRef::Blob(value) => SortValue::Blob(value.to_vec()),
    }
}

fn sort_rank(value: &SortValue) -> u8 {
    match value {
        SortValue::Null => 0,
        SortValue::Integer(_) | SortValue::Real(_) => 1,
        SortValue::Text(_) => 2,
        SortValue::Blob(_) => 3,
    }
}

fn compare_integer_real(integer: i64, real: f64) -> Ordering {
    const I64_MIN_AS_F64: f64 = -9_223_372_036_854_775_808.0;
    const I64_MAX_PLUS_ONE_AS_F64: f64 = 9_223_372_036_854_775_808.0;
    if real.is_nan() {
        return Ordering::Greater;
    }
    if real < I64_MIN_AS_F64 {
        return Ordering::Greater;
    }
    if real >= I64_MAX_PLUS_ONE_AS_F64 {
        return Ordering::Less;
    }
    let truncated = real as i64;
    match integer.cmp(&truncated) {
        Ordering::Equal if (integer as f64) < real => Ordering::Less,
        Ordering::Equal if (integer as f64) > real => Ordering::Greater,
        ordering => ordering,
    }
}

fn compare_sort_values(a: &SortValue, b: &SortValue) -> Ordering {
    match (a, b) {
        (SortValue::Null, SortValue::Null) => Ordering::Equal,
        (SortValue::Integer(a), SortValue::Integer(b)) => a.cmp(b),
        (SortValue::Real(a), SortValue::Real(b)) if a < b => Ordering::Less,
        (SortValue::Real(a), SortValue::Real(b)) if a > b => Ordering::Greater,
        (SortValue::Real(_), SortValue::Real(_)) => Ordering::Equal,
        (SortValue::Integer(a), SortValue::Real(b)) => compare_integer_real(*a, *b),
        (SortValue::Real(a), SortValue::Integer(b)) => compare_integer_real(*b, *a).reverse(),
        (SortValue::Text(a), SortValue::Text(b)) => a.cmp(b),
        (SortValue::Blob(a), SortValue::Blob(b)) => a.cmp(b),
        _ => sort_rank(a).cmp(&sort_rank(b)),
    }
}

fn compare_cursor_values(a: &[SortValue], b: &[SortValue], dirs: &[Direction]) -> Ordering {
    for ((a_value, b_value), direction) in a.iter().zip(b).zip(dirs) {
        let cmp = compare_sort_values(a_value, b_value);
        if cmp != Ordering::Equal {
            return match direction {
                Direction::Desc => cmp.reverse(),
                Direction::Asc => cmp,
            };
        }
    }
    Ordering::Equal
}

fn parse_directions(
    values: Option<&[String]>,
    cursor_count: usize,
) -> Result<Vec<Direction>, String> {
    let Some(values) = values else {
        return Ok(vec![Direction::Desc; cursor_count]);
    };
    if values.len() != cursor_count {
        return Err(format!(
            "sort_directions length {} does not match cursor_indices length {cursor_count}",
            values.len()
        ));
    }
    values
        .iter()
        .map(|value| match value.to_ascii_uppercase().as_str() {
            "ASC" => Ok(Direction::Asc),
            "DESC" => Ok(Direction::Desc),
            _ => Err(format!("unsupported sort direction: {value}")),
        })
        .collect()
}

fn merge_candidates<T>(
    mut candidates: Vec<CandidateRow<T>>,
    directions: &[Direction],
    limit: usize,
) -> Vec<CandidateRow<T>> {
    if !directions.is_empty() {
        candidates
            .sort_by(|a, b| compare_cursor_values(&a.cursor_values, &b.cursor_values, directions));
    }
    candidates.truncate(limit);
    candidates
}

fn validate_fan_out_request(db_paths: &[String], limit: i64) -> PyResult<()> {
    if db_paths.is_empty() {
        return Err(value_error("db_paths 不能为空"));
    }
    if limit <= 0 {
        return Err(value_error("limit must be greater than zero"));
    }
    Ok(())
}

fn validate_cursor_indices(cursor_indices: &[usize], column_count: usize) -> PyResult<()> {
    if let Some(index) = cursor_indices.iter().find(|&&index| index >= column_count) {
        return Err(value_error(format!(
            "cursor index {index} is outside the {column_count} selected columns"
        )));
    }
    Ok(())
}

fn collect_cursor_values(
    row: &rusqlite::Row<'_>,
    cursor_indices: &[usize],
) -> PyResult<Vec<SortValue>> {
    cursor_indices
        .iter()
        .map(|&index| row.get_ref(index).map(sort_value).map_err(runtime_error))
        .collect()
}

fn collect_cells(
    py: Python<'_>,
    row: &rusqlite::Row<'_>,
    column_count: usize,
) -> PyResult<Vec<PyObject>> {
    (0..column_count)
        .map(|index| value_ref_to_py(py, row.get_ref(index).map_err(runtime_error)?))
        .collect()
}

fn collect_candidate_rows(
    py: Python<'_>,
    rows: &mut rusqlite::Rows<'_>,
    column_count: usize,
    cursor_indices: &[usize],
    shard_idx: usize,
) -> PyResult<Vec<CandidateRow<Vec<PyObject>>>> {
    let mut candidates = Vec::new();
    while let Some(row) = rows.next().map_err(runtime_error)? {
        candidates.push(CandidateRow {
            cells: collect_cells(py, row, column_count)?,
            cursor_values: collect_cursor_values(row, cursor_indices)?,
            _shard_idx: shard_idx,
        });
    }
    Ok(candidates)
}

fn read_shard(
    py: Python<'_>,
    db_path: &str,
    sql: &str,
    bound: &[Value],
    cursor_indices: &[usize],
    shard_idx: usize,
) -> PyResult<ShardRows> {
    let conn = open_conn(db_path)?;
    let mut stmt = conn.prepare(sql).map_err(runtime_error)?;
    let column_names = statement_column_names(&stmt);
    validate_cursor_indices(cursor_indices, column_names.len())?;
    let refs = sql_refs(bound);
    let mut rows = stmt.query(refs.as_slice()).map_err(runtime_error)?;
    let candidates =
        collect_candidate_rows(py, &mut rows, column_names.len(), cursor_indices, shard_idx)?;
    Ok(ShardRows {
        column_names,
        candidates,
    })
}

fn validate_shard_schema(expected: &[String], actual: &[String], shard_idx: usize) -> PyResult<()> {
    if expected != actual {
        return Err(runtime_error(format!(
            "shard schema mismatch at index {shard_idx}: expected {expected:?}, got {actual:?}"
        )));
    }
    Ok(())
}

fn collect_shard_candidates(
    py: Python<'_>,
    db_paths: &[String],
    sql: &str,
    bound: &[Value],
    cursor_indices: &[usize],
) -> PyResult<ShardRows> {
    let paged_sql = page_sql(sql, true);
    let mut expected_columns: Option<Vec<String>> = None;
    let mut all_candidates = Vec::new();
    for (shard_idx, db_path) in db_paths.iter().enumerate() {
        let mut shard_rows = read_shard(py, db_path, &paged_sql, bound, cursor_indices, shard_idx)?;
        match expected_columns.as_ref() {
            Some(expected) => validate_shard_schema(expected, &shard_rows.column_names, shard_idx)?,
            None => expected_columns = Some(std::mem::take(&mut shard_rows.column_names)),
        }
        all_candidates.append(&mut shard_rows.candidates);
    }
    Ok(ShardRows {
        column_names: expected_columns.unwrap_or_default(),
        candidates: all_candidates,
    })
}

fn append_candidate_rows<'py>(
    py: Python<'py>,
    py_rows: &Bound<'py, PyList>,
    candidates: &[CandidateRow<Vec<PyObject>>],
    cursor_indices: &[usize],
) -> PyResult<Option<Vec<PyObject>>> {
    let mut last_cursor = None;
    for candidate in candidates {
        let py_row = PyList::empty_bound(py);
        for cell in &candidate.cells {
            py_row.append(cell.clone_ref(py))?;
        }
        py_rows.append(py_row)?;
        last_cursor = Some(
            cursor_indices
                .iter()
                .map(|&index| candidate.cells[index].clone_ref(py))
                .collect(),
        );
    }
    Ok(last_cursor)
}

fn set_last_cursor(
    py: Python<'_>,
    result: &Bound<'_, PyDict>,
    last_cursor: Option<Vec<PyObject>>,
) -> PyResult<()> {
    let Some(values) = last_cursor else {
        return result.set_item("last_cursor", py.None());
    };
    let cursor_list = PyList::empty_bound(py);
    for value in values {
        cursor_list.append(value)?;
    }
    result.set_item("last_cursor", cursor_list)
}

fn build_shard_result(
    py: Python<'_>,
    column_names: Vec<String>,
    candidates: &[CandidateRow<Vec<PyObject>>],
    cursor_indices: &[usize],
) -> PyResult<PyObject> {
    let py_rows = PyList::empty_bound(py);
    let last_cursor = append_candidate_rows(py, &py_rows, candidates, cursor_indices)?;
    let result = PyDict::new_bound(py);
    result.set_item("columns", column_names)?;
    result.set_item("rows", py_rows)?;
    set_last_cursor(py, &result, last_cursor)?;
    Ok(result.into())
}

/// 跨分片 fan-out 查询
///
/// Args:
///     db_paths: shard 文件路径列表
///     sql: 主查询 (会被每个 shard 各执行一次,不含 LIMIT/OFFSET)
///     params: SQL 占位符参数
///     limit: 跨片归并后取的总行数
///     cursor_indices: cursor 列在 SELECT 中的下标 (供 last_cursor 提取 + 归并排序)
///     sort_directions: 与 cursor_indices 等长,每列 "DESC"/"ASC"
///
/// Returns:
///     dict {"columns", "rows", "last_cursor"} - 与 fetch_page 同结构
fn fan_out_fetch_page_impl(py: Python<'_>, input: FanOutInput<'_, '_>) -> PyResult<PyObject> {
    validate_fan_out_request(&input.db_paths, input.limit)?;
    let cursor_indices = input.cursor_indices.unwrap_or_default();
    let directions = parse_directions(input.sort_directions.as_deref(), cursor_indices.len())
        .map_err(value_error)?;
    let mut bound = extract_params(input.params)?;
    bound.push(Value::Integer(input.limit));
    let shard_rows =
        collect_shard_candidates(py, &input.db_paths, input.sql, &bound, &cursor_indices)?;
    let candidates = merge_candidates(shard_rows.candidates, &directions, input.limit as usize);
    build_shard_result(py, shard_rows.column_names, &candidates, &cursor_indices)
}

#[allow(clippy::useless_conversion)]
mod python_api {
    use super::{fan_out_fetch_page_impl, FanOutInput};
    use pyo3::prelude::*;

    /// 跨分片 fan-out 查询
    ///
    /// Args:
    ///     db_paths: shard 文件路径列表
    ///     sql: 主查询 (会被每个 shard 各执行一次,不含 LIMIT/OFFSET)
    ///     params: SQL 占位符参数
    ///     limit: 跨片归并后取的总行数
    ///     cursor_indices: cursor 列在 SELECT 中的下标 (供 last_cursor 提取 + 归并排序)
    ///     sort_directions: 与 cursor_indices 等长,每列 "DESC"/"ASC"
    ///
    /// Returns:
    ///     dict {"columns", "rows", "last_cursor"} - 与 fetch_page 同结构
    #[pyfunction]
    #[pyo3(signature = (db_paths, sql, params=None, limit=1000, cursor_indices=None, sort_directions=None))]
    fn fan_out_fetch_page(
        py: Python,
        db_paths: Vec<String>,
        sql: &str,
        params: Option<&Bound<'_, PyAny>>,
        limit: i64,
        cursor_indices: Option<Vec<usize>>,
        sort_directions: Option<Vec<String>>,
    ) -> PyResult<PyObject> {
        fan_out_fetch_page_impl(
            py,
            FanOutInput {
                db_paths,
                sql,
                params,
                limit,
                cursor_indices,
                sort_directions,
            },
        )
    }

    pub(super) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(fan_out_fetch_page, m)?)?;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    python_api::register(m)
}

#[cfg(test)]
mod tests {
    use super::{
        compare_sort_values, merge_candidates, parse_directions, sort_value, CandidateRow,
        Connection, Direction, SortValue,
    };
    use std::cmp::Ordering;

    fn candidate(id: &'static str, cursor_values: Vec<SortValue>) -> CandidateRow<&'static str> {
        CandidateRow {
            cells: id,
            cursor_values,
            _shard_idx: 0,
        }
    }

    fn query_ids(conn: &Connection, sql: &str) -> Vec<String> {
        let mut stmt = conn.prepare(sql).expect("prepare id query");
        stmt.query_map([], |row| row.get(0))
            .expect("query ids")
            .collect::<rusqlite::Result<Vec<_>>>()
            .expect("collect ids")
    }

    fn seed_edge_ordering_values(conn: &Connection) {
        conn.execute_batch(
            "CREATE TABLE sortable(id TEXT, value);\
             INSERT INTO sortable VALUES ('null', NULL);\
             INSERT INTO sortable VALUES ('text-80', CAST(X'80' AS TEXT));\
             INSERT INTO sortable VALUES ('text-81', CAST(X'81' AS TEXT));\
             INSERT INTO sortable VALUES ('blob', X'00');",
        )
        .expect("seed storage classes");
        conn.execute(
            "INSERT INTO sortable VALUES (?1, ?2)",
            rusqlite::params!["real-rounded", 9_007_199_254_740_992.0_f64],
        )
        .expect("insert rounded real");
        conn.execute(
            "INSERT INTO sortable VALUES (?1, ?2)",
            rusqlite::params!["integer-exact", 9_007_199_254_740_993_i64],
        )
        .expect("insert exact integer");
    }

    fn edge_ordering_candidates(conn: &Connection) -> Vec<CandidateRow<String>> {
        let mut stmt = conn
            .prepare("SELECT id, value FROM sortable ORDER BY rowid DESC")
            .expect("prepare candidate query");
        stmt.query_map([], |row| {
            Ok(CandidateRow {
                cells: row.get(0)?,
                cursor_values: vec![sort_value(row.get_ref(1)?)],
                _shard_idx: 0,
            })
        })
        .expect("query candidates")
        .collect::<rusqlite::Result<Vec<_>>>()
        .expect("collect candidates")
    }

    #[test]
    fn directions_are_strict_and_default_to_descending() {
        assert_eq!(parse_directions(None, 2).unwrap(), vec![Direction::Desc; 2]);
        assert_eq!(
            parse_directions(Some(&["asc".to_string(), "DESC".to_string()]), 2).unwrap(),
            vec![Direction::Asc, Direction::Desc]
        );
        assert!(parse_directions(Some(&["SIDEWAYS".to_string()]), 1).is_err());
        assert!(parse_directions(Some(&["ASC".to_string()]), 2).is_err());
    }

    #[test]
    fn shard_merge_orders_multiple_columns_and_truncates() {
        let candidates = vec![
            candidate(
                "ten-b",
                vec![SortValue::Integer(10), SortValue::Text(b"b".to_vec())],
            ),
            candidate(
                "nine",
                vec![SortValue::Integer(9), SortValue::Text(b"z".to_vec())],
            ),
            candidate(
                "ten-a",
                vec![SortValue::Integer(10), SortValue::Text(b"a".to_vec())],
            ),
        ];
        let merged = merge_candidates(candidates, &[Direction::Desc, Direction::Asc], 2);
        assert_eq!(
            merged.iter().map(|row| row.cells).collect::<Vec<_>>(),
            ["ten-a", "ten-b"]
        );
    }

    #[test]
    fn shard_merge_matches_sqlite_storage_class_and_null_order() {
        let candidates = vec![
            candidate("text", vec![SortValue::Text(b"a".to_vec())]),
            candidate("number", vec![SortValue::Integer(1)]),
            candidate("null", vec![SortValue::Null]),
        ];
        let ascending = merge_candidates(candidates, &[Direction::Asc], 3);
        assert_eq!(
            ascending.iter().map(|row| row.cells).collect::<Vec<_>>(),
            ["null", "number", "text"]
        );
    }

    #[test]
    fn shard_merge_matches_bundled_sqlite_edge_ordering() {
        let conn = Connection::open_in_memory().expect("open test database");
        seed_edge_ordering_values(&conn);
        let actual = merge_candidates(
            edge_ordering_candidates(&conn),
            &[Direction::Asc],
            usize::MAX,
        )
        .into_iter()
        .map(|row| row.cells)
        .collect::<Vec<_>>();
        let expected = query_ids(&conn, "SELECT id FROM sortable ORDER BY value ASC");

        assert_eq!(actual, expected);
        assert_eq!(
            compare_sort_values(&SortValue::Real(-0.0), &SortValue::Real(0.0)),
            Ordering::Equal
        );
    }
}
