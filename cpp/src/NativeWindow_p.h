// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#pragma once

#include <QtGlobal>
#include <memory>

namespace prism {

constexpr bool nativeLongPtrCallSucceeded(qlonglong result,
                                          quint32 errorCode) noexcept {
    return result != 0 || errorCode == 0;
}

class NativeWindowPlatform {
public:
    virtual ~NativeWindowPlatform() = default;

    virtual bool getStyle(qulonglong hwnd, qlonglong *style,
                          quint32 *errorCode) = 0;
    virtual bool setStyle(qulonglong hwnd, qlonglong style,
                          qlonglong *previousStyle, quint32 *errorCode) = 0;
    virtual bool applyFrameChanged(qulonglong hwnd, quint32 *errorCode) = 0;
};

class NativeWindowRawApi {
public:
    virtual ~NativeWindowRawApi() = default;

    virtual void clearLastError() = 0;
    virtual quint32 lastError() = 0;
    virtual qlonglong getWindowLongPtr(qulonglong hwnd) = 0;
    virtual qlonglong setWindowLongPtr(qulonglong hwnd, qlonglong style) = 0;
    virtual bool setWindowPos(qulonglong hwnd) = 0;
};

class CheckedNativeWindowPlatform final : public NativeWindowPlatform {
public:
    explicit CheckedNativeWindowPlatform(
        std::unique_ptr<NativeWindowRawApi> rawApi);
    ~CheckedNativeWindowPlatform() override;

    bool getStyle(qulonglong hwnd, qlonglong *style,
                  quint32 *errorCode) override;
    bool setStyle(qulonglong hwnd, qlonglong style,
                  qlonglong *previousStyle, quint32 *errorCode) override;
    bool applyFrameChanged(qulonglong hwnd, quint32 *errorCode) override;

private:
    std::unique_ptr<NativeWindowRawApi> m_rawApi;
};

}  // namespace prism
