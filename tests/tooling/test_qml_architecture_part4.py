# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 4/7 of the former test_qml_architecture.py."""
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

def test_tip_popup_keeps_auto_close_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/"
        "TipPopupAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TipPopupAutoCloseTimer {" in source
    assert "id: autoCloseTimer" in source
    assert "host: control" in source
    assert "autoCloseTimer.stop()" in source
    assert "autoCloseTimer.start()" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "tipPopupAutoCloseTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host.close()" in helper_source
    assert "onTriggered: control.close()" not in source

def test_tooltip_core_keeps_follow_anchor_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/TooltipCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/"
        "TooltipFollowAnchorTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 232
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TooltipFollowAnchorTimer {" in source
    assert "id: followTimer" in source
    assert "host: control" in source
    assert "nativeHost: windowHost" in source
    assert "\n            Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var nativeHost" in helper_source
    assert 'objectName: "tooltipFollowAnchorTimer"' in helper_source
    assert "FrameAnimation {" in helper_source
    assert "interval:" not in helper_source
    assert "repeat:" not in helper_source
    assert "running: host.followAnchor && nativeHost.windowVisible" in helper_source
    assert "onTriggered: host._reposition()" in helper_source
    assert "running: control.followAnchor && windowHost.windowVisible" not in source

def test_action_keeps_tooltip_show_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/Action.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/ActionTooltipShowTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as MenuInternal' in source
    assert "MenuInternal.ActionTooltipShowTimer {" in source
    assert "id: tooltipShowTimer" in source
    assert "actionControl: control" in source
    assert "hoverArea: itemArea" in source
    assert "tooltip: actionTooltip" in source
    assert "\n            Timer {" not in source
    assert "required property var actionControl" in helper_source
    assert "required property var hoverArea" in helper_source
    assert "required property var tooltip" in helper_source
    assert 'objectName: "actionTooltipShowTimer"' in helper_source
    assert "interval: 600" in helper_source
    assert "repeat: false" in helper_source
    assert 'running: actionControl.toolTip !== "" && hoverArea.containsMouse' in helper_source
    assert "onTriggered: tooltip.show()" in helper_source
    assert "onTriggered: actionTooltip.show()" not in source

def test_auto_updater_keeps_update_dialog_wiring_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterUpdateDialog.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterUpdateDialog {" in source
    assert "updateDialogComponent.createObject(root)" in source
    assert "UpdateDialog {" in helper_source
    assert "required property var updaterControl" in helper_source
    assert "updaterControl._awaitingDecision" in helper_source
    assert "updaterControl._beginDownload" in helper_source
    assert "updaterControl._clearPending()" in helper_source
    for marker in (
        "\n        UpdateDialog {",
        "onConfirmed:",
        "onCancelled:",
        "\n            id: updateDialog\n",
    ):
        assert marker not in source

def test_auto_updater_keeps_feedback_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 50
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterFeedbackTimer {" in source
    assert "required property var host" in helper_source
    assert 'objectName: "autoUpdaterFeedbackTimer"' in helper_source
    assert "interval: host._feedbackDuration" in helper_source
    assert "running: host._feedbackActive" in helper_source
    assert "host._feedbackDuration > Enums.duration.none" in helper_source
    assert "onTriggered: host._dismissFeedback()" in helper_source
    assert "\n    Timer {" not in source

def test_auto_updater_keeps_signal_orchestration_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterSignalConnections.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert "FeedbackInternal.AutoUpdaterSignalConnections {" in source
    assert "host: root" in source
    assert "required property var host" in helper_source
    assert "target: host.updater" in helper_source
    assert "ignoreUnknownSignals: true" in helper_source
    assert "function onUpdateAvailable(" in helper_source
    assert "function onDownloadFinished(" in helper_source
    assert "function onInstallPreparationFinished(" in helper_source
    assert "\n    Connections {" not in source
    assert "function onUpdateAvailable(" not in source

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

def test_auto_updater_toast_presenter_keeps_sync_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdaterToastPresenter.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterToastSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterToastSyncTimer {" in source
    assert "id: syncTimer" in source
    assert "host: root" in source
    assert "syncTimer.restart()" in source
    assert source.count("syncTimer.stop()") == 2
    assert "required property var host" in helper_source
    assert 'objectName: "autoUpdaterToastSyncTimer"' in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "onTriggered: host._sync()" in helper_source
    assert "\n    Timer {" not in source

def test_info_bar_keeps_shared_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/InfoBarCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/_internal/"
        "InfoBarCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert 'import "_internal" as InfoBarInternal' in source
    assert "InfoBarInternal.InfoBarCloseTimer {" in source
    assert "id: closeTimer" in source
    assert "host: control" in source
    assert helper_source.count("Timer {") == 1
    assert "required property var host" in helper_source
    assert "readonly property bool completeMode" in helper_source
    assert 'objectName: "infoBarCloseTimer"' in helper_source
    assert "running: host._autoCloseActive || host._completeCloseActive" in helper_source
    assert "interval: completeMode ? host.completeDuration : host.duration" in helper_source
    assert "restart()" in helper_source
    assert "onTriggered: host.hide()" in helper_source
    assert "readonly property bool completeMode" not in source
    assert "\n    Timer {" not in source

def test_toast_keeps_auto_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "ToastAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastAutoCloseTimer {" in source
    assert "id: hideTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "\n        interval: control.duration\n" not in source
    assert "\n        running: control.visible && control.duration > 0 && !_isProgressMode\n" not in source
    assert "onTriggered: control.hide()" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "toastHideTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "running: host.visible && host.duration > 0 && !host._isProgressMode" in helper_source
    assert "onTriggered: host.hide()" in helper_source

def test_toast_keeps_progress_complete_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "ToastProgressCompleteTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 155
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastProgressCompleteTimer {" in source
    assert "id: completeTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "toastCompleteTimer"' in helper_source
    assert "running: host._progressComplete && host.visible" in helper_source
    assert "interval: host.completeDuration" in helper_source
    assert "onTriggered: host.hide()" in helper_source

def test_desktop_notification_keeps_auto_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/"
        "DesktopNotification.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "DesktopNotificationAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 235
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.DesktopNotificationAutoCloseTimer {" in source
    assert "id: autoCloseTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "interval: duration" not in source
    assert "onTriggered: control.hide()" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "desktopNotificationAutoCloseTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "onTriggered: host.hide()" in helper_source

def test_notification_animator_keeps_geometry_update_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/"
        "NotificationAnimator.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "NotificationAnimatorGeometryUpdateTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 270
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as NotificationInternal' in source
    assert "property Timer _geometryUpdateTimer:" in source
    assert "NotificationInternal.NotificationAnimatorGeometryUpdateTimer {" in source
    assert "host: animator" in source
    assert "required property var host" in helper_source
    assert (
        'objectName: "notificationAnimatorGeometryUpdateTimer"'
        in helper_source
    )
    assert "interval: Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host.updatePosition()" in helper_source
    assert "_geometryUpdateTimer.restart()" in source
    assert "_geometryUpdateTimer.stop()" in source
    assert "property Timer _geometryUpdateTimer: Timer {" not in source
    assert "onTriggered: animator.updatePosition()" not in source

def test_window_outside_notification_keeps_native_overlay_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "WindowOutsideOverlay.qml"
    )
    geometry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "WindowOutsideGeometry.qml"
    )
    animator = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationAnimator.qml"
    )
    source = entry.read_text(encoding="utf-8")
    geometry_source = geometry.read_text(encoding="utf-8")
    animator_source = animator.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert len(geometry_source.splitlines()) < 45
    assert len(animator_source.splitlines()) < 270
    assert "required property var hostWindow" in source
    assert "property alias animator: animator" in source
    assert "property alias content: container" in source
    assert "property bool _attached: false" in source
    assert "function _releaseAttachment()" in source
    assert "if (!_attached) return false" in source
    assert "NotificationInternal.WindowOutsideGeometry {" in source
    assert "parentItem: outsideGeometry" in source
    assert "reverseShowDirection: true" in source
    assert "NotificationAnimator {" in source
    assert "target: control" in source
    assert "property bool reverseShowDirection: false" in animator_source
    assert "WindowHelper.registerWindowAttachment(" in source
    assert "WindowHelper.unregisterWindowAttachment(control)" in source
    assert "target: control.hostWindow" in source
    assert "target: typeof WindowHelper !== \"undefined\" ? WindowHelper : null" in source
    assert "required property var hostWindow" in geometry_source
    assert "required property int position" in geometry_source
    assert "required property real targetWidth" in geometry_source
    assert "required property real targetHeight" in geometry_source
    assert "WindowHelper.windowAttachmentGeometry(" in geometry_source
    assert "parentItem && typeof parentItem.calculate === \"function\"" in animator_source
    assert "var attachedGeometry = parentItem" in animator_source
    assert "property var hostWindow" not in animator_source

def test_notification_manager_keeps_outside_mode_as_internal_component_wiring():
    manager = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    qmldir = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/qmldir"
    )
    source = manager.read_text(encoding="utf-8")
    qmldir_source = qmldir.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert "property var _windowOutsideComponent: null" in source
    assert "Enums.notification.mode_window_outside" in source
    assert "function _createWindowOutside(" in source
    assert "_getWindowOutsideComponent()" in source
    assert "WindowHelper" not in source
    assert "WindowOutsideGeometry" not in source
    assert "WindowOutsideOverlay WindowOutsideOverlay.qml" in qmldir_source
    assert "WindowOutsideGeometry WindowOutsideGeometry.qml" in qmldir_source

def test_marquee_keeps_layout_start_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Marquee.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/MarqueeStartTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 130
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as DataInternal' in source
    assert "DataInternal.MarqueeStartTimer {" in source
    assert "id: startTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "marqueeStartTimer"' in helper_source
    assert "interval: 100" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._tryStartAnimation()" in helper_source

def test_paginator_keeps_page_settle_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Paginator.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "PaginatorPageSettleTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.PaginatorPageSettleTimer {" in source
    assert "id: pageSettleTimer" in source
    assert "host: root" in source
    assert "slideAnimation: pageSlideAnimation" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var slideAnimation" in helper_source
    assert 'objectName: "paginatorPageSettleTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "if (!slideAnimation.running) host._settleLoadedPages()" in helper_source
    assert "if (!pageSlideAnimation.running) root._settleLoadedPages()" not in source

def test_menu_bar_keeps_dynamic_close_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/MenuBar.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/MenuBarCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as NavigationInternal' in source
    assert "id: closeTimerComponent" in source
    assert "NavigationInternal.MenuBarCloseTimer {" in source
    assert "menuBar: control" in source
    assert "closeTimerComponent.createObject(" in source
    assert '"menuButton": menuBtn' in source
    assert '"ownerItem": menuItemContainer' in source
    assert "required property Item menuBar" in helper_source
    assert "required property Item menuButton" in helper_source
    assert "required property Item ownerItem" in helper_source
    assert 'objectName: "menuBarCloseTimer"' in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert "ownerItem._closeTimer = null" in helper_source
    assert "destroy()" in helper_source
    assert "\n        Timer {" not in source
    assert "if (!menuButton.hovered)" not in source

def test_breadcrumb_keeps_dynamic_stage_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Breadcrumb.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/BreadcrumbStageTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 360
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal"' in source
    assert "id: stageTimerComponent" in source
    assert "BreadcrumbStageTimer {}" in source
    assert "stageTimerComponent.createObject(" in source
    assert '"timerInterval": timerInterval' in source
    assert '"triggerCallback": triggerCallback' in source
    assert '"releaseCallback": releaseCallback' in source
    assert "required property int timerInterval" in helper_source
    assert "required property var triggerCallback" in helper_source
    assert "required property var releaseCallback" in helper_source
    assert 'objectName: "breadcrumbStageTimer"' in helper_source
    assert "interval: timerInterval" in helper_source
    assert "repeat: false" in helper_source
    assert helper_source.index("triggerCallback()") < helper_source.index(
        "releaseCallback(stageTimer)"
    )
    assert helper_source.index("releaseCallback(stageTimer)") < helper_source.index(
        "destroy()"
    )
    assert "\n        Timer {" not in source
    assert "releaseCallback(stageTimer)" not in source

def test_scroll_viewport_state_keeps_phase_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/ScrollViewportState.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "ScrollViewportPhaseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as ScrollBarInternal' in source
    assert "ScrollBarInternal.ScrollViewportPhaseTimer {" in source
    assert "id: phaseTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "scrollViewportPhaseTimer"' in helper_source
    assert "host._phase === host._phaseContentUpdate" in helper_source
    assert "host._phase === host._phaseSuppressionClear" in helper_source
    assert "Enums.duration.fast" in helper_source
    assert "Enums.duration.instant" in helper_source
    assert "Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._runPhase()" in helper_source
    assert "phaseTimer.restart()" in source
    assert "phaseTimer.stop()" in source
    assert "\n    Timer {" not in source
    assert "onTriggered: control._runPhase()" not in source

def test_hover_behavior_keeps_unmatched_target_timer_modularized():
    entry = _source("prismqml/PrismQML/effects/HoverBehavior.qml")
    helper = _source(
        "prismqml/PrismQML/effects/_internal/"
        "HoverBehaviorUnmatchedTargetTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as EffectsInternal' in source
    assert "property QtObject _unmatchedTargetTimer:" in source
    assert "EffectsInternal.HoverBehaviorUnmatchedTargetTimer {" in source
    assert "host: root" in source
    assert "required property var host" in helper_source
    assert 'objectName: "hoverBehaviorUnmatchedTargetTimer"' in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._awaitingActiveAfterTarget = false" in helper_source
    assert "_unmatchedTargetTimer.stop()" in source
    assert "_unmatchedTargetTimer.restart()" in source
    assert "property QtObject _unmatchedTargetTimer: Timer {" not in source
    assert "onTriggered: root._awaitingActiveAfterTarget = false" not in source
