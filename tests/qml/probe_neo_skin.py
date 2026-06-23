# coding: utf-8
# SPDX-License-Identifier: MIT
"""Neobrutalism Button + Card 几何探针。

用 register_types 注册 ThemeManager, 切 skin 后实例化控件读真实几何。
退出码 0=全过, 1=失败。
"""
import sys
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem

import fluentqml  # noqa: E402
from fluentqml import Skin, setSkin, register_types  # noqa: E402

_KEEP = []


def build(engine, qml):
    comp = QQmlComponent(engine)
    comp.setData(qml, QUrl("inline"))
    if comp.isError():
        print("加载错误:", [e.toString() for e in comp.errors()])
        sys.exit(1)
    obj = comp.create(engine.rootContext())
    if obj is None:
        print("create None:", [e.toString() for e in comp.errors()])
        sys.exit(1)
    _KEEP.append((comp, obj))
    return obj


def has_hard_shadow(obj, off=4):
    """是否存在可见、x≈y≈off 的纯黑硬阴影矩形"""
    for r in obj.findChildren(QQuickItem):
        if r.property("visible") and abs((r.property("x") or -99) - off) < 0.6 and abs((r.property("y") or -99) - off) < 0.6:
            return r
    return None


def main():
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    register_types(engine)
    failures = []

    def check(cond, msg):
        print(("  [OK] " if cond else "  [FAIL] ") + msg)
        if not cond:
            failures.append(msg)

    BTN = b'import FluentQML\nButton { text: "Click"; width: 120; height: 36 }\n'
    CARD = b'import FluentQML\nCard { width: 200; height: 120 }\n'

    print("--- Fluent ---")
    setSkin(Skin.FLUENT)
    b = build(engine, BTN)
    check(b.property("_neoPressShift") == 0, "fluent Button: 按下位移=0")
    check(b.property("radius") == 4, "fluent Button: radius=4")
    check(has_hard_shadow(b) is None, "fluent Button: 无硬阴影")
    c = build(engine, CARD)
    check(has_hard_shadow(c) is None, "fluent Card: 无硬阴影")

    print("--- Neobrutalism ---")
    setSkin(Skin.NEOBRUTALISM)
    b = build(engine, BTN)
    check(b.property("radius") == 6, "neo Button: radius=6")
    check(has_hard_shadow(b) is not None, "neo Button: 有硬阴影(x=y=4)")
    c = build(engine, CARD)
    cs = has_hard_shadow(c)
    check(cs is not None, "neo Card: 有硬阴影(x=y=4)")
    if cs is not None:
        print(f"    Card硬阴影 color={cs.property('color')} radius={cs.property('radius')}")

    QTimer.singleShot(0, app.quit)
    app.exec()

    print("\n" + "=" * 50)
    if failures:
        print(f"失败 {len(failures)} 项: " + "; ".join(failures))
        sys.exit(1)
    print("全部断言通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
