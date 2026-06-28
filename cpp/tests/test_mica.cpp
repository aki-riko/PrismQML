// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - MicaManager DWM 调用验证 (需真实 Windows 平台, Build>=22621)
#include "prism/MicaManager.h"
#include "prism/ShadowManager.h"

#include <QGuiApplication>
#include <QQuickWindow>
#include <QTimer>
#include <QVariant>
#include <QFile>
#include <QTextStream>
#include <QProcessEnvironment>
#include <QDebug>

static int g_failed = 0;
static QStringList g_log;
#define CHECK(cond, name) do { \
    if (cond) { qInfo() << "  PASS:" << name; g_log << QStringLiteral("PASS: ") + name; } \
    else { qCritical() << "  FAIL:" << name; g_log << QStringLiteral("FAIL: ") + name; ++g_failed; } \
} while (0)

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    using namespace prism;

    qInfo() << "=== MicaManager DWM 验证 (真实平台) ===";
    MicaManager *mica = MicaManager::instance();
    qInfo() << "  isWin11 =" << mica->isWin11();
    CHECK(mica->isWin11(), "isWin11=true (本机 Build 26100)");

    // 创建真实窗口才有 HWND
    QQuickWindow win;
    win.setWidth(400);
    win.setHeight(300);
    win.show();

    ShadowManager *shadow = ShadowManager::instance();
    CHECK(shadow->useNative(), "ShadowManager.useNative=true (Windows)");

    // 延迟到窗口有 HWND 后调 DWM
    QTimer::singleShot(500, [&]() {
        QVariant wv = QVariant::fromValue(static_cast<QObject *>(&win));
        bool micaOk = mica->setMicaEffect(wv, true, false);
        qInfo() << "  setMicaEffect ->" << micaOk;
        CHECK(micaOk, "setMicaEffect 返回 true (DWM backdrop 设置成功)");

        bool shadowOk = shadow->enableShadowForWindow(wv);
        qInfo() << "  enableShadowForWindow ->" << shadowOk;
        CHECK(shadowOk, "enableShadowForWindow 返回 true (DWM 阴影成功)");

        qInfo() << "";
        if (g_failed == 0) qInfo() << "ALL_TESTS_PASSED";
        else qCritical() << "TESTS_FAILED:" << g_failed;

        // 结果写文件 (真实平台 GUI 子系统 stdout 不回传管道)
        const QString out = QProcessEnvironment::systemEnvironment()
                                .value(QStringLiteral("PRISM_MICA_OUT"));
        if (!out.isEmpty()) {
            QFile f(out);
            if (f.open(QIODevice::WriteOnly)) {
                QTextStream ts(&f);
                ts << "isWin11=" << (mica->isWin11() ? "true" : "false") << "\n";
                for (const QString &l : g_log) ts << l << "\n";
                ts << (g_failed == 0 ? "ALL_TESTS_PASSED" : "TESTS_FAILED") << "\n";
            }
        }
        QCoreApplication::exit(g_failed == 0 ? 0 : 1);
    });

    return app.exec();
}
