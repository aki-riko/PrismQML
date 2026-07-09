# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Timeline virtualized shadow padding regression test.

The virtualized Timeline keeps delegate rows clipped to avoid stale reused
content. Card shadows must therefore be drawn inside the row bounds; otherwise
the first visible card is clipped when a row aligns with the viewport top.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from prismqml.python.core.utils import register_types  # noqa: E402

QML = """
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    visible: true
    width: 420
    height: 260
    property int expectedShadowPadding: Fluent.Enums.spacing.cardShadow

    Fluent.Timeline {
        anchors.fill: parent
        virtualized: true
        items: [
            {
                "title": "今天",
                "status": "info",
                "cards": [
                    {
                        "text": "fix: 安卓IM会话设置校验当前会话",
                        "description": "c5c70782 · Aquila"
                    },
                    {
                        "text": "chore: 升级版本号到2.0.1.301",
                        "description": "bcafe016 · Aquila"
                    }
                ]
            }
        ]
    }
}
"""


def walk_visual_tree(item):
    items = []
    for child in item.childItems():
        items.append(child)
        items.extend(walk_visual_tree(child))
    return items


def has_list_view_ancestor(item):
    parent = item.parentItem()
    while parent is not None:
        if "ListView" in parent.metaObject().className():
            return True
        parent = parent.parentItem()
    return False


def visible_virtual_cards(root):
    cards = []
    for item in walk_visual_tree(root.contentItem()):
        if item.property("cardType") is None or item.property("clickEnabled") is not True:
            continue
        parent = item.parentItem()
        if parent is None or parent.height() <= 0:
            continue
        if has_list_view_ancestor(item):
            cards.append(item)
    return cards


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    register_types(engine)

    component = QQmlComponent(engine)
    component.setData(QML.encode("utf-8"), QUrl("inline"))
    root = component.create()

    failures = []
    if root is None:
        failures.append("Timeline test window create() returned None")
        for error in component.errors():
            print("  [ERR]", error.toString())
    else:
        loop = QEventLoop()
        QTimer.singleShot(900, loop.quit)
        loop.exec()

        expected = root.property("expectedShadowPadding")
        cards = visible_virtual_cards(root)
        if not cards:
            failures.append("No visible virtualized Timeline cards were created")

        for index, card in enumerate(cards):
            row = card.parentItem().parentItem()
            if not row.clip():
                failures.append(f"Card row {index} is not clipped; test no longer covers the regression")
            if card.y() < expected:
                failures.append(
                    f"Card row {index} y={card.y()} should be >= shadow padding {expected}"
                )
            if row.height() < card.y() + card.height():
                failures.append(
                    f"Card row {index} height={row.height()} does not contain card bottom "
                    f"{card.y() + card.height()}"
                )

        print(f"  virtual_cards={len(cards)} expected_shadow_padding={expected}")

    QTimer.singleShot(0, app.quit)
    app.exec()

    if failures:
        print("RESULT: FAIL - Timeline virtual shadow padding regression")
        for failure in failures:
            print("  [FAIL]", failure)
        sys.exit(1)

    print("RESULT: PASS - Timeline virtual rows preserve card shadow padding")
    sys.exit(0)


if __name__ == "__main__":
    main()
