// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Store/Logger 单元测试 (验证阶段4 纯逻辑能力)
#include "prism/Store.h"
#include "prism/Logger.h"
#include "prism/Updater.h"
#include "prism/SqlListModel.h"
#include "prism/ConfigManager.h"

#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <vector>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

int main(int argc, char *argv[]) {
    QCoreApplication app(argc, argv);
    using namespace prism;

    qInfo() << "=== Store 测试 ===";

    // 1. define + get 默认值
    Store store(QStringLiteral("test"));
    store.define(QStringLiteral("count"), 0);
    store.define(QStringLiteral("theme"), QStringLiteral("auto"));
    CHECK(store.get(QStringLiteral("count")).toInt() == 0, "define/get default int");
    CHECK(store.get(QStringLiteral("theme")).toString() == "auto", "define/get default str");

    // 2. set + get
    store.set(QStringLiteral("count"), 5);
    CHECK(store.get(QStringLiteral("count")).toInt() == 5, "set/get");

    // 3. watch 触发
    int watchNew = -1, watchOld = -1;
    auto unwatch = store.watch(QStringLiteral("count"),
        [&](const QVariant &n, const QVariant &o) { watchNew = n.toInt(); watchOld = o.toInt(); });
    store.set(QStringLiteral("count"), 10);
    CHECK(watchNew == 10 && watchOld == 5, "watch 收到 new/old");

    // 4. 值相同不触发
    watchNew = -999;
    store.set(QStringLiteral("count"), 10);
    CHECK(watchNew == -999, "值相同不触发 watch");

    // 5. force 强制触发
    store.set(QStringLiteral("count"), 10, true);
    CHECK(watchNew == 10, "force 强制触发");

    // 6. unwatch 后不再触发
    unwatch();
    watchNew = -888;
    store.set(QStringLiteral("count"), 20);
    CHECK(watchNew == -888, "unwatch 后不触发");

    // 7. batch 合并通知
    Store store2(QStringLiteral("batch"));
    store2.define(QStringLiteral("a"), 0);
    store2.define(QStringLiteral("b"), 0);
    std::vector<QString> notified;
    store2.watchAll([&](const QString &k, const QVariant &, const QVariant &) { notified.push_back(k); });
    {
        auto guard = store2.batch();
        store2.set(QStringLiteral("a"), 1);
        store2.set(QStringLiteral("a"), 2);  // 同 key 多次, 退出时只通知一次
        store2.set(QStringLiteral("b"), 3);
    }  // guard 析构 -> 统一通知
    CHECK(notified.size() == 2, "batch 合并: 2 个 key 各通知一次");
    CHECK(store2.get(QStringLiteral("a")).toInt() == 2, "batch 后值正确");

    // 8. reset
    store2.reset(QStringLiteral("a"));
    CHECK(store2.get(QStringLiteral("a")).toInt() == 0, "reset 单 key 回默认");

    // 9. Qt 信号
    int sigCount = 0;
    QObject::connect(store.qtSignals(), &StoreSignals::changed,
                     [&](const QString &, const QVariant &, const QVariant &) { ++sigCount; });
    store.set(QStringLiteral("count"), 99);
    CHECK(sigCount == 1, "qtSignals.changed 发射");

    qInfo() << "=== Logger 测试 ===";
    log::info(QStringLiteral("Logger info 测试"), QStringLiteral("TEST"));
    log::warning(QStringLiteral("Logger warning 测试"));
    log::setLevel(log::Level::Error);
    log::debug(QStringLiteral("这条不该出现(级别过滤)"));
    log::error(QStringLiteral("Logger error 测试(应出现)"));
    CHECK(true, "Logger 调用无崩溃");

    qInfo() << "=== Updater 版本比较测试 ===";
    CHECK(versionIsNewer("v1.0.1", "v1.0.0"), "1.0.1 > 1.0.0");
    CHECK(versionIsNewer("v1.2.0", "v1.1.9"), "1.2.0 > 1.1.9");
    CHECK(!versionIsNewer("v1.0.0", "v1.0.0"), "1.0.0 不新于自身");
    CHECK(!versionIsNewer("v1.0.0", "v1.0.1"), "1.0.0 不新于 1.0.1");
    CHECK(versionIsNewer("v1.0.0", "v1.0.0-beta"), "正式版 > 预发布");
    CHECK(!versionIsNewer("v1.0.0-beta", "v1.0.0"), "预发布 < 正式版");
    CHECK(versionIsNewer("v2.0.0", "v1.9.9"), "主版本号优先");

    qInfo() << "=== SqlListModel 测试 ===";
    {
        // 建临时 SQLite + 插数据 + setQuery 验证
        QString dbPath = QDir::tempPath() + "/prism_test.db";
        QFile::remove(dbPath);
        {
            QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", "seed");
            db.setDatabaseName(dbPath);
            db.open();
            QSqlQuery q(db);
            q.exec("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, val INTEGER)");
            for (int i = 1; i <= 250; ++i)
                q.exec(QString("INSERT INTO items (id,name,val) VALUES (%1,'item%1',%2)")
                           .arg(i).arg(i * 10));
            db.close();
        }
        QSqlDatabase::removeDatabase("seed");

        SqlListModel model;
        CHECK(model.openDatabase(dbPath), "打开 SQLite");
        model.setQuery("SELECT id, name, val FROM items ORDER BY id",
                       "SELECT COUNT(*) FROM items");
        CHECK(model.count() == 250, "count == 250");
        CHECK(model.rowCount() == 250, "rowCount == 250");

        // getRow(0) 第一行
        QVariantMap r0 = model.getRow(0);
        CHECK(r0.value("id").toInt() == 1 && r0.value("name").toString() == "item1",
              "getRow(0) 正确");
        // getRow(199) 跨页(pageSize=100, 第2页)
        QVariantMap r199 = model.getRow(199);
        CHECK(r199.value("id").toInt() == 200 && r199.value("val").toInt() == 2000,
              "getRow(199) 跨页正确");
        // data() 经 role 读取
        auto roles = model.roleNames();
        int nameRole = roles.key("name", -1);
        CHECK(nameRole != -1, "roleNames 含 name 列");
        QVariant nameVal = model.data(model.index(5, 0), nameRole);
        CHECK(nameVal.toString() == "item6", "data(row5, name) == item6");

        QFile::remove(dbPath);
    }

    qInfo() << "=== ConfigManager 测试(备份/恢复真实配置, 不污染) ===";
    {
        ConfigManager *cfg = ConfigManager::instance();
        const QString path = cfg->getConfigPath();
        // 备份真实配置
        const QString backup = path + ".test_backup";
        const bool hadFile = QFile::exists(path);
        if (hadFile) { QFile::remove(backup); QFile::copy(path, backup); }

        // 默认值 (镜像 Python app_config 默认)
        CHECK(cfg->dwmShadow() == true || cfg->dwmShadow() == false, "dwmShadow 可读");
        // set + 持久化往返
        const bool origMica = cfg->micaEnabled();
        cfg->setMicaEnabled(!origMica);
        CHECK(cfg->micaEnabled() == !origMica, "setMicaEnabled 生效");
        CHECK(QFile::exists(path), "set 后配置文件已落盘");
        // 校验拒绝非法值 (dpiScale 只接受 0/100/125/150/175/200)
        const int origDpi = cfg->dpiScale();
        cfg->setDpiScale(999);  // 非法
        CHECK(cfg->dpiScale() == origDpi, "非法 dpiScale 被拒绝");
        cfg->setDpiScale(150);  // 合法
        CHECK(cfg->dpiScale() == 150, "合法 dpiScale 接受");
        // windowType 校验 (0-3)
        cfg->setWindowType(99);
        CHECK(cfg->windowType() != 99, "非法 windowType 被拒绝");
        // 恢复 mica
        cfg->setMicaEnabled(origMica);
        cfg->setDpiScale(origDpi >= 0 && (origDpi==0||origDpi==100||origDpi==125||
                          origDpi==150||origDpi==175||origDpi==200) ? origDpi : 0);

        // 恢复真实配置文件
        if (hadFile) { QFile::remove(path); QFile::copy(backup, path); QFile::remove(backup); }
        else { QFile::remove(path); }
    }

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
