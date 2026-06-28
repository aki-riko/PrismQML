// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Logger 实现 (镜像 Python core/logger.py)
#include "prism/Logger.h"

#include <QDateTime>
#include <QTextStream>
#include <QtGlobal>
#include <cstdio>

namespace prism {
namespace log {

namespace {
Level g_level = Level::Debug;

// ANSI 颜色 (镜像 Python Colors)
const char *kReset = "\033[0m";
const char *levelColor(Level lv) {
    switch (lv) {
        case Level::Debug:   return "\033[36m";  // cyan
        case Level::Info:    return "\033[32m";  // green
        case Level::Warning: return "\033[33m";  // yellow
        case Level::Error:   return "\033[31m";  // red
    }
    return "";
}
const char *levelName(Level lv) {
    switch (lv) {
        case Level::Debug:   return "DEBUG";
        case Level::Info:    return "INFO";
        case Level::Warning: return "WARN";
        case Level::Error:   return "ERROR";
    }
    return "";
}

void emitLog(Level lv, const QString &msg, const QString &tag) {
    if (static_cast<int>(lv) < static_cast<int>(g_level))
        return;
    const QString ts = QDateTime::currentDateTime().toString(QStringLiteral("HH:mm:ss"));
    const QString tagPart = tag.isEmpty() ? QString() : QStringLiteral("[%1] ").arg(tag);
    // 输出到 stderr (与 Qt 默认一致), 带颜色
    fprintf(stderr, "%s%s %-5s%s %s%s\n",
            levelColor(lv), ts.toUtf8().constData(), levelName(lv), kReset,
            (tagPart + msg).toUtf8().constData(), "");
    fflush(stderr);
}
}  // namespace

void debug(const QString &msg, const QString &tag)   { emitLog(Level::Debug, msg, tag); }
void info(const QString &msg, const QString &tag)    { emitLog(Level::Info, msg, tag); }
void warning(const QString &msg, const QString &tag) { emitLog(Level::Warning, msg, tag); }
void error(const QString &msg, const QString &tag)   { emitLog(Level::Error, msg, tag); }
void exception(const QString &msg, const QString &tag) { emitLog(Level::Error, msg, tag); }

void setLevel(Level level) { g_level = level; }

// Qt 消息处理: 把 QML/Qt 日志映射到统一格式 (镜像 install_qt_message_handler)
static void qtMessageHandler(QtMsgType type, const QMessageLogContext &ctx, const QString &message) {
    QString tag = QStringLiteral("Qt");
    if (ctx.category && qstrcmp(ctx.category, "default") != 0)
        tag = QString::fromUtf8(ctx.category);
    switch (type) {
        case QtDebugMsg:    debug(message, tag); break;
        case QtInfoMsg:     info(message, tag); break;
        case QtWarningMsg:  warning(message, tag); break;
        case QtCriticalMsg: error(message, tag); break;
        case QtFatalMsg:    error(message, tag); break;
    }
}

void installQtMessageHandler() {
    qInstallMessageHandler(qtMessageHandler);
}

}  // namespace log
}  // namespace prism
