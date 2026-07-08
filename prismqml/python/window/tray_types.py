# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML SystemTray Types - 系统托盘类型
"""

from enum import IntEnum
from PySide6.QtWidgets import QSystemTrayIcon

class MessageIcon(IntEnum):
    """消息图标类型 Message icon type"""

    NoIcon = QSystemTrayIcon.MessageIcon.NoIcon.value
    Information = QSystemTrayIcon.MessageIcon.Information.value
    Warning = QSystemTrayIcon.MessageIcon.Warning.value
    Critical = QSystemTrayIcon.MessageIcon.Critical.value


class ActivationReason(IntEnum):
    """激活原因 Activation reason

    `value` 直接为底层 Qt int,与 SystemTrayIcon.activated(int) 信号一致比对:
        if reason == ActivationReason.Trigger.value: ...
    """

    Unknown = QSystemTrayIcon.ActivationReason.Unknown.value
    Context = QSystemTrayIcon.ActivationReason.Context.value
    DoubleClick = QSystemTrayIcon.ActivationReason.DoubleClick.value
    Trigger = QSystemTrayIcon.ActivationReason.Trigger.value
    MiddleClick = QSystemTrayIcon.ActivationReason.MiddleClick.value
