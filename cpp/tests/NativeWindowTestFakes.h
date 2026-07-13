// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// NativeWindow injectable test doubles. NativeWindow 可注入测试替身。
#pragma once

#include "NativeWindow_p.h"

#include <QList>
#include <QStringList>
#include <optional>

namespace prism::test {

inline constexpr quint32 kUnexpectedNativeWindowError = 1400;

struct NativeWindowOutcome {
    bool success = true;
    qlonglong value = 0;
    quint32 error = 0;
};

class FakeNativeWindowPlatform final : public NativeWindowPlatform {
public:
    QList<NativeWindowOutcome> gets;
    QList<NativeWindowOutcome> sets;
    QList<NativeWindowOutcome> frames;
    QStringList calls;

    bool getStyle(qulonglong hwnd, qlonglong *style,
                  quint32 *errorCode) override {
        calls.append(QStringLiteral("get:%1").arg(hwnd));
        const NativeWindowOutcome outcome = take(gets, QStringLiteral("get"));
        *style = outcome.value;
        *errorCode = outcome.error;
        return outcome.success;
    }

    bool setStyle(qulonglong hwnd, qlonglong style, qlonglong *previousStyle,
                  quint32 *errorCode) override {
        calls.append(QStringLiteral("set:%1:%2").arg(hwnd).arg(style));
        const NativeWindowOutcome outcome = take(sets, QStringLiteral("set"));
        *previousStyle = outcome.value;
        *errorCode = outcome.error;
        return outcome.success;
    }

    bool applyFrameChanged(qulonglong hwnd, quint32 *errorCode) override {
        calls.append(QStringLiteral("frame:%1").arg(hwnd));
        const NativeWindowOutcome outcome = take(frames, QStringLiteral("frame"));
        *errorCode = outcome.error;
        return outcome.success;
    }

private:
    NativeWindowOutcome take(QList<NativeWindowOutcome> &outcomes,
                             const QString &operation) {
        if (!outcomes.isEmpty())
            return outcomes.takeFirst();
        calls.append(QStringLiteral("unexpected:%1").arg(operation));
        return {false, 0, kUnexpectedNativeWindowError};
    }
};

struct NativeWindowRawOutcome {
    qlonglong value = 0;
    std::optional<quint32> error;
};

class FakeNativeWindowRawApi final : public NativeWindowRawApi {
public:
    QList<NativeWindowRawOutcome> gets;
    QList<NativeWindowRawOutcome> sets;
    QList<NativeWindowRawOutcome> frames;
    QStringList calls;
    quint32 error = kUnexpectedNativeWindowError;

    void clearLastError() override {
        calls.append(QStringLiteral("clear"));
        error = 0;
    }

    quint32 lastError() override {
        calls.append(QStringLiteral("last"));
        return error;
    }

    qlonglong getWindowLongPtr(qulonglong hwnd) override {
        calls.append(QStringLiteral("get:%1").arg(hwnd));
        return take(gets, QStringLiteral("get")).value;
    }

    qlonglong setWindowLongPtr(qulonglong hwnd, qlonglong style) override {
        calls.append(QStringLiteral("set:%1:%2").arg(hwnd).arg(style));
        return take(sets, QStringLiteral("set")).value;
    }

    bool setWindowPos(qulonglong hwnd) override {
        calls.append(QStringLiteral("frame:%1").arg(hwnd));
        return take(frames, QStringLiteral("frame")).value != 0;
    }

private:
    NativeWindowRawOutcome take(QList<NativeWindowRawOutcome> &outcomes,
                                const QString &operation) {
        if (outcomes.isEmpty()) {
            calls.append(QStringLiteral("unexpected:%1").arg(operation));
            error = kUnexpectedNativeWindowError;
            return {};
        }
        const NativeWindowRawOutcome outcome = outcomes.takeFirst();
        if (outcome.error.has_value())
            error = outcome.error.value();
        return outcome;
    }
};

}  // namespace prism::test
