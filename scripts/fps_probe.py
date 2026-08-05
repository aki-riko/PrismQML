# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ScrollArea 掉帧 profiler.

复用 gallery 的引擎初始化, 打开窗口后程序化驱动一个 default 模式 ScrollArea
连续滚动, 用 QQuickWindow.frameSwapped 统计真实帧间隔, 报告 fps / 卡顿帧。

用法: python scripts/fps_probe.py [page_index]
"""
import sys
import os
import time
import gc

# 排除 Python GC stop-the-world 对帧测量的污染 (真实用户滚动不经 Python)
if os.environ.get("PROBE_NOGC") == "1":
    gc.disable()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QML_XHR_ALLOW_FILE_READ"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db=false"

from PySide6.QtCore import QTimer, QPointF, QPoint, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication


class FrameStats:
    def __init__(self):
        self.intervals = []
        self.last = None

    def tick(self):
        now = time.perf_counter()
        if self.last is not None:
            self.intervals.append((now - self.last) * 1000.0)
        self.last = now

    def report(self, label):
        if not self.intervals:
            print(f"[{label}] 无帧数据")
            return
        n = len(self.intervals)
        avg = sum(self.intervals) / n
        mx = max(self.intervals)
        # 卡顿帧: 帧间隔 > 20ms (低于 50fps)
        janky = [i for i in self.intervals if i > 20.0]
        # 严重卡顿: > 33ms (低于 30fps)
        severe = [i for i in self.intervals if i > 33.0]
        fps = 1000.0 / avg if avg > 0 else 0
        # 尖峰发生位置 (帧序号), 看是集中在开头还是均匀分布
        spikes = [(idx, round(v, 1)) for idx, v in enumerate(self.intervals) if v > 33.0]
        # 中位数 (反映"典型"帧, 不被尖峰污染)
        srt = sorted(self.intervals)
        med = srt[n // 2]
        p95 = srt[int(n * 0.95)]
        print(f"[{label}] 帧数={n} 平均={avg:.2f}ms(~{fps:.0f}fps) 中位={med:.2f}ms p95={p95:.1f}ms "
              f"最大={mx:.1f}ms 卡顿(>20ms)={len(janky)}({100*len(janky)/n:.0f}%) "
              f"严重(>33ms)={len(severe)}")
        if spikes:
            print(f"    严重尖峰位置(帧序号,ms): {spikes[:20]}")


def main():
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow

    import examples.main as gallery
    from prismqml.python.config import getConfigManager

    config_manager = getConfigManager()

    # 控制变量: 用环境变量强制覆盖 mica / dwmShadow, 定位 swap 阻塞元凶
    _mica = os.environ.get("PROBE_MICA")
    if _mica is not None:
        config_manager.setMicaEnabled(_mica == "1")
        print(f"[probe] 强制 MicaEnabled = {_mica == '1'}")
    _dwm = os.environ.get("PROBE_DWM")
    if _dwm is not None:
        config_manager.setDwmShadow(_dwm == "1")
        print(f"[probe] 强制 DwmShadow = {_dwm == '1'}")

    def find_window():
        app = QApplication.instance()
        if app is None:
            return None
        for w in app.topLevelWindows():
            if isinstance(w, QQuickWindow) and w.isVisible():
                return w
        return None

    PAGE_NAMES = {0: "按钮页(default)", 10: "图标页(grid)", 8: "容器页(default嵌套)"}
    target_page = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    def run_probe():
        app = QApplication.instance()
        if app is None:
            print("[ERROR] QApplication 尚未创建")
            return
        win = find_window()
        if win is None:
            print("[ERROR] 找不到可见 QQuickWindow"); app.quit(); return
        actual_api = win.rendererInterface().graphicsApi()
        actual_api_name = getattr(actual_api, "name", str(actual_api))
        print(f"[probe] actual graphics backend = {actual_api_name}")
        if actual_api_name != "Direct3D11":
            print(
                "[ERROR] 性能探针只接受 Direct3D11，"
                f"实际为 {actual_api_name}"
            )
            app.exit(5)
            return

        # 切页: 通过 win.contentItem 的 visual 子树找带 currentIndex+count 的 StackedWidget
        items = []
        walk_visual(win.contentItem(), items)
        sw = None
        for obj in items:
            meta_object = obj.metaObject()
            if (
                meta_object.indexOfProperty("currentIndex") < 0
                or meta_object.indexOfProperty("count") < 0
            ):
                continue
            count = obj.property("count")
            if isinstance(count, (int, float)) and count >= 10:
                sw = obj
                break
        if sw is not None and target_page != 0:
            print(f"切换到页 {target_page} ({PAGE_NAMES.get(target_page,'?')})")
            sw.setProperty("currentIndex", target_page)
        else:
            print(f"测试页 {target_page} ({PAGE_NAMES.get(target_page,'?')})  stackedWidget={'找到' if sw else '未找到'}")

        QTimer.singleShot(1500, lambda: do_scroll(win))

    def do_scroll(win):
        app = QApplication.instance()
        if app is None:
            print("[ERROR] QApplication 已销毁")
            return
        fs = FrameStats()
        win.frameSwapped.connect(fs.tick)
        # 鼠标停在窗口偏左中部 (避开右侧详情面板, 命中主滚动区)
        cx, cy = win.width() * 0.4, win.height() * 0.55
        pos = QPointF(cx, cy); gpos = QPointF(win.x() + cx, win.y() + cy)
        state = {"count": 0, "dir": 1}

        def send_wheel():
            dy = state["dir"] * 120
            ev = QWheelEvent(pos, gpos, QPoint(0, 0), QPoint(0, dy),
                             Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            app.sendEvent(win, ev)
            state["count"] += 1
            if state["count"] % 10 == 0:
                state["dir"] *= -1

        wheel_timer = QTimer(); wheel_timer.setInterval(40)
        wheel_timer.timeout.connect(send_wheel)

        # 阶段1: 静止基线 1.5s
        def phase_idle_done():
            fs.report("静止基线")
            fs.intervals.clear(); fs.last = None
            wheel_timer.start()

        def phase_scroll_done():
            wheel_timer.stop()
            fs.report(PAGE_NAMES.get(target_page, "页") + " 滚动")
            app.quit()

        fs.intervals.clear(); fs.last = None
        QTimer.singleShot(1500, phase_idle_done)
        QTimer.singleShot(7000, phase_scroll_done)

    def walk_visual(item, out, depth=0):
        # 递归遍历 QML visual tree (childItems), 收集所有 QObject
        if item is None or depth > 40:
            return
        out.append(item)
        for k in item.childItems():
            walk_visual(k, out, depth + 1)

    class _ProbeEngine(QQmlApplicationEngine):
        def load(self, url) -> None:
            super().load(url)
            if not self.rootObjects():
                return
            # 等窗口/页面加载稳定
            QTimer.singleShot(2500, run_probe)
            # 兜底超时
            QTimer.singleShot(20000, QApplication.instance().quit)

    gallery.QQmlApplicationEngine = _ProbeEngine
    return int(gallery.main())


if __name__ == "__main__":
    sys.exit(main())
