# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""Card autoHeight 回归测试 — 普通卡片可选地跟随内容自撑。

背景: Card 默认高度固定(Enums.controlSize.cardHeight=64), 内容超出会溢出/重叠。
新增 `autoHeight` 开关(默认 false 保持原固定高度行为), 开启后普通卡片高度跟随
内容(contentLoader.childrenRect.height + 上下 border 边距, 带 cardHeight 最小兜底)。

⚠️ autoHeight 内容必须用 width: parent.width 自然堆叠, 不能用 anchors.fill: parent
(fill 的子项不计入 childrenRect → 自撑失效退回兜底)。

判据(真实窗口渲染后量化):
  1. autoHeight 内容多的卡 height > cardHeight(64), 且 > 内容少的卡
  2. autoHeight 内容少的卡 height == cardHeight(64 兜底)
  3. 默认(autoHeight=false)显式 height 的卡保持该值不变(原行为不破坏)
  4. 全程无 binding loop 警告

用法: <venv>/python tests/qml/test_card_autoheight.py
退出码: 0=通过, 1=失败
"""
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from prismqml.python.core.utils import register_types  # noqa: E402

QML = '''
import QtQuick
import PrismQML as Fluent
Item { width: 400; height: 800
 Column { width: 320; spacing: 10
  Fluent.Card { objectName: "ah_tall"; autoHeight: true; cardType: Fluent.Enums.card.type_default; width: 300
   Column { width: parent.width; spacing: 6
    Text { text: "r1" } Text { text: "r2" } Text { text: "r3" }
    Text { text: "r4" } Text { text: "r5" } Text { text: "r6 long row content" } } }
  Fluent.Card { objectName: "ah_short"; autoHeight: true; cardType: Fluent.Enums.card.type_hover; width: 300
   Column { width: parent.width; Text { text: "one line" } } }
  Fluent.Card { objectName: "fixed"; cardType: Fluent.Enums.card.type_default; width: 300; height: 60
   Column { anchors.fill: parent; anchors.margins: 12; Text { text: "fixed card" } } }
 } }
'''


def main():
    warns = []
    app = QGuiApplication(sys.argv)
    eng = QQmlApplicationEngine()
    register_types(eng)
    eng.warnings.connect(lambda errs: warns.extend(e.toString() for e in errs))

    comp = QQmlComponent(eng)
    comp.setData(QML.encode("utf-8"), QUrl("inline"))
    obj = comp.create()
    loop = QEventLoop()
    QTimer.singleShot(700, loop.quit)
    loop.exec()

    def find(name):
        for ch in obj.findChildren(object):
            if ch.property("objectName") == name:
                return ch
        return None

    failures = []
    if obj is None:
        for e in comp.errors():
            print("  [ERR]", e.toString())
        failures.append("组件创建失败")
    else:
        th = find("ah_tall").property("height")
        sh = find("ah_short").property("height")
        fh = find("fixed").property("height")
        loops = [w for w in warns if "loop" in w.lower()]
        if loops:
            failures.append(f"出现 binding loop: {loops[0]}")
        if not th or th <= 64:
            failures.append(f"autoHeight 内容多的卡未自撑(height={th}, 应>64)")
        if th <= sh:
            failures.append(f"内容多的卡({th})未比内容少的卡({sh})高")
        if abs(sh - 64) > 1:
            failures.append(f"autoHeight 内容少的卡应=64兜底, 实际{sh}")
        if abs(fh - 60) > 1:
            failures.append(f"固定高卡(height:60)应保持60, 实际{fh}(默认行为被破坏)")
        print(f"  ah_tall={th} ah_short={sh} fixed={fh} loops={len(loops)}")

    if failures:
        print("RESULT: FAIL - Card autoHeight 回归失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - Card autoHeight 自撑且不破坏默认行为")
        result = 0

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
