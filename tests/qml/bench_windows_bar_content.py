# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsBar content D3D11 benchmark. WindowsBar 内容 D3D11 手工基准。"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import (
    Property,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface

import prismqml
from prismqml import configure_qml_environment, register_types


MODES = ("desktop", "compact")
QML_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/_internal" as Internal

Window {
    id: window

    function selectFirst() {
        host.currentIndex = 0
        window.update()
    }

    function selectSecond() {
        host.currentIndex = 1
        window.update()
    }

    width: 900
    height: 600
    x: 64
    y: 64
    visible: false
    color: Enums.backgroundColor

    QtObject {
        id: host

        property var navigationItems: __MODEL__
        property var bottomNavigationItems: []
        property bool navigationSmoothScroll: false
        property int navigationScrollDuration: Enums.duration.none
        property real navigationScrollStep: Enums.spacing.navigationScrollStep
        property bool _micaActive: false
        property bool _pythonLoading: false
        property bool _pythonPageMode: false
        property color contentBgColor: Enums.backgroundColor
        property int contentCornerRadius: Enums.radius.large
        property var pageSources: []
        property bool lazyLoading: false
        property int currentIndex: 0
        property string loadingText: "Loading"

        signal currentPageChanged(int index)

        function profileTime(message) {}
        function _handleBottomItemClicked(index, navPanel, stack, sources) {
            return -1
        }
    }

    Internal.WindowsBarContent {
        anchors.fill: parent
        hostWindow: host
    }
}
"""
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


class _PlatformInfo(QObject):
    def __init__(self, compact: bool, parent: QObject) -> None:
        super().__init__(parent)
        self._compact = compact

    @Property(bool, constant=True)
    def isCompact(self) -> bool:
        return self._compact

    @Property(int, constant=True)
    def touchTargetSize(self) -> int:
        return 48 if self._compact else 32


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default="desktop")
    parser.add_argument("--items", type=int, default=8)
    parser.add_argument("--image-output", type=Path)
    return parser.parse_args(argv)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for_frame(window: QQuickWindow, action, timeout_ms: int = 3000) -> float:
    swapped_at = []

    def on_frame_swapped():
        if not swapped_at:
            swapped_at.append(time.perf_counter())

    window.frameSwapped.connect(on_frame_swapped)
    started_at = time.perf_counter()
    try:
        action()
        elapsed = 0
        while not swapped_at and elapsed < timeout_ms:
            _pump(10)
            elapsed += 10
    finally:
        window.frameSwapped.disconnect(on_frame_swapped)
    if not swapped_at:
        raise RuntimeError("D3D11 frame was not presented within 3000 ms")
    return (swapped_at[0] - started_at) * 1000


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        if current.isNull():
            raise RuntimeError("D3D11 grabWindow returned an empty image")
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise RuntimeError("D3D11 WindowsBar frame did not stabilize within 800 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _visual_items(window: QQuickWindow) -> list[QQuickItem]:
    items = []
    pending = [window.contentItem()]
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


def _owned_objects(window: QQuickWindow, visual_items) -> list[QObject]:
    objects = []
    pending = [window, *visual_items]
    seen = set()
    while pending:
        obj = pending.pop()
        identity = id(obj)
        if identity in seen:
            continue
        seen.add(identity)
        objects.append(obj)
        pending.extend(obj.children())
    return objects


def _navigation_item_count(visual_items: list[QQuickItem]) -> int:
    return sum(
        "NavigationBarItem" in item.metaObject().className()
        for item in visual_items
    )


def _model(item_count: int) -> list[dict[str, object]]:
    return [
        {
            "text": f"Page {index + 1}",
            "icon": "",
            "selectedIcon": "",
            "badgeCount": 0,
            "key": f"page_{index}",
        }
        for index in range(item_count)
    ]


def _qml_source(item_count: int) -> bytes:
    model = json.dumps(_model(item_count), ensure_ascii=True)
    return QML_TEMPLATE.replace("__MODEL__", model).encode("utf-8")


def _invoke(window: QQuickWindow, method: str) -> None:
    if not QMetaObject.invokeMethod(window, method):
        raise RuntimeError(f"WindowsBar benchmark method failed: {method}")


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.items < 2:
        raise SystemExit("--items must be at least 2")

    package_path = Path(prismqml.__file__).resolve()
    try:
        package_path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(
            f"WindowsBar benchmark imported PrismQML outside checkout: {package_path}"
        ) from error

    configure_qml_environment()
    QQuickWindow.setGraphicsApi(
        QSGRendererInterface.GraphicsApi.Direct3D11
    )
    app = QGuiApplication(sys.argv)
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    platform_info = _PlatformInfo(args.mode == "compact", engine)
    engine.rootContext().setContextProperty("PlatformInfo", platform_info)
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)

    load_started = time.perf_counter()
    component.setData(
        _qml_source(args.items),
        QUrl.fromLocalFile(str(ROOT / "tests/qml/windows-bar-content-bench.qml")),
    )
    while component.status() == QQmlComponent.Status.Loading:
        _pump()
    qml_load_ms = (time.perf_counter() - load_started) * 1000
    if component.status() != QQmlComponent.Status.Ready:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    create_started = time.perf_counter()
    window = component.create(engine.rootContext())
    construction_ms = (time.perf_counter() - create_started) * 1000
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("WindowsBar benchmark window creation failed")

    ready_frame_ms = _wait_for_frame(window, window.show)
    actual_api = window.rendererInterface().graphicsApi()
    actual_api_name = getattr(actual_api, "name", str(actual_api))
    if actual_api_name != "Direct3D11":
        raise RuntimeError(
            f"WindowsBar benchmark requires Direct3D11; actual={actual_api_name}"
        )

    initial_image = _stable_window_image(window)
    _invoke(window, "selectSecond")
    selected_image = _stable_window_image(window)
    _invoke(window, "selectFirst")
    restored_image = _stable_window_image(window)
    if selected_image == initial_image:
        raise RuntimeError("WindowsBar selection did not change D3D11 pixels")
    if restored_image != initial_image:
        raise RuntimeError("WindowsBar selection did not restore stable D3D11 pixels")

    if args.image_output is not None:
        args.image_output.parent.mkdir(parents=True, exist_ok=True)
        if not initial_image.save(str(args.image_output)):
            raise RuntimeError(f"Failed to save D3D11 image: {args.image_output}")

    navigation_bar = window.findChild(QObject, "navigationBar")
    bottom_tab_bar = window.findChild(QObject, "bottomTabBarContent")
    if navigation_bar is None:
        raise RuntimeError("WindowsBar benchmark could not find NavigationBar")
    if args.mode == "compact" and bottom_tab_bar is None:
        raise RuntimeError("Compact WindowsBar did not create BottomTabBar")
    if args.mode == "desktop" and bottom_tab_bar is not None:
        raise RuntimeError("Desktop WindowsBar unexpectedly created BottomTabBar")

    visual_items = _visual_items(window)
    failures = [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]
    if failures:
        raise RuntimeError("; ".join(failures))

    result = {
        "mode": args.mode,
        "items": args.items,
        "requested_graphics_api": "Direct3D11",
        "actual_graphics_api": actual_api_name,
        "package_path": str(package_path),
        "qml_load_ms": round(qml_load_ms, 3),
        "construction_ms": round(construction_ms, 3),
        "ready_frame_ms": round(ready_frame_ms, 3),
        "qquickitem_count": len(visual_items),
        "qobject_count": len(_owned_objects(window, visual_items)),
        "navigation_item_count": _navigation_item_count(visual_items),
        "navigation_bar_visible": navigation_bar.property("visible"),
        "bottom_tab_bar_present": bottom_tab_bar is not None,
        "initial_hash": _image_hash(initial_image),
        "selected_hash": _image_hash(selected_image),
        "restored_hash": _image_hash(restored_image),
        "qt_failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    window.close()
    qInstallMessageHandler(previous_handler)
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
