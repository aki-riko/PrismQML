# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Remaining numeric and nullable-input regressions. 其余数值与可空输入回归。"""

import math
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SLIDER_CASES = (
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "GradientSlider.qml",
        "value",
        2,
        "_safeValue",
        1,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerBrightnessSlider.qml",
        "value",
        -2,
        "_safeValue",
        0,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerHueSlider.qml",
        "value",
        2,
        "_safeValue",
        1,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "ColorPicker" / "_internal" / "ColorPickerChannelSlider.qml",
        "value",
        999,
        "_safeValue",
        255,
    ),
    (
        ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "Slider" / "BeforeAfterSlider.qml",
        "position",
        2,
        "_safePosition",
        1,
    ),
)


SCENE = b"""
import QtQuick
import PrismQML

Item {
    Flickable {
        id: zeroView
        objectName: "zeroView"
        width: 0
        height: 0
        contentWidth: 0
        contentHeight: 0
    }

    ScrollBar {
        id: zeroScrollBar
        objectName: "zeroScrollBar"
        target: zeroView
        width: 0
        height: 0
    }

    ScrollBarEntry {
        id: zeroScrollBarEntry
        objectName: "zeroScrollBarEntry"
        flickable: zeroView
        width: 0
        height: 0
    }

    readonly property real zeroScrollBarRatio: zeroScrollBar.children.length > 0
        ? zeroScrollBar.children[0].ratio : 0
    readonly property real zeroScrollBarEntryRatio: zeroScrollBarEntry.children.length > 1
        ? zeroScrollBarEntry.children[1].ratio : 0
    readonly property real zeroScrollBarEntryPosition: zeroScrollBarEntry.children.length > 1
        ? zeroScrollBarEntry.children[1].position : 0

    PipsPager {
        objectName: "pips"
        pageCount: -3
        currentIndex: -2
        visiblePipCount: 0
    }

    Marquee {
        objectName: "marquee"
        width: 0
        text: "edge"
        forceScroll: true
        speed: 0
        scrollGap: -5
    }

    AudioWaveform {
        objectName: "waveform"
        width: 0
        height: 0
        waveformData: [null, 2, -1]
        progress: 2
    }

    Stepper {
        objectName: "stepper"
        steps: [null, {text: "Done"}]
        currentStep: 99
    }

    Stepper {
        objectName: "nullStepper"
        steps: null
    }

    CycleWheelPicker {
        objectName: "nullCyclePicker"
        items: null
        itemHeight: 0
        visibleItems: 0
        width: 0
        height: 0
    }

    ChartDataZoom {
        objectName: "dataZoom"
        width: 0
        height: 0
        chartData: [null, {value: "bad"}, {value: 3}]
        series: [null]
        viewportStart: -2
        viewportEnd: 2
    }

    SliderCore {
        objectName: "slider"
        readonly property real testedPosition: _safePosition(value)
        width: 0
        height: 0
        value: 50
    }
}
"""


NULLABLE_COLLECTION_SCENE = b"""
import QtQuick
import PrismQML

Item {
    CommandBar {
        objectName: "nullCommandBar"
        primaryCommands: null
        secondaryCommands: null
    }
    DropZone {
        objectName: "nullDropZone"
        allowedExtensions: null
    }
    LoginWindow {
        objectName: "nullLoginWindow"
        oauthProviders: null
    }
    Pivot { objectName: "nullPivot"; items: null }
    SegmentedControl { objectName: "nullSegmented"; items: null }
    SettingsCard {
        objectName: "nullSettingsCard"
        model: null
        options: null
        folders: null
    }
    ToggleNavigationBar {
        objectName: "nullToggleNavigation"
        model: null
        bottomItems: null
    }
    ListWidget { objectName: "nullListWidget"; model: null }
    TreeWidget {
        objectName: "nullTreeWidget"
        model: null
        headerLabels: null
    }
    TableWidget { objectName: "nullTableWidget"; tableData: []; columns: null }
    StackedWidget { objectName: "nullStackedWidget"; pageSources: null }
    ComboBox { objectName: "nullComboBox"; model: null }
    ComboBoxTree { objectName: "nullComboBoxTree"; model: null }
    ComboBoxMulti {
        objectName: "nullComboBoxMulti"
        model: null
        selectedIndices: null
    }
    ComboBoxMultiTree {
        objectName: "nullComboBoxMultiTree"
        model: null
        selectedPaths: null
    }
    LocalSearchBar { objectName: "nullLocalSearchBar"; entries: null }
    SystemTrayMenu { objectName: "nullSystemTrayMenu"; initialActions: null }
}
"""


NULLABLE_ELEMENT_SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    property bool nullPathSelected: true
    property bool invalidTreePathFound: true
    property string nullTableCellText: "pending"
    property int nullListRow: -1
    property int tabIndexAfterRemove: -1

    CommandBar {
        objectName: "elementCommandBar"
        primaryCommands: [null]
        secondaryCommands: [null]
    }
    LoginWindow {
        objectName: "elementLoginWindow"
        oauthProviders: [null]
    }
    SettingsCard {
        objectName: "elementSettingsCard"
        model: [null]
        options: [null]
        folders: [null]
    }
    ListWidget { id: elementListWidget; objectName: "elementListWidget"; model: [null] }
    TreeWidget {
        id: elementTreeWidget
        objectName: "elementTreeWidget"
        model: [{children: null}, null]
    }
    TableWidget {
        id: elementTableWidget
        objectName: "elementTableWidget"
        tableData: [null, {value: "row"}]
        columns: [null, {role: "value"}]
    }
    TableView { objectName: "elementTableView"; model: []; columns: [null] }
    Pivot { objectName: "elementPivot"; items: [null] }
    SegmentedControl { objectName: "elementSegmented"; items: [null] }
    ToggleNavigationBar {
        objectName: "elementToggleNavigation"
        model: [null]
        bottomItems: [null]
    }
    NavigationBar {
        objectName: "elementNavigationBar"
        model: [null]
        bottomItems: [null]
    }
    NavigationView {
        objectName: "elementNavigationView"
        model: [null]
        bottomItems: [null]
    }
    StatusBar {
        objectName: "elementStatusBar"
        leftItems: [null]
        rightItems: [null]
    }
    MenuBar { objectName: "elementMenuBar"; items: [null] }
    FilterBar {
        objectName: "elementFilterBar"
        items: [null]
        selectedIndices: [null]
    }
    Carousel { objectName: "elementCarousel"; model: [null] }
    Timeline { objectName: "elementTimeline"; items: [{cards: [null]}] }
    Timeline { objectName: "elementTimelineVirtual"; items: [{cards: [null]}]; virtualized: true; height: 120 }
    Timeline {
        objectName: "elementTimelineGraph"
        type: Enums.timeline.type_graph
        virtualized: true
        height: 180
        items: [{
            graph: {nodeLane: 0, segments: [null], labels: [null]},
            cards: [{labels: [null], graph: {segments: [null]}}]
        }]
    }
    LineEdit {
        objectName: "elementTagLineEdit"
        inputType: Enums.input.type_tag
        tags: [null]
        suggestions: [null]
        extraSeparators: [null]
    }
    ChartView {
        objectName: "elementChartView"
        chartData: [null]
        indicators: [null]
        series: [null]
        boxplotData: [null]
    }
    Button {
        objectName: "elementDropdownButton"
        feature: Enums.button.feature_dropdown
        menuItems: [null]
    }
    StackedWidget { objectName: "elementStackedWidget"; pageSources: [null] }
    TabWidget {
        id: elementTabWidget
        objectName: "elementTabWidget"
        tabs: [null, {title: "Second"}]
        currentIndex: 1
    }
    ComboBox { objectName: "elementComboBox"; model: [null] }
    ComboBoxTree { objectName: "elementComboBoxTree"; model: [null] }
    ComboBoxMulti {
        objectName: "elementComboBoxMulti"
        model: [null]
        selectedIndices: [null]
    }
    ComboBoxMultiTree {
        id: elementComboBoxMultiTree
        objectName: "elementComboBoxMultiTree"
        model: [null]
        selectedPaths: [null]
    }
    LocalSearchBar { objectName: "elementLocalSearchBar"; entries: [null] }
    SystemTrayMenu { objectName: "elementSystemTrayMenu"; initialActions: [null] }
    Confetti {
        id: elementConfetti
        objectName: "elementConfetti"
        colors: [null]
        particleCount: 1
    }
    ColorPicker {
        objectName: "elementColorPicker"
        type: Enums.colorPicker.type_circle
        circleColors: [null]
    }

    Component.onCompleted: {
        nullPathSelected = elementComboBoxMultiTree._isSelected(["leaf"])
        invalidTreePathFound = elementTreeWidget._findOriginalItem("0,0,0") !== null
        nullTableCellText = elementTableWidget.item(0, 0).text
        elementTableWidget.sortItems(0, 0)
        elementListWidget.addItem(null)
        nullListRow = elementListWidget.row(null)
        elementTabWidget.removeTab(1)
        tabIndexAfterRemove = elementTabWidget.currentIndex
        elementConfetti.start()
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visual_tree(root: QQuickItem) -> list[QQuickItem]:
    result = [root]
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def test_nullable_lists_and_zero_geometry_stay_finite(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inline:remaining-numeric-robustness.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump()
        pips = root.findChild(type(root), "pips")
        marquee = root.findChild(type(root), "marquee")
        waveform = root.findChild(type(root), "waveform")
        stepper = root.findChild(type(root), "stepper")
        null_stepper = root.findChild(type(root), "nullStepper")
        null_cycle_picker = root.findChild(type(root), "nullCyclePicker")
        data_zoom = root.findChild(type(root), "dataZoom")
        slider = root.findChild(type(root), "slider")
        assert pips is not None and marquee is not None
        assert waveform is not None and stepper is not None and null_stepper is not None
        assert null_cycle_picker is not None
        assert data_zoom is not None
        assert slider is not None
        assert math.isfinite(float(root.property("zeroScrollBarRatio")))
        assert math.isfinite(float(root.property("zeroScrollBarEntryRatio")))
        assert math.isfinite(float(root.property("zeroScrollBarEntryPosition")))

        assert pips.property("_safePageCount") == 0
        assert pips.property("_safeVisiblePipCount") == 1
        assert pips.property("_safeCurrentIndex") == 0

        assert marquee.property("_safeSpeed") == 1
        assert marquee.property("_safeScrollGap") == 0
        assert math.isfinite(float(marquee.property("_scrollDuration")))

        assert waveform.property("_safeWaveformData").toVariant() == [0, 1, 0]
        assert waveform.property("_safeProgress") == 1

        assert stepper.property("_safeSteps").toVariant() == [None, {"text": "Done"}]
        assert stepper.property("_safeCurrentStep") == 1
        assert math.isfinite(float(stepper.property("_lineWidth")))
        assert null_stepper.property("_safeSteps").toVariant() == []
        assert null_stepper.property("_safeCurrentStep") == 0
        assert null_stepper.property("_stepWidth") == 0
        assert null_cycle_picker.property("_safeItems").toVariant() == []
        assert null_cycle_picker.property("_safeItemHeight") == 1
        assert null_cycle_picker.property("_safeVisibleItems") == 1

        assert data_zoom.property("_safeViewportStart") == 0
        assert data_zoom.property("_safeViewportEnd") == 1
        assert slider.property("testedPosition") == 0.5
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_zero_width_slider_variants_keep_finite_geometry(qapp):
    for source_path, value_name, value, safe_name, expected in SLIDER_CASES:
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        register_types(engine)
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(source_path)))
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        slider = component.create(engine.rootContext())
        assert isinstance(slider, QQuickItem), [
            error.toString() for error in component.errors()
        ]
        try:
            slider.setWidth(0)
            slider.setProperty(value_name, value)
            _pump()
            assert slider.property(safe_name) == expected
            assert all(
                math.isfinite(number)
                for item in _visual_tree(slider)
                for number in (item.x(), item.y(), item.width(), item.height())
            )
            assert warnings == []
        finally:
            slider.deleteLater()
            component.deleteLater()
            engine.collectGarbage()
            engine.clearComponentCache()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            QCoreApplication.processEvents()


def test_nullable_public_collections_have_no_qml_runtime_errors(qapp):
    """公共集合输入为 null 时保持空视图且不产生 QML TypeError。"""
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        NULLABLE_COLLECTION_SCENE,
        QUrl("inline:nullable-public-collections.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump(100)
        assert warnings == []
        for name in (
            "nullCommandBar",
            "nullDropZone",
            "nullLoginWindow",
            "nullPivot",
            "nullSegmented",
            "nullSettingsCard",
            "nullToggleNavigation",
            "nullListWidget",
            "nullTreeWidget",
            "nullTableWidget",
            "nullStackedWidget",
            "nullComboBox",
            "nullComboBoxTree",
            "nullComboBoxMulti",
            "nullComboBoxMultiTree",
            "nullLocalSearchBar",
            "nullSystemTrayMenu",
        ):
            assert root.findChild(type(root), name) is not None
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_nullable_collection_elements_have_no_qml_runtime_errors(qapp):
    """公共集合包含 null 元素时也不得触发 delegate/宽度计算 TypeError。"""
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        NULLABLE_ELEMENT_SCENE,
        QUrl("inline:nullable-public-collection-elements.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump(100)
        assert not warnings, "\\n".join(warnings)
        assert root.property("nullPathSelected") is False
        assert root.property("invalidTreePathFound") is False
        assert root.property("nullTableCellText") == ""
        assert root.property("nullListRow") == 0
        assert root.property("tabIndexAfterRemove") == 0
        for name in (
            "elementCommandBar",
            "elementLoginWindow",
            "elementSettingsCard",
            "elementListWidget",
            "elementTreeWidget",
            "elementTableWidget",
            "elementTableView",
            "elementPivot",
            "elementSegmented",
            "elementToggleNavigation",
            "elementNavigationBar",
            "elementNavigationView",
            "elementStatusBar",
            "elementMenuBar",
            "elementFilterBar",
            "elementCarousel",
            "elementTimeline",
            "elementTimelineVirtual",
            "elementTimelineGraph",
            "elementTagLineEdit",
            "elementChartView",
            "elementDropdownButton",
            "elementStackedWidget",
            "elementTabWidget",
            "elementComboBox",
            "elementComboBoxTree",
            "elementComboBoxMulti",
            "elementComboBoxMultiTree",
            "elementLocalSearchBar",
            "elementSystemTrayMenu",
            "elementConfetti",
            "elementColorPicker",
        ):
            assert root.findChild(type(root), name) is not None
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_painted_row_null_columns_have_no_qml_runtime_errors(qapp):
    """PaintedRow 的列定义包含 null 时，绘制和命中测试保持安全。"""
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    source_path = ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Table" / "PaintedRow.qml"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(source_path)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    row = component.create(engine.rootContext())
    assert isinstance(row, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    try:
        row.setWidth(120)
        row.setHeight(32)
        row.setProperty("columns", [None])
        row.setProperty("rowData", {})
        _pump(100)
        assert warnings == [], warnings
    finally:
        row.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
