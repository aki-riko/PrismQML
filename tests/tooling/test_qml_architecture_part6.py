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

    assert len(source.splitlines()) < 175
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.OverlayDialogRestoreParentTimer {" in source
    assert "id: _restoreParentTimer" in source
    assert "host: control" in source
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
    assert source.count("spinControl: control") == 4
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

    assert len(source.splitlines()) < 210
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
