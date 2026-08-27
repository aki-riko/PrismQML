"""Measure overlay-vs-main geometry during the close collapse. 量关闭收紧时覆盖窗与主窗几何。

The overlay path fixed the flash, but the collapsing circle now extends past the screen.
The shader centres the circle at its own texture centre and QMLPageCircleFrame fills the
overlay window, so the circle is only centred on the window if the overlay's ACTUAL
geometry matches the main window's. _syncOverlayGeometry sets it from
captureItem.mapToGlobal(0,0) and captureItem.width/height — this checks what Windows
actually gave back, at 150% DPI where logical/device pixel handling is easy to get wrong.

覆盖窗口那条路把闪烁解决了, 但收紧的圆现在超出屏幕。shader 的圆心是自身纹理中心, 而
QMLPageCircleFrame 填满覆盖窗口, 所以圆要正好居中于窗口, 前提是覆盖窗的**实到**几何与主窗
一致。_syncOverlayGeometry 按 captureItem.mapToGlobal(0,0) 和 captureItem.width/height 设置
它 —— 这里检查 Windows 实际给回来的值, 在 150% 缩放下逻辑/设备像素很容易弄错。

Prints the requested vs actual overlay rect, the main window rect, and the delta. A
non-zero delta in origin or size localises the bug to _syncOverlayGeometry; a zero delta
means the geometry is right and the circle radius itself is wrong.
打印覆盖窗的请求值与实到值、主窗矩形, 以及差值。原点或尺寸差值非零 → 问题定位在
_syncOverlayGeometry; 差值为零 → 几何是对的, 问题在圆的半径本身。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Insert the repo root first or a stale copy inside .venv gets imported.
# 必须把仓库根插到最前, 否则会加载 .venv 里的旧副本。
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

_OVERLAY_NAME = "lazyPageCircleOverlayWindow"
_report: list[str] = []
_logged = {"count": 0}


def _find(app, predicate):
    for window in app.allWindows():
        if predicate(window):
            return window
    return None


def _poll():
    """Sample geometry while the overlay is visible. 覆盖窗可见期间采样几何。"""
    app = QApplication.instance()
    if app is None:
        return

    overlay = _find(app, lambda w: w.objectName() == _OVERLAY_NAME)
    # _closeInProgress only exists on the PrismQML window, so it identifies the main window
    # without depending on a title.
    # _closeInProgress 只有 PrismQML 窗口才有, 用它识别主窗就不必依赖标题。
    main = _find(app, lambda w: w.property("_closeInProgress") is not None)

    if overlay is not None and overlay.isVisible() and _logged["count"] < 4:
        _logged["count"] += 1
        line = (
            f"[几何] 覆盖窗 实到 x={overlay.x()} y={overlay.y()} "
            f"w={overlay.width()} h={overlay.height()} dpr={overlay.devicePixelRatio()}"
        )
        if main is not None:
            line += (
                f"\n       主窗   x={main.x()} y={main.y()} "
                f"w={main.width()} h={main.height()} dpr={main.devicePixelRatio()}"
                f"\n       差值   dx={overlay.x() - main.x()} dy={overlay.y() - main.y()} "
                f"dw={overlay.width() - main.width()} dh={overlay.height() - main.height()}"
                f"\n       主窗可见={main.isVisible()} 主窗opacity={main.opacity():.2f}"
            )
        screen = overlay.screen()
        if screen is not None:
            geometry = screen.geometry()
            line += (
                f"\n       屏幕   w={geometry.width()} h={geometry.height()}"
                f" 覆盖窗右下=({overlay.x() + overlay.width()},"
                f"{overlay.y() + overlay.height()})"
            )
        print(line, flush=True)
        _report.append(line)

    QTimer.singleShot(16, _poll)


def _dump():
    if not _report:
        print("[几何] 未捕到覆盖窗可见帧 —— 关闭时覆盖窗没显示, 或采样太慢", flush=True)
        return
    out = ROOT / ".artifacts" / "close_overlay_geometry.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(_report), encoding="utf-8")
    print(f"\n报告已写入: {out}", flush=True)


def _dump_wiring(app, main):
    """Report which backend loaded and whether the overlay switch reached it.

    The overlay window never became visible and no QML fallback warning was logged, so the
    question is whether preferOverlayWindow actually arrived at the backend that loaded.
    Read it from Python; QML console output is swallowed by the gallery's logging setup.
    覆盖窗一帧都没可见, 且没有 QML 兜底警告, 所以问题是 preferOverlayWindow 到底有没有到达
    真正加载的那个后端。从 Python 读取; QML 的 console 输出被 gallery 的日志系统吞掉了。
    """
    names = [w.objectName() or "(无名)" for w in app.allWindows()]
    print(f"[接线] 全部窗口 = {names}", flush=True)

    transition = main.findChild(object, "windowClosePageTransition")
    if transition is None:
        print("[接线] 找不到 windowClosePageTransition", flush=True)
        return
    print(
        f"[接线] 门面 preferOverlayWindow={transition.property('preferOverlayWindow')}"
        f" animationType={transition.property('animationType')}"
        f" customAnimation={transition.property('customAnimation')}",
        flush=True,
    )
    backend = main.findChild(object, "qmlPageCircleTransition")
    if backend is None:
        print("[接线] 找不到后端 qmlPageCircleTransition", flush=True)
        return
    # Two objects share this objectName (facade default and the inner radius engine), so
    # print the type to show which one findChild returned.
    # 两个对象共用这个 objectName(门面的默认后端与内层半径引擎), 打印类型以显示 findChild
    # 返回的是哪一个。
    print(
        f"[接线] 后端 type={type(backend).__name__}"
        f" preferOverlayWindow={backend.property('preferOverlayWindow')}",
        flush=True,
    )


def _trigger_close():
    """Close the main window the same way the caption button does. 用与标题栏按钮相同的方式关闭主窗。"""
    app = QApplication.instance()
    if app is None:
        return
    main = _find(app, lambda w: w.property("_closeInProgress") is not None)
    if main is None:
        QTimer.singleShot(200, _trigger_close)
        return
    _dump_wiring(app, main)
    print("[探针] 触发关闭", flush=True)
    main.close()


def main() -> int:
    sys.path.insert(0, str(ROOT / "examples"))
    import main as gallery_main  # noqa: PLC0415 - 必须在 sys.path 调整之后

    original_app = gallery_main.App

    class _ProbedApp(original_app):
        """Arm the timers from inside __init__.

        QTimer.singleShot needs a QCoreApplication to schedule against, so arming before
        gallery_main.main() silently drops the timers.
        QTimer.singleShot 需要已存在的 QCoreApplication 才能排程, 在 gallery_main.main()
        之前武装会让定时器被静默丢弃。
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            QTimer.singleShot(1500, _poll)
            # Close unattended so the probe needs no human clicking the button.
            # 自动关闭, 好让探针不需要人点按钮就能跑完。
            QTimer.singleShot(3200, _trigger_close)

    gallery_main.App = _ProbedApp
    try:
        return gallery_main.main()
    finally:
        gallery_main.App = original_app
        _dump()


if __name__ == "__main__":
    raise SystemExit(main())
