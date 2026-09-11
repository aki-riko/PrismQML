# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 7/7 of the former test_qml_architecture.py."""
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

def test_viewport_detection_has_exactly_one_owner():
    """视口检测算法只允许 ViewportMixin 一处实现, 消费者只能委托。

    Skeleton, ProgressBarImpl and ProgressRingImpl each carried a line-for-line
    copy of the ancestor walk and the in-viewport arithmetic. They now delegate to
    ViewportMixin. This gate blocks a fourth copy from reappearing anywhere in the
    QML tree.
    """
    owner = "prismqml/PrismQML/controls/utils/ViewportMixin.qml"
    consumers = (
        "prismqml/PrismQML/controls/feedback/State/Skeleton.qml",
        "prismqml/PrismQML/controls/feedback/Progress/_internal/"
        "ProgressBarImpl.qml",
        "prismqml/PrismQML/controls/feedback/Progress/_internal/"
        "ProgressRingImpl.qml",
    )

    reimplementers = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        if "function _updateViewport()" in source and relative != owner:
            reimplementers.append(relative)

    assert reimplementers == []

    owner_source = _source(owner).read_text(encoding="utf-8")
    assert "function _updateViewport()" in owner_source
    assert "function _findFlickable()" in owner_source

    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert "ViewportMixin {" in source, relative
        assert "readonly property bool _isInViewport: viewport.isInViewport" in (
            source
        ), relative
        assert "function _findFlickable()" not in source, relative

def test_tree_traversal_has_exactly_one_owner():
    """树遍历算法只允许 ComboBoxTreeNodes.js 一处实现。

    ComboBoxTree and ComboBoxMultiTree each carried an identical node-id scheme,
    search-match rule and walk order, differing only in how a visible row is
    emitted. The walk now lives in one pure library that takes an emit callback.
    """
    owner_path = (
        QML_ROOT / "controls" / "inputs" / "ComboBox" / "_internal"
        / "ComboBoxTreeNodes.js"
    )
    assert owner_path.exists()
    owner_source = owner_path.read_text(encoding="utf-8")

    # Pure shared library, so it must not reach for QML objects.
    # 纯共享库，因此不得触碰 QML 对象。
    assert ".pragma library" in owner_source
    assert "function flatten(" in owner_source
    assert "function hasMatchingDescendants(" in owner_source
    assert "function collectExpandable(" in owner_source
    assert "function toggleExpanded(" in owner_source
    assert "control." not in owner_source
    assert "Qt." not in owner_source

    consumers = (
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxTree.qml",
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxMultiTree.qml",
    )
    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert 'import "_internal/ComboBoxTreeNodes.js" as TreeNodes' in source, (
            relative
        )
        assert "TreeNodes.flatten(" in source, relative
        assert "function _flattenTree(" not in source, relative
        assert "function _hasMatchingDescendants(" not in source, relative

    # No third copy anywhere in the tree. 整棵树不得出现第三份副本。
    reimplementers = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        if "function _hasMatchingDescendants(" in source:
            reimplementers.append(path.relative_to(ROOT).as_posix())

    assert reimplementers == []

def test_window_page_stack_has_exactly_one_owner():
    """页面栈与懒加载 overlay 只允许 WindowsPageStack.qml 一处实现。

    WindowsFilled, WindowsSplit and WindowsBarContent each carried the same
    StackedWidget bindings and overlay Loader lifecycle, differing only in the
    navigation id they read, whether the host may be null, and where the loading
    caption comes from. Those three are now parameters on one helper.
    """
    owner = QML_ROOT / "_internal" / "WindowsPageStack.qml"
    assert owner.exists()
    owner_source = owner.read_text(encoding="utf-8")

    for prop in (
        "required property var host",
        "required property bool navAnimationEnabled",
        "required property bool overlayActive",
        "required property string overlayText",
    ):
        assert prop in owner_source, prop

    # The activation budget is measured from collapse start and LazyLoadingHelper
    # subtracts the elapsed collapse from it, so a hardcoded budget lets any
    # collapse-duration change silently squeeze the loading indicator to the
    # timer floor. It must stay derived from coverDuration.
    # 激活预算从收紧开始计算, LazyLoadingHelper 会减去已花掉的收紧时长, 所以写死
    # 预算会让任何收紧时长改动把加载指示器静默压到定时器下限。必须由
    # coverDuration 推导。
    assert (
        "Enums.lazyLoadingTransitionMetrics.coverDuration\n"
        "              + Enums.lazyLoadingTransitionMetrics."
        "loaderActivationHeadroom" in owner_source
    )
    assert "lazyActivationDelay: root.navAnimationEnabled\n" in owner_source
    assert "? Enums.duration.dialog" not in owner_source
    assert "readonly property alias stackAlias: stack" in owner_source
    assert 'objectName: "loadingOverlayLoader"' in owner_source
    # The loading state machine stays in NavigationWindowLoading.js.
    # loading 状态机仍归 NavigationWindowLoading.js。
    assert "function start(" not in owner_source
    assert "function finish(" not in owner_source

    consumers = (
        "prismqml/PrismQML/_internal/WindowsFilled.qml",
        "prismqml/PrismQML/_internal/WindowsSplit.qml",
        "prismqml/PrismQML/_internal/WindowsBarContent.qml",
    )
    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert "WindowsPageStack {" in source, relative
        assert "property alias stackAlias: pageStack.stackAlias" in source, relative
        # No third copy of the extracted view layer. 不得留下第三份视图层副本。
        assert 'objectName: "loadingOverlayLoader"' not in source, relative
        assert "StackedWidget {" not in source, relative

    # Nothing else in the tree may declare the overlay loader either.
    # 整棵树内不得有其他文件声明该 overlay loader。
    declarers = sorted(
        path.relative_to(ROOT).as_posix()
        for path in QML_ROOT.rglob("*.qml")
        if 'objectName: "loadingOverlayLoader"' in path.read_text(encoding="utf-8")
    )
    assert declarers == ["prismqml/PrismQML/_internal/WindowsPageStack.qml"]

def test_chart_math_owns_series_statistics():
    """average/findMinMaxIndices 只允许在 ChartMath.js 内实现一次。"""
    source = _CHART_MATH.read_text(encoding="utf-8")
    assert "function average(" in source
    assert "function findMinMaxIndices(" in source
    # Contract: pure maths only, no Canvas/QML/theme coupling. 契约: 只放纯算式。
    # Checked as code, not as prose — the comments above legitimately name these.
    # 按代码而非文字检查, 因为文件注释本身会提到这些词。
    for banned in ("ctx.", "import QtQuick", "Enums.colorPicker", "Enums.chart"):
        assert banned not in source, banned

def test_chart_series_statistics_have_no_second_implementation():
    """除 ChartMath.js 外, 任何 Chart 文件都不得自带这两个算法的循环实现。"""
    for path in sorted(_CHART_INTERNAL.rglob("*")):
        if not path.is_file() or path.suffix not in {".js", ".qml"}:
            continue
        if path == _CHART_MATH:
            continue
        source = path.read_text(encoding="utf-8")
        # The min/max scan and the series-sum loop are the two duplicated shapes.
        # Matched narrowly: XYMultiTooltip.qml legitimately sums one hovered point
        # across series, which is a different computation.
        # 精确匹配: XYMultiTooltip.qml 是对多系列同一悬停点求和, 属不同计算。
        assert "if (values[i] < values[minIdx])" not in source, path.name
        assert "if (values[index] < values[minIdx])" not in source, path.name
        assert "i < values.length; i++) sum += values[i]" not in source, path.name
        assert (
            "index < values.length; index++) sum += values[index]" not in source
        ), path.name

def test_color_picker_hsv_owns_conversion():
    """decompose/compose 只允许在 ColorPickerHsv.js 内实现一次, 且保持纯函数。"""
    source = _PICKER_HSV.read_text(encoding="utf-8")
    assert "function decompose(" in source
    assert "function compose(" in source
    # The hue floor must stay a caller-supplied parameter, never an Enums read
    # or a magic number here. 色相下限必须由调用方传入, 本文件不得读 Enums 或写魔数。
    assert "achromaticHue" in source
    assert "Enums." not in source
    for banned in ("import QtQuick", "signal ", "Component.onCompleted"):
        assert banned not in source, banned

def test_color_picker_consumers_delegate_hsv_conversion():
    """两处消费者都必须转发给 helper, 不得自带 HSV 读写。"""
    for path in (_PICKER_DIALOG, _PICKER_DROPDOWN):
        source = path.read_text(encoding="utf-8")
        assert 'import "ColorPickerHsv.js" as Hsv' in source, path.name
        assert "Hsv.decompose(" in source, path.name
        assert "Hsv.compose(" in source, path.name
        # No second copy of the state conversion. Presentation-only Qt.hsva calls
        # (spectrum GradientStop) are untouched on purpose.
        # 不得有第二份状态换算。呈现用的 Qt.hsva（色谱渐变）有意不动。
        assert "selectedColor = Qt.hsva(" not in source, path.name
        assert "selectedColor.hsvHue" not in source, path.name
        assert "selectedColor.hsvSaturation" not in source, path.name
        # The floor stays an Enums token at the call site, not a literal.
        assert "Enums.opacityLevel.invisible" in source, path.name

def test_color_picker_notification_and_alpha_asymmetry_preserved():
    """两处的通知契约与 alpha 回读差异是有意的, 门禁锁住不许被 helper 吞掉。"""
    dialog = _PICKER_DIALOG.read_text(encoding="utf-8")
    dropdown = _PICKER_DROPDOWN.read_text(encoding="utf-8")
    # Distinct signals. 各自的信号名。
    assert "colorUpdated(selectedColor)" in dialog
    assert "colorChanged(selectedColor)" in dropdown
    # Dialog reads alpha back into its own integer range; dropdown must not.
    # 对话框把 alpha 回读到自己的整数区间; 下拉不回读。
    assert "hsv.alpha" in dialog
    assert "hsv.alpha" not in dropdown
