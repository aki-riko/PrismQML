# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""handleWheel 容器的平滑滚轮层合同。Smooth wheel-layer contracts for handleWheel surfaces.

回归来源: SmoothScrollWheelArea 的 z 若低于所属 Flickable, 交互式(触摸拖拽启用)的
Flickable 会先按原生路径消费滚轮, SmoothScrollHelper 收不到事件, 750ms 平滑动画退化成
短促的原生缓动, 表现为"平滑滚动没了"。
"""

import re
from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
WHEEL_LAYER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "ScrollBar"
    / "_internal"
    / "SmoothScrollWheelArea.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "handle-wheel-smooth-scroll.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as ScrollBarLib

Window {
    width: 620
    height: 300
    visible: true

    ScrollBarLib.ScrollAreaList {
        id: areaList
        objectName: "areaList"
        x: 20
        y: 20
        width: 240
        height: 200
        itemHeight: 30
        model: 40
        delegate: Rectangle { width: 220; height: 30; color: "transparent" }
    }

    ListWidget {
        id: listWidget
        objectName: "listWidget"
        x: 300
        y: 20
        width: 260
        height: 200
        model: {
            var rows = []
            for (var i = 0; i < 40; i++) rows.push("row " + i)
            return rows
        }
        itemDelegate: Rectangle { width: 220; height: 30; color: "transparent" }
    }
}
"""

LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def code_only(source: str) -> str:
    """Drop comments so the gate measures code, not prose. 去注释, 只量代码。"""
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", source))


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(root):
    result = []
    seen = set()
    pending = [root]
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        result.append(item)
        if hasattr(item, "childItems"):
            pending.extend(item.childItems())
        pending.extend(item.children())
    return result


def _first_by_class(control, fragment: str):
    for child in _descendants(control):
        if fragment in child.metaObject().className():
            return child
    return None


def _viewport(control):
    for child in _descendants(control):
        if "QQuickListView" in child.metaObject().className() and (
            child.metaObject().indexOfProperty("contentY") >= 0
        ):
            return child
    return None


def _send_wheel(window: QQuickWindow, item: QQuickItem, delta: int) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(window.x() + position.x(), window.y() + position.y())
    event = QWheelEvent(
        position,
        global_position,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump()
    _pump()
    controls = {
        name: window.findChild(QQuickItem, name) for name in ("areaList", "listWidget")
    }
    assert all(controls.values()), controls
    return engine, component, window, controls, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


@pytest.mark.parametrize("surface", ["areaList", "listWidget"])
def test_handle_wheel_surfaces_drive_smooth_scroll_helper(qapp, surface):
    """A real wheel tick must animate through SmoothScrollHelper. 真实滚轮必须经平滑滚动助手驱动。"""
    engine, component, window, controls, warnings = _create_scene()
    try:
        control = controls[surface]
        viewport = _viewport(control)
        assert viewport is not None
        helper = _first_by_class(control, "SmoothScrollHelper")
        assert helper is not None
        assert helper.property("enabled")
        assert viewport.property("contentHeight") > viewport.property("height")

        viewport.setProperty("contentY", 0)
        assert QCoreApplication.processEvents() is None
        _send_wheel(window, viewport, -120)

        # Native Flickable scrolling moves contentY without ever touching these
        # two properties, so a zeroed target is the regression signature. The
        # handler's own blocking mode owns the event, so isAccepted() is not a
        # usable signal here. 原生 Flickable 滚动只改 contentY, 从不触碰这两个属性;
        # 目标值为 0 即回归特征。处理器以自己的 blocking 模式接管事件, 因此不能用
        # isAccepted() 作为判据。
        target = helper.property("_targetY")
        assert target == pytest.approx(helper.property("step")), (
            "wheel bypassed SmoothScrollHelper and used native scrolling"
        )
        assert helper.property("_smoothY") < target, "smooth animation was applied instantly"
        assert _wait_for(
            lambda: viewport.property("contentY") == pytest.approx(target)
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_wheel_layer_handles_wheel_as_a_handler():
    """Rollback guard: the shared wheel layer must stay a blocking handler. 防回流: 滚轮层必须保持为阻止原生滚动的处理器。"""
    code = code_only(WHEEL_LAYER_SOURCE.read_text(encoding="utf-8"))
    # A MouseArea competes as a plain item: lowered it loses the wheel to the
    # target's native scrolling, raised it outranks nested controls.
    # MouseArea 以普通项竞争: 下沉会被目标原生滚动抢走, 抬升则压过内嵌控件。
    assert "WheelHandler {" in code
    assert "MouseArea {" not in code
    assert "blocking: true" in code
    assert "Enums.zIndex.background" not in code
    # Nested priority belongs to Qt's handler competition; this layer must not
    # re-implement a hand-off that Qt cannot honor.
    # 内嵌优先权归 Qt 处理器竞争; 本层不得重复实现 Qt 无法兑现的交还。
    assert "_nestedScrollableAt" not in code


def test_wheel_layer_source_follows_conventions():
    path = PurePosixPath(WHEEL_LAYER_SOURCE.relative_to(ROOT).as_posix())
    violations = [
        violation
        for violation in scan_source_text(
            WHEEL_LAYER_SOURCE.read_text(encoding="utf-8"), path
        )
        if violation.rule in {"QML008", "QML009"}
    ]
    assert violations == []
