# coding: utf-8
# SPDX-License-Identifier: MIT
"""帧时间基准: 对比 Fluent vs neobrutalism 皮肤下控件密集页的渲染帧间隔。

做法: 实例化一批控件(模拟密集页), 连续触发重绘(改 hovered/滚动), 用 frameSwapped
记录帧间隔, 统计 >20ms 卡帧数与平均帧时间。两皮肤各跑一轮对比。
退出码 0。结果落盘 C:/Users/Kotori/frame_bench.txt。
"""
import sys
import time
from PySide6.QtCore import QUrl, QTimer, QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

import prismqml
from prismqml import Skin, setSkin, register_types

# 控件密集场景: 一列 N 个卡片, 每个含按钮/输入/开关/徽章 — 触发滚动重绘
QML = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: win
    visible: true
    width: 600; height: 700
    color: Enums.isNeobrutalism ? Enums.neo.background : Enums.backgroundColor
    property alias flick: flick

    Flickable {
        id: flick
        anchors.fill: parent
        contentHeight: col.height

        // QML 内部驱动滚动(Python 取不到 Flickable 对象), 往返滚动触发持续重绘
        SequentialAnimation on contentY {
            running: true
            loops: Animation.Infinite
            NumberAnimation { from: 0; to: Math.max(1, flick.contentHeight - win.height); duration: 1500 }
            NumberAnimation { to: 0; duration: 1500 }
        }
        Column {
            id: col
            width: parent.width
            spacing: 12
            padding: 16
            Repeater {
                model: 40
                Card {
                    width: 560; height: 90
                    cardType: Enums.card.type_elevated
                    Row {
                        anchors.centerIn: parent
                        spacing: 12
                        Button { text: "按钮" + index; style: Enums.button.style_primary }
                        CheckBox { text: "选"; checked: index % 2 === 0 }
                        ToggleSwitch { checked: true }
                        Badge { count: index; level: Enums.statusLevel.error }
                    }
                }
            }
        }
    }
}
"""

_KEEP = []


def bench_skin(engine, skin, label, out):
    setSkin(skin)
    comp = QQmlComponent(engine)
    comp.setData(QML.encode("utf-8"), QUrl("inline"))
    win = comp.create(engine.rootContext())
    if win is None:
        out.append(f"[{label}] create 失败: " + "; ".join(e.toString() for e in comp.errors()))
        return
    _KEEP.append((comp, win))

    intervals = []
    last = [0.0]
    state = {"phase": 0}

    def on_swap():
        now = time.perf_counter() * 1000
        if last[0] > 0 and state["phase"] == 1:
            intervals.append(now - last[0])
        last[0] = now

    win.frameSwapped.connect(on_swap)

    # QML 内部 SequentialAnimation 自动滚动, Python 只测帧间隔
    loop_done = [False]

    def start_measure():
        intervals.clear()
        state["phase"] = 1

    def finish():
        loop_done[0] = True

    # 预热 0.6s 再清零开始, 测 4s
    QTimer.singleShot(600, start_measure)
    QTimer.singleShot(4600, finish)

    while not loop_done[0]:
        QApplication.processEvents()
        time.sleep(0.001)

    win.frameSwapped.disconnect(on_swap)
    if intervals:
        avg = sum(intervals) / len(intervals)
        janky = sum(1 for i in intervals if i > 20)
        p95 = sorted(intervals)[int(len(intervals) * 0.95)]
        out.append(f"[{label}] 帧数={len(intervals)} 平均={avg:.1f}ms p95={p95:.1f}ms 卡帧(>20ms)={janky} ({100*janky/len(intervals):.0f}%)")
    else:
        out.append(f"[{label}] 无帧数据")
    win.setProperty("visible", False)


def main():
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGL)
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    register_types(engine)

    out = []
    bench_skin(engine, Skin.FLUENT, "fluent", out)
    bench_skin(engine, Skin.NEOBRUTALISM, "neo", out)

    text = "\n".join(out)
    print(text)
    open(r"C:/Users/Kotori/frame_bench.txt", "w", encoding="utf-8").write(text)
    QTimer.singleShot(100, app.quit)
    app.exec()


if __name__ == "__main__":
    main()
