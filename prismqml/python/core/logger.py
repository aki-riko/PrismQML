# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML Logger - 统一日志组件 Unified logging component

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
from collections import deque

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
        except (OSError, AttributeError) as exc:
            # Console mode not available, ignore 控制台模式不可用
            logging.getLogger(__name__).debug("Windows ANSI console mode unavailable: %s", exc)


# Enable on import 导入时启用
_enable_windows_ansi()


# ==================== Color Formatter 彩色格式化器 ====================


def _append_exception_text(
    formatter: logging.Formatter, record: logging.LogRecord, rendered: str
) -> str:
    """Append a formatted exception traceback. 追加格式化异常堆栈。"""
    if record.exc_info and not record.exc_text:
        record.exc_text = formatter.formatException(record.exc_info)
    if not record.exc_text:
        return rendered
    return f"{rendered}\n{record.exc_text}"


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

        rendered = f"{time_str} {level_str} {tag_str}{record.getMessage()}"
        return _append_exception_text(self, record, rendered)


class PlainFormatter(logging.Formatter):
    """Plain log formatter for file output 文件输出的纯文本格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        time_str = f"{self.formatTime(record, self.datefmt)}.{int(record.msecs):03d}"
        tag = getattr(record, "tag", "")
        tag_str = f"[{tag}] " if tag else ""
        rendered = f"{time_str} [{record.levelname}] {tag_str}{record.getMessage()}"
        return _append_exception_text(self, record, rendered)


# ==================== Module Tag Mapping 模块标签映射 ====================

# Filename to tag mapping 文件名到标签的映射
MODULE_TAGS = {
    "shadow.py": "Shadow",
    "mica_window.py": "Mica",
    "theme.py": "Theme",
    "window.py": "Window",
    "qrcode_generator.py": "QRCode",
    "dpi.py": "DPI",
    "settings_core.py": "Config",
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


def _create_console_handler(level: int, colored: bool) -> logging.StreamHandler:
    """Create the configured console handler. 创建已配置的控制台处理器。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter_type = ColoredFormatter if colored else PlainFormatter
    handler.setFormatter(formatter_type(datefmt="%H:%M:%S"))
    return handler


def _create_rotating_file_handler(
    log_file: str, level: int, max_bytes: int, backup_count: int
) -> RotatingFileHandler:
    """Create the configured rotating file handler. 创建已配置的轮转文件处理器。"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(PlainFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    return handler


# ==================== Logger Class ====================


class Logger:
    """PrismQML统一日志组件 Unified logging component"""

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
        name: str = "PrismQML",
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

        self.logger.addHandler(_create_console_handler(level, colored))

        # File handler with rotation 带轮转的文件处理器
        if log_file:
            self.logger.addHandler(
                _create_rotating_file_handler(
                    log_file, level, max_bytes, backup_count
                )
            )

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
    name: str = "PrismQML",
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

_QT_CONTEXT_TEXT_LIMIT = 240
_QT_BREADCRUMB_CAPACITY = 32
_QT_BREADCRUMB_REPLAY_LIMIT = 12
_QT_BREADCRUMB_PREFIXES = ("[懒加载诊断]", "[启动剖析]")


def _shorten_qt_context_value(value) -> str:
    """Bound and escape Qt context text. 限制并转义 Qt 上下文文本。"""
    text = str(value or "<unknown>").replace("\x00", "\\0")
    if len(text) <= _QT_CONTEXT_TEXT_LIMIT:
        return text
    return f"{text[:_QT_CONTEXT_TEXT_LIMIT]}..."


def _qt_message_context(context) -> str:
    """Format source metadata carried by QMessageLogContext. 格式化 Qt 源信息。"""
    return (
        "[QtContext] "
        f"category={_shorten_qt_context_value(getattr(context, 'category', None))} "
        f"file={_shorten_qt_context_value(getattr(context, 'file', None))} "
        f"line={getattr(context, 'line', 0) or 0} "
        f"function={_shorten_qt_context_value(getattr(context, 'function', None))}"
    )


def _qt_message_tag(context) -> str:
    """Resolve the project tag for a Qt message. 解析 Qt 消息项目标签。"""
    category = context.category.lower() if context.category else "qml"
    category_tags = {"js": "QML:JS", "qml": "QML", "default": "QML"}
    return category_tags.get(category, f"QML:{category.upper()}")


def _is_qt_source_location_only_message(context, message: str) -> bool:
    """Detect a QML warning that contains only its source location. 识别只含源码位置的 QML 警告。"""
    source_file = getattr(context, "file", None)
    source_line = getattr(context, "line", 0) or 0
    if not source_file or not source_line:
        return False

    prefix = f"{source_file}:{source_line}:"
    if not message.startswith(prefix):
        return False

    column, separator, body = message[len(prefix) :].partition(":")
    return bool(separator) and column.isdigit() and not body.strip()


def _create_qt_message_handler(qt_msg_type):
    """Create the Qt-to-project logger callback. 创建 Qt 到项目日志的回调。"""
    level_map = {
        qt_msg_type.QtDebugMsg: logging.DEBUG,
        qt_msg_type.QtInfoMsg: logging.INFO,
        qt_msg_type.QtWarningMsg: logging.WARNING,
        qt_msg_type.QtCriticalMsg: logging.ERROR,
        qt_msg_type.QtFatalMsg: logging.CRITICAL,
    }
    breadcrumbs = deque(maxlen=_QT_BREADCRUMB_CAPACITY)
    breadcrumb_version = 0
    replayed_version = -1

    def qt_message_handler(mode, context, message):
        nonlocal breadcrumb_version, replayed_version
        if not message:
            return
        stripped_message = message.strip()
        if not stripped_message:
            return
        if _is_qt_source_location_only_message(context, stripped_message):
            return
        level = level_map.get(mode, logging.INFO)
        if stripped_message.startswith(_QT_BREADCRUMB_PREFIXES):
            breadcrumbs.append(stripped_message)
            breadcrumb_version += 1

        rendered_message = stripped_message
        if level >= logging.WARNING:
            rendered_message = f"{rendered_message} {_qt_message_context(context)}"

        logger = getLogger()
        logger._log(
            level,
            rendered_message,
            tag=_qt_message_tag(context),
        )

        if (
            level >= logging.WARNING
            and breadcrumbs
            and replayed_version != breadcrumb_version
        ):
            recent = list(breadcrumbs)[-_QT_BREADCRUMB_REPLAY_LIMIT:]
            for position, breadcrumb in enumerate(recent, start=1):
                logger._log(
                    logging.DEBUG,
                    f"[QML诊断回放 {position}/{len(recent)}] {breadcrumb}",
                    tag="QML:BREADCRUMB",
                )
            replayed_version = breadcrumb_version

    return qt_message_handler


def install_qt_message_handler():
    """Install Qt message handler to redirect QML/Qt logs to project logger
    安装Qt消息处理程序，将QML/Qt日志重定向到项目日志
    """
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except ImportError as exc:
        debug(f"PySide6 unavailable, skip Qt message handler: {exc}", tag="Logger")
        return

    try:
        qInstallMessageHandler(_create_qt_message_handler(QtMsgType))
    except Exception as exc:
        exception(
            "Failed to install Qt message handler: "
            f"{type(exc).__name__}: {exc}",
            tag="Logger",
        )
