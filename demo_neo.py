# coding: utf-8
# SPDX-License-Identifier: MIT
"""Neobrutalism 皮肤真机预览 — 摆 Button/Card 各状态, 肉眼看硬阴影/粗边/橙主色/按下位移。

用法: .venv/Scripts/python.exe demo_neo.py
环境变量 SKIN=fluent 可对比 Fluent 原样(默认 neobrutalism)。
"""
import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QTimer

import fluentqml
from fluentqml import Skin, setSkin, register_types

QML = """
import QtQuick
import QtQuick.Window
import FluentQML

Window {
    id: win
    visible: true
    width: 720; height: 520
    title: "Neobrutalism 预览"
    color: Enums.isNeobrutalism ? Enums.neo.background : Enums.backgroundColor

    Column {
        anchors.centerIn: parent
        spacing: 24

        Text {
            text: Enums.isNeobrutalism ? "Neobrutalism 皮肤" : "Fluent 皮肤"
            font.pixelSize: 22; font.bold: true
            color: Enums.isNeobrutalism ? Enums.neo.foreground : Enums.foregroundColor
        }

        // 按钮一排: 默认 / primary / filled(success) / filled(danger) / 文本
        Row {
            spacing: 16
            Button { text: "默认" }
            Button { text: "主色"; style: Enums.button.style_primary }
            Button { text: "成功"; style: Enums.button.style_filled; level: Enums.statusLevel.success }
            Button { text: "危险"; style: Enums.button.style_filled; level: Enums.statusLevel.error }
            Button { text: "文本"; style: Enums.button.style_text }
        }

        // 卡片一排: 普通卡 / 悬浮卡(hover 阴影加大)
        Row {
            spacing: 24
            Card {
                width: 220; height: 120
                Text {
                    anchors.centerIn: parent
                    text: "普通卡片\\n黑边 + 硬阴影"
                    horizontalAlignment: Text.AlignHCenter
                    color: Enums.isNeobrutalism ? Enums.neo.foreground : Enums.foregroundColor
                }
            }
            Card {
                width: 220; height: 120
                cardType: Enums.card.type_elevated
                Text {
                    anchors.centerIn: parent
                    text: "悬浮卡片\\nhover 阴影加大"
                    horizontalAlignment: Text.AlignHCenter
                    color: Enums.isNeobrutalism ? Enums.neo.foreground : Enums.foregroundColor
                }
            }
        }

        // 表单控件一排: 输入框 / 下拉框 (聚焦/展开时边框转橙)
        Row {
            spacing: 16
            LineEdit {
                width: 220
                placeholderText: "点我聚焦,边框变橙"
            }
            ComboBoxDefault {
                width: 200
                model: ["选项一", "选项二", "选项三"]
            }
        }

        Text {
            text: "鼠标按住按钮看「压平」效果;悬停悬浮卡看阴影变化;点输入框/下拉看橙色聚焦"
            font.pixelSize: 13
            color: Enums.isNeobrutalism ? Enums.neo.secondaryForeground : Enums.secondaryForeground
        }
    }
}
"""


def main():
    app = QApplication(sys.argv)
    skin = os.environ.get("SKIN", "neobrutalism").lower()
    setSkin(Skin.NEOBRUTALISM if skin == "neobrutalism" else Skin.FLUENT)

    engine = QQmlApplicationEngine()
    register_types(engine)
    engine.loadData(QML.encode("utf-8"))

    if not engine.rootObjects():
        print("加载失败:")
        sys.exit(1)
    print(f"窗口已拉起, 皮肤={skin}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
