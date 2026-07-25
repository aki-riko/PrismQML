// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - MicaManager DWM 调用验证 (需真实 Windows 平台, Build>=22621)
#include "prism/MicaManager.h"
#include "prism/ShadowManager.h"
#include "prism/WindowHelper.h"
#include "TestProcess.h"

#include <QGuiApplication>
#include <QQuickWindow>
#include <QTimer>
#include <QVariant>
#include <QFile>
#include <QTextStream>
#include <QProcessEnvironment>
#include <QDebug>
#include <QtGlobal>

#ifdef Q_OS_WIN
#include <windows.h>
#endif

static int g_failed = 0;
static QStringList g_log;
static constexpr int kSkipReturnCode = 77;
#define CHECK(cond, name) do { \
    if (cond) { qInfo() << "  PASS:" << name; g_log << QStringLiteral("PASS: ") + name; } \
    else { qCritical() << "  FAIL:" << name; g_log << QStringLiteral("FAIL: ") + name; ++g_failed; } \
} while (0)

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QGuiApplication app(argc, argv);
    using namespace prism;

    qInfo() << "=== MicaManager DWM 验证 (真实 Windows 11 平台) ===";
#if !defined(Q_OS_WIN)
    qInfo() << "SKIP: Mica/DWM 仅支持 Windows";
    return kSkipReturnCode;
#endif

    MicaManager *mica = MicaManager::instance();
    qInfo() << "  isWin11 =" << mica->isWin11();
    if (!mica->isWin11()) {
        qInfo() << "SKIP: 当前 Windows 版本不支持 Mica";
        return kSkipReturnCode;
    }
    CHECK(mica->isWin11(), "isWin11=true");

    // 创建真实但保持隐藏的 HWND，避免自动化测试闪现窗口。
    QQuickWindow win;
    win.setWidth(400);
    win.setHeight(300);
    const auto nativeId = win.winId();
    CHECK(nativeId != 0, "隐藏测试窗口已创建 HWND");
    CHECK(!win.isVisible(), "测试窗口保持隐藏");
#ifdef Q_OS_WIN
    CHECK(IsWindowVisible(reinterpret_cast<HWND>(nativeId)) == FALSE,
          "原生 HWND 保持隐藏");
#endif

    ShadowManager *shadow = ShadowManager::instance();
    CHECK(shadow->useNative(), "ShadowManager.useNative=true (Windows)");
    CHECK(!shadow->enableShadow(0), "enableShadow 拒绝空 HWND");
    CHECK(!shadow->disableShadow(0), "disableShadow 拒绝空 HWND");

    QQuickWindow follower;
    follower.setFlags(Qt::Tool | Qt::FramelessWindowHint);
    follower.setTransientParent(nullptr);
    follower.setWidth(180);
    follower.setHeight(300);
    const auto followerId = follower.winId();
    CHECK(followerId != 0, "隐藏附属窗口已创建 HWND");

    QQuickWindow popup;
    popup.setFlags(Qt::Popup);
    popup.setTransientParent(&win);
    const auto popupId = popup.winId();
    CHECK(popupId != 0, "隐藏弹层已创建 HWND");

    // 进入一次事件循环后调用 DWM，但窗口始终不 show。
    QTimer::singleShot(0, [&]() {
        CHECK(!win.isVisible(), "DWM 调用前测试窗口仍隐藏");
        QVariant wv = QVariant::fromValue(static_cast<QObject *>(&win));
        bool micaOk = mica->setMicaEffect(wv, true, false);
        qInfo() << "  setMicaEffect ->" << micaOk;
        CHECK(micaOk, "setMicaEffect 返回 true (DWM backdrop 设置成功)");
        CHECK(mica->setWindowCorner(wv, true),
              "setWindowCorner 返回 true (DWM 圆角设置成功)");

        bool shadowOk = shadow->enableShadowForWindow(wv);
        qInfo() << "  enableShadowForWindow ->" << shadowOk;
        CHECK(shadowOk, "enableShadowForWindow 返回 true (DWM 阴影成功)");
        bool disableOk = shadow->disableShadowForWindow(wv);
        qInfo() << "  disableShadowForWindow ->" << disableOk;
        CHECK(disableOk, "disableShadowForWindow 返回 true (DWM 阴影禁用成功)");
#ifdef Q_OS_WIN
        SetWindowPos(
            reinterpret_cast<HWND>(nativeId), HWND_TOP,
            100, 120, 600, 400, SWP_NOACTIVATE);
        SetWindowPos(
            reinterpret_cast<HWND>(followerId), HWND_TOP,
            650, 90, 180, 300, SWP_NOACTIVATE);
        WindowHelper *helper = WindowHelper::instance();
        SetWindowLongPtrW(
            reinterpret_cast<HWND>(popupId), GWLP_HWNDPARENT, 0);
        QVariant popupVariant = QVariant::fromValue(static_cast<QObject *>(&popup));
        CHECK(GetWindow(reinterpret_cast<HWND>(popupId), GW_OWNER) == nullptr,
              "弹层原生 owner 缺失输入已复现");
        CHECK(helper->ensurePopupWindowOwner(popupVariant, wv),
              "ensurePopupWindowOwner 修复并抬升弹层");
        CHECK(GetWindow(reinterpret_cast<HWND>(popupId), GW_OWNER)
                  == reinterpret_cast<HWND>(nativeId),
              "弹层原生 owner 指向宿主窗口");
        QVariant followerVariant = QVariant::fromValue(static_cast<QObject *>(&follower));
        CHECK(GetWindow(reinterpret_cast<HWND>(followerId), GW_OWNER) == nullptr,
              "外侧附属窗口没有 owner, 可位于宿主下层");
        CHECK(helper->updateWindowFollowerGeometry(wv, followerVariant, 2, 90),
              "updateWindowFollowerGeometry 原子提交顶部动画帧");
        RECT animatedTop{};
        const bool animatedTopRectOk = GetWindowRect(
            reinterpret_cast<HWND>(followerId), &animatedTop);
        const int animatedTopExtent = qRound(90 * win.devicePixelRatio());
        const QString animatedTopGeometryMessage = QStringLiteral(
            "顶部动画帧同时更新位置和尺寸 actual=(%1,%2,%3,%4)")
                .arg(animatedTop.left).arg(animatedTop.top)
                .arg(animatedTop.right).arg(animatedTop.bottom);
        CHECK(animatedTopRectOk
                  && animatedTop.left == 100
                  && animatedTop.top == 120 - animatedTopExtent
                  && animatedTop.right == 700
                  && animatedTop.bottom == 120,
              animatedTopGeometryMessage);
        CHECK(helper->updateWindowFollowerGeometry(wv, followerVariant, 1, 180),
              "updateWindowFollowerGeometry 准备右侧完整尺寸");
        const int animatedRightExtent = qRound(180 * win.devicePixelRatio());
        CHECK(helper->registerWindowFollower(wv, followerVariant, 1, 180),
              "registerWindowFollower 注册右侧原生跟随");
        RECT registered{};
        const bool registeredRectOk = GetWindowRect(
            reinterpret_cast<HWND>(followerId), &registered);
        const QString registeredGeometryMessage = QStringLiteral(
            "registerWindowFollower 立即同步 actual=(%1,%2,%3,%4)")
                .arg(registered.left).arg(registered.top)
                .arg(registered.right).arg(registered.bottom);
        CHECK(registeredRectOk
                  && registered.left == 700
                  && registered.top == 120
                  && registered.right == 700 + animatedRightExtent
                  && registered.bottom == 520,
              registeredGeometryMessage);
        CHECK(GetWindow(reinterpret_cast<HWND>(followerId), GW_HWNDPREV)
                  == reinterpret_cast<HWND>(nativeId),
              "附属窗口紧贴宿主窗口下层");
        WINDOWPOS attemptedRaise{
            reinterpret_cast<HWND>(followerId), HWND_TOP,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE};
        MSG zOrderChanging{};
        zOrderChanging.hwnd = reinterpret_cast<HWND>(followerId);
        zOrderChanging.message = WM_WINDOWPOSCHANGING;
        zOrderChanging.lParam = reinterpret_cast<LPARAM>(&attemptedRaise);
        helper->nativeEventFilter("windows_generic_MSG", &zOrderChanging, nullptr);
        CHECK(attemptedRaise.hwndInsertAfter == reinterpret_cast<HWND>(nativeId)
                  && (attemptedRaise.flags & SWP_NOZORDER) == 0,
              "附属窗口抬升请求被改写到宿主下层");
        RECT proposed{240, 260, 880, 680};
        MSG moving{};
        moving.hwnd = reinterpret_cast<HWND>(nativeId);
        moving.message = WM_MOVING;
        moving.lParam = reinterpret_cast<LPARAM>(&proposed);
        helper->nativeEventFilter("windows_generic_MSG", &moving, nullptr);
        RECT actual{};
        const bool followerRectOk = GetWindowRect(
            reinterpret_cast<HWND>(followerId), &actual);
        const QString followerGeometryMessage = QStringLiteral(
            "WM_MOVING proposed RECT 同步附属窗口 actual=(%1,%2,%3,%4)")
                .arg(actual.left).arg(actual.top).arg(actual.right).arg(actual.bottom);
        CHECK(followerRectOk
                  && actual.left == 880 && actual.top == 260
                  && actual.right == 880 + animatedRightExtent
                  && actual.bottom == 680,
              followerGeometryMessage);
        CHECK(helper->unregisterWindowFollower(followerVariant),
              "unregisterWindowFollower 清理附属窗口绑定");
#endif
        CHECK(!win.isVisible(), "DWM 调用后测试窗口仍隐藏");
#ifdef Q_OS_WIN
        CHECK(IsWindowVisible(reinterpret_cast<HWND>(nativeId)) == FALSE,
              "DWM 调用后原生 HWND 仍隐藏");
#endif

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
