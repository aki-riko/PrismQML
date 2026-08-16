# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML architecture boundaries and size gates. QML 架构边界与大小门禁。"""

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
OVERSIZED_QML_EXCEPTIONS = {
    "prismqml/PrismQML/PrismEnums/Metrics.qml",
}


def _source(relative_path: str) -> Path:
    return ROOT / relative_path


def _assert_modularized(entry_path: str, helper_path: str, helper_type: str) -> None:
    entry = _source(entry_path)
    helper = _source(helper_path)

    assert entry.exists()
    assert helper.exists()
    assert len(entry.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert f"{helper_type} {{" in entry.read_text(encoding="utf-8")


def test_qml_files_respect_hard_size_limit():
    violations = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(ROOT).as_posix()
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 700 and relative not in OVERSIZED_QML_EXCEPTIONS:
            violations.append(f"{relative}: {line_count} lines")

    assert violations == []


def test_windows_core_keeps_frame_modularized():
    entry = _source("prismqml/PrismQML/WindowsCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsCoreFrame.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "WindowsCoreFrame {" in source
    assert "required property var targetWindow" in helper_source
    assert "property alias contentData: contentContainer.data" in helper_source
    assert "property alias leftPanelData: leftPanelContainer.data" in helper_source
    assert "id: windowFrame\n" not in source
    assert "id: contentContainer" not in source
    assert "WindowDragHandle {" not in source


def test_windows_core_keeps_resize_timer_modularized():
    entry = _source("prismqml/PrismQML/WindowsCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsResizeHandlesTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "WindowsResizeHandlesTimer {" in source
    assert "id: _resizeHandlesTimer" in source
    assert "host: window" in source
    assert "required property var host" in helper_source
    assert "interval: Enums.window.resizeHandlesDelayMs" in helper_source
    assert "host._resizeHandlesReady = true" in helper_source
    assert "\n    Timer {" not in source


def test_login_window_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/auth/LoginWindow.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/auth/_internal/LoginWindowContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "LoginWindowContent {" in source
    assert "required property var loginControl" in helper_source
    assert "property alias usernameInput: usernameInput" in helper_source
    assert "property alias passwordInput: passwordInput" in helper_source
    assert "MatrixRain {" not in source
    assert "ShadowedRectangle {" not in source
    assert 'objectName: "loginModeToggleArea"' not in source


def test_data_widget_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/DataWidgetCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/DataWidgetContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "DataWidgetContent {" in source
    assert "required property var dataControl" in helper_source
    assert "property alias listView: listView" in helper_source
    assert "property alias scrollViewportState: scrollViewportState" in helper_source
    assert "contentLayer.needsVerticalScrollBar" in source
    assert "function createHorizontalScrollMixin()" in helper_source
    assert "horizontalScrollMixinComponent.createObject(contentArea)" in helper_source
    assert "contentLayer.createHorizontalScrollMixin()" in source
    assert "RectangularShadow {" not in source
    assert "QtQ.ListView {" not in source
    assert "HorizontalScrollMixin {" not in source


def test_navigation_window_core_keeps_orchestration_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    loading = _source(
        "prismqml/PrismQML/_internal/NavigationWindowLoading.js"
    )
    routing = _source(
        "prismqml/PrismQML/_internal/NavigationWindowRouting.js"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (loading, routing):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source

    assert (
        'import "_internal/NavigationWindowLoading.js" '
        "as NavigationWindowLoading"
    ) in source
    assert (
        'import "_internal/NavigationWindowRouting.js" '
        "as NavigationWindowRouting"
    ) in source
    assert "NavigationWindowLoading.start(window, index)" in source
    assert "NavigationWindowLoading.completeVisual(window, index)" in source
    assert "NavigationWindowRouting.moveDefaultPages(window," in source
    assert "NavigationWindowRouting.syncSelection(window," in source
    assert "NavigationWindowRouting.handleBottomItemClicked(window," in source


def test_navigation_window_core_keeps_splash_timer_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/NavigationSplashTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 480
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert 'import "_internal"' in source
    assert "NavigationSplashTimer {" in source
    assert "id: _splashTimer" in source
    assert "host: window" in source
    assert "Timer {" in helper_source
    assert "required property var host" in helper_source
    assert "property bool _minimumVisiblePhase: false" in helper_source
    assert "property int _minimumVisibleInterval:" in helper_source
    assert "property var _onTimeout: null" in helper_source
    assert "host._scheduleSplashDismiss()" in helper_source
    assert "Enums.duration.splashTimeout" in helper_source
    assert "property bool _minimumVisiblePhase: false" not in source
    assert "property var _onTimeout: null" not in source


def test_navigation_window_core_keeps_mica_timers_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    backdrop = _source(
        "prismqml/PrismQML/_internal/NavigationMicaBackdropCommitTimer.qml"
    )
    reapply = _source(
        "prismqml/PrismQML/_internal/NavigationMicaReapplyTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    backdrop_source = backdrop.read_text(encoding="utf-8")
    reapply_source = reapply.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 470
    for helper in (backdrop, reapply):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "NavigationMicaBackdropCommitTimer {" in source
    assert source.count("NavigationMicaReapplyTimer {") == 2
    assert "id: _micaBackdropCommitTimer" in source
    assert "id: _micaReapplyTimer" in source
    assert "id: _micaLateReapplyTimer" in source
    assert "required property var host" in backdrop_source
    assert "required property var host" in reapply_source
    assert "required property bool late" in reapply_source
    assert "host._micaBackdropReady = true" in backdrop_source
    assert "host._applyMicaEffect(" in reapply_source
    assert "Enums.window.micaReapplyDelayMs" in backdrop_source
    assert "Enums.window.micaLateReapplyDelayMs" in reapply_source
    assert "interval: Enums.window.micaReapplyDelayMs" not in source
    assert "interval: Enums.window.micaLateReapplyDelayMs" not in source
    assert "window._micaBackdropReady = true" not in source


def test_navigation_panel_keeps_background_layer_modularized():
    entry = _source("prismqml/PrismQML/navigation/NavigationPanelCore.qml")
    background = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBackground.qml"
    )
    border = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBorder.qml"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "NavigationPanelBackground {" in source
    assert "NavigationPanelBorder {" in source
    for helper in (background, border):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 300
        assert "required property var panel" in helper_source
        assert "readonly property var control: panel" in helper_source
    assert "z: -2" in background.read_text(encoding="utf-8")
    assert "id: bgCanvas" not in source
    assert "id: acrylicLayer" not in source
    assert "id: rightBorderCanvas" not in source
    assert "TicketPaper {" not in source


def test_navigation_panel_keeps_indicator_timers_modularized():
    entry = _source("prismqml/PrismQML/navigation/NavigationPanelCore.qml")
    tracker = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorTrackerTimer.qml"
    )
    scroll_stop = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorScrollStopTimer.qml"
    )
    init_timer = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tracker_source = tracker.read_text(encoding="utf-8")
    scroll_stop_source = scroll_stop.read_text(encoding="utf-8")
    init_source = init_timer.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (tracker, scroll_stop, init_timer):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "NavigationIndicatorTrackerTimer {" in source
    assert "NavigationIndicatorScrollStopTimer {" in source
    assert "NavigationIndicatorInitTimer {" in source
    assert "id: indicatorTracker" in source
    assert "id: _scrollStopTimer" in source
    assert "id: _initTimer" in source
    assert source.count("host: control") == 2
    assert "indicator: navIndicator" in source
    assert "tracker: indicatorTracker" in source
    assert "required property var host" in tracker_source
    assert "required property var indicator" in tracker_source
    assert "required property var tracker" in scroll_stop_source
    assert "required property var host" in init_source
    assert "property bool _scrolling: false" in tracker_source
    assert "Enums.duration.tick" in tracker_source
    assert "host._updateIndicatorPositionRealtime()" in tracker_source
    assert "tracker._scrolling = false" in scroll_stop_source
    assert "Enums.duration.fast" in scroll_stop_source
    assert "interval: 50" in init_source
    assert "host._initIndicatorPosition()" in init_source
    assert "\n    Timer {" not in source


def test_toggle_navigation_bar_keeps_indicator_timers_modularized():
    entry = _source("prismqml/PrismQML/navigation/ToggleNavigationBar.qml")
    tracker = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "ToggleNavigationIndicatorTrackerTimer.qml"
    )
    scroll_stop = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorScrollStopTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tracker_source = tracker.read_text(encoding="utf-8")
    scroll_stop_source = scroll_stop.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    for helper in (tracker, scroll_stop):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "ToggleNavigationIndicatorTrackerTimer {" in source
    assert "NavigationIndicatorScrollStopTimer {" in source
    assert "id: _indicatorTracker" in source
    assert "id: _scrollStopTimer" in source
    assert "host: control" in source
    assert "tracker: _indicatorTracker" in source
    assert "required property var host" in tracker_source
    assert "property bool _scrolling: false" in tracker_source
    assert "Enums.duration.tick" in tracker_source
    assert "host._updateIndicator(false)" in tracker_source
    assert "required property var tracker" in scroll_stop_source
    assert "Enums.duration.fast" in scroll_stop_source
    assert "tracker._scrolling = false" in scroll_stop_source
    assert "\n    Timer {" not in source


def test_button_core_keeps_behavior_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    logic = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonLogic.js"
    )
    helper_paths = (
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonFeatureLoader.qml",
            "ButtonFeatureLoader",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonInteraction.qml",
            "ButtonInteraction",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonCountdown.qml",
            "ButtonCountdown",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonSurface.qml",
            "ButtonSurface",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonContentLayer.qml",
            "ButtonContentLayer",
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert logic.exists()
    logic_source = logic.read_text(encoding="utf-8")
    assert len(logic_source.splitlines()) < 500
    assert ".pragma library" in logic_source
    assert "Enums" not in logic_source

    for relative_path, helper_type in helper_paths:
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert 'import "_internal" as ButtonInternal' in source
    assert 'import "_internal/ButtonLogic.js" as ButtonLogic' in source
    assert "ButtonLogic.click(control, Enums)" in source
    assert "ButtonLogic.updateTargetColors(" in source
    assert "ButtonLogic.prewarmMenu(control, Enums," in source


def test_button_core_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonSurface {" in source
    assert "required property var buttonControl" in helper_source
    for alias in (
        "background",
        "border",
        "bgColorAnimation",
        "borderColorAnimation",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "readonly property real animatedPressShift:" in helper_source
    assert "readonly property var pressTransform:" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "sourceComponent: ButtonNeoShadow" in helper_source
    assert "ColorAnimation {" in helper_source
    assert "RectangularShadow {" not in source
    assert "NeumorphicShadow {" not in source
    assert "sourceComponent: ButtonNeoShadow" not in source
    assert "ColorAnimation {" not in source


def test_button_core_keeps_content_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonContentLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert "ButtonInternal.ButtonContentLayer {" in source
    assert "required property var buttonControl" in helper_source
    assert "required property var pressTransform" in helper_source
    assert "default property alias contentData: customContentContainer.data" in helper_source
    assert "property alias customContentContainer: customContentContainer" in helper_source
    assert "property alias contentLoader: contentLoader" in helper_source
    assert "ButtonContent {" in helper_source
    assert "Item {\n        id: customContentContainer" not in source
    assert "Loader {\n        id: contentLoader" not in source
    assert "ButtonContent {" not in source


def test_button_dropdown_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonDropdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonDropdownSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 160
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonDropdownSurface {" in source
    assert "required property var dropdownControl" in helper_source
    for state in ("mainHovered", "mainPressed", "dropHovered", "dropPressed"):
        assert f"readonly property bool {state}:" in helper_source
        assert f"dropdownSurface.{state}" in source
    for marker in (
        "id: splitMainArea",
        "id: splitDropArea",
        "id: splitMainMouse",
        "id: splitDropMouse",
        "id: menuArrow",
    ):
        assert marker not in source


def test_popup_window_core_keeps_animation_logic_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/utils/PopupWindowCore.qml",
        "prismqml/PrismQML/controls/utils/_internal/PopupAnimations.qml",
        "PopupAnimations",
    )


def test_popup_window_core_keeps_positioning_and_prewarm_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    helpers = (
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPositioning.js"
        ),
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPrewarm.js"
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in helpers:
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source
        assert "Enums" not in helper_source

    assert (
        'import "_internal/PopupPositioning.js" as PopupPositioning'
        in source
    )
    assert 'import "_internal/PopupPrewarm.js" as PopupPrewarm' in source
    assert "PopupPositioning.calcControlsPopupPosition(" in source
    assert "PopupPositioning.applyTrackedPosition(" in source
    assert "PopupPrewarm.doPrewarm(" in source


def test_popup_window_core_keeps_lifecycle_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    prewarm = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPrewarmTimer.qml"
    )
    lifecycle = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupLifecycleTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    prewarm_source = prewarm.read_text(encoding="utf-8")
    lifecycle_source = lifecycle.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (prewarm, lifecycle):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "PopupPrewarmTimer {" in source
    assert "PopupLifecycleTimer {" in source
    assert "id: prewarmTimer" in source
    assert "id: lifecycleTimer" in source
    assert "host: control" in source
    assert "readonly property alias _lifecycleTimer: lifecycleTimer" in source
    assert "required property var host" in prewarm_source
    assert "required property var host" in lifecycle_source
    assert "interval: 0" in prewarm_source
    assert "host._doPrewarm()" in prewarm_source
    assert "Enums.popupMetrics.showAnimDelayMs" in lifecycle_source
    assert "PopupLifecycle.onTimer(host)" in lifecycle_source
    assert "\n    Timer {" not in source


def test_list_widget_keeps_data_and_selection_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/List/ListWidget.qml"
    )
    controller = _source(
        "prismqml/PrismQML/controls/data/List/_internal/ListDataController.js"
    )
    source = entry.read_text(encoding="utf-8")
    controller_source = controller.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert controller.exists()
    assert len(controller_source.splitlines()) < 500
    assert ".pragma library" in controller_source
    assert (
        'import "_internal/ListDataController.js" as ListDataController'
        in source
    )

    delegated_methods = (
        "addItem", "addItems", "insertItem", "insertItems", "takeItem",
        "item", "row", "currentItem", "setCurrentItem", "currentRow",
        "setCurrentRow", "selectedItems", "clearSelection", "selectAll",
        "setSelectionMode", "findItems", "sortItems", "clear",
        "setItemText", "setItemIcon", "setItemData", "itemData",
        "setItemCheckState", "itemCheckState", "setItemSelected",
        "handleItemClick", "updateSelectedRows",
    )
    for method in delegated_methods:
        assert f"function {method}(" in controller_source
        assert f"ListDataController.{method}(" in source


def test_stacked_widget_keeps_source_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/StackedSourcePages.qml",
        "StackedSourcePages",
    )


def test_stacked_widget_keeps_switching_orchestration_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/StackedWidget.qml")
    source = entry.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 500

    for relative_path, helper_type in (
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedLazyController.qml",
            "StackedLazyController",
        ),
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedVisibilityController.qml",
            "StackedVisibilityController",
        ),
    ):
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert "lazyController.preloadLazyHelperWhenReady" in source
    assert "visibilityController.doAnimation" in source


def test_stacked_widget_keeps_direct_pages_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/StackedDirectPages.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 480
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedDirectPages {" in source
    assert "property Item containerItem: directPages" in source
    assert "required property Item host" in helper_source
    assert 'objectName: "stackLayout"' in helper_source
    assert "host._displayIndex" in helper_source
    assert "child.width = Qt.binding" in helper_source
    assert "child.height = Qt.binding" in helper_source
    for marker in (
        "\n        id: stackLayout\n",
        "stackLayout.children",
        "child.width = Qt.binding",
        "child.height = Qt.binding",
    ):
        assert marker not in source


def test_stacked_widget_keeps_lazy_helper_loader_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "StackedLazyHelperLoader.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 470
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedLazyHelperLoader {" in source
    assert helper_source.startswith("// Copyright 2026 aki-riko")
    assert "Loader {" in helper_source
    assert "required property Item host" in helper_source
    assert "host._asynchronousPageLoaderEnabled" in helper_source
    assert "host._configureLazyHelper(item)" in helper_source
    assert "host._flushPendingLazySwitch()" in helper_source
    for handler in ("onActiveChanged:", "onStatusChanged:", "onLoaded:"):
        assert helper_source.count(handler) == 1
        assert handler not in source
    assert "id: lazyHelperLoader" in source
    assert "host: control" in source
    assert "lazyHelperLoader.setSource(Qt.resolvedUrl" in source
    assert "lazyHelperLoader: lazyHelperLoader" in source
    assert "StackedLazyHelperLoader {\n        id: lazyHelperLoader\n        host: control\n" in source


def test_tab_widget_keeps_content_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/TabWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/TabContentPages.qml",
        "TabContentPages",
    )


def test_tab_widget_keeps_tab_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source("prismqml/PrismQML/controls/navigation/_internal/TabItem.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "TabItem {" in entry.read_text(encoding="utf-8")


def test_tab_widget_keeps_edge_auto_scroll_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabEdgeAutoScroll.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 450
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "TabEdgeAutoScroll {" in source
    assert "FrameAnimation {" in helper_source
    assert "required property Item host" in helper_source
    assert "required property Flickable tabFlickable" in helper_source
    assert "host._dragging" in helper_source
    assert "host._dragPointerRowX" in helper_source
    assert "frameTime" in helper_source
    assert "onTriggered:" in helper_source
    assert "var edgeMargin = 40" not in source
    assert "var step = 480 * frameTime" not in source
    assert "id: _edgeAutoScrollTimer" in source
    assert "host: control" in source
    assert "tabFlickable: tabFlickable" in source


def test_tab_widget_keeps_indicator_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabIndicator.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 250
    assert "TabIndicator {" in source
    assert "Item {" in helper_source
    for required_property in (
        "required property Item host",
        "required property Item tabBar",
        "required property Flickable tabFlickable",
        "required property var tabRepeater",
        "required property Item tabRow",
    ):
        assert required_property in helper_source
    for binding in (
        "host: control",
        "tabBar: tabBarBg",
        "tabFlickable: tabFlickable",
        "tabRepeater: tabRepeater",
        "tabRow: tabRow",
    ):
        assert binding in source
    assert "function _scheduleSync(animate)" in helper_source
    assert "function syncIndicator(animate)" in helper_source
    assert "SlidingIndicatorAnimation {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "NeoShadow {" in helper_source
    assert "id: slidingIndicator" in source
    for marker in (
        "property int _currentTabKey:",
        "function _scheduleSync(animate)",
        "SlidingIndicatorAnimation {",
        "id: indicatorBg",
    ):
        assert marker not in source


def test_bar_chart_keeps_single_series_delegate_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartBar.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert entry.read_text(encoding="utf-8").count("BarChartBar {") == 2


def test_line_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 300
    assert "LineChartCanvas {" in source
    assert "lineControl: root" in source
    assert "required property var lineControl" in helper_source
    assert "function paintSingleSeries(" in helper_source
    assert "function paintMultiSeries(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintSingleSeries(" not in source
    assert "function paintMultiSeries(" not in source


def test_boxplot_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "BoxplotChartCanvas {" in source
    assert "boxplotControl: root" in source
    assert "required property var boxplotControl" in helper_source
    assert "readonly property var control: boxplotControl" in helper_source
    assert "function paintVertical(" in helper_source
    assert "function paintHorizontal(" in helper_source
    assert "Geometry.paintRange(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintVertical(" not in source
    assert "function paintHorizontal(" not in source


def test_drawer_keeps_outside_window_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Drawer/Drawer.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/"
        "DrawerOutsideWindow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as DrawerInternal' in source
    assert "DrawerInternal.DrawerOutsideWindow {" in source
    assert "property var drawerControl: control" in source
    assert "drawerControl: outsideDrawerWindowLoader.drawerControl" in source
    assert "required property var drawerControl" in helper_source
    assert "readonly property alias panel: outsideDrawerPanel" in helper_source
    assert "readonly property var control: drawerControl" in helper_source
    assert 'objectName: "outsideDrawerWindow"' in helper_source
    for token in (
        'objectName: "outsideDrawerViewport"',
        'objectName: "outsideDrawerPanel"',
        "transientParent: null",
        "\n            Window {",
    ):
        assert token not in source

    surface = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/DrawerSurface.qml"
    )
    surface_source = surface.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 370
    assert surface.exists()
    assert len(surface_source.splitlines()) < 220
    assert "DrawerInternal.DrawerSurface {" in source
    assert "required property var drawerControl" in surface_source
    assert "default property alias content: contentItem.data" in surface_source
    assert "readonly property alias panel: drawer" in surface_source
    for token in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "\n        id: drawer\n",
        "\n        id: contentItem\n",
    ):
        assert token not in source


def test_smooth_scroll_helper_keeps_wheel_input_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollWheelArea.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as ScrollBarInternal' in source
    assert "ScrollBarInternal.SmoothScrollWheelArea {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "parent: scrollHelper.target" in helper_source
    assert "anchors.fill: parent" in helper_source
    assert "onWheel:" in helper_source
    assert "MouseArea {" not in source
    assert "onWheel:" not in source


def test_smooth_scroll_helper_keeps_bounce_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollBounceTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "ScrollBarInternal.SmoothScrollBounceTimer {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "required property bool verticalAxis" in helper_source
    assert "scrollHelper._releaseBounceTimer(verticalAxis, bounceTimer)" in helper_source
    assert "\n        Timer {\n            id: bounceTimer\n" not in source


def test_constants_keeps_theme_colors_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Constants.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/ConstantsThemeColors.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ConstantsInternal' in source
    assert (
        "readonly property QtObject themeColors: "
        "ConstantsInternal.ConstantsThemeColors {}"
    ) in source
    assert "readonly property QtObject themeColors: QtObject {" not in source
    assert "readonly property color backgroundDark" in helper_source
    assert "readonly property color accentForeground" in helper_source
    assert "readonly property color tabSelectedLight" in helper_source
    assert "required property bool isDark" not in helper_source


def test_metrics_keeps_shadow_logic_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Metrics.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/MetricsShadow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 900
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as MetricsInternal' in source
    assert "readonly property QtObject shadow: MetricsInternal.MetricsShadow {" in source
    assert "isDark: root.isDark" in source
    assert "isTicket: root.isTicket" in source
    assert "readonly property QtObject shadow: QtObject {" not in source
    assert "required property bool isDark" in helper_source
    assert "required property bool isTicket" in helper_source
    for level in (2, 4, 8, 16, 28):
        assert f"readonly property QtObject level{level}: QtObject {{" in helper_source
        assert f"function applyLevel{level}(target)" in helper_source


def test_combo_box_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxCoreContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "ComboBoxCoreContent {" in source
    assert "required property var comboControl" in helper_source
    for alias in (
        "editableInput",
        "mouseArea",
        "editableClickArea",
        "comboTextMeasureLoader",
        "popup",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "property alias _popup: comboContent.popup" in source
    assert "layer.enabled: true" in helper_source
    assert "PopupWindowCore {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "PopupWindowCore {" not in source
    assert "layer.enabled: true" not in source


def test_combo_box_multi_tree_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxMultiTree.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxMultiTreeContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 220
    assert 'import "_internal"' in source
    assert "ComboBoxMultiTreeContent {" in source
    assert "required property var comboControl" in helper_source
    assert "property alias _flatListModel: multiTreeContent.flatListModel" in source
    assert "property alias tokenFlickable: multiTreeContent.tokenFlickable" in source
    assert "property alias flatListModel: internalFlatListModel" in helper_source
    assert "property alias tokenFlickable: tokenFlickable" in helper_source
    assert "property alias popupContent: treePopupContent" in helper_source
    for visual_type in ("PopupSearchBox", "TreeMenuDelegate", "MultiSelectToken"):
        assert f"{visual_type} {{" in helper_source
        assert f"{visual_type} {{" not in source
    assert "ListModel {" in helper_source
    assert "Flickable {" in helper_source
    assert "popupContent: multiTreeContent.popupContent" in source


def test_xy_chart_core_keeps_axes_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartAxes.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "XYChartAxes {" in source
    assert "chartControl: root" in source
    assert "required property var chartControl" in helper_source
    assert "required property var axisFontMetrics" in helper_source
    assert "readonly property Item chartArea: axesLayer.chartArea" in source
    assert "readonly property Item chartArea: chartAreaItem" in helper_source
    assert "readonly property var control: chartControl" in helper_source
    for token in (
        "id: gridLines",
        "id: horizontalYAxisLabels",
        "id: xAxisLabels",
        "id: scatterXAxisLabels",
        "HoverBehavior on color",
        'objectName: "chartXAxisViewport"',
    ):
        assert token not in source


def test_chart_view_keeps_render_layer_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Chart/ChartView.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/ChartRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "ChartRenderLayer {" in source
    assert "required property var chartControl" in helper_source
    assert "renderLayer.chart" not in helper_source
    for loader_name in (
        "xyChartBaseLoader", "barContentLoader", "lineContentLoader",
        "scatterContentLoader",
    ):
        assert f"property alias {loader_name}: {loader_name}" in helper_source
        assert f'objectName: "{loader_name}"' in helper_source
    for property_name, loader_name in (
        ("_xyChartBase", "xyChartBaseLoader"),
        ("_barContent", "barContentLoader"),
        ("_lineContent", "lineContentLoader"),
        ("_scatterContent", "scatterContentLoader"),
    ):
        assert (
            f"readonly property var {property_name}: "
            f"renderLayer.{loader_name}.item"
        ) in source


def test_settings_card_keeps_render_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/SettingsCard.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/_internal/"
        "SettingsCardRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "SettingsCardRenderLayer {" in source
    assert "required property var cardControl" in helper_source
    assert "property alias cardLoader: cardLoader" in helper_source
    assert "readonly property var control: cardControl" in helper_source
    assert "Component {" not in source
    assert "FolderDialog {" not in source


def test_chat_message_list_keeps_slot_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageSlot.qml"
    )
    viewport = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "ChatMessageSlot {" in viewport.read_text(encoding="utf-8")


def test_chat_message_list_keeps_viewport_content_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageViewport {" in source
    assert "required property var chatControl" in helper_source
    assert "required property var messageModel" in helper_source
    for alias in ("viewport", "contentColumn", "repeater"):
        assert f"property alias {alias}:" in helper_source
    for alias in ("messageViewport", "messageColumn", "messageRepeater"):
        assert f"property alias {alias}: messageContent." in source
    for marker in (
        "id: messageViewport",
        "id: messageColumn",
        "id: messageRepeater",
        "ChatMessageSlot {",
    ):
        assert marker not in source


def test_tip_popup_keeps_main_window_surface_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPopupWindow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TipPopupWindow {" in source
    assert "required property var popupControl" in helper_source
    assert "required property var positionHelper" in helper_source
    assert 'objectName: "tipPopupSurface"' in helper_source
    assert "\n                id: popupWindow\n" not in source
    for marker in (
        'objectName: "tipPopupSurface"',
        'objectName: "tipPrimaryActionButton"',
        'objectName: "tipSecondaryActionButton"',
    ):
        assert marker not in source


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


def test_menu_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source("prismqml/PrismQML/controls/menus/_internal/MenuContent.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "MenuContent {" in entry.read_text(encoding="utf-8")


def test_menu_core_keeps_submenu_open_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/MenuSubmenuOpenTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var host" in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert (
        "host._pendingSubmenuAction.hovered" in helper_source
    )
    assert "host._openSubmenuForAction(" in helper_source
    assert "MenuSubmenuOpenTimer {" in source
    assert "id: submenuOpenTimer" in source
    assert "host: control" in source
    assert "\n Timer {" not in source
    assert "interval: Enums.duration.fast" not in source
    assert "_pendingSubmenuAction && _pendingSubmenuAction.hovered" not in source


def test_infobar_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/InfoBar/InfoBarCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/_internal/InfoBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as InfoBarInternal' in source
    assert "InfoBarInternal.InfoBarContent {" in source
    assert "required property var infoBar" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalContentHeight" in helper_source
    assert "readonly property real verticalContentHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_toast_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/ToastContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastContent {" in source
    assert "required property var toast" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalHeight" in helper_source
    assert "readonly property real verticalHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_calendar_picker_core_keeps_content_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/CalendarPickerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/_internal/"
        "CalendarPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 200
    assert helper.exists()
    assert len(helper_source.splitlines()) < 450
    assert 'import "_internal" as DatePickerInternal' in source
    assert "DatePickerInternal.CalendarPickerContent {" in source
    assert "required property var calendarControl" in helper_source
    assert "property alias gridWrapperBehavior: gridWrapperBehavior" in helper_source
    assert "property alias dayGrid: dayGrid" in helper_source
    assert "property alias nextGrid: nextGrid" in helper_source
    assert "readonly property real gridContainerHeight" in helper_source

    for marker in (
        "\n    Column {",
        "\n    Timer {",
        "CalendarNavButton {",
        "Grid {",
        "Repeater {",
    ):
        assert marker not in source


def test_date_time_picker_keeps_display_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Picker/DateTimePicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Picker/_internal/"
        "DateTimePickerDisplay.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 380
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "./_internal" as PickerInternal' in source
    assert "PickerInternal.DateTimePickerDisplay {" in source
    assert "required property var pickerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "parent ? parent.width /" in helper_source
    assert "parent ? parent.height : 0" in helper_source
    assert "Row {" not in source
    assert "Repeater {" not in source


def test_color_picker_keeps_content_and_popup_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/ColorPicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/_internal/"
        "ColorPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert 'import "_internal" as ColorPickerInternal' in source
    assert "ColorPickerInternal.ColorPickerContent {" in source
    assert "required property var colorControl" in helper_source
    for alias in (
        "property alias circleLoader: circleLoader",
        "property alias popup: popup",
        "property alias paletteDialogLoader: paletteDialogLoader",
        "property alias dialogLoader: dialogLoader",
    ):
        assert alias in helper_source
    assert helper_source.count("parent: colorControl") == 6

    for marker in (
        "Loader {",
        "PopupWindowCore {",
        "ColorPickerTrigger {",
        "ColorPalette {",
        "ColorPickerDropdown {",
        "ColorPickerDialog {",
        "CustomButtonCore {",
        "Connections {",
    ):
        assert marker not in source


def test_filter_bar_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/FilterBarCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/_internal/"
        "FilterBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as FilterBarInternal' in source
    assert "FilterBarInternal.FilterBarContent {" in source
    assert "required property var filterControl" in helper_source
    assert "property alias itemRepeater: itemRepeater" in helper_source
    assert "readonly property real contentWidth" in helper_source
    assert helper_source.count("parent: filterControl") == 2

    for marker in (
        "NeumorphicShadow {",
        "Repeater {",
        "MouseArea {",
        "Icon {",
        "Label {",
    ):
        assert marker not in source


def test_audio_waveform_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/data/AudioWaveform.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/AudioWaveformContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as DataInternal' in source
    assert "DataInternal.AudioWaveformContent {" in source
    assert "required property var waveformControl" in helper_source
    assert "property alias waveformContainer: waveformContainer" in helper_source
    assert "property alias mouseArea: mouseArea" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../../effects\"\n\n"
        "// AudioWaveformContent"
    )
    assert "ShadowedRectangle {" in helper_source
    assert helper_source.count("parent: waveformControl") == 2

    for marker in (
        "ShadowedRectangle {",
        "Repeater {",
        "MouseArea {",
        "\n    Item {",
    ):
        assert marker not in source


def test_shortcut_editor_keeps_scrollable_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ShortcutEditor.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/ShortcutEditorContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.ShortcutEditorContent {" in source
    assert "required property var editorControl" in helper_source
    assert "required property var cancelButton" in helper_source
    assert "property alias contentRow: contentRow" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../buttons\"\n"
        "import \"../../data/Label\"\n\n"
        "// ShortcutEditorContent"
    )

    for marker in (
        "\n    Flickable {",
        "\n        Repeater {",
        "\n        Label {",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_scroll_buttons_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerButtons.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerButtons {" in source
    assert "required property var wheelControl" in helper_source
    assert "\nRectangle {\n" in helper_source
    assert helper_source.count("parent: wheelControl") == 1

    for marker in (
        "\n    Rectangle {",
        "\n        Icon {",
        "\n        MouseArea {",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_delegates_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml"
    )
    path_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerPathDelegate.qml"
    )
    list_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerListDelegate.qml"
    )
    source = entry.read_text(encoding="utf-8")
    path_source = path_delegate.read_text(encoding="utf-8")
    list_source = list_delegate.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 270
    assert path_delegate.exists()
    assert list_delegate.exists()
    assert len(path_source.splitlines()) < 100
    assert len(list_source.splitlines()) < 110
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerPathDelegate {" in source
    assert "InputInternal.CycleWheelPickerListDelegate {" in source
    for helper_source in (path_source, list_source):
        assert "required property var wheelControl" in helper_source
        assert "required property var modelData" in helper_source
        assert "wheelControl._distanceFromCenter" in helper_source
    assert "required property int index" in list_source
    assert "ListView.view.currentIndex" in list_source
    assert "PathView.isCurrentItem" in path_source

    for marker in (
        "\n        delegate: Item {",
        "property real distanceFromCenter:",
        "text: String(modelData)",
    ):
        assert marker not in source


def test_pips_pager_keeps_navigation_button_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerNavButton.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerNavButton {" in source
    assert "required property var pagerControl" in helper_source
    assert "required property bool isNext" in helper_source
    assert "pagerControl.next()" in helper_source
    assert "pagerControl.previous()" in helper_source
    assert "navButtonComponent.createObject(control" in source
    assert "ButtonCore {" not in source


def test_pips_pager_keeps_pips_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 150
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerContent {" in source
    assert "required property var pagerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "Behavior on _animatedScrollOffset" in helper_source
    assert "Item {\n        id: pipsContainer" not in source
    assert "Repeater {" not in source
    assert "property real _scrollOffset" not in source


def test_carousel_keeps_dynamic_factories_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Carousel/Carousel.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Carousel/_internal/"
        "CarouselFactories.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as CarouselInternal' in source
    assert "CarouselInternal.CarouselFactories {" in source
    assert "required property var carouselControl" in helper_source
    for component_name in (
        "contentAreaComponent",
        "indicatorComponent",
        "navButtonComponent",
    ):
        assert f"property alias {component_name}:" in helper_source
        assert f"carouselFactories.{component_name}.createObject(control" in source
    for marker in (
        "CarouselContent {",
        "FlipViewControls.PipsPager {",
        "CarouselNavButton {",
    ):
        assert marker not in source


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
