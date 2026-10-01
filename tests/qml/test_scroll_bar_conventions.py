# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/1 of the former test_scroll_bar_conventions.py."""
import pytest  # noqa: F401
from PySide6.QtCore import Q_ARG  # noqa: F401
from PySide6.QtQml import QQmlEngine  # noqa: F401
from scroll_bar_conventions_shared import *
from scroll_bar_conventions_shared import (
    _pump,
    _wait_for,
    _wait_for_stable,
    _smooth_scroll_helper,
    _send_wheel,
    _new_visible_windows,
    _outward_excursions,
    _create_scene,
    _dispose_scene,
)

def test_smooth_helpers_clamp_animate_and_sync(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene
    assert window.property("verticalMax") == pytest.approx(480)
    assert window.property("horizontalMax") == pytest.approx(520)

    assert QMetaObject.invokeMethod(window, "scrollVertical")
    assert window.property("verticalTarget") == pytest.approx(180)
    assert _wait_for(lambda: window.property("verticalY") > 0)
    assert window.property("verticalY") < 180
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(180))

    assert QMetaObject.invokeMethod(window, "overshootVertical")
    assert window.property("verticalTarget") == pytest.approx(480)
    assert window.property("verticalOvershot")
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(480))
    assert _wait_for(lambda: not window.property("verticalOvershot"))

    assert QMetaObject.invokeMethod(window, "syncVertical")
    assert window.property("verticalTarget") == pytest.approx(75)
    assert window.property("verticalY") == pytest.approx(75)

    assert QMetaObject.invokeMethod(window, "scrollHorizontal")
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(260))
    assert QMetaObject.invokeMethod(window, "scrollPopup")
    assert _wait_for(lambda: window.property("popupY") == pytest.approx(380))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_popup_scroll_supports_native_drag(scroll_scene):
    """Popup scrolling must accept native touch/mouse drags. 弹层滚动必须支持原生触摸/鼠标拖拽。"""
    window, items, warnings, windows_before = scroll_scene
    popup = items["popupFlick"]
    assert popup.property("interactive") is True
    popup.setProperty("contentY", popup.property("originY"))
    _pump(60)
    pos = popup.mapToScene(QPointF(popup.width() / 2, popup.height() * 0.75)).toPoint()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    for _ in range(6):
        pos = QPoint(pos.x(), pos.y() - 12)
        QTest.mouseMove(window, pos)
        _pump(16)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    _pump(220)
    assert popup.property("contentY") > 0
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_native_drag_then_wheel_continues_from_current_position(scroll_scene):
    """Native drag must rebase smooth scrolling before the next wheel tick. 原生拖拽后下一次滚轮必须从当前位置继续。"""
    window, items, warnings, windows_before = scroll_scene
    flick = next(
        item
        for item in items["defaultArea"].findChildren(QQuickItem)
        if "QQuickFlickable" in item.metaObject().className()
    )
    assert flick.property("interactive") is True
    flick.setProperty("contentY", flick.property("originY"))
    _pump(60)
    pos = flick.mapToScene(QPointF(flick.width() / 2, flick.height() * 0.75)).toPoint()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    for _ in range(6):
        pos = QPoint(pos.x(), pos.y() - 12)
        QTest.mouseMove(window, pos)
        _pump(16)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos)
    assert _wait_for(lambda: not flick.property("moving"), timeout_ms=3_000)
    dragged_y = float(flick.property("contentY"))
    assert dragged_y > 0

    _send_wheel(window, items["defaultArea"], 120)
    _pump(45)
    helper = _smooth_scroll_helper(items["defaultArea"], Qt.Orientation.Vertical)
    assert float(helper.property("targetPos")) < dragged_y
    _pump(700)
    assert float(flick.property("contentY")) < dragged_y
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_scroll_area_discards_stale_bounce_peak_after_gui_stall(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    maximum = helper.property("maxScroll")

    values = []
    area.contentYChanged.connect(
        lambda: values.append(float(area.property("contentY")))
    )
    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")

    _send_wheel(window, area, -360)
    _pump(45)
    assert values
    before_stall = values[-1]
    resume_index = len(values)

    QTest.qSleep(160)
    _pump(1000)
    resumed_values = values[resume_index:]
    assert resumed_values
    assert max(resumed_values) <= before_stall + 0.5
    assert area.property("contentY") == pytest.approx(maximum)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_scroll_area_preserves_original_return_curve_for_large_bounce(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    maximum = helper.property("maxScroll")
    step = helper.property("step")

    values = []
    area.contentYChanged.connect(
        lambda: values.append(float(area.property("contentY")))
    )

    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    _send_wheel(window, area, -120)
    _pump(1000)
    normal_values = values.copy()
    normal_peak = max(normal_values)
    normal_trough = min(normal_values)
    assert maximum - step * 0.08 <= normal_trough <= maximum - step * 0.03
    assert area.property("contentY") == pytest.approx(maximum)

    values.clear()
    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    _send_wheel(window, area, -360)
    _pump(1000)
    large_peak = max(values)
    peak_index = values.index(large_peak)
    return_values = values[peak_index:]
    large_trough = min(return_values)
    trough_index = return_values.index(large_trough)
    assert large_peak > normal_peak
    assert maximum - large_trough > maximum - normal_trough
    assert any(
        current > previous + 0.5
        for previous, current in zip(
            return_values[trough_index:], return_values[trough_index + 1:]
        )
    )
    assert area.property("contentY") == pytest.approx(maximum)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_horizontal_bounce_discards_stale_peak_after_gui_stall(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    flick = items["horizontalFlick"]

    assert QMetaObject.invokeMethod(window, "scrollHorizontalToEnd")
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(520))
    values = []
    flick.contentXChanged.connect(
        lambda: values.append(float(window.property("horizontalX")))
    )

    assert QMetaObject.invokeMethod(window, "overshootHorizontal")
    _pump(45)
    assert values
    before_stall = values[-1]
    resume_index = len(values)

    QTest.qSleep(160)
    _pump(1000)
    resumed_values = values[resume_index:]
    assert resumed_values
    assert max(resumed_values) <= before_stall + 0.5
    assert window.property("horizontalX") == pytest.approx(520)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_scroll_area_same_direction_wheel_does_not_amplify_bounce(scroll_scene):
    """Same-direction wheel during a bounce must not grow the peak.

    回弹期间的同向滚轮不得放大峰值。
    """
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    maximum = float(helper.property("maxScroll"))
    overshoot_limit = float(helper.property("_maxOvershoot"))

    values = []
    area.contentYChanged.connect(
        lambda: values.append(float(area.property("contentY")))
    )
    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")

    _send_wheel(window, area, -120)
    _pump(45)
    assert values
    first_peak = max(values)
    assert first_peak > maximum

    # Five more ticks in the same direction while the bounce is in flight.
    # 回弹进行中再发五次同向滚轮。
    for _ in range(5):
        _send_wheel(window, area, -120)
        _pump(40)
    _pump(1200)

    assert max(values) <= maximum + overshoot_limit + 0.5, max(values)
    assert _outward_excursions(values, maximum, False) == 1, values
    assert area.property("contentY") == pytest.approx(maximum)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def _outward_peaks(samples, tolerance=0.5):
    """Apex of each separate outward leg in (contentY, boundary) samples."""
    peaks = []
    current = None
    for content_y, maximum in samples:
        if content_y > maximum + tolerance:
            current = content_y if current is None else max(current, content_y)
        elif current is not None:
            peaks.append(current)
            current = None
    if current is not None:
        peaks.append(current)
    return peaks


def test_scroll_area_wheel_keeps_one_bounce_while_bounds_move(scroll_scene):
    """Bounds moving mid-overshoot must not amplify or relaunch the outward leg.

    超出期间边界移动不得放大或重启外移腿。

    The target is a DragAndOvershootBounds view, which declares that going out of
    bounds is legitimate. When its own bounds move it rewrites the axis to keep its
    position; the helper must treat that as a re-anchor rather than as the view
    rejecting the overshoot, otherwise the bounce is cancelled for the whole input
    burst. What must hold instead: the excursion stays inside the overshoot limit,
    never grows past the apex the same input burst already reached, and returns.
    目标是声明允许越界的 DragAndOvershootBounds 视图。它自身边界移动时会改写轴向以维持
    位置；helper 必须把该写入当作重新锚定，而不是视图拒绝超出，否则整个输入串的回弹都会被
    取消。此时应成立的是：位移不超出上限、不会被同一输入串放大、并能正常返回。
    """
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)

    assert QMetaObject.invokeMethod(helper, "scrollToEnd")
    assert _wait_for(
        lambda: not helper.property("isOvershot")
        and float(area.property("contentY"))
        == pytest.approx(float(helper.property("maxScroll")), abs=0.5),
        timeout_ms=3000,
    )

    # A moving boundary legitimately puts a stationary position out of bounds, so
    # counting boundary crossings cannot separate that from a relaunch. Jitter is
    # amplification of the apex within one input burst plus a peak past the limit.
    # 边界移动会合法地把静止位置变成越界，故穿越计数无法与重启区分。抖动的判据是
    # 同一输入串内峰值被放大，以及峰值超过超出上限。
    overshoot_limit = float(helper.property("_maxOvershoot"))
    samples = []
    area.contentYChanged.connect(
        lambda: samples.append(
            (
                round(float(area.property("contentY")), 1),
                round(float(helper.property("maxScroll")), 1),
            )
        )
    )
    outward_states = []
    helper._isOutwardBounceVChanged.connect(
        lambda: outward_states.append(bool(helper.property("_isOutwardBounceV")))
    )

    # Same-direction ticks while the bottom boundary keeps moving underneath.
    # 底部边界持续移动期间的同向滚轮。
    for index in range(6):
        _send_wheel(window, area, -120)
        if index % 2 == 0:
            assert QMetaObject.invokeMethod(window, "shrinkDefaultContent")
        else:
            assert QMetaObject.invokeMethod(window, "restoreDefaultContent")
        _pump(40)
    assert QMetaObject.invokeMethod(window, "restoreDefaultContent")
    _pump(1200)

    assert samples
    peaks = _outward_peaks(samples)
    assert peaks, samples
    # The input burst stays on its original outward leg and within the overshoot limit.
    # 连续输入保持原外移腿，且不得超出越界上限。
    assert peaks[-1] - peaks[0] <= overshoot_limit + 0.5, peaks
    peak_beyond = max(content_y - maximum for content_y, maximum in samples)
    assert peak_beyond <= overshoot_limit + 0.5, peak_beyond
    # An overshoot-capable view must never have its boundary revoked by its own
    # re-measure, which is the defect that killed the bounce on list surfaces.
    # 支持越界的视图不得因为自身重测而被撤销边界，正是该缺陷让列表面的回弹失效。
    guard = helper.property("verticalOvershootGuard")
    assert guard.property("revokedBoundary") == 0
    assert outward_states.count(True) == 1, outward_states
    # Growing content below the viewport must not drag the view down, so resting
    # anywhere inside the restored range is correct.
    # 视口下方内容变长不应拖动视图，故停在恢复后区间内的任意位置都正确。
    resting = float(area.property("contentY"))
    assert -0.5 <= resting <= float(helper.property("maxScroll")) + 0.5, resting
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def _flickable_item(item):
    return next(
        child
        for child in item.findChildren(QQuickItem)
        if "QQuickFlickable" in child.metaObject().className()
    )


def _scroll_to_boundary(helper, target, position_name, edge):
    method = "scrollToEnd" if edge == "end" else "scrollToStart"
    boundary = "maxScroll" if edge == "end" else "minScroll"
    assert QMetaObject.invokeMethod(helper, method)
    assert _wait_for(
        lambda: float(target.property(position_name))
        == pytest.approx(float(helper.property(boundary)), abs=0.5),
        timeout_ms=3000,
    )


def _prepare_bounds_shrink(window, area, helper, policy, edge, delta):
    target = _flickable_item(area)
    target.setProperty("boundsBehavior", window.property(policy))
    vertical = helper.property("orientation") == Qt.Orientation.Vertical.value
    axis = "Y" if vertical else "X"
    direction = "V" if vertical else "H"
    position_name = f"content{axis}"
    guard_name = "verticalOvershootGuard" if vertical else "horizontalOvershootGuard"
    guard = helper.property(guard_name)
    boundary_property = "maxScroll" if edge == "end" else "minScroll"
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    _scroll_to_boundary(helper, target, position_name, edge)
    original_maximum = float(helper.property("maxScroll"))
    original_edge = float(helper.property("minScroll" if edge == "start" else "maxScroll"))
    samples = []
    getattr(target, f"{position_name}Changed").connect(
        lambda: samples.append(
            (
                float(target.property(position_name)),
                float(helper.property(boundary_property)),
            )
        )
    )
    if vertical:
        _send_wheel(window, area, delta)
    else:
        method = "overshootDefaultHorizontal" if edge == "end" else "overshootDefaultHorizontalLeft"
        assert QMetaObject.invokeMethod(window, method)
    outward = f"_isOutwardBounce{direction}"
    sign = 1 if edge == "end" else -1
    assert _wait_for(
        lambda: helper.property(outward)
        and (float(target.property(position_name)) - original_edge) * sign > 20
    )
    return target, axis, position_name, guard, samples, original_maximum


def _assert_rebased_bounds(helper, target, axis, position_name, guard, samples, edge):
    limit = float(helper.property("_maxOvershoot"))
    edge_property = "maxScroll" if edge == "end" else "minScroll"
    boundary = float(helper.property(edge_property))
    assert _wait_for(
        lambda: float(helper.property(f"_target{axis}"))
        == pytest.approx(float(helper.property(edge_property)), abs=0.5)
        and float(guard.property("outwardEdgePosition"))
        == pytest.approx(float(helper.property(edge_property)), abs=0.5)
    )
    assert _wait_for(
        lambda: (float(helper.property(f"_smooth{axis}")) - boundary)
        * (1 if edge == "end" else -1) <= limit + 1.0
    )
    assert guard.property("revokedBoundary") == 0
    assert _wait_for(
        lambda: not helper.property("isOvershot")
        and float(target.property(position_name))
        == pytest.approx(float(helper.property(edge_property)), abs=1.0),
        timeout_ms=3000,
    )
    sign = 1 if edge == "end" else -1
    assert samples and max((value - edge) * sign for value, edge in samples) <= limit + 1.0


def _run_large_bounds_shrink(window, area, helper, policy, edge, resize_method, delta):
    target, axis, position, guard, samples, original_maximum = _prepare_bounds_shrink(
        window, area, helper, policy, edge, delta
    )
    assert QMetaObject.invokeMethod(window, resize_method)
    assert _wait_for(lambda: helper.property("maxScroll") < original_maximum - 100)
    _assert_rebased_bounds(helper, target, axis, position, guard, samples, edge)


@pytest.mark.parametrize(
    ("policy", "orientation", "edge", "resize_method", "delta"),
    (
        ("dragOverBoundsValue", Qt.Orientation.Vertical, "end", "shrinkDefaultContentFar", -360),
        ("overshootBoundsValue", Qt.Orientation.Vertical, "end", "shrinkDefaultContentFar", -360),
        ("dragAndOvershootBoundsValue", Qt.Orientation.Vertical, "end", "shrinkDefaultContentFar", -360),
        ("dragOverBoundsValue", Qt.Orientation.Vertical, "start", "shrinkDefaultContentFar", 360),
        ("overshootBoundsValue", Qt.Orientation.Vertical, "start", "shrinkDefaultContentFar", 360),
        ("dragAndOvershootBoundsValue", Qt.Orientation.Vertical, "start", "shrinkDefaultContentFar", 360),
        ("dragOverBoundsValue", Qt.Orientation.Horizontal, "end", "shrinkDefaultContentWidthFar", 1000),
        ("overshootBoundsValue", Qt.Orientation.Horizontal, "end", "shrinkDefaultContentWidthFar", 1000),
        ("dragAndOvershootBoundsValue", Qt.Orientation.Horizontal, "end", "shrinkDefaultContentWidthFar", 1000),
        ("dragOverBoundsValue", Qt.Orientation.Horizontal, "start", "shrinkDefaultContentWidthFar", -1000),
        ("overshootBoundsValue", Qt.Orientation.Horizontal, "start", "shrinkDefaultContentWidthFar", -1000),
        ("dragAndOvershootBoundsValue", Qt.Orientation.Horizontal, "start", "shrinkDefaultContentWidthFar", -1000),
    ),
)
def test_supported_overshoot_rebases_after_large_bounds_shrink(
    scroll_scene, policy, orientation, edge, resize_method, delta
):
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, orientation)
    _run_large_bounds_shrink(window, area, helper, policy, edge, resize_method, delta)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []



def test_supported_overshoot_keeps_excursion_across_repeated_view_rewrites(scroll_scene):
    """A view that keeps re-measuring must not reset the live excursion every frame.

    持续重测的视图不得逐帧重置进行中的位移。

    A re-measuring list writes the edge back on every layout pass. Each of those
    writes is a rebase, not a rejection: the animation value still carries the
    excursion, so re-anchoring the animation on the edge makes the leg restart from
    zero over and over and the user never sees a bounce (measured 7px instead of the
    requested 72px on a real chat list).
    重测中的列表每次布局都会把边缘写回来。这些写入都是重锚而非拒绝：动画值仍持有位移，
    因此把动画重新锚到边缘会让外移腿反复从零重启，用户永远看不到回弹
    （真实聊天列表实测只有 7px，而请求的是 72px）。
    """
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    target = _flickable_item(area)
    target.setProperty("boundsBehavior", window.property("dragAndOvershootBoundsValue"))
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    _scroll_to_boundary(helper, target, "contentY", "end")

    edge = float(helper.property("maxScroll"))
    limit = float(helper.property("_maxOvershoot"))
    step = float(helper.property("step"))
    assert 0 < step <= limit

    _send_wheel(window, area, -120)
    assert _wait_for(lambda: helper.property("_isOutwardBounceV"))

    # Simulate the layout passes of a re-measuring list: every write lands the axis
    # back on the edge while our outward leg is still live.
    # 模拟重测列表的布局过程：外移腿仍在进行时，每次写入都把轴放回边缘。
    peak = 0.0
    for _ in range(10):
        if not helper.property("_isOutwardBounceV"):
            break
        target.setProperty("contentY", edge)
        _pump(15)
        excursion = float(target.property("contentY")) - edge
        peak = max(peak, excursion)
        # A live outward leg must never fall back to the edge once it has carried
        # the axis out; that is the signature of the leg restarting from zero.
        # 外移腿一旦把轴带出，就不得在存活期间回落到边缘；回落即是从零重启的形态。
        assert excursion >= peak - 2.0, (excursion, peak, step)

    assert peak > step * 0.3, (peak, step, limit)
    assert peak <= limit + 1.0, (peak, limit)
    assert helper.property("verticalOvershootGuard").property("revokedBoundary") == 0
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_external_position_during_return_rebases_active_overshoot(scroll_scene):
    _window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert QMetaObject.invokeMethod(helper, "scrollToEnd")
    assert _wait_for(
        lambda: not helper.property("isOvershot")
        and float(area.property("contentY"))
        == pytest.approx(float(helper.property("maxScroll")), abs=0.5)
    )
    _send_wheel(_window, area, -120)
    assert _wait_for(lambda: helper.property("_isOutwardBounceV"))
    assert _wait_for(
        lambda: helper.property("isOvershot")
        and not helper.property("_isOutwardBounceV"),
        timeout_ms=3000,
    )

    external_position = float(helper.property("maxScroll")) - 100.0
    area.setProperty("contentY", external_position)
    _pump(35)
    assert float(area.property("contentY")) <= external_position + 40.0
    assert _wait_for(
        lambda: not helper.property("isOvershot")
        and float(area.property("contentY"))
        == pytest.approx(float(helper.property("maxScroll")), abs=1.0),
        timeout_ms=3000,
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, _window) == []

def test_stop_at_bounds_view_revokes_overshoot_when_bounds_move(scroll_scene):
    """A view that refuses overshoot keeps the strict revoke contract.

    禁止越界的视图保留严格撤销契约。

    StopAtBounds declares that going out of bounds is not allowed, so an
    out-of-bounds write that the view clamps away is a rejection. The guard must
    revoke that boundary for the input burst instead of re-publishing the excursion
    at a view that will keep clamping it.
    StopAtBounds 声明不允许越界，因此视图夹掉的越界写入就是一次拒绝。门闸必须在该输入串内
    撤销该边界，而不是对一个会持续夹紧的视图反复重新发布位移。
    """
    window, items, warnings, windows_before = scroll_scene
    flick = items["stopFlick"]
    content = items["stopContent"]
    helper = _smooth_scroll_helper(flick, Qt.Orientation.Vertical)
    guard = helper.property("verticalOvershootGuard")
    assert guard.property("revokedBoundary") == 0
    assert helper.property("_maxOvershoot") > 0
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)

    assert QMetaObject.invokeMethod(helper, "scrollToEnd")
    assert _wait_for(
        lambda: not helper.property("isOvershot")
        and float(flick.property("contentY"))
        == pytest.approx(float(helper.property("maxScroll")), abs=0.5),
        timeout_ms=3000,
    )

    # Drive the helper directly: the wheel-to-helper hand-off is covered by the
    # neighbouring cases, and this case is about the guard's revoke contract.
    # 直接驱动 helper：滚轮到 helper 的转交由相邻用例覆盖，本用例只验证门闸的撤销契约。
    _send_wheel(window, flick, -240)
    assert _wait_for(lambda: helper.property("isOvershot"))
    assert _wait_for(
        lambda: float(flick.property("contentY"))
        > float(helper.property("maxScroll")) + 1.0
    )

    # Move the bound inward while the axis is outside it: the view clamps, and the
    # guard must revoke this boundary rather than adopt the write.
    # 轴向越界期间把边界内移：视图夹紧，门闸必须撤销该边界而不是采纳该写入。
    content.setProperty("height", 360)
    assert _wait_for(lambda: guard.property("revokedBoundary") == 1, timeout_ms=2000)
    boundary = float(helper.property("maxScroll"))

    _send_wheel(window, flick, -240)
    _pump(60)
    assert guard.property("revokedBoundary") == 1

    # The return leg still has to finish, so assert it converges on the new edge.
    # 返回腿仍需走完，故断言其收敛到新边界。
    assert _wait_for(
        lambda: abs(float(flick.property("contentY")) - boundary) <= 1.5
        and guard.property("revokedBoundary") == 1,
        timeout_ms=3000,
    )

    content.setProperty("height", 420)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_smooth_helpers_keep_boundary_target_when_content_grows(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene

    assert QMetaObject.invokeMethod(window, "scrollVerticalToEnd")
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(480))
    assert QMetaObject.invokeMethod(window, "growVerticalContent")
    assert _wait_for(lambda: window.property("verticalMax") == pytest.approx(600))
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(600))

    assert QMetaObject.invokeMethod(window, "scrollHorizontalToEnd")
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(520))
    assert QMetaObject.invokeMethod(window, "growHorizontalContent")
    assert _wait_for(lambda: window.property("horizontalMax") == pytest.approx(640))
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(640))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_scroll_bars_follow_position_and_real_drag(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    flick = items["verticalFlick"]
    bar = items["scrollBar"]
    entry = items["scrollBarEntry"]
    assert bar.isVisible()
    assert entry.property("active")

    assert QMetaObject.invokeMethod(window, "setVerticalHalf")
    bar_handle = next(
        item
        for item in bar.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
    )
    entry_thumb = next(
        item
        for item in entry.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.height() < entry.height()
    )
    bar_handle_area = next(
        item
        for item in bar_handle.childItems()
        if "MouseArea" in item.metaObject().className()
    )
    assert bar_handle.height() == pytest.approx(30)
    assert entry_thumb.height() == pytest.approx(30)
    assert _wait_for(lambda: bar_handle.y() == pytest.approx(45))
    assert _wait_for(lambda: entry_thumb.y() == pytest.approx(45))

    start = bar_handle.mapToScene(
        QPointF(bar_handle.width() / 2, bar_handle.height() / 2)
    ).toPoint()
    target = start + QPoint(0, 30)
    middle = start + QPoint(0, 15)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    assert _wait_for(lambda: bar_handle_area.property("pressed"))
    QTest.mouseMove(window, middle, delay=20)
    QTest.mouseMove(window, target, delay=20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    assert _wait_for(lambda: flick.property("contentY") > 240), (
        flick.property("contentY"),
        bar_handle.y(),
    )

    values = []
    pressed = []
    released = []
    moved = []
    entry.valueChanged.connect(values.append)
    entry.sliderPressed.connect(lambda: pressed.append(True))
    entry.sliderReleased.connect(lambda: released.append(True))
    entry.sliderMoved.connect(lambda: moved.append(True))
    assert QMetaObject.invokeMethod(window, "setVerticalHalf")
    start = entry_thumb.mapToScene(
        QPointF(entry_thumb.width() / 2, entry_thumb.height() / 2)
    ).toPoint()
    target = start + QPoint(0, 25)
    middle = start + QPoint(0, 13)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, middle, delay=20)
    QTest.mouseMove(window, target, delay=20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    assert _wait_for(lambda: values and moved and released)
    assert pressed == [True]
    assert len(values) == 2
    assert values == sorted(values)
    assert len(moved) == 2
    expected_content_y = 240 + (
        (target.y() - start.y())
        / (entry.height() - entry_thumb.height())
        * (flick.property("contentHeight") - flick.height())
    )
    assert flick.property("contentY") == pytest.approx(
        expected_content_y, abs=1.0
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_scroll_area_variants_geometry_and_public_methods(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene
    assert _wait_for(lambda: window.property("defaultContentWidth") == pytest.approx(380))
    assert window.property("defaultContentHeight") == pytest.approx(440)
    assert _wait_for(lambda: window.property("listCount") == 20)
    assert _wait_for(lambda: window.property("gridCount") == 20)
    assert window.property("listContentHeight") > 120
    # The vertical gutter changes this fixed scene from three to two columns.
    # 垂直避让槽会让该固定场景从三列重排为两列，滚动前必须等布局稳定。
    assert _wait_for_stable(
        lambda: window.property("gridContentHeight") == pytest.approx(400)
    )

    assert QMetaObject.invokeMethod(window, "scrollDefault")
    assert _wait_for(lambda: window.property("defaultY") == pytest.approx(160))
    assert _wait_for(lambda: window.property("defaultX") == pytest.approx(120))
    assert QMetaObject.invokeMethod(window, "scrollList")
    assert _wait_for(lambda: window.property("listY") == pytest.approx(300))
    assert QMetaObject.invokeMethod(window, "scrollGrid")
    assert _wait_for(
        lambda: window.property("gridY")
        == pytest.approx(
            window.property("gridOriginY")
            + window.property("gridContentHeight")
            - 120
        )
    ), (
        window.property("gridY"),
        window.property("gridOriginY"),
        window.property("gridContentHeight"),
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_nested_blocking_wheel_handler_consumes_wheel_before_outer_area(scroll_scene):
    """A nested blocking wheel handler must win over the outer scroll area. 内层 blocking 滚轮处理器必须优先于外层滚动区。"""
def _nested_scene_items(items):
    outer = items["nestedTarget"]
    host = items["nestedEditorHost"]
    inner = next(
        child
        for child in host.findChildren(QQuickItem)
        if child.objectName() == "nestedEditor"
    )
    return outer, host, inner


def _wheel_at(window, item, delta):
    """Dispatch a real wheel event through Qt hit testing. 通过 Qt 命中测试派发真实滚轮事件。"""
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.wheelEvent(
        window,
        QPoint(round(center.x()), round(center.y())),
        QPoint(0, delta),
    )
    _pump(120)


def test_nested_blocking_wheel_handler_consumes_wheel_before_outer_area(scroll_scene):
    """A nested blocking wheel handler must win over the outer scroll area. 内层 blocking 滚轮处理器必须优先于外层滚动区。"""
    window, items, warnings, windows_before = scroll_scene
    outer, host, inner = _nested_scene_items(items)
    inner.setProperty("contentY", 0.0)
    outer.setProperty("contentY", 0.0)
    _pump(60)

    _wheel_at(window, host, -120)
    _pump(120)

    assert float(inner.property("contentY")) > 0, (
        "nested scrollable input did not scroll:",
        inner.property("contentY"),
    )
    assert abs(float(outer.property("contentY"))) <= 1, (
        "outer scroll area stole the wheel event:",
        outer.property("contentY"),
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_bar_sources_follow_conventions():
    violations = []
    source_paths = sorted(SOURCE_DIR.glob("*.qml")) + [
        SOURCE_DIR / "_internal" / "SmoothScrollWheelArea.qml"
    ]
    for source_path in source_paths:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
