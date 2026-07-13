// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// NativeWindow state and QML contract regressions. NativeWindow 状态与 QML 合同回归。
#include "prism/NativeWindow.h"
#include "prism/ConfigContracts.h"
#include "prism/Registry.h"
#include "NativeWindow_p.h"
#include "NativeWindowQmlTestSupport.h"
#include "NativeWindowTestFakes.h"
#include "TestProcess.h"

#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QMetaMethod>
#include <QMetaType>
#include <QTemporaryDir>
#include <QWindow>
#include <memory>

namespace {

constexpr qulonglong kHwnd = 101;
constexpr qulonglong kSecondHwnd = 202;
constexpr qlonglong kObservedStyle = 0x10;
constexpr qlonglong kPreviousStyle = 0x20;
constexpr qlonglong kNativeStyle = 0x00CF0010;
constexpr quint32 kAccessDenied = 5;
constexpr quint32 kInvalidWindow = 1400;
const QStringList kReattachAfterRestoreCalls = {
    QStringLiteral("get:101"),
    QStringLiteral("set:101:%1").arg(kNativeStyle),
    QStringLiteral("frame:101"),
    QStringLiteral("set:101:%1").arg(kPreviousStyle),
    QStringLiteral("frame:101"),
    QStringLiteral("get:101"),
    QStringLiteral("set:101:%1").arg(kNativeStyle),
    QStringLiteral("frame:101"),
};

int gFailures = 0;

#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++gFailures; } \
} while (0)

using FakePlatform = prism::test::FakeNativeWindowPlatform;
using FakeRawApi = prism::test::FakeNativeWindowRawApi;

}  // namespace

namespace prism {

struct NativeWindowTestAccess {
    static std::unique_ptr<NativeWindow> create(
        std::unique_ptr<NativeWindowPlatform> platform) {
        return std::unique_ptr<NativeWindow>(new NativeWindow(std::move(platform)));
    }

    static bool attach(NativeWindow &window, qulonglong hwnd) {
        return window.attachHwnd(hwnd, true);
    }

    static bool finalize(NativeWindow &window, qulonglong hwnd) {
        return window.finalizeHwnd(hwnd);
    }

    static bool detach(NativeWindow &window, qulonglong hwnd) {
        return window.detachHwnd(hwnd);
    }

    static bool attachOwner(NativeWindow &window, QObject *owner) {
        return window.attach(QVariant::fromValue(owner));
    }

    static bool finalizeOwner(NativeWindow &window, QObject *owner) {
        return window.finalizeAttach(QVariant::fromValue(owner));
    }

    static bool detachOwner(NativeWindow &window, QObject *owner) {
        return window.detach(QVariant::fromValue(owner));
    }

    static bool stateMatches(const NativeWindow &window,
                             const QSet<qulonglong> &attached,
                             const QSet<qulonglong> &framechanged,
                             const QHash<qulonglong, qlonglong> &styles,
                             const QSet<qulonglong> &restorePending = {}) {
        if (window.m_hwnds != attached ||
            window.m_framechangedHwnds != framechanged ||
            window.m_originalStyles != styles ||
            window.m_restorePendingHwnds != restorePending)
            return false;
        if (window.m_originalStyles.size() != window.m_hwnds.size())
            return false;
        for (auto it = window.m_originalStyles.cbegin();
             it != window.m_originalStyles.cend(); ++it) {
            if (!window.m_hwnds.contains(it.key()))
                return false;
        }
        for (qulonglong hwnd : window.m_framechangedHwnds) {
            if (!window.m_hwnds.contains(hwnd))
                return false;
        }
        for (qulonglong hwnd : window.m_restorePendingHwnds) {
            if (!window.m_hwnds.contains(hwnd) ||
                window.m_framechangedHwnds.contains(hwnd))
                return false;
        }
        return true;
    }
};

}  // namespace prism

namespace {

using prism::NativeWindow;
using prism::NativeWindowTestAccess;

std::unique_ptr<NativeWindow> makeWindow(FakePlatform **platform) {
    auto fake = std::make_unique<FakePlatform>();
    *platform = fake.get();
    return NativeWindowTestAccess::create(std::move(fake));
}

struct RawPlatformFixture {
    std::unique_ptr<FakeRawApi> rawOwner = std::make_unique<FakeRawApi>();
    FakeRawApi *raw = rawOwner.get();
    prism::CheckedNativeWindowPlatform platform{std::move(rawOwner)};
    qlonglong value = -1;
    quint32 errorCode = kAccessDenied;
};

void queueTwoSuccessfulAttaches(FakePlatform *platform,
                                qlonglong firstPreviousStyle,
                                qlonglong secondPreviousStyle) {
    platform->gets = {
        {true, kObservedStyle, 0}, {true, kObservedStyle, 0}};
    platform->sets = {
        {true, firstPreviousStyle, 0}, {true, secondPreviousStyle, 0}};
    platform->frames = {{true, 0, 0}, {true, 0, 0}};
}

void testMetaObjectContract() {
    qInfo() << "=== NativeWindow QML metaobject contract ===";
    const QMetaObject *meta = NativeWindow::instance()->metaObject();
    const QList<QByteArray> methods = {
        QByteArrayLiteral("attach(QVariant)"),
        QByteArrayLiteral("finalizeAttach(QVariant)"),
        QByteArrayLiteral("detach(QVariant)"),
    };
    for (const QByteArray &signature : methods) {
        const int index = meta->indexOfMethod(signature.constData());
        CHECK(index >= 0, signature.constData());
        if (index >= 0) {
            CHECK(meta->method(index).returnMetaType().id() == QMetaType::Bool,
                  "公开 NativeWindow 方法统一返回 bool");
        }
    }
}

void testLongPtrResultRules() {
    CHECK(prism::nativeLongPtrCallSucceeded(0, 0),
          "LongPtr 返回零且 LastError 零是成功");
    CHECK(!prism::nativeLongPtrCallSucceeded(0, kAccessDenied),
          "LongPtr 返回零且 LastError 非零是失败");
    CHECK(prism::nativeLongPtrCallSucceeded(kPreviousStyle, kAccessDenied),
          "LongPtr 非零返回始终代表成功");
}

void testCheckedGetStyleContract() {
    RawPlatformFixture fixture;
    fixture.raw->gets = {{0, std::nullopt}};
    CHECK(fixture.platform.getStyle(
              kHwnd, &fixture.value, &fixture.errorCode),
          "Get 前清零使零返回 + 未改 LastError 成为成功");
    CHECK(fixture.value == 0 && fixture.errorCode == 0, "Get 返回合法零样式");
    CHECK((fixture.raw->calls == QStringList{
              QStringLiteral("clear"), QStringLiteral("get:101"),
              QStringLiteral("last")}),
          "Get 严格执行 clear-call-read");
    fixture.raw->calls.clear();
    fixture.raw->error = kAccessDenied;
    fixture.raw->gets = {{0, kInvalidWindow}};
    CHECK(!fixture.platform.getStyle(
              kHwnd, &fixture.value, &fixture.errorCode),
          "Get 零返回 + 新 LastError 失败");
    CHECK(fixture.errorCode == kInvalidWindow, "Get 传播真实 LastError");
}

void testCheckedSetStyleContract() {
    RawPlatformFixture fixture;
    fixture.raw->sets = {{0, std::nullopt}};
    CHECK(fixture.platform.setStyle(
              kHwnd, kNativeStyle, &fixture.value, &fixture.errorCode),
          "Set 前清零使零旧样式成为成功");
    CHECK(fixture.value == 0 && fixture.errorCode == 0,
          "Set 保存 API 返回的真实旧样式");
    CHECK((fixture.raw->calls == QStringList{
              QStringLiteral("clear"),
              QStringLiteral("set:101:%1").arg(kNativeStyle),
              QStringLiteral("last")}),
          "Set 严格执行 clear-call-read");
    fixture.raw->calls.clear();
    fixture.raw->error = kAccessDenied;
    fixture.raw->sets = {{0, kAccessDenied}};
    CHECK(!fixture.platform.setStyle(
              kHwnd, kNativeStyle, &fixture.value, &fixture.errorCode),
          "Set 零返回 + 新 LastError 失败");
    CHECK(fixture.errorCode == kAccessDenied, "Set 传播真实 LastError");
}

void testCheckedFrameChangedContract() {
    RawPlatformFixture fixture;
    fixture.raw->frames = {{0, std::nullopt}};
    CHECK(!fixture.platform.applyFrameChanged(kHwnd, &fixture.errorCode),
          "SetWindowPos 返回零即使 LastError 零也失败");
    CHECK(fixture.errorCode == 0, "SetWindowPos 保留零错误码供上层诊断");
    CHECK((fixture.raw->calls == QStringList{
              QStringLiteral("clear"), QStringLiteral("frame:101"),
              QStringLiteral("last")}),
          "SetWindowPos 严格执行 clear-call-read");
}

void testRawWinApiResultContract() {
    qInfo() << "=== raw WinAPI result contract ===";
    testLongPtrResultRules();
    testCheckedGetStyleContract();
    testCheckedSetStyleContract();
    testCheckedFrameChangedContract();
}

void testAttachReadFailure() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{false, 0, kInvalidWindow}};
    CHECK(!NativeWindowTestAccess::attach(*window, kHwnd),
          "GetWindowLongPtrW 失败返回 false");
    CHECK(NativeWindowTestAccess::stateMatches(*window, {}, {}, {}),
          "GetWindowLongPtrW 失败零状态");
    CHECK((platform->calls == QStringList{QStringLiteral("get:101")}),
          "Get 失败不调用后续原生操作");
}

void testAttachWriteFailure() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {{false, 0, kAccessDenied}};
    CHECK(!NativeWindowTestAccess::attach(*window, kHwnd),
          "SetWindowLongPtrW 失败返回 false");
    CHECK(NativeWindowTestAccess::stateMatches(*window, {}, {}, {}),
          "SetWindowLongPtrW 失败零状态");
}

void testZeroStyleAttach() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, 0, 0}};
    platform->sets = {{true, 0, 0}};
    platform->frames = {{true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd),
          "Get/Set 返回零且 LastError 零仍成功");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {kHwnd}, {{kHwnd, 0}}),
          "合法零样式被完整跟踪");
}

void testAttachFailureBoundaries() {
    qInfo() << "=== attach failure boundaries ===";
    testAttachReadFailure();
    testAttachWriteFailure();
    testZeroStyleAttach();
}

void testFramechangedRetry() {
    qInfo() << "=== framechanged retry ===";
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {{true, kPreviousStyle, 0}};
    platform->frames = {
        {false, 0, 0},
        {true, 0, 0},
    };
    CHECK(!NativeWindowTestAccess::attach(*window, kHwnd),
          "SetWindowPos 返回零且 LastError 零仍 fail closed");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {}, {{kHwnd, kPreviousStyle}}),
          "framechanged 失败保留可恢复 partial 状态");
    CHECK(NativeWindowTestAccess::finalize(*window, kHwnd),
          "finalize 重试 framechanged 成功");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {kHwnd}, {{kHwnd, kPreviousStyle}}),
          "成功后才提交 framechanged 状态");
    CHECK((platform->calls == QStringList{
              QStringLiteral("get:101"),
              QStringLiteral("set:101:%1").arg(kNativeStyle),
              QStringLiteral("frame:101"),
              QStringLiteral("frame:101"),
          }), "重试只补 SetWindowPos");
}

void testDetachStyleRestoreFailure() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0}, {false, 0, kAccessDenied}};
    platform->frames = {{true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "准备已 attach 状态");
    CHECK(!NativeWindowTestAccess::detach(*window, kHwnd),
          "恢复 style 失败返回 false");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {kHwnd}, {{kHwnd, kPreviousStyle}}),
          "恢复 style 失败保留完整状态");
}

void testDetachFrameRestoreRetry() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0}, {true, kObservedStyle, 0}};
    platform->frames = {
        {true, 0, 0}, {false, 0, kAccessDenied}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "准备第二个 attach 状态");
    CHECK(!NativeWindowTestAccess::detach(*window, kHwnd),
          "恢复 framechanged 失败返回 false");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {}, {{kHwnd, kPreviousStyle}}, {kHwnd}),
          "style 已恢复但 framechanged 待重试状态显式记录");
    CHECK(NativeWindowTestAccess::detach(*window, kHwnd),
          "第二次 detach 可重试成功");
    CHECK(NativeWindowTestAccess::stateMatches(*window, {}, {}, {}),
          "两个恢复步骤成功后才清状态");
    CHECK((platform->calls == QStringList{
              QStringLiteral("get:101"),
              QStringLiteral("set:101:%1").arg(kNativeStyle),
              QStringLiteral("frame:101"),
              QStringLiteral("set:101:%1").arg(kPreviousStyle),
              QStringLiteral("frame:101"),
              QStringLiteral("frame:101"),
          }), "恢复待刷新重试不重复恢复 style");
}

void testReattachAfterRestorePending() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    constexpr qlonglong kReplacementPreviousStyle = 0x30;
    platform->gets = {
        {true, kObservedStyle, 0}, {true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0},
        {true, kObservedStyle, 0},
        {true, kReplacementPreviousStyle, 0}};
    platform->frames = {
        {true, 0, 0}, {false, 0, kAccessDenied}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd),
          "准备 detach-frame 失败后重挂状态");
    CHECK(!NativeWindowTestAccess::detach(*window, kHwnd),
          "重挂前形成 restore-pending 状态");
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd),
          "restore-pending 上重新 attach 必须完整调用 WinAPI");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd}, {kHwnd},
              {{kHwnd, kReplacementPreviousStyle}}),
          "重挂保存新一代真实旧样式并清 pending");
    CHECK(platform->calls == kReattachAfterRestoreCalls,
          "restore-pending 重挂不会命中旧 finalized 快捷路径");
}

void testDetachFailureBoundaries() {
    qInfo() << "=== detach failure boundaries ===";
    testDetachStyleRestoreFailure();
    testDetachFrameRestoreRetry();
    testReattachAfterRestorePending();
}

void testNativeOperationIdempotence() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0}, {true, kObservedStyle, 0}};
    platform->frames = {{true, 0, 0}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "首次 attach 成功");
    const int callsAfterAttach = platform->calls.size();
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "重复 attach 幂等");
    CHECK(NativeWindowTestAccess::finalize(*window, kHwnd), "重复 finalize 幂等");
    CHECK(platform->calls.size() == callsAfterAttach, "完整状态不重复调用 WinAPI");
    CHECK(NativeWindowTestAccess::detach(*window, kHwnd), "首次 detach 成功");
    const int callsAfterDetach = platform->calls.size();
    CHECK(NativeWindowTestAccess::detach(*window, kHwnd), "重复 detach 幂等");
    CHECK(platform->calls.size() == callsAfterDetach, "重复 detach 零 WinAPI 调用");
}

void testHwndReuseAndIndependentState() {
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    platform->gets = {
        {true, kObservedStyle, 0}, {true, kObservedStyle, 0},
        {true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0}, {true, kObservedStyle, 0},
        {true, kPreviousStyle, 0}, {true, kPreviousStyle, 0}};
    platform->frames = {
        {true, 0, 0}, {true, 0, 0}, {true, 0, 0}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "准备 HWND 复用状态");
    CHECK(NativeWindowTestAccess::detach(*window, kHwnd), "复用前 detach 成功");
    CHECK(NativeWindowTestAccess::attach(*window, kHwnd), "同值 HWND 可重新 attach");
    CHECK(NativeWindowTestAccess::attach(*window, kSecondHwnd), "第二窗口独立 attach");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kHwnd, kSecondHwnd}, {kHwnd, kSecondHwnd},
              {{kHwnd, kPreviousStyle}, {kSecondHwnd, kPreviousStyle}}),
          "多窗口状态互不污染");
}

void testIdempotenceAndHwndReuse() {
    qInfo() << "=== idempotence and HWND reuse ===";
    testNativeOperationIdempotence();
    testHwndReuseAndIndependentState();
}

void testOwnerDetachUsesBoundHwnd() {
    qInfo() << "=== owner-bound HWND detach ===";
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    QObject owner;
    owner.setProperty("winId", QVariant::fromValue(kHwnd));
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0},
        {true, kObservedStyle, 0},
    };
    platform->frames = {{true, 0, 0}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attachOwner(*window, &owner),
          "owner 首次 attach 成功");
    owner.setProperty("winId", QVariant::fromValue(kSecondHwnd));
    CHECK(NativeWindowTestAccess::detachOwner(*window, &owner),
          "detach 使用 owner 已绑定旧 HWND");
    CHECK(NativeWindowTestAccess::stateMatches(*window, {}, {}, {}),
          "句柄变化后 detach 清理旧绑定状态");
    CHECK((platform->calls == QStringList{
              QStringLiteral("get:101"),
              QStringLiteral("set:101:%1").arg(kNativeStyle),
              QStringLiteral("frame:101"),
              QStringLiteral("set:101:%1").arg(kPreviousStyle),
              QStringLiteral("frame:101"),
          }), "detach 未错误操作新 HWND");
}

void testOwnerHandleChangeRotatesGeneration() {
    qInfo() << "=== owner HWND generation change ===";
    FakePlatform *platform = nullptr;
    auto window = makeWindow(&platform);
    QObject changingOwner;
    changingOwner.setProperty("winId", QVariant::fromValue(kHwnd));
    queueTwoSuccessfulAttaches(platform, kPreviousStyle, kPreviousStyle);
    CHECK(NativeWindowTestAccess::attachOwner(*window, &changingOwner),
          "同 owner 初代 HWND attach 成功");
    changingOwner.setProperty("winId", QVariant::fromValue(kSecondHwnd));
    CHECK(NativeWindowTestAccess::attachOwner(*window, &changingOwner),
          "同 owner 新 HWND 重新完整 attach");
    CHECK(NativeWindowTestAccess::stateMatches(
              *window, {kSecondHwnd}, {kSecondHwnd},
              {{kSecondHwnd, kPreviousStyle}}),
          "同 owner 句柄变化遗忘旧代状态");
    CHECK((platform->calls == QStringList{
              QStringLiteral("get:101"),
              QStringLiteral("set:101:%1").arg(kNativeStyle),
              QStringLiteral("frame:101"),
              QStringLiteral("get:202"),
              QStringLiteral("set:202:%1").arg(kNativeStyle),
              QStringLiteral("frame:202"),
          }), "句柄变化不命中旧 HWND finalized 快捷路径");
}

struct ReusedOwnerScenario {
    FakePlatform *platform = nullptr;
    std::unique_ptr<NativeWindow> window;
    std::unique_ptr<QObject> retiredOwner;
    std::unique_ptr<QObject> currentOwner;
    qlonglong currentPreviousStyle = 0x30;
};

ReusedOwnerScenario makeReusedOwnerScenario() {
    ReusedOwnerScenario scenario;
    scenario.window = makeWindow(&scenario.platform);
    scenario.retiredOwner = std::make_unique<QObject>();
    scenario.currentOwner = std::make_unique<QObject>();
    scenario.retiredOwner->setProperty("winId", QVariant::fromValue(kHwnd));
    scenario.currentOwner->setProperty("winId", QVariant::fromValue(kHwnd));
    queueTwoSuccessfulAttaches(
        scenario.platform, kPreviousStyle, scenario.currentPreviousStyle);
    CHECK(NativeWindowTestAccess::attachOwner(
              *scenario.window, scenario.retiredOwner.get()),
          "首 owner attach 复用目标 HWND");
    CHECK(NativeWindowTestAccess::attachOwner(
              *scenario.window, scenario.currentOwner.get()),
          "新 owner 复用同值 HWND 时完整 attach");
    return scenario;
}

void checkCurrentOwnerState(const ReusedOwnerScenario &scenario,
                            const char *message) {
    CHECK(NativeWindowTestAccess::stateMatches(
              *scenario.window, {kHwnd}, {kHwnd},
              {{kHwnd, scenario.currentPreviousStyle}}), message);
}

void testNewOwnerReusingHwndRetiresPreviousOwner() {
    qInfo() << "=== new owner reuses HWND ===";
    auto scenario = makeReusedOwnerScenario();
    checkCurrentOwnerState(scenario, "同值 HWND 保存新 owner 的真实旧样式");
    const QStringList callsAfterReplacement = scenario.platform->calls;
    CHECK(!NativeWindowTestAccess::finalizeOwner(
              *scenario.window, scenario.retiredOwner.get()),
          "旧 owner 迟到 finalize 被拒绝");
    CHECK(!NativeWindowTestAccess::attachOwner(
              *scenario.window, scenario.retiredOwner.get()),
          "旧 owner 迟到 attach 被拒绝");
    CHECK(NativeWindowTestAccess::detachOwner(
              *scenario.window, scenario.retiredOwner.get()),
          "旧 owner 显式 detach 幂等返回成功");
    CHECK(scenario.platform->calls == callsAfterReplacement,
          "旧 owner 迟到操作不调用原生平台");
    checkCurrentOwnerState(scenario, "旧 owner 操作不清新 owner 状态");
}

void testRetiredDestroyedGenerationDoesNotClearCurrentOwner() {
    qInfo() << "=== retired destroyed generation ===";
    auto scenario = makeReusedOwnerScenario();
    scenario.retiredOwner.reset();
    checkCurrentOwnerState(
        scenario,
        "旧 generation destroyed 回调不清新 owner 状态");
    scenario.currentOwner.reset();
    CHECK(NativeWindowTestAccess::stateMatches(
              *scenario.window, {}, {}, {}),
          "当前 owner destroyed 回调清理句柄状态");
}

void testUntrackedDetachDoesNotCreatePlatformWindow() {
    qInfo() << "=== untracked public detach is no-op ===";
    FakePlatform *platform = nullptr;
    auto nativeWindow = makeWindow(&platform);
    QWindow owner;
    CHECK(owner.handle() == nullptr, "测试窗口尚未创建 platform window");
    CHECK(NativeWindowTestAccess::detachOwner(*nativeWindow, &owner),
          "从未 attach 的 public detach 幂等成功");
    CHECK(owner.handle() == nullptr, "public detach 不反向创建 platform window");
    CHECK(platform->calls.isEmpty(), "未跟踪 detach 不调用原生平台");
}

void testDuplicateDetachDoesNotRecreatePlatformWindow() {
    qInfo() << "=== duplicate public detach is no-op ===";
    FakePlatform *platform = nullptr;
    auto nativeWindow = makeWindow(&platform);
    QWindow owner;
    platform->gets = {{true, kObservedStyle, 0}};
    platform->sets = {
        {true, kPreviousStyle, 0},
        {true, kObservedStyle, 0},
    };
    platform->frames = {{true, 0, 0}, {true, 0, 0}};
    CHECK(NativeWindowTestAccess::attachOwner(*nativeWindow, &owner),
          "public attach 创建并跟踪窗口");
    CHECK(NativeWindowTestAccess::detachOwner(*nativeWindow, &owner),
          "首次 public detach 成功");
    const QStringList callsAfterDetach = platform->calls;
    owner.destroy();
    CHECK(owner.handle() == nullptr, "显式 destroy 后 platform window 已释放");
    CHECK(NativeWindowTestAccess::detachOwner(*nativeWindow, &owner),
          "重复 public detach 幂等成功");
    CHECK(owner.handle() == nullptr, "重复 detach 不重建 platform window");
    CHECK(platform->calls == callsAfterDetach, "重复 detach 不调用原生平台");
}

QObject *prepareNativeWindowFake(QQmlEngine &engine,
                                 const QVariantList &outcomes) {
    const auto result = prism::test::createNativeWindowFake(engine, outcomes);
    if (result.status != QQmlComponent::Ready) {
        for (const QString &error : result.errors)
            qCritical() << error;
    }
    CHECK(result.status == QQmlComponent::Ready && result.object,
          "可控 NativeWindow fake 创建成功");
    return result.object;
}

void checkWindowsCoreConsumer(
    const prism::test::QmlCreationResult &result,
    const QStringList &messages, int expectedReadyCount) {
    const auto state =
        prism::test::inspectWindowsCoreConsumer(result.object, messages);
    CHECK(result.status == QQmlComponent::Ready, "WindowsCore 组件可创建");
    CHECK(result.object != nullptr, "WindowsCore 实例创建成功");
    CHECK(!state.missingFinalizeMethod, "C++ Host 不再缺少 finalizeAttach");
    CHECK(state.initializationDone, "原生初始化尝试完成");
    CHECK(state.showAnimationStarted, "原生增强结果不阻断首次显示启动");
    CHECK(state.opacityReady, "原生增强失败也不阻断窗口显示");
    CHECK(state.readyCount == expectedReadyCount,
          "nativeHookReady 只发布已提交成功");
}

void checkNativeWindowFake(QObject *fake, int expectedFinalizeCalls) {
    CHECK(fake->property("finalizeCalls").toInt() == expectedFinalizeCalls,
          "NativeWindow finalize 调用次数符合单次重试合同");
    CHECK(fake->property("detachCalls").toInt() == 1,
          "WindowsCore 析构恰好 detach 一次");
}

void exerciseRealWindowsCoreConsumer(const QString &qmlImportPath,
                                     const QVariantList &outcomes,
                                     int expectedFinalizeCalls,
                                     int expectedReadyCount,
                                     const char *scenario) {
    qInfo() << "=== registerTypes + WindowsCore real consumer ===" << scenario;
    QQmlEngine engine;
    prism::registerTypes(&engine, qmlImportPath);
    QObject *fake = prepareNativeWindowFake(engine, outcomes);
    if (!fake)
        return;
    engine.rootContext()->setContextProperty(QStringLiteral("NativeWindow"), fake);
    QStringList messages;
    {
        prism::test::QtMessageCapture capture(messages);
        const auto consumer = prism::test::createWindowsCoreConsumer(engine);
        checkWindowsCoreConsumer(consumer, messages, expectedReadyCount);
        prism::test::destroyQmlObject(consumer.object);
        checkNativeWindowFake(fake, expectedFinalizeCalls);
    }
    prism::test::destroyQmlObject(fake);
}

void testRealWindowsCoreConsumer(const QString &qmlImportPath) {
    exerciseRealWindowsCoreConsumer(
        qmlImportPath, QVariantList{true}, 1, 1, "success");
    exerciseRealWindowsCoreConsumer(
        qmlImportPath, QVariantList{false, false}, 2, 0,
        "persistent failure");
}

int runNativeWindowContracts(const QString &qmlImportPath) {
    testMetaObjectContract();
    testRawWinApiResultContract();
    testAttachFailureBoundaries();
    testFramechangedRetry();
    testDetachFailureBoundaries();
    testIdempotenceAndHwndReuse();
    testOwnerDetachUsesBoundHwnd();
    testOwnerHandleChangeRotatesGeneration();
    testNewOwnerReusingHwndRetiresPreviousOwner();
    testRetiredDestroyedGenerationDoesNotClearCurrentOwner();
    testUntrackedDetachDoesNotCreatePlatformWindow();
    testDuplicateDetachDoesNotRecreatePlatformWindow();
    if (qmlImportPath.isEmpty()) {
        qCritical() << "FAIL: missing QML import path";
        ++gFailures;
    } else {
        testRealWindowsCoreConsumer(qmlImportPath);
    }
    if (gFailures == 0) qInfo() << "NATIVE_WINDOW_CONTRACT_PASSED";
    return gFailures == 0 ? 0 : 1;
}

}  // namespace

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QTemporaryDir configDirectory;
    if (!configDirectory.isValid()) {
        qCritical() << "FAIL: unable to create isolated config directory";
        return 2;
    }
    const QString configPath =
        QDir(configDirectory.path()).filePath(QStringLiteral("app.json"));
    qputenv(prism::kConfigFilePathEnvironment, QFile::encodeName(configPath));
    QGuiApplication app(argc, argv);
    const QString qmlImportPath =
        argc >= 2 ? QString::fromLocal8Bit(argv[1]) : QString();
    return runNativeWindowContracts(qmlImportPath);
}
