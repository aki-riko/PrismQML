// coding: utf-8
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Native fatal-process fixture. 原生致命进程夹具。

#include <QtCore/qlogging.h>
#include <QtCore/qstring.h>

#include <windows.h>

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace {

constexpr DWORD kFixtureFailureExitCode = 70;
constexpr DWORD kChildShutdownWaitMilliseconds = 5000;
constexpr DWORD kStatusFailFastException = 0xC0000602U;
constexpr char kDesktopPrefix[] = "PrismQMLTest-";
constexpr char kJobPrefix[] = "PrismQMLTestJob-";

bool utf8Text(const wchar_t *value, std::string &text) {
    const int requiredChars = WideCharToMultiByte(
        CP_UTF8, 0, value, -1, nullptr, 0, nullptr, nullptr);
    if (requiredChars <= 1) return false;
    std::vector<char> buffer(static_cast<size_t>(requiredChars));
    if (!WideCharToMultiByte(CP_UTF8, 0, value, -1, buffer.data(),
                             requiredChars, nullptr, nullptr)) {
        return false;
    }
    text.assign(buffer.data());
    return true;
}

bool desktopName(DWORD threadId, std::string &name) {
    HDESK desktop = GetThreadDesktop(threadId);
    if (desktop == nullptr) return false;
    DWORD requiredBytes = 0;
    GetUserObjectInformationW(desktop, UOI_NAME, nullptr, 0, &requiredBytes);
    if (requiredBytes == 0) return false;
    std::vector<wchar_t> wideName(
        (requiredBytes + sizeof(wchar_t) - 1) / sizeof(wchar_t));
    if (!GetUserObjectInformationW(desktop, UOI_NAME, wideName.data(),
                                   requiredBytes, &requiredBytes)) {
        return false;
    }
    return utf8Text(wideName.data(), name);
}

bool processInBoundaryJob(HANDLE process, const std::string &desktop,
                          std::string &jobName) {
    if (desktop.rfind(kDesktopPrefix, 0) != 0) return false;
    jobName = kJobPrefix + desktop.substr(sizeof(kDesktopPrefix) - 1);
    const std::wstring wideJobName(jobName.begin(), jobName.end());
    HANDLE job = OpenJobObjectW(JOB_OBJECT_QUERY, FALSE, wideJobName.c_str());
    if (job == nullptr) return false;
    BOOL inJob = FALSE;
    const bool queried = IsProcessInJob(process, job, &inJob) && inJob;
    const bool closed = CloseHandle(job) != FALSE;
    return queried && closed;
}

bool writeBoundaryMarker(const wchar_t *mode) {
    std::string desktop;
    std::string jobName;
    std::string modeName;
    const bool hasDesktop = desktopName(GetCurrentThreadId(), desktop);
    const bool hasMode = utf8Text(mode, modeName);
    const bool inJob = hasDesktop && processInBoundaryJob(
        GetCurrentProcess(), desktop, jobName);
    std::fprintf(
        stderr,
        "PRISM_NATIVE_FAILURE mode=%s pid=%lu desktop=%s job=%s in_job=%d "
        "error_mode=0x%X\n",
        hasMode ? modeName.c_str() : "<error>", GetCurrentProcessId(),
        hasDesktop ? desktop.c_str() : "<error>",
        inJob ? jobName.c_str() : "<error>", inJob ? 1 : 0,
        GetErrorMode());
    std::fflush(stderr);
    return hasDesktop && hasMode && inJob;
}

std::wstring quoted(const std::wstring &value) {
    return L"\"" + value + L"\"";
}

bool createSuspendedChild(const std::wstring &executable,
                          const std::wstring &argument,
                          const std::string &desktop,
                          PROCESS_INFORMATION &child) {
    std::wstring commandLine = quoted(executable);
    if (!argument.empty()) commandLine += L" " + quoted(argument);
    std::vector<wchar_t> mutableCommand(commandLine.begin(), commandLine.end());
    mutableCommand.push_back(L'\0');
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    const std::wstring requestedDesktop(desktop.begin(), desktop.end());
    startup.lpDesktop = const_cast<wchar_t *>(requestedDesktop.c_str());
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    if (!CreateProcessW(executable.c_str(), mutableCommand.data(), nullptr,
                        nullptr, TRUE, CREATE_SUSPENDED, nullptr, nullptr,
                        &startup, &child)) {
        std::fprintf(stderr, "PRISM_NATIVE_SPAWN create_error=%lu\n",
                     GetLastError());
        return false;
    }
    return true;
}

bool closeChild(PROCESS_INFORMATION &child) {
    bool closed = true;
    if (!CloseHandle(child.hThread)) {
        std::fprintf(stderr,
                     "PRISM_NATIVE_CLEANUP handle=thread close_error=%lu\n",
                     GetLastError());
        closed = false;
    }
    if (!CloseHandle(child.hProcess)) {
        std::fprintf(stderr,
                     "PRISM_NATIVE_CLEANUP handle=process close_error=%lu\n",
                     GetLastError());
        closed = false;
    }
    if (!closed) std::fflush(stderr);
    child = {};
    return closed;
}

int stopInvalidChild(PROCESS_INFORMATION &child) {
    if (!TerminateProcess(child.hProcess, kFixtureFailureExitCode)) {
        std::fprintf(stderr, "PRISM_NATIVE_SPAWN terminate_error=%lu\n",
                     GetLastError());
        closeChild(child);
        return static_cast<int>(kFixtureFailureExitCode);
    }
    const DWORD waitResult = WaitForSingleObject(
        child.hProcess, kChildShutdownWaitMilliseconds);
    if (waitResult != WAIT_OBJECT_0) {
        std::fprintf(stderr, "PRISM_NATIVE_SPAWN terminate_wait=%lu\n",
                     waitResult);
    }
    closeChild(child);
    return static_cast<int>(kFixtureFailureExitCode);
}

[[noreturn]] void propagateChildExit(PROCESS_INFORMATION &child) {
    const DWORD waitResult = WaitForSingleObject(child.hProcess, INFINITE);
    DWORD childExitCode = kFixtureFailureExitCode;
    if (waitResult != WAIT_OBJECT_0 ||
        !GetExitCodeProcess(child.hProcess, &childExitCode)) {
        childExitCode = kFixtureFailureExitCode;
    }
    if (!closeChild(child)) childExitCode = kFixtureFailureExitCode;
    ExitProcess(childExitCode);
}

int spawnAndPropagate(const std::wstring &executable,
                      const std::wstring &argument) {
    std::string currentDesktop;
    if (!desktopName(GetCurrentThreadId(), currentDesktop)) {
        return static_cast<int>(kFixtureFailureExitCode);
    }
    PROCESS_INFORMATION child{};
    if (!createSuspendedChild(executable, argument, currentDesktop, child)) {
        return static_cast<int>(kFixtureFailureExitCode);
    }
    std::string jobName;
    const bool childInJob = processInBoundaryJob(
        child.hProcess, currentDesktop, jobName);
    std::fprintf(stderr,
                 "PRISM_NATIVE_SPAWN parent_pid=%lu child_pid=%lu "
                 "requested_desktop=%s job=%s child_in_job=%d\n",
                 GetCurrentProcessId(), child.dwProcessId,
                 currentDesktop.c_str(),
                 childInJob ? jobName.c_str() : "<error>",
                 childInJob ? 1 : 0);
    std::fflush(stderr);
    if (!childInJob || ResumeThread(child.hThread) == DWORD(-1)) {
        return stopInvalidChild(child);
    }
    propagateChildExit(child);
}

std::wstring modulePath() {
    std::vector<wchar_t> buffer(32768);
    const DWORD length = GetModuleFileNameW(
        nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (length == 0 || length >= buffer.size()) return {};
    return std::wstring(buffer.data(), length);
}

void writeTriggerMarker(const char *mode) {
    std::fprintf(stderr, "PRISM_NATIVE_TRIGGER mode=%s pid=%lu\n", mode,
                 GetCurrentProcessId());
    std::fflush(stderr);
}

void writeQtMessage(QtMsgType type, const QMessageLogContext &,
                    const QString &message) {
    const QByteArray utf8 = message.toUtf8();
    std::fprintf(stderr,
                 "PRISM_NATIVE_QT_MESSAGE type=%s pid=%lu message=%s\n",
                 type == QtFatalMsg ? "fatal" : "unexpected",
                 GetCurrentProcessId(), utf8.constData());
    std::fflush(stderr);
}

int triggerFatalMode(const std::wstring &mode) {
    if (mode == L"abort") {
        writeTriggerMarker("abort");
        std::abort();
    }
    if (mode == L"qfatal") {
        writeTriggerMarker("qfatal");
        qInstallMessageHandler(writeQtMessage);
        qFatal("PRISM_NATIVE_QFATAL_SENTINEL");
    }
    if (mode == L"access-violation") {
        writeTriggerMarker("access-violation");
        RaiseException(EXCEPTION_ACCESS_VIOLATION, EXCEPTION_NONCONTINUABLE,
                       0, nullptr);
    }
    if (mode == L"fail-fast") {
        writeTriggerMarker("fail-fast");
        EXCEPTION_RECORD record{};
        record.ExceptionCode = kStatusFailFastException;
        record.ExceptionFlags = EXCEPTION_NONCONTINUABLE;
        RaiseFailFastException(&record, nullptr, 0);
    }
    return static_cast<int>(kFixtureFailureExitCode);
}

}  // namespace

int wmain(int argc, wchar_t *argv[]) {
    if (argc < 2 || !writeBoundaryMarker(argv[1])) {
        return static_cast<int>(kFixtureFailureExitCode);
    }
    const std::wstring mode = argv[1];
    if (mode == L"spawn-self" && argc == 3) {
        const std::wstring executable = modulePath();
        return executable.empty()
                   ? static_cast<int>(kFixtureFailureExitCode)
                   : spawnAndPropagate(executable, argv[2]);
    }
    if (mode == L"spawn-executable" && argc == 3) {
        return spawnAndPropagate(argv[2], L"");
    }
    return triggerFatalMode(mode);
}
