// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SqlListModel 实现 (基于 QtSql, 镜像 sql_list_model.py 核心)
#include "prism/SqlListModel.h"
#include "prism/DataModels.h"

#include <QSqlDatabase>
#include <QSqlQuery>
#include <QSqlRecord>
#include <QSqlError>
#include <QUuid>
#include <QDebug>
#include <algorithm>

namespace prism {

SqlListModel::SqlListModel(QObject *parent) : QAbstractListModel(parent) {}

// 打开单个 SQLite 库, 返回连接名 (空=失败)
static QString openShardConn(const QString &dbPath) {
    const QString conn = QStringLiteral("prism_sql_%1")
                             .arg(QUuid::createUuid().toString(QUuid::Id128));
    QSqlDatabase db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), conn);
    db.setDatabaseName(dbPath);
    if (!db.open()) {
        qWarning() << "prism::SqlListModel 打开数据库失败:" << db.lastError().text();
        return QString();
    }
    return conn;
}

bool SqlListModel::openDatabase(const QString &dbPath) {
    const QString conn = openShardConn(dbPath);
    if (conn.isEmpty())
        return false;
    m_connName = conn;
    m_shardConns = QStringList{conn};   // 单库=单 shard
    return true;
}

void SqlListModel::setRouter(DbRouter *router) {
    m_router = router;
}

void SqlListModel::setCursorColumns(const QStringList &columns) {
    m_cursorColumns = columns;
}

void SqlListModel::setQuery(const QString &sql, const QString &countSql,
                            const QVariantList &params) {
    beginResetModel();
    m_sql = sql;
    m_countSql = countSql;
    m_params = params;
    m_cache.clear();
    m_lruOrder.clear();
    m_endCursors.clear();

    // 多 shard 路由: 若设置了 router, 用 route(params) 决定命中的 shard 集合
    if (m_router) {
        const QStringList shards = m_router->route(params);
        m_shardConns.clear();
        for (const QString &path : shards) {
            const QString conn = openShardConn(path);
            if (!conn.isEmpty())
                m_shardConns << conn;
        }
        if (!m_shardConns.isEmpty())
            m_connName = m_shardConns.first();  // 列解析/count 用第一个 shard
    }

    m_rowCount = computeCount();
    resolveColumns();
    if (useKeyset())
        resolveCursorDirections();
    endResetModel();
    emit queryChanged();
    emit countChanged();
}

int SqlListModel::computeCount() {
    if (m_countSql.isEmpty() || m_shardConns.isEmpty())
        return 0;
    // 多 shard: 累加各 shard 的 COUNT (fan-out 归并的总行数)
    int total = 0;
    for (const QString &conn : m_shardConns) {
        QSqlQuery q(QSqlDatabase::database(conn));
        q.prepare(m_countSql);
        for (const QVariant &p : m_params)
            q.addBindValue(p);
        if (!q.exec()) {
            qWarning() << "prism::SqlListModel count 失败:" << q.lastError().text();
            continue;
        }
        if (q.next())
            total += q.value(0).toInt();
    }
    return total;
}

// 解析 SELECT 的列名 (用 LIMIT 0 prepare, 镜像 _resolve_columns)
void SqlListModel::resolveColumns() {
    m_columns.clear();
    m_roleNames.clear();
    m_colToRole.clear();
    if (m_sql.isEmpty() || m_connName.isEmpty())
        return;
    QSqlQuery q(QSqlDatabase::database(m_connName));
    q.prepare(m_sql + QStringLiteral(" LIMIT 0"));
    for (const QVariant &p : m_params)
        q.addBindValue(p);
    if (!q.exec()) {
        qWarning() << "prism::SqlListModel 解析列失败:" << q.lastError().text();
        return;
    }
    const QSqlRecord rec = q.record();
    int role = Qt::UserRole + 1;
    for (int i = 0; i < rec.count(); ++i) {
        const QString col = rec.fieldName(i);
        m_columns << col;
        m_roleNames.insert(role, col.toUtf8());
        m_colToRole.insert(col, role);
        ++role;
    }
}

// 取一页数据 (分派): 多 shard→fan-out 归并; keyset→游标谓词; 否则 LIMIT/OFFSET
QVariantList SqlListModel::fetchPage(int pageIdx) const {
    if (isMultiShard())
        return fetchPageFanOut(pageIdx);
    if (useKeyset())
        return fetchPageKeyset(pageIdx);

    // 单 shard 默认路径: LIMIT/OFFSET (原逻辑, 零回归)
    QVariantList rows;
    if (m_sql.isEmpty() || m_connName.isEmpty())
        return rows;
    QSqlQuery q(QSqlDatabase::database(m_connName));
    q.prepare(m_sql + QStringLiteral(" LIMIT %1 OFFSET %2")
                          .arg(m_pageSize).arg(pageIdx * m_pageSize));
    for (const QVariant &p : m_params)
        q.addBindValue(p);
    if (!q.exec()) {
        qWarning() << "prism::SqlListModel fetchPage 失败:" << q.lastError().text();
        return rows;
    }
    while (q.next()) {
        QVariantMap row;
        for (const QString &col : m_columns)
            row.insert(col, q.value(col));
        rows.append(row);
    }
    return rows;
}

// 解析 SQL 的 ORDER BY 子句 -> (列名, 是否 DESC) 列表。用于 fan-out 全局归并排序
// 与 keyset 谓词方向。仅解析简单形式 "ORDER BY a, b DESC, c ASC" (无表达式/函数)。
struct OrderKey { QString col; bool desc; };
static QList<OrderKey> parseOrderBy(const QString &sql) {
    QList<OrderKey> keys;
    const int idx = sql.lastIndexOf(QStringLiteral("ORDER BY"), -1, Qt::CaseInsensitive);
    if (idx < 0)
        return keys;
    QString clause = sql.mid(idx + 8);  // "ORDER BY" 长 8
    // 截断到 LIMIT/OFFSET (若有)
    const int lim = clause.indexOf(QStringLiteral("LIMIT"), 0, Qt::CaseInsensitive);
    if (lim >= 0)
        clause = clause.left(lim);
    const QStringList parts = clause.split(QLatin1Char(','), Qt::SkipEmptyParts);
    for (const QString &raw : parts) {
        const QString t = raw.trimmed();
        if (t.isEmpty())
            continue;
        const QStringList toks = t.split(QLatin1Char(' '), Qt::SkipEmptyParts);
        OrderKey k;
        k.col = toks.first();
        // 去掉表限定前缀 (t.col -> col)
        const int dot = k.col.lastIndexOf(QLatin1Char('.'));
        if (dot >= 0)
            k.col = k.col.mid(dot + 1);
        k.desc = (toks.size() > 1 &&
                  toks.at(1).compare(QStringLiteral("DESC"), Qt::CaseInsensitive) == 0);
        keys.append(k);
    }
    return keys;
}

// 比较两行按 ORDER BY 键的大小: <0 a 在前, >0 b 在前, 0 相等
static int compareRows(const QVariantMap &a, const QVariantMap &b, const QList<OrderKey> &keys) {
    for (const OrderKey &k : keys) {
        const QVariant va = a.value(k.col);
        const QVariant vb = b.value(k.col);
        int cmp = 0;
        if (va != vb)
            cmp = QVariant::compare(va, vb) == QPartialOrdering::Less ? -1 : 1;
        if (cmp != 0)
            return k.desc ? -cmp : cmp;
    }
    return 0;
}

// 从 ORDER BY 解析游标列的排序方向, 填充 m_cursorDesc (与 m_cursorColumns 对齐)
void SqlListModel::resolveCursorDirections() {
    m_cursorDesc.clear();
    const QList<OrderKey> keys = parseOrderBy(m_sql);
    for (const QString &col : m_cursorColumns) {
        bool desc = false;
        for (const OrderKey &k : keys)
            if (k.col == col) { desc = k.desc; break; }
        m_cursorDesc.append(desc);
    }
}

// 多 shard fan-out: 对每 shard 取前 (pageIdx+1)*pageSize 行, 归并后按 ORDER BY
// 全局排序, 切出第 pageIdx 页 (镜像 Python shard.fan_out_fetch_page 的归并语义)。
QVariantList SqlListModel::fetchPageFanOut(int pageIdx) const {
    QVariantList merged;
    if (m_sql.isEmpty() || m_shardConns.isEmpty())
        return merged;
    const int need = (pageIdx + 1) * m_pageSize;   // 归并需覆盖到目标页末
    for (const QString &conn : m_shardConns) {
        QSqlQuery q(QSqlDatabase::database(conn));
        // 每 shard 只需前 need 行 (全局第 need 名之后的行不可能进本页)
        q.prepare(m_sql + QStringLiteral(" LIMIT %1").arg(need));
        for (const QVariant &p : m_params)
            q.addBindValue(p);
        if (!q.exec()) {
            qWarning() << "prism::SqlListModel fetchPageFanOut 失败:" << q.lastError().text();
            continue;
        }
        while (q.next()) {
            QVariantMap row;
            for (const QString &col : m_columns)
                row.insert(col, q.value(col));
            merged.append(row);
        }
    }

    // 全局排序 (按 SQL 的 ORDER BY 键)
    const QList<OrderKey> keys = parseOrderBy(m_sql);
    if (!keys.isEmpty()) {
        std::stable_sort(merged.begin(), merged.end(),
                         [&keys](const QVariant &a, const QVariant &b) {
                             return compareRows(a.toMap(), b.toMap(), keys) < 0;
                         });
    }

    // 切出第 pageIdx 页
    QVariantList page;
    const int start = pageIdx * m_pageSize;
    for (int i = start; i < merged.size() && i < start + m_pageSize; ++i)
        page.append(merged.at(i));
    return page;
}

// keyset 分页: 用上一页缓存的末行游标做 WHERE (cursorCols) >/< 谓词, 避免大 OFFSET。
// 仅单 shard 生效; 顺序翻页时命中前页 end_cursor, 随机跳页则回退到等价 LIMIT/OFFSET。
QVariantList SqlListModel::fetchPageKeyset(int pageIdx) const {
    QVariantList rows;
    if (m_sql.isEmpty() || m_connName.isEmpty())
        return rows;

    // 第 0 页或无前页游标: 直接 LIMIT (无 OFFSET)
    QString sql = m_sql;
    QVariantList bind = m_params;
    const bool haveCursor = pageIdx > 0 && m_endCursors.contains(pageIdx - 1);
    if (haveCursor) {
        const QVariantList cursor = m_endCursors.value(pageIdx - 1);
        // 构建 (c1,c2,..) 与方向一致的行值比较谓词。SQLite 支持行值比较,
        // 但方向可能混合, 故逐列展开为 OR 链更稳: 见下方按字典序展开。
        QStringList orTerms;
        for (int i = 0; i < m_cursorColumns.size(); ++i) {
            QStringList andTerms;
            for (int j = 0; j < i; ++j)
                andTerms << QStringLiteral("%1 = ?").arg(m_cursorColumns[j]);
            const bool desc = (i < m_cursorDesc.size()) ? m_cursorDesc[i] : false;
            andTerms << QStringLiteral("%1 %2 ?").arg(m_cursorColumns[i],
                                                      desc ? QStringLiteral("<")
                                                           : QStringLiteral(">"));
            orTerms << QStringLiteral("(%1)").arg(andTerms.join(QStringLiteral(" AND ")));
        }
        const QString pred = QStringLiteral("(%1)").arg(orTerms.join(QStringLiteral(" OR ")));
        // 注入到 WHERE: 若已有 WHERE 则 AND, 否则新增 WHERE (插在 ORDER BY 前)
        const int ob = sql.lastIndexOf(QStringLiteral("ORDER BY"), -1, Qt::CaseInsensitive);
        const QString head = ob >= 0 ? sql.left(ob) : sql;
        const QString tail = ob >= 0 ? sql.mid(ob) : QString();
        const bool hasWhere = head.contains(QStringLiteral("WHERE"), Qt::CaseInsensitive);
        sql = head + (hasWhere ? QStringLiteral(" AND ") : QStringLiteral(" WHERE "))
            + pred + QLatin1Char(' ') + tail;
        // 绑定: 原 params + 每个 OR term 的游标值 (前缀相等列 + 本列)
        for (int i = 0; i < m_cursorColumns.size(); ++i) {
            for (int j = 0; j < i; ++j)
                bind << cursor.value(j);
            bind << cursor.value(i);
        }
    }

    QSqlQuery q(QSqlDatabase::database(m_connName));
    q.prepare(sql + QStringLiteral(" LIMIT %1").arg(m_pageSize));
    for (const QVariant &p : bind)
        q.addBindValue(p);
    if (!q.exec()) {
        qWarning() << "prism::SqlListModel fetchPageKeyset 失败:" << q.lastError().text();
        // 回退到 OFFSET 路径 (随机跳页无前页游标时)
        QSqlQuery q2(QSqlDatabase::database(m_connName));
        q2.prepare(m_sql + QStringLiteral(" LIMIT %1 OFFSET %2")
                               .arg(m_pageSize).arg(pageIdx * m_pageSize));
        for (const QVariant &p : m_params)
            q2.addBindValue(p);
        if (!q2.exec())
            return rows;
        while (q2.next()) {
            QVariantMap row;
            for (const QString &col : m_columns)
                row.insert(col, q2.value(col));
            rows.append(row);
        }
        // 回退路径也缓存末行游标, 供后续顺序翻页命中 keyset
        if (!rows.isEmpty()) {
            const QVariantMap last = rows.last().toMap();
            QVariantList endCursor;
            for (const QString &col : m_cursorColumns)
                endCursor << last.value(col);
            m_endCursors.insert(pageIdx, endCursor);
        }
        return rows;
    }
    while (q.next()) {
        QVariantMap row;
        for (const QString &col : m_columns)
            row.insert(col, q.value(col));
        rows.append(row);
    }
    // 缓存本页末行游标供下一页 keyset (镜像 Python end_cursor)
    if (!rows.isEmpty()) {
        const QVariantMap last = rows.last().toMap();
        QVariantList endCursor;
        for (const QString &col : m_cursorColumns)
            endCursor << last.value(col);
        m_endCursors.insert(pageIdx, endCursor);
    }
    return rows;
}

int SqlListModel::rowCount(const QModelIndex &parent) const {
    if (parent.isValid())
        return 0;
    return m_rowCount;
}

QVariant SqlListModel::data(const QModelIndex &index, int role) const {
    if (!index.isValid() || index.row() < 0 || index.row() >= m_rowCount)
        return QVariant();
    const int row = index.row();
    const int pageIdx = pageOf(row);

    // 缓存命中检查 + LRU 维护
    if (!m_cache.contains(pageIdx)) {
        QVariantList page = fetchPage(pageIdx);
        m_cache.insert(pageIdx, page);
        m_lruOrder.removeAll(pageIdx);
        m_lruOrder.append(pageIdx);
        while (m_lruOrder.size() > kMaxCachedPages) {
            const int evict = m_lruOrder.takeFirst();
            m_cache.remove(evict);
        }
    } else {
        m_lruOrder.removeAll(pageIdx);
        m_lruOrder.append(pageIdx);
    }

    const QVariantList &page = m_cache[pageIdx];
    const int offsetInPage = row - pageIdx * m_pageSize;
    if (offsetInPage < 0 || offsetInPage >= page.size())
        return QVariant();
    const QVariantMap rowMap = page.at(offsetInPage).toMap();
    const QByteArray colName = m_roleNames.value(role);
    if (colName.isEmpty())
        return QVariant();
    return rowMap.value(QString::fromUtf8(colName));
}

QHash<int, QByteArray> SqlListModel::roleNames() const {
    return m_roleNames;
}

QVariantMap SqlListModel::getRow(int index) {
    QVariantMap result;
    if (index < 0 || index >= m_rowCount)
        return result;
    const QModelIndex idx = this->index(index, 0);
    for (auto it = m_roleNames.constBegin(); it != m_roleNames.constEnd(); ++it) {
        result.insert(QString::fromUtf8(it.value()), data(idx, it.key()));
    }
    return result;
}

void SqlListModel::refresh() {
    beginResetModel();
    m_cache.clear();
    m_lruOrder.clear();
    m_rowCount = computeCount();
    endResetModel();
    emit countChanged();
}

}  // namespace prism
