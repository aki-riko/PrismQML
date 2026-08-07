# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Adaptive chart-axis and bottom-layer layout regressions. 图表自适应坐标轴与底层布局回归。"""

from PySide6.QtCore import QPointF
from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from test_chart_data_zoom_performance import _data_zoom_hosts
from test_chart_legend_performance import _legends
from test_chart_runtime_performance import (
    _evaluate,
    _loaders,
    _pump,
    windowed_chart_scene,
)


GOLD_LABELS = [
    {"label": f"2026-07-{day:02d}"}
    for day in range(1, 32)
]
GOLD_SERIES = [
    {"name": "WBL", "values": [990.0] * 31},
    {"name": "UU898", "values": [188.0 + (index % 4) for index in range(31)]},
    {
        "name": "DD373",
        "values": [
            205.0,
            214.0,
            211.0,
            202.0,
            195.0,
            192.0,
            190.0,
            198.0,
            1005.52,
            200.0,
            199.0,
            198.0,
            197.0,
            196.0,
            195.0,
            194.0,
            193.0,
            192.0,
            191.0,
            190.0,
            189.0,
            188.0,
            187.0,
            186.0,
            185.0,
            184.0,
            183.0,
            182.0,
            181.0,
            180.0,
            179.0,
        ],
    },
]


def _class_name(item) -> str:
    return item.metaObject().className().split("_QMLTYPE_")[0]


def _has_ancestor_type(item: QQuickItem, type_name: str) -> bool:
    parent = item.parentItem()
    while parent is not None:
        if _class_name(parent) == type_name:
            return True
        parent = parent.parentItem()
    return False


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _caption_labels(root: QQuickItem) -> list[QQuickItem]:
    context = QQmlEngine.contextForObject(root)
    caption_type = _evaluate(
        QQmlExpression(context, root, "Enums.label.type_caption")
    )
    return [
        item
        for item in [root, *_visual_descendants(root)]
        if item.metaObject().indexOfProperty("type") >= 0
        and item.property("type") == caption_type
        and not _has_ancestor_type(item, "ChartTitle")
    ]


def _has_mouse_area(item: QQuickItem) -> bool:
    return any("MouseArea" in _class_name(child) for child in item.childItems())


def _category_labels(root: QQuickItem) -> list[QQuickItem]:
    return [label for label in _caption_labels(root) if _has_mouse_area(label)]


def _assert_visible_text_fits(labels: list[QQuickItem]) -> None:
    visible = [label for label in labels if label.isVisible()]
    assert visible
    for label in visible:
        assert label.property("implicitWidth") <= label.width() + 0.5, (
            label.property("text"),
            label.property("implicitWidth"),
            label.width(),
        )
        assert label.property("truncated") is False


def _set_gold_chart(chart: QQuickItem) -> None:
    window = chart.window()
    assert window is not None
    window.resize(1_400, 560)
    chart.setWidth(1_400)
    chart.setHeight(520)
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("lineType"))
    chart.setProperty("chartData", GOLD_LABELS)
    chart.setProperty("series", GOLD_SERIES)
    chart.setProperty("showLegend", True)
    chart.setProperty("showLabels", True)
    chart.setProperty("showValues", False)
    chart.setProperty("dataZoomEnabled", True)
    formatter = QQmlExpression(
        QQmlEngine.contextForObject(chart),
        chart,
        "(function(value) { return Number(value).toFixed(2) })",
    )
    chart.setProperty("valueFormatter", _evaluate(formatter))
    _pump(80)


def test_gold_chart_axis_labels_fit_without_repeated_elision(
    windowed_chart_scene,
):
    chart, warnings = windowed_chart_scene
    _set_gold_chart(chart)
    chart_base = chart.property("_xyChartBase")
    assert isinstance(chart_base, QQuickItem)

    category_labels = _category_labels(chart_base)
    visible_categories = [label for label in category_labels if label.isVisible()]
    assert 2 <= len(visible_categories) < len(GOLD_LABELS)
    _assert_visible_text_fits(category_labels)

    value_labels = [
        label
        for label in _caption_labels(chart_base)
        if not _has_mouse_area(label)
    ]
    _assert_visible_text_fits(value_labels)
    assert all(label.parentItem().property("clip") is False for label in value_labels)
    assert warnings == []


def test_xy_legend_stays_above_data_zoom(windowed_chart_scene):
    chart, warnings = windowed_chart_scene
    _set_gold_chart(chart)

    legend = _legends(chart)[0]
    data_zoom = _data_zoom_hosts(chart)[0]
    assert isinstance(legend, QQuickItem)
    assert isinstance(data_zoom, QQuickItem)
    legend_bottom = legend.mapToScene(QPointF(0, legend.height())).y()
    data_zoom_top = data_zoom.mapToScene(QPointF(0, 0)).y()
    assert legend_bottom <= data_zoom_top
    assert warnings == []


def test_horizontal_and_scatter_axes_keep_labels_inside_plot(
    windowed_chart_scene,
):
    chart, warnings = windowed_chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("showLegend", False)
    chart.setProperty("showLabels", True)
    chart.setProperty("chartType", chart.property("barType"))
    horizontal_orientation = _evaluate(
        QQmlExpression(
            QQmlEngine.contextForObject(chart),
            chart,
            "Enums.chart.orientation_horizontal",
        )
    )
    chart.setProperty("barOrientation", horizontal_orientation)
    chart.setProperty(
        "chartData",
        [
            {"label": "唯我独尊服务器", "value": 100_000},
            {"label": "梦江南服务器", "value": 75_000},
            {"label": "长安城服务器", "value": 50_000},
        ],
    )
    _pump(50)

    chart_base = chart.property("_xyChartBase")
    assert isinstance(chart_base, QQuickItem)
    _assert_visible_text_fits(_category_labels(chart_base))

    chart_area = chart_base.property("chartArea")
    assert isinstance(chart_area, QQuickItem)
    area_left = chart_area.mapToScene(QPointF(0, 0)).x()
    area_right = chart_area.mapToScene(QPointF(chart_area.width(), 0)).x()
    numeric_labels = [
        label
        for label in _caption_labels(chart_base)
        if not _has_mouse_area(label) and label.isVisible()
    ]
    assert numeric_labels
    for label in numeric_labels:
        left = label.mapToScene(QPointF(0, 0)).x()
        right = label.mapToScene(QPointF(label.width(), 0)).x()
        assert left >= area_left - 0.5
        assert right <= area_right + 0.5

    chart.setProperty("chartType", chart.property("scatterType"))
    chart.setProperty("series", [{"name": "跨度", "data": [[1_000, 1], [9_000, 9]]}])
    _pump(50)
    chart_base = chart.property("_xyChartBase")
    chart_area = chart_base.property("chartArea")
    area_left = chart_area.mapToScene(QPointF(0, 0)).x()
    area_right = chart_area.mapToScene(QPointF(chart_area.width(), 0)).x()
    scatter_labels = [
        label
        for label in _caption_labels(chart_base)
        if not _has_mouse_area(label) and label.isVisible()
    ]
    assert len(scatter_labels) == 11
    for label in scatter_labels:
        scene_y = label.mapToScene(QPointF(0, 0)).y()
        if scene_y <= chart_area.mapToScene(QPointF(0, chart_area.height())).y():
            continue
        left = label.mapToScene(QPointF(0, 0)).x()
        right = label.mapToScene(QPointF(label.width(), 0)).x()
        assert left >= area_left - 0.5
        assert right <= area_right + 0.5
    assert warnings == []


def test_boxplot_axes_adapt_to_large_values_and_long_categories(
    windowed_chart_scene,
):
    chart, warnings = windowed_chart_scene
    chart.setProperty("animated", False)
    chart.setProperty("chartType", chart.property("boxplotType"))
    chart.setProperty(
        "boxplotData",
        [
            {
                "label": f"2026年季度样本{index + 1}",
                "min": 91_000 + index,
                "q1": 94_000 + index,
                "median": 97_000 + index,
                "q3": 101_000 + index,
                "max": 113_780 + index,
                "outliers": [],
            }
            for index in range(8)
        ],
    )
    _pump(50)

    boxplot_area = _loaders(chart)["boxplotAreaLoader"].property("item")
    assert isinstance(boxplot_area, QQuickItem)
    labels = _caption_labels(boxplot_area)
    visible_labels = [label for label in labels if label.isVisible()]
    assert 8 <= len(visible_labels) < 14
    _assert_visible_text_fits(labels)
    assert warnings == []
