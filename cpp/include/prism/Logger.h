// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Logger 日志系统 (镜像 Python core/logger.py)
#pragma once

#include <QString>

namespace prism {
namespace log {

enum class Level { Debug = 0, Info = 1, Warning = 2, Error = 3 };

// 全局日志函数 (镜像 Python debug/info/warning/error/exception)
void debug(const QString &msg, const QString &tag = QString());
void info(const QString &msg, const QString &tag = QString());
void warning(const QString &msg, const QString &tag = QString());
void error(const QString &msg, const QString &tag = QString());
void exception(const QString &msg, const QString &tag = QString());

void setLevel(Level level);

// 安装 Qt 消息处理器: 把 QML/Qt 日志重定向到统一格式 (镜像 install_qt_message_handler)
void installQtMessageHandler();

}  // namespace log
}  // namespace prism
