// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 关闭契约验证 (镜像 Python closeEvent + requestHideOnClose)
//
// 覆盖: 宿主关闭回调的接受/取消/隐藏式关闭三种收尾, 关闭期间的重复请求, 以及收尾后
// 关闭状态必须复位 (否则 _closeInProgress 永久闩住, 窗口再也关不掉)。全部在
// offscreen 平台跑, 只做零交互正确性回归。
#include "prism/App.h"
#include "prism/Window.h"
#include "TestProcess.h"

#include <QApplication>
#include <QDebug>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

namespace {

// 关闭收尾要等收缩动画(约 420ms)与帧尾握手全部跑完。
constexpr int kCloseSettleMs = 1400;
constexpr int kShowSettleMs = 300;

struct CloseCall {
    bool accepted = false;
    bool hideOnCloseRequested = false;
};

// 宿主关闭回调的可编程替身: 记录每次请求, 按测试设定的行为回复。
struct CloseController {
    enum class Reply { Accept, Reject, HideOnly };

    Reply reply = Reply::Accept;
    int calls = 0;
    QList<CloseCall> observed;

    void operator()(prism::WindowCloseEvent &event) {
        ++calls;
        CloseCall call;
        call.accepted = event.isAccepted();
        call.hideOnCloseRequested = event.hideOnCloseRequested();
        observed.append(call);
        switch (reply) {
            case Reply::Accept:
                break;
            case Reply::Reject:
                event.ignore();
                break;
            case Reply::HideOnly:
                event.requestHideOnClose();
                break;
        }
    }
};

QObject *findByObjectName(QObject *root, const QString &objectName) {
    if (!root)
        return nullptr;
    if (root->objectName() == objectName)
        return root;
    return root->findChild<QObject *>(objectName);
}

bool invokeRequestClose(prism::Window &window) {
    return QMetaObject::invokeMethod(window.rootObject(), "requestClose");
}

bool hostVisible(QObject *hostWindow) {
    return hostWindow && hostWindow->property("visible").toBool();
}

// visible 是 QML 字面量赋值, C++ setter 会被它遮蔽, 故统一走属性写。
bool showHost(QObject *hostWindow) {
    return hostWindow && hostWindow->setProperty("visible", true);
}

// 复现 Python 回归的判定方式: 按类名定位内容层, 而不是按 QML id。
QQuickItem *findFrameLayer(QObject *rootObject) {
    auto *window = qobject_cast<QQuickWindow *>(rootObject);
    if (!window || !window->contentItem())
        return nullptr;
    const QList<QQuickItem *> children = window->contentItem()->childItems();
    for (QQuickItem *child : children) {
        if (QString::fromLatin1(child->metaObject()->className())
                .contains(QStringLiteral("WindowsCoreFrame")))
            return child;
    }
    return nullptr;
}

}  // namespace

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    prism::App app(argc, argv);
    using namespace prism;

    qInfo() << "=== Window close contract (C++ host) ===";

    Window &window = app.createWindow(WindowType::Bar);
    window.setSplash(false);
    window.setWindowTitle(QStringLiteral("Window close contract"));
    window.show();
    QTest::qWait(kShowSettleMs);

    QObject *rootObject = window.rootObject();
    CHECK(rootObject != nullptr, "窗口根对象已创建");
    QObject *hostWindow = findByObjectName(rootObject, QStringLiteral("mainWindow"));
    CHECK(hostWindow != nullptr, "可按 objectName 取到 QML 宿主窗口");
    if (!rootObject || !hostWindow) {
        qCritical() << "TESTS_FAILED: 1";
        return 1;
    }

    CloseController controller;
    window.onClosing([&controller](WindowCloseEvent &event) { controller(event); });

    // ---- 1. 默认接受: 回调收到一次已接受请求, 关闭动画正常收尾 ----
    controller.reply = CloseController::Reply::Accept;
    controller.calls = 0;
    controller.observed.clear();

    CHECK(invokeRequestClose(window), "requestClose 可经元对象调用");
    // QML 在已接受关闭发起时同步置 _closeInProgress; 关闭期间再次请求必须被忽略。
    CHECK(rootObject->property("_closeInProgress").toBool(),
          "已接受关闭同步进入关闭中状态");
    CHECK(invokeRequestClose(window), "关闭期间的重复 requestClose 仍可调用");
    QTest::qWait(kCloseSettleMs);

    // 一次关闭只交付一次宿主回调: 收尾那次原生关闭投递属于同一次请求, 不再重复交付。
    CHECK(controller.calls == 1, "默认关闭只触发一次宿主回调");
    CHECK(controller.observed.size() == 1 && controller.observed.at(0).accepted,
          "宿主回调收到已接受的关闭事件");
    CHECK(controller.observed.size() == 1
              && !controller.observed.at(0).hideOnCloseRequested,
          "未请求隐藏式关闭时事件不声明隐藏");
    CHECK(!hostVisible(hostWindow), "默认关闭真正关闭窗口");
    // 关键回归: 关闭只隐藏窗口, 关闭状态必须复位, 否则窗口再也关不掉。
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "默认关闭收尾后关闭状态已复位");
    CHECK(!rootObject->property("_closeCompletionPending").toBool(),
          "默认关闭收尾后帧尾等待标记已复位");
    CHECK(!rootObject->property("_closeHideOnlyLatched").toBool(),
          "默认关闭收尾后隐藏式关闭闩锁已复位");

    // ---- 2. 取消关闭: 窗口继续存活且画面状态还原 ----
    CHECK(showHost(hostWindow), "默认关闭后窗口可再次显示");
    QTest::qWait(kShowSettleMs);

    controller.reply = CloseController::Reply::Reject;
    controller.calls = 0;
    controller.observed.clear();

    CHECK(invokeRequestClose(window), "取消路径 requestClose 可调用");
    QTest::qWait(200);

    CHECK(controller.calls == 1, "取消关闭触发一次宿主回调");
    CHECK(rootObject->property("closeRequestAccepted").toBool() == false,
          "取消关闭写回 closeRequestAccepted=false");
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "取消关闭未遗留关闭中状态");
    CHECK(hostVisible(hostWindow), "取消关闭后窗口仍可见");
    CHECK(qAbs(rootObject->property("_animOpacity").toDouble() - 1.0) < 0.01,
          "取消关闭后内容层不透明度已还原");

    // ---- 3. 隐藏式关闭: 播完动画后隐藏而非销毁, 状态全部复位 ----
    controller.reply = CloseController::Reply::HideOnly;
    controller.calls = 0;
    controller.observed.clear();

    CHECK(invokeRequestClose(window), "隐藏式关闭 requestClose 可调用");
    CHECK(rootObject->property("_closeHideOnlyLatched").toBool(),
          "隐藏式关闭在已接受关闭发起时闩锁");
    QTest::qWait(kCloseSettleMs);

    CHECK(controller.calls == 1, "隐藏式关闭触发一次宿主回调");
    CHECK(controller.observed.size() == 1 && controller.observed.at(0).accepted,
          "隐藏式关闭仍是已接受事件");
    CHECK(rootObject->property("closeRequestHideOnly").toBool(),
          "隐藏式关闭写回 closeRequestHideOnly=true");
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "隐藏式关闭收尾后关闭状态已复位");
    CHECK(!hostVisible(hostWindow), "隐藏式关闭把窗口隐藏而非销毁");
    CHECK(qAbs(hostWindow->property("opacity").toDouble() - 1.0) < 0.01,
          "隐藏式关闭后窗口不透明度已复位");

    // ---- 4. 隐藏后可再次显示, 内容层与关闭能力一并恢复 ----
    CHECK(showHost(hostWindow), "隐藏式关闭后窗口可再次显示");
    QTest::qWait(kShowSettleMs);

    CHECK(hostVisible(hostWindow), "隐藏式关闭后窗口重新可见");
    QQuickItem *frameLayer = findFrameLayer(rootObject);
    CHECK(frameLayer != nullptr, "关闭后可定位窗口内容层");
    CHECK(frameLayer && frameLayer->isVisible(), "再次显示后内容层可见");

    // ---- 5. 再次关闭必须完整重跑握手, 并仍然隐藏而非销毁 ----
    controller.calls = 0;
    controller.observed.clear();
    CHECK(invokeRequestClose(window), "第二次隐藏式关闭可调用");
    QTest::qWait(kCloseSettleMs);

    CHECK(controller.calls == 1, "第二次隐藏式关闭触发一次宿主回调");
    CHECK(!hostVisible(hostWindow), "第二次隐藏式关闭同样隐藏窗口");
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "第二次隐藏式关闭收尾后关闭状态已复位");

    // ---- 6. 默认收尾仍然真正关闭, 且关闭状态复位后可再次关闭 ----
    controller.reply = CloseController::Reply::Accept;
    controller.calls = 0;
    controller.observed.clear();

    CHECK(showHost(hostWindow), "最终关闭前窗口可再次显示");
    QTest::qWait(kShowSettleMs);
    CHECK(invokeRequestClose(window), "最终默认关闭可调用");
    QTest::qWait(kCloseSettleMs);

    CHECK(controller.calls == 1, "最终默认关闭触发一次宿主回调");
    CHECK(!hostVisible(hostWindow), "最终默认关闭真正关闭窗口");
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "最终默认关闭未遗留关闭中状态");

    // 关闭状态复位后才可能再次关闭: 再走一次完整握手并再次成功关窗。
    // 这里清掉宿主回调, 只验证真实关闭的视觉收尾与状态复位不受回调影响。
    window.onClosing(nullptr);
    controller.calls = 0;
    controller.observed.clear();
    CHECK(showHost(hostWindow), "关闭后窗口仍可再次显示");
    QTest::qWait(kShowSettleMs);
    CHECK(hostVisible(hostWindow), "关闭后窗口重新可见");
    CHECK(invokeRequestClose(window), "关闭状态复位后再次关闭可调用");
    QTest::qWait(kCloseSettleMs);

    CHECK(!hostVisible(hostWindow), "再次关闭同样真正关闭窗口");
    CHECK(!rootObject->property("_closeInProgress").toBool(),
          "再次关闭收尾后关闭状态已复位");

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;
    return g_failed == 0 ? 0 : 1;
}
