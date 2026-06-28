// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTray/SingleInstance 运行时烟测 (需 QApplication)
#include "prism/SystemTray.h"
#include "prism/SingleInstance.h"

#include <QApplication>
#include <QTimer>
#include <QDebug>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    using namespace prism;

    qInfo() << "=== SystemTray 烟测 ===";
    // 构造 + addAction + addSeparator 不崩 (QApplication 下 QMenu 正常)
    {
        SystemTrayIcon tray(QString(), QStringLiteral("测试托盘"));
        bool clicked = false;
        tray.addAction(QStringLiteral("打开"), [&clicked]() { clicked = true; });
        tray.addSeparator();
        tray.addAction(QStringLiteral("退出"), nullptr);
        CHECK(true, "SystemTrayIcon 构造+addAction+addSeparator 无崩溃");
        CHECK(true, QStringLiteral("isAvailable=%1(环境相关)")
                        .arg(SystemTrayIcon::isAvailable()).toUtf8().constData());
    }

    qInfo() << "=== SingleInstance 烟测 ===";
    {
        // 首个实例: 不应判定为 running
        SingleInstance si(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(!si.isRunning(), "首个实例 isRunning=false");

        // 第二个同 id 实例: 应判定为 running
        SingleInstance si2(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(si2.isRunning(), "第二实例 isRunning=true");
    }

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;

    // 不进事件循环, 直接返回 (烟测不需要)
    return g_failed == 0 ? 0 : 1;
}
