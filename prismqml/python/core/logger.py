# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
FluentQML Logger - 统一日志组件 Unified logging component

功能 Features:
- 时间戳（精确到毫秒）Timestamp (millisecond precision)
- 自动模块标签 Auto module tag from filename
- 彩色终端输出 Colored terminal output (Windows compatible)
- 多级别日志 Multi-level logging (DEBUG/INFO/WARNING/ERROR)
- 日志轮转 Log rotation support
- 异常堆栈追踪 Exception stack trace
"""

import os
import sys
import logging
import traceback
import time

# 模块加载时记录初始时间（供性能测试用）
_start_time = time.perf_counter()
from typing import Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ==================== Color Support 彩色支持 ====================


# ANSI color codes ANSI颜色码
class Colors:
    """Terminal color codes 终端颜色码"""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Log level colors 日志级别颜色
    DEBUG = "\033[36m"  # Cyan 青色
    INFO = "\033[32m"  # Green 绿色
    WARNING = "\033[33m"  # Yellow 黄色
    ERROR = "\033[31m"  # Red 红色

    # Component colors 组件颜色
    TAG = "\033[35m"  # Magenta 洋红
    TIME = "\033[90m"  # Gray 灰色


def _enable_windows_ansi():
    """Enable ANSI color support on Windows 在Windows上启用ANSI颜色支持"""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            # Windows 控制台常量
            STD_OUTPUT_HANDLE = -11
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

            # 先读取当前控制台模式，再 OR 上 VT 标志，避免覆盖其他设置
            mode = wintypes.DWORD()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, new_mode)
        except (OSError, AttributeError):
            # Console mode not available, ignore 控制台模式不可用
            pass


# Enable on import 导入时启用
_enable_windows_ansi()


# ==================== Color Formatter 彩色格式化器 ====================


class ColoredFormatter(logging.Formatter):
    """Colored log formatter 彩色日志格式化器"""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Get level color 获取级别颜色
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)

        # Format: TIME [LEVEL] [TAG] message
        time_str = f"{Colors.TIME}{self.formatTime(record, self.datefmt)}.{int(record.msecs):03d}{Colors.RESET}"
        level_str = f"{level_color}[{record.levelname}]{Colors.RESET}"

        # Tag from record (set by Logger)
        tag = getattr(record, "tag", "")
        tag_str = f"{Colors.TAG}[{tag}]{Colors.RESET} " if tag else ""

        return f"{time_str} {level_str} {tag_str}{record.getMessage()}"


class PlainFormatter(logging.Formatter):
    """Plain log formatter for file output 文件输出的纯文本格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        time_str = f"{self.formatTime(record, self.datefmt)}.{int(record.msecs):03d}"
        tag = getattr(record, "tag", "")
        tag_str = f"[{tag}] " if tag else ""
        return f"{time_str} [{record.levelname}] {tag_str}{record.getMessage()}"


# ==================== Module Tag Mapping 模块标签映射 ====================

# Filename to tag mapping 文件名到标签的映射
MODULE_TAGS = {
    "shadow.py": "Shadow",
    "mica_window.py": "Mica",
    "theme.py": "Theme",
    "window.py": "Window",
    "qrcode_generator.py": "QRCode",
    "dpi.py": "DPI",
    "settings_base.py": "Config",
    "config_manager.py": "Config",
    "app_config.py": "Config",
    "config_item.py": "Config",
    "validators.py": "Config",
    "clipboard.py": "Clipboard",
    "screen_eyedropper.py": "Eyedropper",
    "svg_provider.py": "SVG",
    "layout.py": "Layout",
    "widgets.py": "Widgets",
    "components.py": "Components",
    "common.py": "Common",
    "utils.py": "Utils",
}


def _get_module_tag(filename: str) -> str:
    """Get module tag from filename 从文件名获取模块标签"""
    # Check mapping first 先检查映射
    if filename in MODULE_TAGS:
        return MODULE_TAGS[filename]

    # Auto-generate from filename 从文件名自动生成
    # shadow.py -> Shadow, mica_window.py -> MicaWindow
    name = Path(filename).stem
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts)


# ==================== Logger Class ====================


class Logger:
    """FluentQML统一日志组件 Unified logging component"""

    # Log levels 日志级别
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    # Singleton 单例
    _instance: Optional["Logger"] = None
    _initialized: bool = False

    # Default config 默认配置
    DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5MB
    DEFAULT_BACKUP_COUNT = 3

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "FluentQML",
        log_file: Optional[str] = None,
        level: int = logging.DEBUG,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        colored: bool = True,
    ):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        self._colored = colored

        # Console handler 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        if colored:
            console_handler.setFormatter(ColoredFormatter(datefmt="%H:%M:%S"))
        else:
            console_handler.setFormatter(PlainFormatter(datefmt="%H:%M:%S"))
        self.logger.addHandler(console_handler)

        # File handler with rotation 带轮转的文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(PlainFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
            self.logger.addHandler(file_handler)

        self._initialized = True

    def _get_caller_tag(self, stack_level: int = 4) -> str:
        """Get module tag from caller 从调用者获取模块标签"""
        try:
            stack = traceback.extract_stack()
            # Find first frame outside logger.py
            for frame in reversed(stack[:-stack_level]):
                filename = Path(frame.filename).name
                if filename != "logger.py":
                    return _get_module_tag(filename)
            return "Unknown"
        except (IndexError, ValueError):
            # Stack trace unavailable 堆栈不可用
            return "Unknown"

    def _log(
        self, level: int, msg: str, tag: Optional[str] = None, exc_info: bool = False
    ):
        """Internal log method 内部日志方法"""
        # Auto tag if not provided 未提供则自动标签
        if tag is None:
            tag = self._get_caller_tag()

        # Create log record with tag 创建带标签的日志记录
        extra = {"tag": tag}
        self.logger.log(level, msg, exc_info=exc_info, extra=extra)

    def debug(self, msg: str, tag: Optional[str] = None):
        """DEBUG level log DEBUG级别日志"""
        self._log(logging.DEBUG, msg, tag)

    def info(self, msg: str, tag: Optional[str] = None):
        """INFO level log INFO级别日志"""
        self._log(logging.INFO, msg, tag)

    def warning(self, msg: str, tag: Optional[str] = None):
        """WARNING level log WARNING级别日志"""
        self._log(logging.WARNING, msg, tag)

    def error(self, msg: str, tag: Optional[str] = None, exc_info: bool = False):
        """ERROR level log ERROR级别日志"""
        self._log(logging.ERROR, msg, tag, exc_info=exc_info)

    def exception(self, msg: str, tag: Optional[str] = None):
        """Exception log with stack trace 带堆栈的异常日志"""
        self._log(logging.ERROR, msg, tag, exc_info=True)

    def set_level(self, level: int):
        """Set log level 设置日志级别"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# ==================== Global Singleton 全局单例 ====================

_logger: Optional[Logger] = None


def getLogger(
    name: str = "FluentQML",
    log_file: Optional[str] = None,
    level: int = logging.DEBUG,
    colored: bool = True,
) -> Logger:
    """Get logger singleton 获取日志单例"""
    global _logger
    if _logger is None:
        _logger = Logger(name, log_file, level, colored=colored)
    return _logger


# ==================== Convenience Functions 便捷函数 ====================


def debug(msg: str, tag: Optional[str] = None):
    """DEBUG log DEBUG日志"""
    getLogger().debug(msg, tag)


def info(msg: str, tag: Optional[str] = None):
    """INFO log INFO日志"""
    getLogger().info(msg, tag)


def warning(msg: str, tag: Optional[str] = None):
    """WARNING log WARNING日志"""
    getLogger().warning(msg, tag)


def error(msg: str, tag: Optional[str] = None, exc_info: bool = False):
    """ERROR log ERROR日志"""
    getLogger().error(msg, tag, exc_info)


def exception(msg: str, tag: Optional[str] = None):
    """Exception log with stack trace 带堆栈的异常日志"""
    getLogger().exception(msg, tag)


def set_level(level: int):
    """Set global log level 设置全局日志级别"""
    getLogger().set_level(level)


def log_time(msg: str) -> None:
    """Print log with millisecond timestamp since module load 打印带模块加载以来毫秒时间戳的性能日志"""
    elapsed = (time.perf_counter() - _start_time) * 1000
    print(f"[{elapsed:8.2f}ms] {msg}")


# ==================== Qt Message Handler Qt消息处理器 ====================


def install_qt_message_handler():
    """Install Qt message handler to redirect QML/Qt logs to project logger
    安装Qt消息处理程序，将QML/Qt日志重定向到项目日志
    """
    try:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType

        # Level mapping 级别映射
        # Map Qt message types to Python logging levels
        level_map = {
            QtMsgType.QtDebugMsg: logging.DEBUG,
            QtMsgType.QtInfoMsg: logging.INFO,
            QtMsgType.QtWarningMsg: logging.WARNING,
            QtMsgType.QtCriticalMsg: logging.ERROR,
            QtMsgType.QtFatalMsg: logging.CRITICAL,
        }

        # Category mapping for better tags 类别映射，提供更好的标签
        # Some common QML categories
        category_tags = {
            "js": "QML:JS",
            "qml": "QML",
            "default": "QML",
        }

        def qt_message_handler(mode, context, message):
            # Skip empty messages 忽略空消息
            if not message:
                return

            # Map level 获取映射级别
            level = level_map.get(mode, logging.INFO)

            # Determine tag 确定标签
            category = context.category.lower() if context.category else "qml"
            tag = category_tags.get(category, f"QML:{category.upper()}")

            # Clean message (remove trailing newlines) 清理消息
            clean_msg = message.strip()

            # Log it 使用内部_log方法
            getLogger()._log(level, clean_msg, tag=tag)

        qInstallMessageHandler(qt_message_handler)
        # info("Qt message handler installed", tag="Logger")
    except ImportError:
        # If PySide6 is not available, just ignore (this satisfies rules about safety)
        pass
    except Exception as e:
        # Use existing logger to report error
        getLogger().error(f"Failed to install Qt message handler: {e}", tag="Logger")
