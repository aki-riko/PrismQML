# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design chart, gallery evidence, resource, and dark-theme coverage."""

from PySide6.QtCore import QFile, QResource

from test_prism_design_skin_support import rgb


def _verify_chart_tooltip(context):
    tooltip = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart", "_internal",
        "ChartTooltip.qml",
    )
    assert rgb(tooltip.property("_tooltipBackground")) == (247, 252, 254)
    assert tooltip.property("_tooltipRadius") == 18
    assert rgb(tooltip.property("_tooltipBorderColor")) == (185, 204, 209)


def _verify_chart_multi_tooltip(context):
    tooltip = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart", "_internal",
        "ChartMultiTooltip.qml",
    )
    assert tooltip.property("_tooltipRadius") == 18
    assert rgb(tooltip.property("_tooltipBackground")) == (247, 252, 254)
    assert rgb(tooltip.property("_tooltipBorderColor")) == (185, 204, 209)


def _verify_chart_legend(context):
    legend = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart", "_internal",
        "ChartBottomLegend.qml",
    )
    assert legend.property("_itemRadius") == 10
    assert rgb(legend.property("_itemHoverColor")) == (234, 244, 247)
    assert rgb(legend.property("_itemBorderColor")) == (220, 233, 237)


def _verify_chart_data_zoom(context):
    data_zoom = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart",
        "ChartDataZoom.qml",
    )
    assert data_zoom.property("_panelRadius") == 14
    assert rgb(data_zoom.property("_panelColor")) == (248, 251, 252)
    assert rgb(data_zoom.property("_panelBorderColor")) == (220, 233, 237)
    assert data_zoom.property("_thumbnailFillAlpha") == 0.3
    assert data_zoom.property("_thumbnailStrokeAlpha") == 0.6


def _assert_gallery_evidence(page):
    assert page.property("galleryEvidenceViewKeys").split("|") == [
        "Token Board",
        "State Wall",
        "Component Matrix",
        "Three Skin Compare",
        "Real App Surface",
        "Dark Audit",
    ]


def _assert_state_wall_evidence(page):
    assert page.property("stateWallEvidenceKeys").split("|") == [
        "normal",
        "hover",
        "pressed",
        "focused",
        "disabled",
        "selected",
        "error",
        "success",
        "loading",
    ]


def _assert_dark_audit_evidence(page):
    assert page.property("darkAuditEvidenceKeys").split("|") == [
        "input",
        "table",
        "overlay",
        "semantic",
        "focus",
        "selection",
    ]


def _verify_gallery_page(context):
    page = context.load("examples", "pages", "PrismDesignPage.qml")
    _assert_gallery_evidence(page)
    _assert_state_wall_evidence(page)
    _assert_dark_audit_evidence(page)


def _verify_gallery_resources(context):
    resource_dir = context.repo_path("examples", "resources")
    qrc_text = (resource_dir / "gallery.qrc").read_text(encoding="utf-8")
    rcc_path = resource_dir / "gallery.rcc"
    registered_gallery_resources = QResource.registerResource(str(rcc_path))
    assert registered_gallery_resources
    try:
        for theme_name in ("light", "dark"):
            for skin_name in ("fluent", "neobrutalism", "prism-design"):
                asset_name = f"image/prism-design/skin-compare-{skin_name}-{theme_name}.png"
                assert (resource_dir / asset_name).is_file()
                assert f"<file>{asset_name}</file>" in qrc_text
                assert QFile.exists(f":/{asset_name}")
    finally:
        QResource.unregisterResource(str(rcc_path))


def _build_dark_tokens(context):
    return context.build(b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool prismDesign: Enums.isPrismDesign
    property color accent: Enums.accentColor
    property color background: Enums.backgroundColor
    property color surface: Enums.surfaceColor
    property color chartFirst: Enums.chartColors.palette[0]
}
""")


def _assert_dark_tokens(tokens):
    assert tokens.property("skinValue") == "prism_design"
    assert tokens.property("prismDesign") is True
    assert rgb(tokens.property("accent")) == (109, 235, 242)
    assert rgb(tokens.property("background")) == (9, 14, 16)
    assert rgb(tokens.property("surface")) == (16, 24, 27)
    assert rgb(tokens.property("chartFirst")) == (109, 235, 242)


def _verify_dark_check_indicator(context):
    indicator = context.build(b"""
import PrismQML
CheckIndicator {
    checkState: 0
}
""")
    assert rgb(indicator.property("_indicatorColor")) == (26, 37, 41)
    assert rgb(indicator.property("_indicatorBorderColor")) == (106, 169, 181)


def _verify_dark_slider(context):
    slider = context.build(b"""
import PrismQML
Slider {
    width: 220
    value: 55
}
""")
    assert rgb(slider.property("handleColor")) == (26, 37, 41)
    assert rgb(slider.property("_trackColor")) == (12, 21, 24)
    assert rgb(slider.property("_progressColor")) == (109, 235, 242)
    assert rgb(slider.property("_handleBorderColor")) == (106, 169, 181)


def _verify_dark_rating(context):
    rating = context.build(b"""
import PrismQML
Rating {
    value: 3
}
""")
    assert rgb(rating.property("_effectiveOutlineColor")) == (115, 138, 145)


def _verify_dark_chart_tooltip(context):
    tooltip = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart", "_internal",
        "ChartTooltip.qml",
    )
    assert rgb(tooltip.property("_tooltipBackground")) == (34, 48, 54)
    assert rgb(tooltip.property("_tooltipBorderColor")) == (50, 72, 79)


def _verify_dark_chart_data_zoom(context):
    data_zoom = context.load(
        "prismqml", "PrismQML", "controls", "data", "Chart",
        "ChartDataZoom.qml",
    )
    assert rgb(data_zoom.property("_panelColor")) == (16, 24, 27)
    assert rgb(data_zoom.property("_panelBorderColor")) == (38, 58, 65)
    assert data_zoom.property("_thumbnailFillAlpha") == 0.3
    assert data_zoom.property("_thumbnailStrokeAlpha") == 0.6


def verify_light_gallery(context):
    _verify_chart_tooltip(context)
    _verify_chart_multi_tooltip(context)
    _verify_chart_legend(context)
    _verify_chart_data_zoom(context)
    _verify_gallery_page(context)
    _verify_gallery_resources(context)


def verify_dark_gallery(context):
    _assert_dark_tokens(_build_dark_tokens(context))
    _verify_dark_check_indicator(context)
    _verify_dark_slider(context)
    _verify_dark_rating(context)
    _verify_dark_chart_tooltip(context)
    _verify_dark_chart_data_zoom(context)
    context.load("examples", "pages", "PrismDesignPage.qml")
