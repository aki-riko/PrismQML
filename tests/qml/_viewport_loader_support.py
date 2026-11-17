# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Force deferred ViewportLoader slots so page tests can reach offscreen cards.
强制创建延迟的 ViewportLoader 槽位，让页面测试能访问视口外的卡片。
"""

from PySide6.QtCore import QCoreApplication
from PySide6.QtQuick import QQuickItem


def _pending_slots(root):
    return [
        item
        for item in root.findChildren(QQuickItem)
        if item.property("_viewportLoader") is True and not item.property("created")
    ]


def create_all_viewport_loaders(root, max_rounds=4):
    """Create every slot under root, including slots revealed by created content.
    创建 root 下的全部槽位，包括新内容里出现的槽位。
    """
    for _ in range(max_rounds):
        pending = _pending_slots(root)
        if not pending:
            return
        for slot in pending:
            slot.metaObject().invokeMethod(slot, "create")
        QCoreApplication.processEvents()
    remaining = _pending_slots(root)
    assert not remaining, f"{len(remaining)} 个 ViewportLoader 槽位未能创建"
