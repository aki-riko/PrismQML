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

from PySide6.QtCore import QEventLoop, QTimer, qInstallMessageHandler  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

CLR_INVALID = 0xFFFFFFFF

# Every mid-collapse bail-out in LazyPageCircleTransition goes through
# _completeWithoutAnimation, which drops the mask early and logs via
# console.warn/error. Capturing Qt messages is the only way to see that from here.
# LazyPageCircleTransition 里每条中途放弃的路径都走 _completeWithoutAnimation, 它会
# 提前摘掉遮罩并经 console.warn/error 打日志。抓 Qt 消息是这里唯一能看到它的办法。
QML_LOG = []


def _install_log_capture():
    def _handler(mode, context, message):
        QML_LOG.append(str(message))

    qInstallMessageHandler(_handler)


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

    _install_log_capture()
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
        color = qwindow.property("windowColor")
        row = (
            transition.property("_usingPageLayer"),
            transition.property("_lastFallbackReason"),
            transition.property("_capturePending"),
            # Discriminator: if _micaTransparent flips false mid-collapse,
            # windowColor turns opaque #f0f4f9 and the culprit is QML, not DWM.
            # 判别器: 若收紧中途 _micaTransparent 翻假, windowColor 会变成不透明
            # #f0f4f9, 那真凶就是 QML 而不是 DWM。
            qwindow.property("_micaTransparent"),
            qwindow.property("_micaBackdropReady"),
            color.name() if hasattr(color, "name") else None,
            round(color.alphaF(), 3) if hasattr(color, "alphaF") else None,
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

    # Ground truth: with the window gone these corners are bare desktop. If a
    # mid-collapse corner equals this, the periphery really was clipped; if it
    # equals the window baseline instead, it was not.
    # 基准真值: 窗口消失后这几个角点就是裸桌面。中段角点等于它 = 外围真裁掉了;
    # 等于窗口基线 = 没裁掉。
    _pump(600)
    desktop = {name: read_pixel(*point) for name, point in corners.items()}

    # Split the collapse in two and judge each: the reported symptom is a
    # full-window white with only a tiny circle left, i.e. progress near 0. The
    # previous window (0.05 < p < 0.6) excluded exactly that, which is why a run
    # could report CLIPPED while the user still saw white.
    # 把收紧分两段分别判: 报告的症状是整窗全白、只剩一个极小的圆, 也就是 progress
    # 接近 0。上一版判据 (0.05 < p < 0.6) 恰好把那一段排除在外, 所以会出现"探针说
    # CLIPPED, 用户仍看到白"。
    def _match_count(rows):
        return sum(
            1
            for _, samples in rows
            for name, value in samples.items()
            if value is not None and value == baseline.get(name)
        )

    midway = [f for f in frames if f[0] is not None and 0.05 < f[0] < 0.85]
    tail = [f for f in frames if f[0] is not None and f[0] <= 0.05]
    matches = _match_count(midway)
    tail_matches = _match_count(tail)
    progresses = [f[0] for f in frames if f[0] is not None]
    span = f"{max(progresses)}->{min(progresses)}" if progresses else "无"
    if not midway and not tail:
        verdict = "INCONCLUSIVE-无中段帧"
    elif baseline == desktop:
        # Window colour and desktop colour are indistinguishable here, so a
        # corner match proves nothing either way — say so instead of reporting a
        # false CLIPPED. 窗口底色与桌面色在这里无法区分, 角点相等什么也证明不了,
        # 直说而不是误报 CLIPPED。
        verdict = "INCONCLUSIVE-桌面色与窗口底色相同"
    elif matches and tail_matches:
        verdict = "PERIPHERY-NOT-CLIPPED-全段"
    elif tail_matches:
        # This is the reported symptom: mid-collapse clips fine, then the tail
        # goes opaque. 这正是报告的症状: 中段裁得好, 末段翻不透明。
        verdict = "PERIPHERY-NOT-CLIPPED-仅末段"
    elif matches:
        verdict = "PERIPHERY-NOT-CLIPPED-仅中段"
    else:
        verdict = "CLIPPED"

    # Write the full report to a file: a real terminal interleaves and truncates
    # this badly enough to be unreadable. 报告落盘: 真机终端会把输出交织截断到
    # 读不出来。
    lines = [
        f"verdict={verdict}",
        f"frames={len(frames)} progress={span}"
        f" midway={len(midway)} tail={len(tail)}",
        f"midwayCornerMatches={matches}/{len(midway) * 4}",
        f"tailCornerMatches={tail_matches}/{len(tail) * 4}",
        f"micaEnabled={qwindow.property('micaEnabled')}",
        f"_micaActive={qwindow.property('_micaActive')}",
        f"_micaTransparent={qwindow.property('_micaTransparent')}",
        f"windowColor={qwindow.property('windowColor')}",
        f"baseline={baseline}",
        f"desktopAfterClose={desktop}",
        f"baselineEqualsDesktop={baseline == desktop}",
        "",
        "# (usingPageLayer, fallbackReason, capturePending,"
        " micaTransparent, backdropReady, windowColor, alpha)",
    ]
    lines.extend(f"path={row}" for row in path_log)
    lines.append("")
    # Only transition-related messages: the app logs a lot of unrelated noise.
    # 只留过渡相关消息: 应用本身日志噪声很多。
    relevant = [
        message
        for message in QML_LOG
        if "Transition" in message or "collapse" in message.lower()
    ]
    lines.append(f"qmlLogTotal={len(QML_LOG)} relevant={len(relevant)}")
    lines.extend(f"qml={message}" for message in relevant[:20])
    lines.append("")
    lines.extend(
        f"frame progress={p} {s}" for p, s in frames if p is not None
    )
    report = ROOT / ".artifacts" / "close_periphery_report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"RESULT: {verdict}")
    print(f"报告已写入: {report}")
    return 3 if verdict.startswith("INCONCLUSIVE") else 0


if __name__ == "__main__":
    raise SystemExit(main())
