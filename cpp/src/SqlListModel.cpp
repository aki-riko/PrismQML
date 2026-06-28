// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SqlListModel 实现 (基于 QtSql, 镜像 sql_list_model.py 核心)
#include "prism/SqlListModel.h"

#include <QSqlDatabase>
#include <QSqlQuery>
#include <QSqlRecord>
#include <QSqlError>
#include <QUuid>
#include <QDebug>

namespace prism {

SqlListModel::SqlListModel(QObject *parent) : QAbstractListModel(parent) {}

bool SqlListModel::openDatabase(const QString &dbPath) {
    m_connName = QStringLiteral("prism_sql_%1").arg(QUuid::createUuid().toString(QUuid::Id128));
    QSqlDatabase db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), m_connName);
    db.setDatabaseName(dbPath);
    if (!db.open()) {
        qWarning() << "prism::SqlListModel 打开数据库失败:" << db.lastError().text();
        return false;
    }
    return true;
}

void SqlListModel::setQuery(const QString &sql, const QString &countSql,
                            const QVariantList &params) {
    beginResetModel();
    m_sql = sql;
    m_countSql = countSql;
    m_params = params;
    m_cache.clear();
    m_lruOrder.clear();
    m_rowCount = computeCount();
    resolveColumns();
    endResetModel();
    emit queryChanged();
    emit countChanged();
}

int SqlListModel::computeCount() {
    if (m_countSql.isEmpty() || m_connName.isEmpty())
        return 0;
    QSqlQuery q(QSqlDatabase::database(m_connName));
    q.prepare(m_countSql);
    for (const QVariant &p : m_params)
        q.addBindValue(p);
    if (!q.exec()) {
        qWarning() << "prism::SqlListModel count 失败:" << q.lastError().text();
        return 0;
    }
    if (q.next())
        return q.value(0).toInt();
    return 0;
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

// PLACEHOLDER_SQL_IMPL2
// 取一页数据 (LIMIT/OFFSET), 每行存为 QVariantMap
QVariantList SqlListModel::fetchPage(int pageIdx) const {
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
