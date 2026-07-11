// coding: utf-8
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Non-interactive native test bootstrap. 原生测试无交互启动保护。
#pragma once

#ifdef _WIN32
#include <cstdlib>
#include <cstdio>
#ifdef _DEBUG
#include <crtdbg.h>
#endif
#include <windows.h>
#include <werapi.h>
#endif

namespace prism::test {

#ifdef _WIN32
inline bool configureCrtReporting() {
    _set_error_mode(_OUT_TO_STDERR);
    if (_set_error_mode(_REPORT_ERRMODE) != _OUT_TO_STDERR) {
        std::fprintf(stderr, "Windows CRT stderr mode was not applied\n");
        return false;
    }
#ifdef _DEBUG
    constexpr int reportTypes[] = {_CRT_WARN, _CRT_ERROR, _CRT_ASSERT};
    for (const int reportType : reportTypes) {
        _CrtSetReportFile(reportType, _CRTDBG_FILE_STDERR);
        _CrtSetReportMode(reportType, _CRTDBG_MODE_FILE);
        if (_CrtSetReportMode(reportType, _CRTDBG_REPORT_MODE) !=
            _CRTDBG_MODE_FILE) {
            std::fprintf(stderr, "Windows Debug CRT report mode failed\n");
            return false;
        }
    }
#endif
    return true;
}

inline bool configureWindowsErrorPolicy() {
    DWORD werFlags = 0;
    HRESULT result = WerGetFlags(GetCurrentProcess(), &werFlags);
    if (result == HRESULT_FROM_WIN32(ERROR_NOT_FOUND)) {
        werFlags = 0;
    } else if (FAILED(result)) {
        std::fprintf(stderr, "WerGetFlags failed: 0x%08lX\n",
                     static_cast<unsigned long>(result));
        return false;
    }

    werFlags &= ~WER_FAULT_REPORTING_ALWAYS_SHOW_UI;
    werFlags |= WER_FAULT_REPORTING_FLAG_QUEUE | WER_FAULT_REPORTING_NO_UI;
    result = WerSetFlags(werFlags);
    if (FAILED(result)) {
        std::fprintf(stderr, "WerSetFlags failed: 0x%08lX\n",
                     static_cast<unsigned long>(result));
        return false;
    }

    constexpr UINT requiredErrorMode =
        SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX;
    SetErrorMode(GetErrorMode() | requiredErrorMode);
    if ((GetErrorMode() & requiredErrorMode) != requiredErrorMode) {
        std::fprintf(stderr, "Windows test error mode was not applied\n");
        return false;
    }
    return true;
}
#endif

inline bool configureNonInteractiveProcess() {
#ifdef _WIN32
    return configureCrtReporting() && configureWindowsErrorPolicy();
#else
    return true;
#endif
}

}  // namespace prism::test
