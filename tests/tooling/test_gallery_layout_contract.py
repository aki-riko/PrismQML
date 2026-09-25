# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "examples" / "pages"
MAIN = ROOT / "examples" / "main.qml"
FLOW = PAGES / "GalleryFlow.qml"
COMPONENT_CARD = ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "ComponentCard.qml"


def test_gallery_pages_do_not_expose_internal_api_paths() -> None:
    """Page headers must describe the capability, not its source import path."""
    forbidden = ("prismqml.controls.", "prismqml.effects")
    for page in PAGES.glob("*.qml"):
        source = page.read_text(encoding="utf-8")
        assert not any(value in source for value in forbidden), page.name


def test_gallery_navigation_follows_capability_order() -> None:
    source = MAIN.read_text(encoding="utf-8")
    expected = (
        "pages/ButtonPage.qml",
        "pages/InputPage.qml",
        "pages/LabelPage.qml",
        "pages/IconPage.qml",
        "pages/ContainerPage.qml",
        "pages/CardPage.qml",
        "pages/NavigationPage.qml",
        "pages/MenuPage.qml",
        "pages/CarouselPage.qml",
        "pages/ChartPage.qml",
        "pages/FeedbackPage.qml",
        "pages/EffectsPage.qml",
        "pages/AutoUpdatePage.qml",
        "pages/SettingsPage.qml",
    )
    positions = [source.index(f'pages/{name.split("/")[-1]}') for name in expected]
    assert positions == sorted(positions)


def test_gallery_flow_is_width_bound_and_height_driven_by_children() -> None:
    source = FLOW.read_text(encoding="utf-8")
    assert "parent && parent.width > 0" in source
    assert "parent.parent.width > 0" in source
    assert "height: childrenRect.height" in source
    assert "flow: Flow.LeftToRight" in source


def test_component_card_labels_wrap_with_a_shared_width_token() -> None:
    source = COMPONENT_CARD.read_text(encoding="utf-8")
    assert "Enums.controlSize.galleryCardLabelMaxWidth" in source
    assert "TextMetrics {" in source
    assert "maximumLineCount: 0" in source
    assert "wrapMode: Text.WordWrap" in source
    assert "elide: Text.ElideNone" in source
