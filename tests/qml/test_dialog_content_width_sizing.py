# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DialogBoxCore.contentWidth sizing semantics.

DialogBoxCore historically drove its width from the body's childrenRect. When
a fixed-width body had a child overflowing that width (and the overflow
oscillated), childrenRect fed back into the dialog width and Qt reported a
"Binding loop detected for property implicitWidth" warning at runtime.

The fix adds an explicit `contentWidth` property: when > 0 the dialog width is
driven by it (breaking the loop); when <= 0 the legacy childrenRect measurement
is kept. This test pins that sizing contract with numeric assertions (the
runtime binding-loop warning itself only reproduces under real rendering, not
offscreen, so it cannot be asserted here — the contract is what we guard).
DialogBoxCore 过去用 body 的 childrenRect 决定宽度；当定宽 body 有子项溢出且
溢出量抖动时，childrenRect 反馈进对话框宽度，运行期报 implicitWidth 绑定循环。
修复新增 contentWidth：>0 时宽度由它决定（断环），<=0 时保留 childrenRect 旧行为。
本测试以数值断言锁定该尺寸契约（绑定循环告警仅在真实渲染下复现、离屏无法触发，
故此处不断言告警本身，而是守住契约）。
"""

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine

from prismqml import register_types


# contentWidth set -> dialog width = contentWidth + Enums.dialog.contentPadding(48).
_QML_EXPLICIT = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    visible: true; width: 900; height: 700
    DialogBoxCore {
        id: box
        objectName: "dlg"
        contentWidth: 520
        Column {
            width: parent.width
            Rectangle { width: 800; height: 40 }  // overflow child that would grow childrenRect
        }
        Component.onCompleted: box.open()
    }
}
"""

# contentWidth unset -> legacy behavior: width = max(minWidth, childrenRect + padding).
_QML_FALLBACK = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    visible: true; width: 900; height: 700
    DialogBoxCore {
        id: box
        objectName: "dlg"
        Column {
            Rectangle { width: 300; height: 40 }
        }
        Component.onCompleted: box.open()
    }
}
"""


def _pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _load_dialog_width(qapp, qml):
    from PySide6.QtQuick import QQuickItem

    engine = QQmlApplicationEngine()
    register_types(engine)
    try:
        engine.loadData(qml, QUrl("inline"))
        roots = engine.rootObjects()
        assert roots, "window failed to load"
        _pump(200)
        win = roots[0]
        # The dialog card surface carries objectName "_background"; its width is
        # the actual rendered dialog width (max(minWidth, implicitWidth+padding)).
        # 对话框卡片背景 objectName 为 "_background"，其宽度即实际渲染的对话框宽度。
        card = next(
            (it for it in win.findChildren(QQuickItem) if it.objectName() == "_background"),
            None,
        )
        assert card is not None, "dialog card (_background) not found"
        return float(card.width())
    finally:
        for obj in engine.rootObjects():
            obj.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()


def test_content_width_drives_dialog_width(qapp):
    # contentWidth=520, padding=48 -> 568, regardless of the 800px overflow child.
    # 内容宽由 contentWidth 决定，不受 800px 溢出子项影响。
    width = _load_dialog_width(qapp, _QML_EXPLICIT)
    assert width == 568.0, f"expected 520+48=568, got {width}"


def test_unset_content_width_falls_back_to_childrenrect(qapp):
    # No contentWidth -> max(minWidth=288, 300+48=348) = 348.
    # 未设 contentWidth 时回退 childrenRect：max(288, 300+48)=348。
    width = _load_dialog_width(qapp, _QML_FALLBACK)
    assert width == 348.0, f"expected max(288, 300+48)=348, got {width}"
