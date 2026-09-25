# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 6/7 of the former test_qml_architecture.py."""
import pytest  # noqa: F401
from qml_architecture_shared import *
from qml_architecture_shared import (
    _source,
    _declaration_indent,
    _assert_modularized,
    _CHART_INTERNAL,
    _CHART_MATH,
    _PICKER_INTERNAL,
    _PICKER_HSV,
    _PICKER_DIALOG,
    _PICKER_DROPDOWN,
)

def test_progress_dialog_keeps_timeout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/dialogs/ProgressDialog.qml")
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "ProgressDialogTimeoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.ProgressDialogTimeoutTimer {" in source
    assert "id: timeoutTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "progressDialogTimeoutTimer"' in helper_source
    assert "interval: host.maxWaitingTime" in helper_source
    assert "running: host._isOpen && host.maxWaitingTime > 0" in helper_source
    assert "host.timeout()" in helper_source
    assert "host.close()" in helper_source

def test_overlay_dialog_keeps_restore_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/dialogs/OverlayDialogCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "OverlayDialogRestoreParentTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    # 父级几何改用绑定 + 打开时重建（布局子项不可用 anchors），行数预算同步 +15
    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.OverlayDialogRestoreParentTimer {" in source
    assert "id: _restoreParentTimer" in source
    assert "host: control" in source
    assert "function _fillOverlayHost()" in source
    assert "_fillOverlayHost()" in source
    assert "anchors.fill: parent" not in source.split("// ==================== Content")[0]
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "overlayDialogRestoreParentTimer"' in helper_source
    assert "interval: Enums.duration.medium + Enums.spacing.xl" in helper_source
    assert "onTriggered: host._restoreParent()" in helper_source

def test_line_edit_core_keeps_variant_factories_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/LineEditCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/_internal/"
        "LineEditVariants.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as LineEditInternal' in source
    assert "LineEditInternal.LineEditVariants {" in source
    assert "required property var lineEditControl" in helper_source
    for component_name in ("normalComponent", "labelComponent", "tagComponent"):
        assert f"property alias {component_name}:" in helper_source
    for marker in (
        "\n    Component {\n        id: normalComponent",
        "\n    Component {\n        id: labelComponent",
        "\n    Component {\n        id: tagComponent",
    ):
        assert marker not in source

def test_line_edit_normal_keeps_hide_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/LineEditNormal.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/_internal/"
        "LineEditNormalHideTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as LineEditInternal' in source
    assert "LineEditInternal.LineEditNormalHideTimer {" in source
    assert "id: _hideTimer" in source
    assert "host: normalInput" in source
    assert "_hideTimer.restart()" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "lineEditNormalHideTimer"' in helper_source
    assert "interval: Enums.duration.medium" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: if (!host.expanded) host._textInputVisible = false" in helper_source
    assert "onTriggered: if (!normalInput.expanded)" not in source

def test_pivot_keeps_indicator_sync_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Pivot.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "PivotIndicatorSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 215
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal"' in source
    assert "PivotIndicatorSyncTimer {" in source
    assert "id: indicatorSyncTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "pivotIndicatorSyncTimer"' in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "repeat: true" in helper_source
    assert "onTriggered: host._updateIndicatorWithAnimation()" in helper_source

def test_pivot_keeps_item_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Pivot.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/PivotItem.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 215
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "PivotItem {" in source
    assert "host: control" in source
    # Delegate visuals and the per-item sizing must not come back to the entry
    # 委托视觉与逐项尺寸不得回流到入口
    assert "Button {" not in source
    assert "required property var host" in helper_source
    assert "required property int index" in helper_source
    assert "required property var modelData" in helper_source
    assert "host.vertical" in helper_source

def test_teaching_tour_keeps_state_reset_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/TeachingTour.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/_internal/"
        "TeachingTourStateResetTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 365
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as OverlayInternal' in source
    assert "OverlayInternal.TeachingTourStateResetTimer {" in source
    assert "id: stateResetTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "teachingTourStateResetTimer"' in helper_source
    assert "interval: Enums.duration.tipHide" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: if (!host._active) host._currentIndex = -1" in helper_source

def test_teaching_tour_keeps_mask_surface_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/TeachingTour.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/_internal/"
        "TeachingTourMaskSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 365
    assert helper.exists()
    assert len(helper_source.splitlines()) < 200
    assert "OverlayInternal.TeachingTourMaskSurface {" in source
    assert "host: control" in source
    # The mask-free scrim lives in the helper, not in the entry
    # 无遮罩蒙层属于助手文件, 不属于入口
    assert "Shape {" not in source
    assert "PathArc {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "teachingTourMaskSurface"' in helper_source
    assert "preferredRendererType: Shape.CurveRenderer" in helper_source
    assert helper_source.count("PathArc {") == 4

def test_chart_data_zoom_keeps_drag_end_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/ChartDataZoom.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/"
        "ChartDataZoomDragEndTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as ChartInternal' in source
    assert "ChartInternal.ChartDataZoomDragEndTimer {" in source
    assert "id: _dragEndTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "chartDataZoomDragEndTimer"' in helper_source
    assert "interval: Enums.duration.slow" in helper_source
    assert "repeat: false" in helper_source
    assert "host._dragging = false" in helper_source
    assert "host.interactiveChanged(false)" in helper_source

def test_segmented_control_keeps_delegate_visuals_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SegmentedControl.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SegmentedItem.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 130
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SegmentedItem {" in source
    assert "required property var segmentedControl" in helper_source
    assert "required property int index" in helper_source
    assert "required property var modelData" in helper_source
    assert "\nItem {\n" in helper_source
    assert "segmentedControl._scheduleSlideSync(false)" in helper_source
    assert "function _scheduleSlideSync(shouldAnimate)" in source
    assert "repeater.itemAt" in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    for marker in (
        "\n            Item {",
        "\n                Rectangle {",
        "\n                Row {",
        "\n                HoverHandler {",
        "\n                TapHandler {",
    ):
        assert marker not in source

def test_segmented_control_keeps_slide_sync_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SegmentedControl.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "SegmentedSlideSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 175
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SegmentedSlideSyncTimer {" in source
    assert "id: slideSyncTimer" in source
    assert "host: control" in source
    assert "segmentRow: segmentRow" in source
    assert "itemRepeater: repeater" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property Item segmentRow" in helper_source
    assert "required property var itemRepeater" in helper_source
    assert 'objectName: "segmentedControlSlideSyncTimer"' in helper_source
    assert "function schedule(shouldAnimate)" in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "itemRepeater.itemAt(host.currentIndex)" in helper_source
    assert "host._updateSlidePosition(false)" in helper_source

def test_command_palette_reuses_the_search_stack():
    entry = _source("prismqml/PrismQML/controls/navigation/CommandPalette.qml")
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    # Reuse, do not re-implement: filtering, ranking, grouping, highlighting and cursor
    # movement stay in the shared search stack. 复用而非重写: 过滤/排名/分组/高亮/光标
    # 移动都留在共享搜索栈里。
    assert 'import "../inputs/Search/_internal" as SearchInternal' in source
    assert "SearchInternal.SearchResultList {" in source
    assert "LineEdit {" in source
    assert "maxSuggestions: control.maxResults" in source
    assert "OverlayDialogCore {" in source
    for marker in ("FuzzyMatcher", "_hits", "_rows", "score"):
        assert marker not in source
    # Key routing stays window-level: the search field's TextInput swallows arrow keys
    # before they can bubble, so Up/Down/Return/Escape are Shortcuts while open.
    # 键路由留在窗口级: 搜索框的 TextInput 会先吞掉方向键, 因此开启期间用 Shortcut。
    assert source.count('sequence: "Up"') == 1
    assert source.count('sequence: "Down"') == 1
    assert 'sequence: "Return"' in source
    assert 'sequence: "Escape"' in source
    assert "Keys.onDownPressed" not in source
    # Registered in both the sub-module and the root module
    # 子模块与根模块都要注册
    assert "CommandPalette CommandPalette.qml" in _source(
        "prismqml/PrismQML/controls/navigation/qmldir"
    ).read_text(encoding="utf-8")
    assert "CommandPalette controls/navigation/CommandPalette.qml" in _source(
        "prismqml/PrismQML/qmldir"
    ).read_text(encoding="utf-8")

def test_selector_bar_keeps_delegates_and_pill_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SelectorBar.qml")
    item_helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SelectorBarItem.qml"
    )
    pill_helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SelectorBarPill.qml"
    )
    timer_helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SelectorBarPillSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    item_source = item_helper.read_text(encoding="utf-8")
    pill_source = pill_helper.read_text(encoding="utf-8")
    timer_source = timer_helper.read_text(encoding="utf-8")

    # 285 lines after adding the boundary-aligned reveal and the smooth-scroll engine
    # wiring; the entry stays far below the repository's 500/700 limits.
    # 加入边界对齐定位与平滑滚动引擎接线后为 285 行, 仍远低于仓库 500/700 的上限。
    assert len(source.splitlines()) < 300
    assert len(item_source.splitlines()) < 140
    assert len(pill_source.splitlines()) < 90
    assert len(timer_source.splitlines()) < 80
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SelectorBarItem {" in source
    assert "NavigationInternal.SelectorBarPill {" in source
    assert "NavigationInternal.SelectorBarPillSyncTimer {" in source
    for name, text in (
        ("SelectorBarItem", item_source),
        ("SelectorBarPill", pill_source),
        ("SelectorBarPillSyncTimer", timer_source),
    ):
        assert name in text
    assert "required property var selectorBar" in item_source
    assert "required property int index" in item_source
    assert "required property var modelData" in item_source
    assert "required property var selectorBar" in pill_source
    assert "required property Item strip" in pill_source
    assert "required property var host" in timer_source
    assert "required property var itemRepeater" in timer_source

    # The delegate re-syncs the pill when its own box settles, which is what makes the
    # pill appear when delegates arrive late; the entry exposes the hook.
    # 委托在自身几何落定时重新同步胶囊, 这是委托晚到时胶囊仍能出现的原因; 入口暴露钩子。
    assert "selectorBar._schedulePillSync(false)" in item_source
    assert "function _schedulePillSync(shouldAnimate)" in source
    assert "Component.onCompleted: if (selected) selectorBar._schedulePillSync(false)" in (
        item_source
    )

    # Auto-scroll prefers a cell boundary as the leading edge so the strip never leaves
    # a half-cut label behind. 自动滚动优先让前缘落在单元格边界, 避免留下半截标签。
    assert "var minOffset = Math.max(0, item.x + item.width - scrollArea.width)" in source
    assert "var maxOffset = Math.min(item.x, maxScrollOffset)" in source
    assert "cell.x >= minOffset && cell.x <= maxOffset" in source

    # The pill owns the sliding geometry and must sit beside the positioner: a
    # Row/Column would lay it out as one more cell. 胶囊自持滑动几何, 且必须与定位器
    # 平级: 否则会被 Row/Column 当成一个单元排版。
    assert source.count("NavigationInternal.SelectorBarPill {") == 2
    for marker in ("property Item target", "Behavior on x", "Behavior on width"):
        assert marker in pill_source
    assert "itemRepeater" not in pill_source

    # The pill's slide uses one timing on all four geometry axes, matching the tab
    # switch slide (duration.slow + OutCubic). 胶囊四个几何轴共用一套时长, 与标签页切换
    # 滑动一致(duration.slow + OutCubic)。
    assert pill_source.count("duration: Enums.duration.slow") == 4
    assert pill_source.count("easing.type: Easing.OutCubic") == 4
    assert "duration: Enums.duration.normal" not in pill_source
    assert "duration: Enums.duration.fast" not in pill_source
    assert pill_source.count("enabled: pill._animate") == 4
    assert "readonly property bool _animate" in pill_source

    # Wheel ownership is explicit: the strip pans itself, because a horizontal
    # Flickable never hands a vertical wheel to its ancestor.
    # 滚轮归属显式声明: 条带自己平移, 因为横向 Flickable 不会把纵向滚轮交给祖先。
    assert "WheelHandler {" in source
    assert "WheelEventUtils.verticalDelta(event)" in source
    assert "revealCurrent()" in source
    assert "interactive: control.scrollable" in source

    # Every programmatic move goes through the shared smooth-scroll engine, so wheel
    # and auto-reveal glide instead of jumping; no direct contentX writes remain.
    # 所有程序化位移都走共享平滑滚动引擎, 滚轮与自动滚入是滑行; 不再直接写 contentX。
    assert 'import "../containers/ScrollBar"' in source
    assert "SmoothScrollHelper {" in source
    assert "orientation: Qt.Horizontal" in source
    assert "handleWheel: false" in source
    assert "scrollHelper.scrollTo(" in source
    assert "scrollHelper.scrollBy(" in source
    assert "scrollArea.contentX =" not in source

    # Registered in both the sub-module and the root module
    # 子模块与根模块都要注册
    assert "SelectorBar SelectorBar.qml" in _source(
        "prismqml/PrismQML/controls/navigation/qmldir"
    ).read_text(encoding="utf-8")
    assert "SelectorBar controls/navigation/SelectorBar.qml" in _source(
        "prismqml/PrismQML/qmldir"
    ).read_text(encoding="utf-8")

    violations = []
    for path, candidate in (
        (entry, source),
        (item_helper, item_source),
        (pill_helper, pill_source),
        (timer_helper, timer_source),
    ):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []


def test_selector_bar_colors_are_registered_tokens():
    state_color = _source("prismqml/PrismQML/PrismEnums/StateColor.qml")
    metrics = _source("prismqml/PrismQML/PrismEnums/Metrics.qml")
    state_source = state_color.read_text(encoding="utf-8")
    metrics_source = metrics.read_text(encoding="utf-8")
    item_source = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SelectorBarItem.qml"
    ).read_text(encoding="utf-8")
    pill_source = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SelectorBarPill.qml"
    ).read_text(encoding="utf-8")

    assert "==================== SelectorBar Colors 选择条颜色 ====================" in (
        state_source
    )
    for token in (
        "selectorBarItemSelected",
        "selectorBarItemSelectedBorder",
        "selectorBarItemHover",
        "selectorBarItemPressed",
    ):
        assert token in state_source
    # Single-sourced values: the names are owned here, the chrome is shared
    # 取值单一来源: 这里拥有名称, 外观复用分段控件的选中样式
    assert (
        "selectorBarItemSelected: isTicket ? _ticket.muted : segmentedSelected"
        in state_source
    )
    assert (
        "selectorBarItemHover: isTicket ? _ticket.muted : segmentedHover"
        in state_source
    )

    assert "readonly property int selectorBarHeight" in metrics_source
    assert "readonly property int selectorBarMinItemWidth" in metrics_source
    assert "Enums.stateColor.selectorBarItemHover" in item_source
    assert "Enums.stateColor.selectorBarItemPressed" in item_source
    assert "Enums.controlSize.selectorBarHeight" in item_source
    assert "Enums.controlSize.selectorBarMinItemWidth" in item_source
    assert "Enums.stateColor.selectorBarItemSelected" in pill_source
    assert "Enums.stateColor.selectorBarItemSelectedBorder" in pill_source

    # No color literal may sneak into the new component files
    # 新组件文件里不得出现颜色字面量
    for text in (item_source, pill_source):
        assert "Qt.rgba(" not in text
        assert "#" not in text.replace("# ", "")


def test_confetti_keeps_lifecycle_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Confetti.qml")
    spawn_helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/ConfettiSpawnTimer.qml"
    )
    stop_helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/ConfettiStopTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    spawn_source = spawn_helper.read_text(encoding="utf-8")
    stop_source = stop_helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 225
    assert spawn_helper.exists() and stop_helper.exists()
    assert len(spawn_source.splitlines()) < 25
    assert len(stop_source.splitlines()) < 25
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.ConfettiSpawnTimer {" in source
    assert "FeedbackInternal.ConfettiStopTimer {" in source
    assert "id: spawnTimer" in source
    assert "id: stopTimer" in source
    assert source.count("host: control") == 2
    assert "\n    Timer {" not in source
    for helper_source in (spawn_source, stop_source):
        assert "required property var host" in helper_source
    assert 'objectName: "confettiSpawnTimer"' in spawn_source
    assert "running: host.running && host._spawnIndex < host.particleCount" in spawn_source
    assert "onTriggered: host._spawnBatch(8)" in spawn_source
    assert 'objectName: "confettiStopTimer"' in stop_source
    assert "interval: host.duration + Enums.duration.dialog" in stop_source
    assert "onTriggered: host.running = false" in stop_source

def test_pin_input_keeps_cell_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/PinInput.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/PinInputCell.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 170
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.PinInputCell {" in source
    assert "required property var pinControl" in helper_source
    assert "required property int index" in helper_source
    assert "\nItem {\n" in helper_source
    assert "pinControl._focusInput()" in helper_source
    assert "function _focusInput()" in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    for marker in (
        "\n            Item {",
        "\n                RectangularShadow {",
        "\n                NeumorphicShadow {",
        "\n                NeoShadow {",
        "\n                MouseArea {",
    ):
        assert marker not in source

def test_spin_box_keeps_dynamic_button_components_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxButtonGroups.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as SpinBoxInternal' in source
    assert "SpinBoxInternal.SpinBoxButtonGroups {" in source
    assert "required property var spinControl" in helper_source
    assert "property alias inlineButtonsComponent: inlineButtonsComponent" in helper_source
    assert "property alias compactButtonsComponent: compactButtonsComponent" in helper_source
    assert "sourceComponent: control.compactMode" in source
    assert "buttonGroups.compactButtonsComponent" in source
    assert "buttonGroups.inlineButtonsComponent" in source
    assert "Loader {" in source
    assert "Loader {" not in helper_source
    assert "onItemChanged:" in source

    for marker in (
        "\n    Component {",
        "\n        SpinBoxButton {",
        "\n        MiniSpinButton {",
    ):
        assert marker not in source

def test_spin_box_keeps_feedback_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as SpinBoxInternal' in source
    assert source.count("SpinBoxInternal.SpinBoxFeedbackTimer {") == 2
    assert "id: upFeedbackTimer" in source
    assert "id: downFeedbackTimer" in source
    assert source.count("spinControl: control") == 5
    assert "increase: true" in source
    assert "increase: false" in source
    assert "required property var spinControl" in helper_source
    assert "required property bool increase" in helper_source
    assert 'objectName: increase' in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert "spinControl._increaseButton" in helper_source
    assert "spinControl._decreaseButton" in helper_source
    assert "pseudoHovered = false" in helper_source
    assert "pseudoPressed = false" in helper_source
    assert "\n    Timer {\n        id: upFeedbackTimer" not in source
    assert "\n    Timer {\n        id: downFeedbackTimer" not in source

def test_spin_box_keeps_unit_icons_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxUnitIcons.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert "SpinBoxInternal.SpinBoxUnitIcons {" in source
    assert "id: unitIcons" in source
    assert "textInputItem: textInput" in source
    assert "TextMetrics {" not in source
    assert "TextMetrics {" in helper_source
    assert "required property var spinControl" in helper_source
    assert "required property var textInputItem" in helper_source
    assert 'objectName: "spinBoxPrefixIcon"' in helper_source
    assert 'objectName: "spinBoxSuffixIcon"' in helper_source
    for marker in (
        'property string prefixIcon: ""',
        'property string suffixIcon: ""',
        "property int iconSize: Enums.iconSize.s",
        "property bool iconThemeAware: true",
    ):
        assert marker in source
    assert "themeAware: unitIcons.spinControl.iconThemeAware" in helper_source
    assert "Enums.spacing.xs" in helper_source

def test_spin_box_keeps_auto_repeat_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxAutoRepeatTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert "SpinBoxInternal.SpinBoxAutoRepeatTimer {" in source
    assert "id: autoRepeatTimer" in source
    assert "spinControl: control" in source
    assert "required property var spinControl" in helper_source
    assert 'objectName: "spinBoxAutoRepeatTimer"' in helper_source
    assert "property bool _inRepeatPhase: false" in helper_source
    assert "interval: _inRepeatPhase" in helper_source
    assert "repeat: _inRepeatPhase" in helper_source
    for marker in (
        "spinControl._repeatCurrentInterval = spinControl.autoRepeatInterval",
        "spinControl._repeatIsUp",
        "spinControl.increase()",
        "spinControl.decrease()",
        "spinControl.autoRepeatMinInterval",
        "Enums.input.spinBoxRepeatAcceleration",
    ):
        assert marker in helper_source
    assert "\n    Timer {\n        id: autoRepeatTimer" not in source

def test_expander_keeps_header_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/Expander/ExpanderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/Expander/_internal/"
        "HeaderContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 240
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ExpanderInternal' in source
    assert "ExpanderInternal.HeaderContent {" in source
    assert "required property var expanderControl" in helper_source
    assert "property alias titleLabel: titleLabel" in helper_source
    assert "property alias contentLabel: contentLabel" in helper_source
    assert "property alias headerContent: headerContentLoader.sourceComponent" in helper_source
    assert "property alias headerContentLoader: headerContentLoader" in helper_source
    assert "expanderControl.toggled(expanderControl.expanded)" in helper_source

    for marker in (
        "\n        Row {\n            id: headerRow",
        "\n            Column {\n                id: titleCol",
        "\n        Loader {\n            id: headerContentLoader",
        "\n        MouseArea {\n            id: headerArea",
        "\n            Icon {\n                icon: Enums.icon.chevron_down",
    ):
        assert marker not in source

def test_slider_keeps_default_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Slider/SliderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Slider/_internal/"
        "SliderDefaultContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 280
    assert helper.exists()
    assert len(helper_source.splitlines()) < 240
    assert 'import "_internal" as SliderInternal' in source
    assert "SliderInternal.SliderDefaultContent {" in source
    assert "required property var sliderControl" in helper_source
    assert "readonly property bool hovered" in helper_source
    assert "sourceComponent: defaultSliderComponent" in source
    assert "sourceComponent: rangeSliderComponent" in source

    for marker in (
        "\n            MouseArea {\n                id: wheelArea",
        "\n                NeumorphicShadow {\n                    target: track",
        "\n                MouseArea {\n                    id: handleArea",
        "text: control._tipText(control.value)",
    ):
        assert marker not in source

def test_slider_keeps_range_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Slider/SliderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Slider/_internal/"
        "SliderRangeContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 230
    assert 'import "_internal" as SliderInternal' in source
    assert "SliderInternal.SliderRangeContent {" in source
    assert "required property var sliderControl" in helper_source
    assert "readonly property real firstPos" in helper_source
    assert "readonly property real secondPos" in helper_source
    assert "component RangeHandle: Rectangle" in helper_source
    assert "sliderControl.sliderMoved(" in helper_source
    assert "sourceComponent: rangeSliderComponent" in source

    for marker in (
        "\n            RangeHandle {",
        "\n            component RangeHandle:",
        "id: rangeHandleArea",
        "property real firstPos:",
    ):
        assert marker not in source

def test_toggle_keeps_visual_assembly_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Toggle/Toggle.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Toggle/_internal/"
        "ToggleContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")
    interaction = _source(
        "prismqml/PrismQML/controls/inputs/Toggle/_internal/"
        "ToggleInteraction.qml"
    )
    interaction_source = interaction.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert interaction.exists()
    assert len(interaction_source.splitlines()) < 80
    assert "ToggleInternal.ToggleInteraction {" in source
    assert "required property var toggleControl" in interaction_source
    assert "readonly property bool containsMouse" in interaction_source
    assert "readonly property bool pressed" in interaction_source
    assert "anchors.fill: parent" in interaction_source
    assert "onClicked: interaction.toggleControl._handleClick()" in interaction_source
    assert "!Touch.isTouch" in interaction_source
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ToggleInternal' in source
    assert "ToggleInternal.ToggleContent {" in source
    assert "required property var toggleControl" in helper_source
    assert "readonly property bool contentLoaded" in helper_source
    assert "sourceComponent: content.toggleControl._isSubtitle" in helper_source

    for marker in (
        "\n    Row {\n        id: mainRow",
        "\n    Component {\n        id: checkboxIndicator",
        "\n    Component {\n        id: radioIndicator",
        "\n    Component {\n        id: switchIndicator",
        "\n    Component {\n        id: defaultContent",
        "\n    Component {\n        id: subtitleContent",
    ):
        assert marker not in source

def test_stacked_animations_monolith_stays_deleted():
    """堆叠动画只允许经 StackedModeAnimations 按模式加载。

    StackedWidget switched to per-mode backends; the old StackedAnimations.qml
    monolith kept a second full copy of every transition with no consumer. This
    gate keeps it deleted and keeps the mode dispatcher as the only entry.
    """
    internal = _source("prismqml/PrismQML/controls/navigation/_internal")
    monolith = internal / "StackedAnimations.qml"
    dispatcher = internal / "StackedModeAnimations.qml"

    assert not monolith.exists()
    assert dispatcher.exists()

    entry_source = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    ).read_text(encoding="utf-8")
    assert "StackedModeAnimations {" in entry_source
    assert "StackedAnimations {" not in entry_source

    dispatcher_source = dispatcher.read_text(encoding="utf-8")
    for backend in (
        "StackedFadeAnimations.qml",
        "StackedPopAnimations.qml",
        "StackedSlideAnimations.qml",
        "StackedSlideFadeAnimations.qml",
        "StackedCardAnimations.qml",
        "StackedZoomAnimations.qml",
    ):
        assert backend in dispatcher_source
        assert (internal / backend).exists()

    assert dispatcher_source.count('"StackedPopAnimations.qml"') == 2
    pop_source = (internal / "StackedPopAnimations.qml").read_text(encoding="utf-8")
    assert "property bool isPopDown: false" in pop_source
    assert "function configure(popDown)" in pop_source
    assert "Easing.OutBounce" in pop_source
    assert "Easing.OutQuad" in pop_source
    assert "StackedPopUpAnimations.qml" not in dispatcher_source
    assert "StackedPopDownAnimations.qml" not in dispatcher_source

    for path in QML_ROOT.rglob("*.qml"):
        assert path.name != "StackedAnimations.qml"
        assert path.name not in {
            "StackedPopUpAnimations.qml",
            "StackedPopDownAnimations.qml",
        }

def test_stacked_slide_z_order_has_one_shared_owner():
    """slide 与 slide_fade 共用同一份 z 顺序保护逻辑。

    Both slide backends temporarily raise the incoming page during a transition.
    The capture/restore state must stay in one helper so fixes cannot drift.
    """
    internal = _source("prismqml/PrismQML/controls/navigation/_internal")
    guard = internal / "StackedZOrderGuard.qml"
    assert guard.exists()
    guard_source = guard.read_text(encoding="utf-8")
    assert "function capture(" in guard_source
    assert "function restore()" in guard_source
    assert "property bool _captured: false" in guard_source
    assert "newWidget.z = oldWidget.z + 1" in guard_source

    consumers = (
        internal / "StackedSlideAnimations.qml",
        internal / "StackedSlideFadeAnimations.qml",
    )
    for path in consumers:
        source = path.read_text(encoding="utf-8")
        assert 'import "." as NavigationInternal' in source
        assert (
            "readonly property QtObject zOrderGuard: "
            "NavigationInternal.StackedZOrderGuard {}"
        ) in source
        assert "zOrderGuard.capture(_oldWidget, _newWidget)" in source
        assert "zOrderGuard.restore()" in source
        assert "_zCaptured" not in source
        assert "function _restoreZOrder()" not in source
        assert "_oldZ = _oldWidget.z" not in source

    owners = sorted(
        path.relative_to(ROOT).as_posix()
        for path in QML_ROOT.rglob("*.qml")
        if "newWidget.z = oldWidget.z + 1" in path.read_text(encoding="utf-8")
    )
    assert owners == [
        "prismqml/PrismQML/controls/navigation/_internal/StackedZOrderGuard.qml"
    ]
