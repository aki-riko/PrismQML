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

// Logger - 日志器类 (镜像 Python core/logger.py 的 Logger 单例)。
// C++ 侧日志核心是 prism::log:: 自由函数; Logger 类提供与 Python 对称的面向对象入口,
// 方法转发到 log:: 命名空间。直接用 prism::log::info(...) 亦可, 两者等价。
class Logger {
public:
    // 单例 (镜像 Python Logger.__new__ 单例)
    static Logger &instance() {
        static Logger s;
        return s;
    }

    void debug(const QString &msg, const QString &tag = QString()) const { log::debug(msg, tag); }
    void info(const QString &msg, const QString &tag = QString()) const { log::info(msg, tag); }
    void warning(const QString &msg, const QString &tag = QString()) const { log::warning(msg, tag); }
    void error(const QString &msg, const QString &tag = QString()) const { log::error(msg, tag); }
    void exception(const QString &msg, const QString &tag = QString()) const { log::exception(msg, tag); }

    void setLevel(log::Level level) const { log::setLevel(level); }
    void installQtMessageHandler() const { log::installQtMessageHandler(); }

private:
    Logger() = default;
};

// getLogger - 取日志器单例 (镜像 Python getLogger)。
inline Logger &getLogger() { return Logger::instance(); }

}  // namespace prism
