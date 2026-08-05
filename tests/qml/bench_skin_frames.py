# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""D3D11 帧时间基准: 对比 Fluent vs neobrutalism 皮肤下控件密集页的渲染帧间隔。

做法: 实例化一批控件(模拟密集页), 连续触发重绘(改 hovered/滚动), 用 frameSwapped
记录帧间隔, 统计 >20ms 卡帧数与平均帧时间。两皮肤各跑一轮对比。
退出码 0。结果路径由 --output、PRISMQML_FRAME_BENCH_OUTPUT 或系统临时目录决定。
"""
import argparse
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Optional
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

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
OUTPUT_ENV = "PRISMQML_FRAME_BENCH_OUTPUT"


def resolve_output_path(output: Optional[Path]) -> Path:
    if output is not None:
        return output.expanduser().resolve()
    configured = os.environ.get(OUTPUT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "prismqml" / "frame_bench.txt"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help=f"结果文件路径；默认读取 {OUTPUT_ENV}，否则写入系统临时目录",
    )
    return parser.parse_args(argv)


def bench_skin(engine, skin, label, out):
    setSkin(skin)
    comp = QQmlComponent(engine)
    comp.setData(QML.encode("utf-8"), QUrl("inline"))
    win = comp.create(engine.rootContext())
    if win is None:
        raise RuntimeError(
            f"[{label}] create 失败: "
            + "; ".join(error.toString() for error in comp.errors())
        )
    _KEEP.append((comp, win))

    intervals = []
    last = [0.0]
    state = {"phase": 0, "backend_error": ""}

    def on_swap():
        now = time.perf_counter() * 1000
        if last[0] > 0 and state["phase"] == 1:
            intervals.append(now - last[0])
        last[0] = now

    win.frameSwapped.connect(on_swap)

    # QML 内部 SequentialAnimation 自动滚动, Python 只测帧间隔
    loop_done = [False]

    def start_measure():
        actual_api = win.rendererInterface().graphicsApi()
        actual_api_name = getattr(actual_api, "name", str(actual_api))
        if actual_api_name != "Direct3D11":
            state["backend_error"] = (
                f"[{label}] 只接受 Direct3D11，实际为 {actual_api_name}"
            )
            loop_done[0] = True
            return
        out.append(f"[{label}] 图形后端={actual_api_name}")
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
    if state["backend_error"]:
        win.setProperty("visible", False)
        raise RuntimeError(state["backend_error"])
    if intervals:
        avg = sum(intervals) / len(intervals)
        janky = sum(1 for i in intervals if i > 20)
        p95 = sorted(intervals)[int(len(intervals) * 0.95)]
        out.append(f"[{label}] 帧数={len(intervals)} 平均={avg:.1f}ms p95={p95:.1f}ms 卡帧(>20ms)={janky} ({100*janky/len(intervals):.0f}%)")
    else:
        out.append(f"[{label}] 无帧数据")
    win.setProperty("visible", False)


def main(argv=None):
    args = parse_args(argv)
    output_path = resolve_output_path(args.output)
    QQuickWindow.setGraphicsApi(
        QSGRendererInterface.GraphicsApi.Direct3D11
    )
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    register_types(engine)

    out = []
    exit_code = 0
    try:
        bench_skin(engine, Skin.FLUENT, "fluent", out)
        bench_skin(engine, Skin.NEOBRUTALISM, "neo", out)
    except RuntimeError as error:
        out.append(f"[ERROR] {error}")
        exit_code = 5

    text = "\n".join(out)
    print(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    print(f"结果文件: {output_path}")
    QTimer.singleShot(100, app.quit)
    app.exec()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
