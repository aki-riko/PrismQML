# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""BottomSheet runtime contracts. BottomSheet 运行时合同。"""

import gc
import time
from pathlib import Path

import pytest
import shiboken6
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
from PySide6.QtGui import QAccessible, QAccessibleActionInterface
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import Skin, getSkin, register_types, setSkin

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "bottom-sheet.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int detentMedium: Enums.sheet.detent_medium
    readonly property int detentLarge: Enums.sheet.detent_large
    readonly property real mediumRatio: Enums.sheet.mediumRatio
    readonly property int topInset: Enums.sheet.topInset
    readonly property real widthRatio: Enums.sheet.widthRatio
    readonly property int modalZ: Enums.zIndex.modal

    width: 800
    height: 600
    visible: true

    BottomSheet {
        id: sheet
        objectName: "sheet"

        Rectangle {
            objectName: "sheetContent"
            width: 80
            height: 40
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _create_scene(source=SCENE_SOURCE, scene_url=SCENE_URL):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, scene_url)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    if shiboken6.isValid(window):
        window.close()
        window.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    # Collect wrapper cycles now: left for a later GC they are torn down inside an
    # unrelated event loop, which crashed Windows CI (0xC0000005).
    # 立即回收包装环：留给之后的 GC 会在无关的事件循环中析构，曾让 Windows CI 崩溃。
    gc.collect()


@pytest.fixture
def sheet_scene(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        panel = sheet.findChild(QQuickItem, "bottomSheetPanel")
        assert sheet is not None and panel is not None
        yield window, sheet, panel, warnings
    finally:
        _dispose_scene(engine, component, window)


def _open(sheet) -> None:
    sheet.metaObject().invokeMethod(sheet, "open")
    assert _wait_for(lambda: sheet.property("revealProgress") == 1)


def _close(sheet) -> None:
    # Record progress at the instant the sheet hides: the slide-out must already be
    # complete, otherwise the base restore timer cut it short.
    # 记录弹层隐藏瞬间的进度：此时滑出必须已完成，否则说明基类恢复计时器截断了它。
    progress_at_hide = []

    def _on_visible_changed():
        if not sheet.isVisible():
            progress_at_hide.append(sheet.property("revealProgress"))

    sheet.visibleChanged.connect(_on_visible_changed)
    try:
        sheet.metaObject().invokeMethod(sheet, "close")
        assert _wait_for(lambda: not sheet.isVisible())
    finally:
        sheet.visibleChanged.disconnect(_on_visible_changed)
    assert progress_at_hide == [0]


def test_bottom_sheet_is_hidden_until_opened(sheet_scene):
    _window, sheet, _panel, warnings = sheet_scene

    assert not sheet.isVisible()
    assert sheet.property("revealProgress") == 0
    assert warnings == []


def test_bottom_sheet_rests_at_medium_detent_on_window_overlay(sheet_scene):
    window, sheet, panel, warnings = sheet_scene

    _open(sheet)

    assert sheet.isVisible()
    assert sheet.parentItem() is window.contentItem()
    assert sheet.property("stackIndex") == 0
    # One stack slot above the modal level, still below the next zIndex level
    # 比 modal 层高一个叠层间隔，仍低于下一 zIndex 级
    assert window.property("modalZ") < sheet.z() < window.property("modalZ") + 1
    expected_height = window.height() * window.property("mediumRatio")
    assert panel.height() == pytest.approx(expected_height)
    assert panel.y() == pytest.approx(window.height() - expected_height)
    assert panel.width() == pytest.approx(window.width() * window.property("widthRatio"))
    assert panel.x() == pytest.approx((window.width() - panel.width()) / 2)
    content = sheet.findChild(QQuickItem, "sheetContent")
    assert content is not None and content.isVisible()
    assert warnings == []


def test_bottom_sheet_large_detent_leaves_top_inset(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene

    sheet.setProperty("detent", window.property("detentLarge"))
    _open(sheet)

    assert panel.y() == pytest.approx(window.property("topInset"))
    assert panel.height() == pytest.approx(
        window.height() - window.property("topInset")
    )


def test_bottom_sheet_close_slides_out_and_hides(sheet_scene):
    window, sheet, panel, warnings = sheet_scene

    _open(sheet)
    _close(sheet)

    assert sheet.property("revealProgress") == 0
    assert panel.y() == pytest.approx(window.height())
    assert sheet.property("opened") is False
    assert warnings == []


def test_bottom_sheet_reopen_after_close(sheet_scene):
    _window, sheet, _panel, warnings = sheet_scene

    _open(sheet)
    _close(sheet)
    _open(sheet)

    assert sheet.isVisible()
    assert warnings == []


@pytest.mark.parametrize("skin", list(Skin))
def test_bottom_sheet_opens_without_warnings_in_every_skin(qapp, skin):
    previous_skin = getSkin()
    setSkin(skin)
    _pump()
    engine, component, window, warnings = _create_scene()
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        _open(sheet)
        assert warnings == [], (skin, warnings)
    finally:
        _dispose_scene(engine, component, window)
        setSkin(previous_skin)
        _pump()


NESTED_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "bottom-sheet-nested.qml")
)
NESTED_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int stackPeek: Enums.sheet.stackPeek
    readonly property int topInset: Enums.sheet.topInset
    readonly property real stackScaleStep: Enums.sheet.stackScaleStep
    readonly property int maxVisibleDepth: Enums.sheet.maxVisibleDepth
    readonly property color transparentColor: Enums.transparent

    width: 800
    height: 600
    visible: true

    BottomSheet {
        objectName: "first"

        BottomSheet {
            objectName: "second"
            detent: Enums.sheet.detent_large

            BottomSheet {
                objectName: "third"
            }
        }
    }

    BottomSheet {
        objectName: "fourth"
    }
}
"""

SHEET_NAMES = ("first", "second", "third", "fourth")


@pytest.fixture
def nested_scene(qapp):
    engine, component, window, warnings = _create_scene(
        NESTED_SCENE_SOURCE, NESTED_SCENE_URL
    )
    try:
        sheets = {name: window.findChild(QQuickItem, name) for name in SHEET_NAMES}
        assert all(sheets.values()), sheets
        panels = {
            name: sheet.findChild(QQuickItem, "bottomSheetPanel")
            for name, sheet in sheets.items()
        }
        yield window, sheets, panels, warnings
    finally:
        _dispose_scene(engine, component, window)


def _settled(*sheets) -> bool:
    return all(
        sheet.property("revealProgress") in (0, 1)
        and sheet.property("stackLift") == int(sheet.property("stackLift"))
        for sheet in sheets
    )


def _open_all(*sheets) -> None:
    for sheet in sheets:
        _open(sheet)
    assert _wait_for(lambda: _settled(*sheets))


def test_nested_sheets_stack_in_open_order(nested_scene):
    window, sheets, panels, warnings = nested_scene
    first, second, third = sheets["first"], sheets["second"], sheets["third"]

    _open_all(first, second, third)

    host = window.contentItem()
    assert all(sheet.parentItem() is host for sheet in (first, second, third))
    assert [s.property("stackIndex") for s in (first, second, third)] == [0, 1, 2]
    assert first.z() < second.z() < third.z()
    assert [s.property("stackLift") for s in (first, second, third)] == [2, 1, 0]
    step = window.property("stackScaleStep")
    assert panels["first"].scale() == pytest.approx(1 - 2 * step)
    assert panels["second"].scale() == pytest.approx(1 - step)
    assert panels["third"].scale() == 1
    assert warnings == []


def test_covered_sheets_peek_above_the_sheet_on_top(nested_scene):
    window, sheets, panels, _warnings = nested_scene
    first, second, third = sheets["first"], sheets["second"], sheets["third"]

    _open_all(first, second, third)

    peek = window.property("stackPeek")
    # A covered sheet rises one peek above the higher of its own resting top and the
    # top of the sheet above, never past the host top. Second (large) already rests
    # above third (medium), so it rises from its own resting top.
    # 被覆盖层从"自身静止顶边"与"上层顶边"中较高者再上移一个露边距离，且不越过宿主顶部。
    # 第二层（全展开）静止时已高于第三层（中档），因此从自身静止顶边上移。
    second_rest = window.property("topInset")
    assert panels["second"].y() == pytest.approx(
        max(0, min(second_rest, panels["third"].y()) - peek)
    )
    first_rest = window.height() - panels["first"].height()
    assert panels["first"].y() == pytest.approx(
        max(0, min(first_rest, panels["second"].y()) - peek)
    )
    assert panels["first"].y() < panels["second"].y() < panels["third"].y()


def test_only_the_bottom_sheet_dims_the_page(nested_scene):
    window, sheets, _panels, _warnings = nested_scene
    first, second = sheets["first"], sheets["second"]

    _open_all(first, second)

    # The base scrim only blocks input; the drawn scrim belongs to the bottom sheet
    # 基类遮罩只拦截输入；绘制的遮罩只属于最底层
    assert first.property("maskColor") == window.property("transparentColor")
    assert second.property("maskColor") == window.property("transparentColor")
    scrim = first.findChild(QQuickItem, "bottomSheetScrim")
    assert scrim.isVisible() and scrim.opacity() == 1
    assert not second.findChild(QQuickItem, "bottomSheetScrim").isVisible()
    dim = first.findChild(QQuickItem, "bottomSheetDim")
    assert dim.isVisible() and dim.opacity() > 0
    assert not second.findChild(QQuickItem, "bottomSheetDim").isVisible()


def test_closing_the_top_sheet_restores_the_one_below(nested_scene):
    _window, sheets, panels, warnings = nested_scene
    first, second = sheets["first"], sheets["second"]

    _open(first)
    resting_y = panels["first"].y()
    _open_all(first, second)
    assert panels["first"].y() < resting_y

    _close(second)

    assert _wait_for(lambda: _settled(first))
    assert second.property("stackIndex") == -1
    assert first.property("stackLift") == 0
    assert panels["first"].scale() == 1
    assert panels["first"].y() == pytest.approx(resting_y)
    assert warnings == []


def test_closing_a_parent_closes_its_nested_sheets(nested_scene):
    _window, sheets, _panels, warnings = nested_scene
    first, second, third = sheets["first"], sheets["second"], sheets["third"]

    _open_all(first, second, third)
    first.metaObject().invokeMethod(first, "close")

    assert _wait_for(
        lambda: not any(s.isVisible() for s in (first, second, third))
    )
    assert all(s.property("stackIndex") == -1 for s in (first, second, third))
    assert warnings == []


def test_reopened_sheet_returns_to_the_top(nested_scene):
    _window, sheets, _panels, _warnings = nested_scene
    first, fourth = sheets["first"], sheets["fourth"]

    _open_all(first, fourth)
    _close(first)
    _open(first)
    assert _wait_for(lambda: _settled(first, fourth))

    assert first.property("stackIndex") == 1
    assert fourth.property("stackIndex") == 0
    assert first.z() > fourth.z()


def test_sheets_past_the_visible_depth_fade_out(nested_scene):
    window, sheets, _panels, _warnings = nested_scene
    ordered = [sheets[name] for name in SHEET_NAMES]

    _open_all(*ordered)

    depth = window.property("maxVisibleDepth")
    assert ordered[0].property("stackLift") == depth
    surface = ordered[0].findChild(QQuickItem, "bottomSheetPanel").parentItem()
    assert surface.opacity() == 0
    assert all(
        s.findChild(QQuickItem, "bottomSheetPanel").parentItem().opacity() == 1
        for s in ordered[1:]
    )


# ==================== Drag and detents 拖拽与停靠 ====================


def _grabber_point(window, sheet) -> QPoint:
    grabber = sheet.findChild(QQuickItem, "bottomSheetGrabber")
    assert grabber is not None and grabber.isVisible()
    center = grabber.mapToItem(
        window.contentItem(), QPointF(grabber.width() / 2, grabber.height() / 2)
    )
    return QPoint(round(center.x()), round(center.y()))


def _wall_wait(milliseconds: int) -> None:
    """Spin the event loop for a real wall-clock span.

    The QTest ``delay`` argument does not reliably separate events on this
    platform: a probe saw QML handle a move and the following release 0.2ms apart
    despite a 300ms delay. Measured gaps must come from real time.
    按真实墙钟时长转动事件循环。QTest 的 ``delay`` 参数在此平台不能可靠拉开事件间隔：
    探针实测设置 300ms 延迟后，QML 处理移动与随后松手只隔 0.2ms。需要测量的间隔必须来自真实时间。
    """
    deadline = time.perf_counter() + milliseconds / 1000
    while time.perf_counter() < deadline:
        _pump(5)


def _drag_grabber(window, sheet, distance: int, steps: int = 8, step_ms: int = 40,
                  pause_ms: int = 0):
    """Drag the grabber vertically with real time between events.

    竖直拖动手柄，事件之间间隔真实时间。
    """
    start = _grabber_point(window, sheet)
    QTest.mouseMove(window, start)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    for index in range(1, steps + 1):
        _wall_wait(step_ms)
        QTest.mouseMove(
            window, QPoint(start.x(), start.y() + distance * index // steps)
        )
    _wall_wait(pause_ms or step_ms)
    end = QPoint(start.x(), start.y() + distance)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, end
    )


def _resting(sheet) -> bool:
    return (
        sheet.property("revealProgress") in (0, 1)
        and sheet.property("_heightExtra") == 0
    )


def test_small_drag_springs_back_to_the_detent(sheet_scene):
    window, sheet, panel, warnings = sheet_scene
    _open(sheet)
    resting_y = panel.y()

    _drag_grabber(window, sheet, 30)

    assert _wait_for(lambda: _resting(sheet))
    assert sheet.property("opened") is True
    assert sheet.property("detent") == window.property("detentMedium")
    assert panel.y() == pytest.approx(resting_y)
    assert warnings == []


def test_drag_down_past_threshold_closes_from_medium(sheet_scene):
    window, sheet, _panel, warnings = sheet_scene
    _open(sheet)

    _drag_grabber(window, sheet, 160)

    assert _wait_for(lambda: not sheet.isVisible())
    assert sheet.property("opened") is False
    assert sheet.property("stackIndex") == -1
    assert sheet.property("_heightExtra") == 0
    assert warnings == []


def test_drag_up_expands_medium_to_large(sheet_scene):
    window, sheet, panel, warnings = sheet_scene
    _open(sheet)

    _drag_grabber(window, sheet, -160)

    assert _wait_for(lambda: _resting(sheet))
    assert sheet.property("detent") == window.property("detentLarge")
    assert panel.y() == pytest.approx(window.property("topInset"))
    assert warnings == []


def test_drag_down_from_large_collapses_to_medium(sheet_scene):
    window, sheet, panel, warnings = sheet_scene
    sheet.setProperty("detent", window.property("detentLarge"))
    _open(sheet)

    _drag_grabber(window, sheet, 160)

    assert _wait_for(lambda: _resting(sheet))
    assert sheet.property("opened") is True
    assert sheet.property("detent") == window.property("detentMedium")
    medium_height = window.height() * window.property("mediumRatio")
    assert panel.y() == pytest.approx(window.height() - medium_height)
    assert warnings == []


def test_fast_flick_down_closes_despite_short_distance(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _open(sheet)

    # 60px is below the dismiss distance; 20px per 10ms is ~2000 px/s, a flick.
    # 60px 未达关闭距离；每 10ms 移动 20px 约合 2000 像素/秒，属于甩动。
    _drag_grabber(window, sheet, 60, steps=3, step_ms=10)

    assert _wait_for(lambda: not sheet.isVisible())
    assert sheet.property("opened") is False


def test_drag_up_is_capped_when_large_detent_is_disallowed(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    sheet.setProperty("allowLargeDetent", False)
    _open(sheet)
    resting_y = panel.y()

    _drag_grabber(window, sheet, -160)

    assert _wait_for(lambda: _resting(sheet))
    assert sheet.property("detent") == window.property("detentMedium")
    assert panel.y() == pytest.approx(resting_y)


def test_tapping_the_grabber_toggles_the_detent(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    _open(sheet)

    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _grabber_point(window, sheet),
    )
    assert _wait_for(lambda: _resting(sheet)
                     and sheet.property("detent") == window.property("detentLarge"))
    assert panel.y() == pytest.approx(window.property("topInset"))

    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _grabber_point(window, sheet),
    )
    assert _wait_for(lambda: _resting(sheet)
                     and sheet.property("detent") == window.property("detentMedium"))


def test_detent_switch_keeps_the_top_edge_still(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    sheet.setProperty("detent", window.property("detentLarge"))
    _open(sheet)
    top_before = panel.y()

    sheet.setProperty("detent", window.property("detentMedium"))

    # Same event-loop turn: no jump, the panel then slides down to medium.
    # 同一事件循环轮次内不跳变，随后面板滑到中档。
    assert panel.y() == pytest.approx(top_before)
    assert _wait_for(lambda: _resting(sheet))
    medium_height = window.height() * window.property("mediumRatio")
    assert panel.y() == pytest.approx(window.height() - medium_height)


def test_only_the_top_sheet_grabber_drags(nested_scene):
    _window, sheets, _panels, _warnings = nested_scene
    first, second = sheets["first"], sheets["second"]

    _open_all(first, second)

    assert not first.findChild(QQuickItem, "bottomSheetGrabber").isEnabled()
    assert second.findChild(QQuickItem, "bottomSheetGrabber").isEnabled()


def test_hidden_grabber_gives_content_the_top_space(qapp):
    source = SCENE_SOURCE.replace(
        b'objectName: "sheet"', b'objectName: "sheet"\n        showGrabber: false'
    )
    engine, component, window, _warnings = _create_scene(source)
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        _open(sheet)
        grabber = sheet.findChild(QQuickItem, "bottomSheetGrabber")
        content = sheet.findChild(QQuickItem, "contentItem")
        assert not grabber.isVisible()
        assert content.y() < grabber.height()
    finally:
        _dispose_scene(engine, component, window)


def test_panel_follows_the_finger_mid_drag(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    sheet.setProperty("allowLargeDetent", False)
    _open(sheet)
    resting_y = panel.y()
    start = _grabber_point(window, sheet)
    QTest.mouseMove(window, start)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    try:
        for step in range(1, 7):
            _wall_wait(30)
            QTest.mouseMove(window, QPoint(start.x(), start.y() + 10 * step))
        # Down: the top edge tracks the finger past the drag threshold
        # 向下：越过拖拽阈值后顶边跟随手指
        down_y = panel.y()
        assert resting_y + 30 < down_y <= resting_y + 60
        for step in range(1, 11):
            _wall_wait(30)
            QTest.mouseMove(window, QPoint(start.x(), start.y() + 60 - 12 * step))
        # Up past the tallest detent: rubber band moves less than the finger
        # 向上越过最高停靠：阻尼使面板位移小于手指位移
        up_shift = resting_y - panel.y()
        assert 0 < up_shift < 60
    finally:
        _wall_wait(30)
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(start.x(), start.y() - 60),
        )
    assert _wait_for(lambda: _resting(sheet))
    assert panel.y() == pytest.approx(resting_y)


def test_pausing_before_release_cancels_a_flick(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _open(sheet)

    # Same flick as the close case, but held still well past the stale window
    # 与关闭用例相同的甩动，但抬起前静止明显超过失效窗口
    _drag_grabber(window, sheet, 60, steps=3, step_ms=10, pause_ms=300)

    assert _wait_for(lambda: _resting(sheet))
    assert sheet.property("opened") is True


# ==================== Keyboard and accessibility 键盘与无障碍 ====================


def _activate(window) -> None:
    window.requestActivate()
    _wait_for(lambda: window.isActive(), 500)


def test_open_sheet_takes_keyboard_focus(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _activate(window)

    _open(sheet)

    assert _wait_for(lambda: sheet.hasActiveFocus())


def test_escape_closes_only_the_top_sheet(nested_scene):
    window, sheets, _panels, warnings = nested_scene
    first, second = sheets["first"], sheets["second"]
    _activate(window)
    _open_all(first, second)
    assert _wait_for(lambda: second.hasActiveFocus())

    QTest.keyClick(window, Qt.Key.Key_Escape)

    assert _wait_for(lambda: not second.isVisible())
    assert first.property("opened") is True
    # Focus returns to the sheet below, so the next Escape closes it
    # 焦点交还给下一层，再按一次 Escape 即关闭它
    assert _wait_for(lambda: first.hasActiveFocus())
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _wait_for(lambda: not first.isVisible())
    assert warnings == []


def test_scrim_click_reaches_only_the_top_sheet(nested_scene):
    window, sheets, panels, _warnings = nested_scene
    first, second = sheets["first"], sheets["second"]
    _open_all(first, second)

    # Above every panel: the covered sheet's scrim lies under the top sheet's
    # 位于所有面板上方：被覆盖层的遮罩在栈顶弹层遮罩之下
    point = QPoint(window.width() // 2, round(panels["first"].y()) // 2)
    assert point.y() > 0
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )

    assert _wait_for(lambda: not second.isVisible())
    assert first.property("opened") is True


def test_sheet_and_grabber_expose_accessible_roles(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _open(sheet)
    grabber = sheet.findChild(QQuickItem, "bottomSheetGrabber")

    sheet_iface = QAccessible.queryAccessibleInterface(sheet)
    grabber_iface = QAccessible.queryAccessibleInterface(grabber)

    assert sheet_iface is not None and grabber_iface is not None
    assert sheet_iface.role() == QAccessible.Role.Dialog
    assert grabber_iface.role() == QAccessible.Role.Button
    assert grabber_iface.text(QAccessible.Text.Name) != ""


def test_grabber_press_action_cycles_the_detent(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _open(sheet)
    grabber = sheet.findChild(QQuickItem, "bottomSheetGrabber")
    action = QAccessible.queryAccessibleInterface(grabber).actionInterface()
    assert action is not None

    action.doAction(QAccessibleActionInterface.pressAction())

    assert _wait_for(lambda: _resting(sheet)
                     and sheet.property("detent") == window.property("detentLarge"))


# ==================== Width and elevation 宽度与立体感 ====================


def test_custom_width_ratio_is_clamped_and_centered(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    sheet.setProperty("sheetWidthRatio", 0.5)
    _open(sheet)
    assert panel.width() == pytest.approx(window.width() * 0.5)
    assert panel.x() == pytest.approx(window.width() * 0.25)

    sheet.setProperty("sheetWidthRatio", 1.5)
    _pump()
    assert panel.width() == pytest.approx(window.width())


def test_shadows_cast_upward_and_shrink_with_the_panel(nested_scene):
    _window, sheets, panels, _warnings = nested_scene
    first, second = sheets["first"], sheets["second"]
    _open_all(first, second)

    for name in ("bottomSheetAmbientShadow", "bottomSheetContactShadow"):
        shadow = first.findChild(QQuickItem, name)
        assert shadow is not None and shadow.isVisible(), name
        # The panel rises from the host bottom; a downward shadow would be off-screen
        # 面板从宿主底部升起，向下的阴影会落在屏幕外
        assert shadow.property("offset").y() < 0, name
        assert shadow.scale() == pytest.approx(panels["first"].scale()), name
    edge = first.findChild(QQuickItem, "bottomSheetEdge")
    assert edge.isVisible()
    assert edge.height() > panels["first"].height()


def test_outlined_skins_skip_the_soft_shadow_stack(qapp):
    previous_skin = getSkin()
    setSkin(Skin.NEOBRUTALISM)
    _pump()
    engine, component, window, warnings = _create_scene()
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        _open(sheet)
        for name in ("bottomSheetAmbientShadow", "bottomSheetContactShadow",
                     "bottomSheetEdge"):
            assert not sheet.findChild(QQuickItem, name).isVisible(), name
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        setSkin(previous_skin)
        _pump()



# ==================== Motion continuity 动效连贯 ====================


def test_scrim_tracks_the_reveal_while_dragging(sheet_scene):
    window, sheet, _panel, _warnings = sheet_scene
    _open(sheet)
    scrim = sheet.findChild(QQuickItem, "bottomSheetScrim")
    start = _grabber_point(window, sheet)
    QTest.mouseMove(window, start)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    try:
        for step in range(1, 7):
            _wall_wait(30)
            QTest.mouseMove(window, QPoint(start.x(), start.y() + 10 * step))
        reveal = sheet.property("revealProgress")
        # Mid-drag the page brightens exactly as far as the sheet has dropped
        # 拖拽中页面变亮的程度与面板下落程度一致
        assert 0 < reveal < 1
        assert scrim.opacity() == pytest.approx(reveal)
    finally:
        _wall_wait(300)
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(start.x(), start.y() + 60),
        )
    assert _wait_for(lambda: _resting(sheet))
    assert scrim.opacity() == 1


def test_deep_sheets_fade_without_losing_the_page_scrim(nested_scene):
    _window, sheets, _panels, _warnings = nested_scene
    ordered = [sheets[name] for name in SHEET_NAMES]
    _open_all(*ordered)

    bottom = ordered[0]
    layer = bottom.findChild(QQuickItem, "bottomSheetPanel").parentItem()
    scrim = bottom.findChild(QQuickItem, "bottomSheetScrim")
    assert layer.opacity() == 0
    assert scrim.isVisible() and scrim.opacity() == 1


def test_release_duration_matches_the_finger_speed(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(b"""
import QtQuick
import "../../prismqml/PrismQML/controls/containers/BottomSheet/_internal/BottomSheetGesture.js" as G
QtObject {
    readonly property var curve: [0.32, 0.72, 0, 1, 1, 1]
    readonly property int fast: G.releaseDuration(300, 2000, curve, 150, 300)
    readonly property int matched: G.releaseDuration(300, 3000, curve, 150, 300)
    readonly property int clamped: G.releaseDuration(300, 20000, curve, 150, 300)
    readonly property int tooSlow: G.releaseDuration(300, 100, curve, 150, 300)
    readonly property int away: G.releaseDuration(300, -2000, curve, 150, 300)
    readonly property int reduced: G.releaseDuration(300, 2000, curve, 0, 0)
}
""", QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "release-duration.qml")))
    obj = component.create()
    try:
        assert obj is not None, [e.toString() for e in component.errors()]
        # 300px at 2000px/s needs 337.5ms (start slope 0.72/0.32 = 2.25), over the cap.
        # Capped at 300ms the curve starts at 2250px/s, 250 off the finger, versus 2000
        # off when starting from rest, so the capped curve wins.
        # 300px、2000px/s 需 337.5ms（起步斜率 2.25），超过上限。截断到 300ms 时起步
        # 2250px/s，与手指差 250；从静止起步差 2000，故取截断曲线。
        assert obj.property("fast") == 300
        # 300px at 3000px/s -> 2.25 * 300 / 3000 s = 225ms, inside [150, 300]
        # 300px、3000px/s 时为 225ms，落在 [150, 300] 区间内
        assert obj.property("matched") == 225
        assert obj.property("clamped") == 150
        # 100px/s: capped start 2250px/s is 2150 off, rest is 100 off, so default
        # 100px/s 时截断起步差 2150，静止起步只差 100，故用默认动效
        assert obj.property("tooSlow") == 0
        assert obj.property("away") == 0
        assert obj.property("reduced") == 0
    finally:
        obj.deleteLater() if obj is not None else None
        component.deleteLater()
        engine.deleteLater()


def test_grabbing_mid_open_hands_the_panel_to_the_finger(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene
    sheet.metaObject().invokeMethod(sheet, "open")
    # Catch the panel while it is still rising 在面板仍在上升时抓住它
    assert _wait_for(lambda: 0.3 < sheet.property("revealProgress") < 0.9, 1000)
    # Press with no event pump between reading the grabber position and pressing:
    # the panel is still rising, and a mouseMove first let it slip past the pointer
    # in 4 of 30 runs, so the drag never started.
    # 读取手柄位置与按下之间不转事件循环：面板仍在上升，先 mouseMove 会让它在 30 次中
    # 有 4 次越过指针，拖拽根本没开始。
    start = _grabber_point(window, sheet)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    try:
        assert sheet.property("_dragging") is False
        for step in range(1, 5):
            _wall_wait(20)
            QTest.mouseMove(window, QPoint(start.x(), start.y() + 10 * step))
        assert sheet.property("_dragging") is True
        held_y = panel.y()
        # Hold still: a leftover open animation would keep pulling the panel up
        # 保持不动：残留的打开动画会继续把面板往上拉
        _wall_wait(400)
        assert panel.y() == pytest.approx(held_y, abs=1)
        assert sheet.property("revealProgress") < 1
    finally:
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(start.x(), start.y() + 40),
        )
    assert _wait_for(lambda: _resting(sheet))
