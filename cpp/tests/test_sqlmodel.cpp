// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SqlListModel 多 shard fan-out + keyset 游标 验证测试。
// 真实建多个 SQLite 库, 断言: ①多 shard 归并全局排序正确 ②keyset 翻页结果==OFFSET 翻页
// ③单库路径回归不变。
#include "prism/SqlListModel.h"
#include "prism/DataModels.h"

#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QSqlDatabase>
#include <QSqlQuery>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

using namespace prism;

// 建一个 SQLite 库并插入指定 (id,val) 行
static void seedDb(const QString &path, const QList<QPair<int, int>> &rows) {
    QFile::remove(path);
    const QString conn = QStringLiteral("seed_%1").arg(path);
    {
        QSqlDatabase db = QSqlDatabase::addDatabase(QStringLiteral("QSQLITE"), conn);
        db.setDatabaseName(path);
        db.open();
        QSqlQuery q(db);
        q.exec(QStringLiteral("CREATE TABLE items (id INTEGER PRIMARY KEY, val INTEGER)"));
        for (const auto &r : rows)
            q.exec(QStringLiteral("INSERT INTO items (id,val) VALUES (%1,%2)")
                       .arg(r.first).arg(r.second));
        db.close();
    }
    QSqlDatabase::removeDatabase(conn);
}

// 一个把两个 shard 都返回的 router
class TwoShardRouter : public DbRouter {
public:
    TwoShardRouter(const QString &a, const QString &b) : m_a(a), m_b(b) {}
    QStringList route(const QVariantList &) const override { return {m_a, m_b}; }
private:
    QString m_a, m_b;
};

int main(int argc, char *argv[]) {
    QCoreApplication app(argc, argv);
    const QString dir = QDir::tempPath();
    const QString dbA = dir + QStringLiteral("/prism_shard_a.db");
    const QString dbB = dir + QStringLiteral("/prism_shard_b.db");
    const QString dbSingle = dir + QStringLiteral("/prism_single.db");

    // shard A: id 1,3,5,7,9 (val=id*10); shard B: id 2,4,6,8,10
    QList<QPair<int, int>> rowsA, rowsB, rowsAll;
    for (int i = 1; i <= 10; ++i) {
        if (i % 2) rowsA << qMakePair(i, i * 10);
        else       rowsB << qMakePair(i, i * 10);
        rowsAll << qMakePair(i, i * 10);
    }
    seedDb(dbA, rowsA);
    seedDb(dbB, rowsB);
    seedDb(dbSingle, rowsAll);

    const QByteArray idRole = "id";

    qInfo() << "=== 多 shard fan-out 归并测试 ===";
    {
        TwoShardRouter router(dbA, dbB);
        SqlListModel model;
        model.setRouter(&router);
        model.setQuery(QStringLiteral("SELECT id, val FROM items ORDER BY id"),
                       QStringLiteral("SELECT COUNT(*) FROM items"));
        // count = 两 shard 累加 = 10
        CHECK(model.count() == 10, "多 shard count 累加=10");
        // 全局排序: 归并后按 id 升序应为 1..10 (跨 shard 交错)
        bool ordered = true;
        for (int i = 0; i < 10; ++i) {
            const QVariantMap r = model.getRow(i);
            if (r.value("id").toInt() != i + 1) { ordered = false; break; }
        }
        CHECK(ordered, "多 shard 全局排序 id=1..10 (跨 shard 交错归并正确)");
        CHECK(model.getRow(0).value("id").toInt() == 1, "首行 id=1(来自 shard A)");
        CHECK(model.getRow(1).value("id").toInt() == 2, "次行 id=2(来自 shard B)");
    }

    // PLACEHOLDER_MORE_TESTS
    qInfo() << "=== keyset 游标翻页测试 (结果须与 OFFSET 路径一致) ===";
    {
        // 基准: 单库 OFFSET 路径, pageSize=3, 读全部 10 行 id 序列
        SqlListModel baseline;
        baseline.setPageSize(3);
        baseline.openDatabase(dbSingle);
        baseline.setQuery(QStringLiteral("SELECT id, val FROM items ORDER BY id"),
                          QStringLiteral("SELECT COUNT(*) FROM items"));
        QList<int> baseIds;
        for (int i = 0; i < baseline.count(); ++i)
            baseIds << baseline.getRow(i).value("id").toInt();

        // keyset: 同库同查询 + cursor_columns=[id], pageSize=3
        SqlListModel ks;
        ks.setPageSize(3);
        ks.openDatabase(dbSingle);
        ks.setCursorColumns(QStringList{QStringLiteral("id")});
        ks.setQuery(QStringLiteral("SELECT id, val FROM items ORDER BY id"),
                    QStringLiteral("SELECT COUNT(*) FROM items"));
        QList<int> ksIds;
        for (int i = 0; i < ks.count(); ++i)
            ksIds << ks.getRow(i).value("id").toInt();

        CHECK(baseIds.size() == 10 && ksIds.size() == 10, "keyset/基准 均 10 行");
        CHECK(ksIds == baseIds, "keyset 翻页 id 序列 == OFFSET 路径 (逐行一致)");
        QList<int> expect = {1,2,3,4,5,6,7,8,9,10};
        CHECK(ksIds == expect, "keyset 结果 = 1..10 有序无重无漏");
    }

    qInfo() << "=== keyset 降序 (DESC) 翻页测试 ===";
    {
        SqlListModel ks;
        ks.setPageSize(4);
        ks.openDatabase(dbSingle);
        ks.setCursorColumns(QStringList{QStringLiteral("id")});
        ks.setQuery(QStringLiteral("SELECT id, val FROM items ORDER BY id DESC"),
                    QStringLiteral("SELECT COUNT(*) FROM items"));
        QList<int> ids;
        for (int i = 0; i < ks.count(); ++i)
            ids << ks.getRow(i).value("id").toInt();
        QList<int> expect = {10,9,8,7,6,5,4,3,2,1};
        CHECK(ids == expect, "keyset DESC 结果 = 10..1 (方向谓词正确)");
    }

    qInfo() << "=== 单库路径回归测试 (无 router/无 cursor) ===";
    {
        SqlListModel model;
        model.openDatabase(dbSingle);
        model.setQuery(QStringLiteral("SELECT id, val FROM items ORDER BY id"),
                       QStringLiteral("SELECT COUNT(*) FROM items"));
        CHECK(model.count() == 10, "单库 count=10");
        CHECK(model.getRow(0).value("id").toInt() == 1, "单库首行 id=1");
        CHECK(model.getRow(9).value("val").toInt() == 100, "单库末行 val=100");
    }


    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
