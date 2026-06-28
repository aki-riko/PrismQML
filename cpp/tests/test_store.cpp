// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Store/Logger 单元测试 (验证阶段4 纯逻辑能力)
#include "prism/Store.h"
#include "prism/Logger.h"

#include <QCoreApplication>
#include <QDebug>
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

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
