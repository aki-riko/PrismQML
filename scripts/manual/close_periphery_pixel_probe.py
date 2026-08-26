"""Sample real screen pixels outside the shrinking close circle.

采样关闭圆环之外的真实屏幕像素, 判断外围到底被裁掉了没有。

Item-tree enumeration cannot answer this: the residue may come from the native
surface (DWM backdrop / non-translucent window) rather than any QML item. This
probe reads the desktop with GetPixel while the circle collapses, so the answer
is measured. 需要真实交互桌面, 在无桌面的会话里 GetPixel 会返回 CLR_INVALID。
"""

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

CLR_INVALID = 0xFFFFFFFF


def _pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _sampler():
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    gdi32.GetPixel.restype = wintypes.DWORD
    hdc = user32.GetDC(0)
    if not hdc:
        raise OSError("GetDC(0) failed — 没有可用桌面")

    def _read(x, y):
        value = gdi32.GetPixel(hdc, int(x), int(y))
        if value == CLR_INVALID:
            return None
        return (value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF)

    return _read


def main() -> int:
    # Silence app logging: on a real terminal it interleaves with the probe
    # output and shreds the verdict. 压掉应用日志: 真机终端上它会和探针输出交织,
    # 把结论搅烂。
    import logging

    logging.disable(logging.CRITICAL)

    QApplication.instance() or QApplication(sys.argv)
    from prismqml import Window, WindowType

    read_pixel = _sampler()

    host = Window(window_type=WindowType.BAR)
    # The reported symptom is on a Mica window, and Mica changes windowColor via
    # _micaTransparent, so reproduce with it on.
    # 报告的症状是在 Mica 窗口上, 且 Mica 会通过 _micaTransparent 改 windowColor,
    # 所以照样开着复现。
    host.setMicaEffectEnabled(True)
    host.addPage(None, "Home", "Home")
    host.show()
    _pump(3000)

    qwindow = host._window
    if qwindow is None:
        print("PROBE-FAIL: 拿不到 QQuickWindow")
        return 1

    # Corner samples sit far outside the circle for most of the collapse, so any
    # window-coloured pixel there is unclipped periphery.
    # 角点在收紧大部分时间里都远在圆外, 那里出现窗口底色就是没被裁掉的外围。
    geo = qwindow.geometry()
    inset = 12
    corners = {
        "左上": (geo.x() + inset, geo.y() + inset),
        "右上": (geo.x() + geo.width() - inset, geo.y() + inset),
        "左下": (geo.x() + inset, geo.y() + geo.height() - inset),
        "右下": (geo.x() + geo.width() - inset, geo.y() + geo.height() - inset),
    }
    baseline = {name: read_pixel(*point) for name, point in corners.items()}
    if all(value is None for value in baseline.values()):
        print("PROBE-FAIL: GetPixel 全返回 CLR_INVALID — 本会话没有交互桌面")
        return 2

    transition = None
    frame_layer = None
    for child in qwindow.contentItem().childItems():
        if child.objectName() == "windowClosePageTransition":
            transition = child
        if "WindowsCoreFrame" in child.metaObject().className():
            frame_layer = child

    frames = []
    path_log = []

    def _log_path():
        """Record which collapse branch ran.

        记录收紧走了哪条分支。

        Do NOT touch frame_layer.property("layer"): PySide6 has no converter for
        QQuickItemLayer* and raises, which would kill every sample and leave the
        whole run INCONCLUSIVE. _usingPageLayer already distinguishes the two
        branches. 不要碰 frame_layer.property("layer"): PySide6 没有
        QQuickItemLayer* 的转换器会直接抛错, 打断每一次采样, 让整轮变成
        INCONCLUSIVE。_usingPageLayer 已经足够区分两条分支。
        """
        if transition is None:
            return
        row = (
            transition.property("_usingPageLayer"),
            transition.property("_lastFallbackReason"),
            transition.property("_capturePending"),
        )
        if row not in path_log:
            path_log.append(row)

    def _sample():
        # A bug in diagnostics must never destroy the measurement.
        # 诊断代码的 bug 绝不能毁掉测量本身。
        progress = None
        try:
            if transition is not None:
                value = transition.property("progress")
                if value is not None:
                    progress = round(float(value), 3)
            _log_path()
        except Exception as exc:  # noqa: BLE001 - 记录而非静默
            if not any(r == ("诊断异常", str(exc), None) for r in path_log):
                path_log.append(("诊断异常", str(exc), None))
        frames.append((progress, {n: read_pixel(*p) for n, p in corners.items()}))

    # 8ms: the collapse is ~420ms, and a 16ms tick only caught 10 frames on a
    # real machine because closing starves the loop.
    # 8ms: 收紧约 420ms, 真机上 16ms 只采到 10 帧, 因为关闭会饿死事件循环。
    timer = QTimer()
    timer.setInterval(8)
    timer.timeout.connect(_sample)
    timer.start()

    qwindow.close()
    _pump(1500)
    timer.stop()

    # Only mid-collapse frames prove anything: at progress≈1 the circle still
    # covers the corners legitimately.
    # 只有收紧中段的帧能说明问题: progress≈1 时圆本就该盖住角点。
    midway = [f for f in frames if f[0] is not None and 0.05 < f[0] < 0.6]
    matches = sum(
        1
        for _, samples in midway
        for name, value in samples.items()
        if value is not None and value == baseline.get(name)
    )
    progresses = [f[0] for f in frames if f[0] is not None]
    span = f"{max(progresses)}->{min(progresses)}" if progresses else "无"
    verdict = (
        "INCONCLUSIVE"
        if not midway
        else ("PERIPHERY-NOT-CLIPPED" if matches else "CLIPPED")
    )

    # Write the full report to a file: a real terminal interleaves and truncates
    # this badly enough to be unreadable. 报告落盘: 真机终端会把输出交织截断到
    # 读不出来。
    lines = [
        f"verdict={verdict}",
        f"frames={len(frames)} progress={span} midway={len(midway)}",
        f"midwayCornerMatches={matches}/{len(midway) * 4}",
        f"micaEnabled={qwindow.property('micaEnabled')}",
        f"_micaActive={qwindow.property('_micaActive')}",
        f"_micaTransparent={qwindow.property('_micaTransparent')}",
        f"windowColor={qwindow.property('windowColor')}",
        f"baseline={baseline}",
        "",
        "# (usingPageLayer, lastFallbackReason, capturePending)",
    ]
    lines.extend(f"path={row}" for row in path_log)
    lines.append("")
    lines.extend(
        f"frame progress={p} {s}" for p, s in frames if p is not None
    )
    report = ROOT / ".artifacts" / "close_periphery_report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"RESULT: {verdict}")
    print(f"报告已写入: {report}")
    if not midway:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
