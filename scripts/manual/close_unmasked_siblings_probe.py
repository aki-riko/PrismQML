"""Enumerate contentItem children that stay opaque during the close collapse.

列出关闭收紧期间仍在画不透明底色、且不在 windowFrameLayer 之下的兄弟节点。

The collapse shader masks windowFrameLayer only. Anything parented directly to
contentItem escapes that mask and stays on screen as a rectangular block. This
probe walks the real window's item tree while the circle shrinks and reports
每个仍可见的兄弟节点, so the culprit is named by observation, not inference.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "qml"))

from _test_process_bootstrap import configure_qml_test_process  # noqa: E402

configure_qml_test_process()

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def _pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _describe(item):
    color = item.property("color")
    return {
        "name": item.objectName() or f"<{type(item).__name__}>",
        "visible": bool(item.isVisible()),
        "opacity": round(float(item.property("opacity") or 0.0), 3),
        "z": round(float(item.property("z") or 0.0), 1),
        "width": round(float(item.width()), 1),
        "height": round(float(item.height()), 1),
        "color": color.name() if hasattr(color, "name") else None,
        "alpha": round(color.alphaF(), 3) if hasattr(color, "alphaF") else None,
    }


def _walk_for_opaque_paint(item, depth=0, out=None):
    """Collect items that paint a non-transparent color. 收集在画非透明底色的项。"""
    if out is None:
        out = []
    info = _describe(item)
    if info["visible"] and info["opacity"] > 0.0 and info["alpha"]:
        if info["alpha"] > 0.0 and info["width"] > 1 and info["height"] > 1:
            info["depth"] = depth
            out.append(info)
    for child in item.childItems():
        _walk_for_opaque_paint(child, depth + 1, out)
    return out


def main() -> int:
    # Without a QApplication first, Window construction dies at 0xC0000409 with
    # no traceback. 没有 QApplication 先行, 构造 Window 会以 0xC0000409 硬崩且无栈。
    QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    # Keep the splash on: the Gallery runs with it enabled, and _splashLoader is
    # one of the suspects. 保持 splash 开启: Gallery 就是开着的, 而 _splashLoader
    # 正是嫌疑之一。
    host = Window(window_type=WindowType.BAR)
    host.addPage(None, "Home", "Home")
    host.show()
    _pump(2500)

    qwindow = host._window
    if qwindow is None or not hasattr(qwindow, "contentItem"):
        print("PROBE-FAIL: 拿不到 QQuickWindow")
        return 1

    content_item = qwindow.contentItem()

    # windowFrameLayer carries no objectName, so identify it by QML type.
    # windowFrameLayer 没有 objectName, 只能按 QML 类型认。
    def _type_of(item):
        return item.metaObject().className()

    children = content_item.childItems()
    frame = next(
        (c for c in children if "WindowsCoreFrame" in _type_of(c)), None
    )
    print(f"windowFrameLayer = {_type_of(frame) if frame else '<未找到>'}")

    siblings = [c for c in children if c is not frame]
    print(f"contentItem 直接子节点数 = {len(children)}")
    for sibling in siblings:
        print(f"  兄弟 [{_type_of(sibling)}]: {_describe(sibling)}")

    # A stub page may never dismiss the splash, which would make any splash
    # finding a probe artifact rather than the real close bug. Wait it out and
    # report the state we actually close from.
    # 桩页面可能永远不撤 splash, 那样"发现 splash"就只是探针假象而非真实关闭 bug。
    # 等它散掉, 并报告我们实际是从什么状态开始关闭的。
    splash_loader = next(
        (c for c in siblings if c.objectName() == "windowSplashLoader"), None
    )
    # A stub page never fires pageLoaded, so the splash never dismisses on its
    # own and would show up as a false positive. Force the real dismiss path and
    # confirm it went away before closing.
    # 桩页面不会发 pageLoaded, splash 自己不会散, 会成为假阳性。走真实 dismiss 路径
    # 并确认它消失后再关闭。
    QMetaObject.invokeMethod(qwindow, "_doDismissSplash")
    _pump(3000)
    if splash_loader is not None:
        print(
            f"\n关闭前 splash: visible={splash_loader.isVisible()} "
            f"active={splash_loader.property('active')} "
            f"dismissed={qwindow.property('_splashDismissed')}"
        )
        if splash_loader.isVisible():
            print("PROBE-WARN: splash 未散, 下面的 splash 结果是假阳性")

    samples = []
    progress_seen = []

    transition = next(
        (c for c in siblings if c.objectName() == "windowClosePageTransition"),
        None,
    )

    def _sample():
        # Record progress too, so a "clean" result can be distinguished from a
        # collapse that never ran. 一并记录 progress, 以便把"干净"和"收紧根本没跑"
        # 区分开。
        if transition is not None:
            value = transition.property("progress")
            if value is not None:
                progress_seen.append(round(float(value), 3))
        rows = []
        for sibling in siblings:
            rows.extend(_walk_for_opaque_paint(sibling))
        if rows:
            samples.append(rows)

    timer = QTimer()
    timer.setInterval(16)
    timer.timeout.connect(_sample)
    timer.start()

    qwindow.close()
    _pump(1200)
    timer.stop()

    if progress_seen:
        print(
            f"收紧 progress: 采样 {len(progress_seen)} 次, "
            f"从 {progress_seen[0]} 到 {progress_seen[-1]}, "
            f"最小 {min(progress_seen)}"
        )
        if min(progress_seen) == max(progress_seen):
            print("PROBE-WARN: progress 没变, 收紧没跑, 下面的结论无效")
    else:
        print("PROBE-WARN: 没采到 progress")
    print(f"\n收紧期间采到 {len(samples)} 帧有不透明兄弟节点")
    if samples:
        seen = {}
        for rows in samples:
            for row in rows:
                seen.setdefault(row["name"], row)
        print("仍在画不透明底色且不受遮罩的节点:")
        for name, row in seen.items():
            print(f"  {name}: {row}")
        print("\nRESULT: FOUND-UNMASKED")
    else:
        print("RESULT: NONE — 收紧期间没有兄弟节点在画不透明底色")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
