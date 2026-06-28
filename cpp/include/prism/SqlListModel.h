// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SqlListModel (镜像 Python models/sql_list_model.py)
//
// 说明: Python 版用 Rust crate prismqml_rs(PyO3, 仅 Python ABI)加速分页 + keyset
// 游标 + 多 shard fan-out。C++ 无法直接复用该 Python 扩展, 故改用 Qt 原生 QtSql
// (QSqlQuery + SQLite) 实现等价功能: setQuery/count/getRow/data/roleNames + 分页缓存。
// keyset 游标 / 多 shard 为高级优化, 当前用 LIMIT/OFFSET 路径(<100M 行场景正常)。
#pragma once

#include <QAbstractListModel>
#include <QString>
#include <QStringList>
#include <QVariant>
#include <QVariantList>
#include <QVariantMap>
#include <QHash>
#include <QByteArray>

namespace prism {

class SqlListModel : public QAbstractListModel {
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)
public:
    explicit SqlListModel(QObject *parent = nullptr);

    // 打开数据库 (SQLite 文件路径)
    Q_INVOKABLE bool openDatabase(const QString &dbPath);

    // 设置查询 (镜像 setQuery 核心): sql 不含 LIMIT/OFFSET, countSql 为 COUNT(*)
    Q_INVOKABLE void setQuery(const QString &sql, const QString &countSql,
                              const QVariantList &params = QVariantList());

    Q_INVOKABLE int count() const { return m_rowCount; }
    Q_INVOKABLE void refresh();
    Q_INVOKABLE QVariantMap getRow(int index);

    // QAbstractListModel 接口
    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QHash<int, QByteArray> roleNames() const override;

signals:
    void queryChanged();
    void countChanged();

private:
    int computeCount();
    void resolveColumns();
    QVariantList fetchPage(int pageIdx) const;
    int pageOf(int row) const { return row / m_pageSize; }

    QString m_connName;          // QSqlDatabase 连接名
    QString m_sql;
    QString m_countSql;
    QVariantList m_params;
    int m_rowCount = 0;
    int m_pageSize = 100;
    QStringList m_columns;
    QHash<int, QByteArray> m_roleNames;   // role -> 列名
    QHash<QString, int> m_colToRole;
    mutable QHash<int, QVariantList> m_cache;  // pageIdx -> rows(每行 QVariantMap)
    mutable QList<int> m_lruOrder;
    static constexpr int kMaxCachedPages = 16;
};

}  // namespace prism
