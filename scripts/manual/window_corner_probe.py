# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Instrument the real window corners: who paints the top-left block?

观测真实窗口四角: 左上角那块色块到底由哪个 QML item 绘制。

需要真实交互桌面 (Mica / DWM 合成), 属手工窗口探针: 会短暂显示窗口。
报告写入 .artifacts/window-diag/corner_probe_<mica|nomica>.txt。

注意: 这里的裸 Window 宿主没有 AcrylicHelper, 面板亚克力层不会激活; 要看亚克力
角落请跑 tests/qml/test_navigation_panel_acrylic_corner.py (离屏像素回归), 或按
examples/main.py 的装配跑真实 Gallery。本探针用于确认"哪里根本没有 QML 绘制"
(只渲染 QML 时 alpha=0 的位置就是露出 DWM 背板/桌面的位置)。
"""

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / ".artifacts" / "window-diag"

from PySide6.QtCore import QEventLoop, QPointF, QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def _pump(ms: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _prop(item, name):
    try:
        value = item.property(name)
    except Exception as exc:  # noqa: BLE001 - 诊断必须记录而不是中断
        return f"<{type(exc).__name__}: {exc}>"
    if isinstance(value, float):
        return round(value, 3)
    return value


def _describe(item) -> str:
    parts = [
        f"class={item.metaObject().className()}",
        f"obj={item.objectName()!r}",
        f"geom=({round(item.x(),2)},{round(item.y(),2)},{round(item.width(),2)},{round(item.height(),2)})",
        f"vis={item.isVisible()}",
        f"op={round(item.opacity(),3)}",
        f"z={round(item.z(),2)}",
    ]
    for name in ("color", "radius", "clip"):
        try:
            value = item.property(name)
        except Exception as exc:  # noqa: BLE001 - 无转换器的属性直接标注
            value = f"<{type(exc).__name__}>"
        if value is not None:
            parts.append(f"{name}={value}")
    return " ".join(parts)


def _walk(item, scene_point, depth, rows, chain):
    """Collect every visible item containing the scene point. 收集包含该点的可见 item。"""
    try:
        local = item.mapFromScene(scene_point)
    except Exception:  # noqa: BLE001
        return
    if not item.contains(local):
        return
    rows.append((depth, chain, item))
    for child in item.childItems():
        if not child.isVisible():
            continue
        _walk(child, scene_point, depth + 1, rows, chain + [child.objectName() or child.metaObject().className()])


def main() -> int:
    logging.disable(logging.CRITICAL)
    from prismqml.python.core.utils import configure_qml_environment

    configure_qml_environment()
    QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    mica = os.environ.get("PRISM_PROBE_MICA", "1") == "1"
    suffix = "mica" if mica else "nomica"

    host = Window(window_type=WindowType.SPLIT)
    host.setMicaEffectEnabled(mica)
    host.addPage(None, "Home", "Home")
    host.show()
    _pump(6000)

    qwindow = host._window
    if qwindow is None:
        print("PROBE-FAIL: 没有 QQuickWindow")
        return 1

    lines = []
    lines.append(f"window size logical={qwindow.width()}x{qwindow.height()}")
    for name in (
        "windowColor",
        "windowRadius",
        "shadowSize",
        "margin",
        "micaEnabled",
        "_micaActive",
        "_micaTransparent",
        "_micaBackdropReady",
        "_useNativeShadow",
        "_useQmlShadow",
        "titleBarHeight",
        "contentBgColor",
        "contentCornerRadius",
        "navCompactWidth",
        "navExpandWidth",
    ):
        lines.append(f"  {name} = {_prop(qwindow, name)}")
    lines.append(f"devicePixelRatio = {qwindow.devicePixelRatio()}")
    lines.append(f"flags = {qwindow.flags()}")

    content = qwindow.contentItem()
    lines.append("contentItem children:")
    for child in content.childItems():
        lines.append(f"  - {_describe(child)}")

    def _dump(item, depth, out):
        out.append(f"{'  ' * depth}- {_describe(item)}")
        if depth >= 5:
            return
        for child in item.childItems():
            _dump(child, depth + 1, out)

    frame = None
    splash = None
    for child in content.childItems():
        if "WindowsCoreFrame" in child.metaObject().className():
            frame = child
        if child.objectName() == "windowSplashLoader":
            splash = child
    lines.append("--- frame subtree ---")
    if frame is not None:
        subtree = []
        _dump(frame, 0, subtree)
        lines.extend(subtree)
    lines.append("--- splash loader subtree ---")
    if splash is not None:
        subtree = []
        _dump(splash, 0, subtree)
        lines.extend(subtree)

    points = {
        "TL(3,3)": QPointF(3, 3),
        "TL(6,6)": QPointF(6, 6),
        "TL(10,10)": QPointF(10, 10),
        "TL(14,14)": QPointF(14, 14),
        "TL(24,24)": QPointF(24, 24),
        "TOP-MID(w/2,4)": QPointF(qwindow.width() / 2, 4),
        "TR(w-6,6)": QPointF(qwindow.width() - 6, 6),
        "BR(w-6,h-6)": QPointF(qwindow.width() - 6, qwindow.height() - 6),
    }
    for label, point in points.items():
        rows = []
        _walk(content, point, 0, rows, [])
        lines.append(f"--- point {label} -> {len(rows)} containing items (paint order) ---")
        for depth, chain, item in rows:
            lines.append(f"  d{depth} {'/'.join(chain[-2:]) or '-'} :: {_describe(item)}")

    # Real screen pixels of the four corners. 四角的真实屏幕像素。
    screen = QGuiApplication.primaryScreen()
    geometry = qwindow.geometry()

    def capture(tag: str) -> None:
        if screen is None:
            return
        # Qt scales the returned pixmap by the screen ratio but keeps x/y in
        # device pixels. The screen grab is only meaningful while this window is
        # unobstructed; the QML-only render below is the reliable half.
        # Qt 会按屏幕比例放大返回位图, 但 x/y 仍按设备像素解释。抓屏只在窗口没有被
        # 其它窗口遮挡时才有意义; 下面那份只渲染 QML 的结果才是可靠的一半。
        ratio = qwindow.devicePixelRatio()
        grabbed = screen.grabWindow(
            0,
            int(round(geometry.x() * ratio)),
            int(round(geometry.y() * ratio)),
            geometry.width(),
            geometry.height(),
        )
        image: QImage = grabbed.toImage()
        if image.isNull():
            lines.append(f"[{tag}] capture failed")
            return
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        shot = OUT_DIR / f"probe-capture-{suffix}-{tag}.png"
        image.save(str(shot))
        lines.append(f"[{tag}] capture saved: {shot} {image.width()}x{image.height()}")
        for label, (px, py) in {
            "TL(4,4)": (4, 4),
            "TL(8,8)": (8, 8),
            "TL(12,12)": (12, 12),
            "TL(16,16)": (16, 16),
            "TL(24,24)": (24, 24),
            "TL(8,40)": (8, 40),
            "TL(8,80)": (8, 80),
            "pane(200,600)": (200, 600),
            "pane(200,1150)": (200, 1150),
            "TR(w-5,5)": (image.width() - 5, 5),
            "BR(w-5,h-5)": (image.width() - 5, image.height() - 5),
            "left-edge(x=1,y=400)": (1, 400),
        }.items():
            pixel = image.pixelColor(px, py)
            lines.append(f"  [{tag}] pixel {label} = {pixel.name()} a={pixel.alpha()}")
        # QML-only render: alpha 0 means nothing painted there, so the DWM
        # backdrop (Mica) is what the user sees. 只渲染 QML: alpha=0 表示那里没有
        # QML 绘制, 用户看到的是 DWM 背板 (云母)。
        qml_image: QImage = qwindow.grabWindow()
        if not qml_image.isNull():
            qml_shot = OUT_DIR / f"probe-qmlonly-{suffix}-{tag}.png"
            qml_image.save(str(qml_shot))
            lines.append(f"[{tag}] qml-only saved: {qml_shot} {qml_image.width()}x{qml_image.height()}")
            for qlabel, (px, py) in {
                "TL(4,4)": (4, 4),
                "TL(8,8)": (8, 8),
                "TL(12,12)": (12, 12),
                "pane(200,600)": (200, 600),
            }.items():
                pixel = qml_image.pixelColor(px, py)
                lines.append(
                    f"  [{tag}] QML-ONLY {qlabel} = {pixel.name()} a={pixel.alpha()}"
                )

    capture("collapsed")

    nav = qwindow.property("navigationView")
    lines.append(f"navigationView = {nav!r}")
    if nav is not None:
        for name in ("isExpanded", "backgroundColor", "acrylicEnabled", "acrylicImageSource"):
            lines.append(f"  nav.{name} = {_prop(nav, name)}")
        try:
            nav.expand()
        except Exception as exc:  # noqa: BLE001 - 诊断记录
            lines.append(f"  nav.expand() failed: {type(exc).__name__}: {exc}")
        _pump(2500)
        for name in ("isExpanded", "backgroundColor", "acrylicEnabled", "acrylicImageSource"):
            lines.append(f"  nav(after expand).{name} = {_prop(nav, name)}")
        capture("expanded")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUT_DIR / f"corner_probe_{suffix}.txt"
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n报告: {report}")

    host.requestClose()
    _pump(1200)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
