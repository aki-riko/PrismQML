# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery runtime registration contracts. Gallery 运行时注册合同。"""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GALLERY_MAIN = ROOT / "examples" / "main.py"
GALLERY_QML = ROOT / "examples" / "main.qml"
GALLERY_STARTUP_BENCHMARK = ROOT / "tests" / "qml" / "bench_gallery_startup.py"
GALLERY_AUTO_UPDATE_PAGE = ROOT / "examples" / "pages" / "AutoUpdatePage.qml"
GALLERY_SETTINGS_PAGE = ROOT / "examples" / "pages" / "SettingsPage.qml"
GALLERY_DRY_RUN_UPDATER = (
    ROOT / "examples" / "pages" / "_internal" / "GalleryDryRunUpdater.qml"
)
GALLERY_LABEL_PAGE = ROOT / "examples" / "pages" / "LabelPage.qml"
GALLERY_MENU_PAGE = ROOT / "examples" / "pages" / "MenuPage.qml"
GALLERY_GIT_GRAPH = ROOT / "examples" / "pages" / "TimelineGitGraphDemo.qml"
PUBLIC_CONTEXT_NAMES = {
    "ThemeManager",
    "ConfigManager",
    "MicaManager",
    "AcrylicHelper",
    "NativeWindow",
    "ClipboardHelper",
    "ShadowManager",
    "WindowHelper",
    "QRCodeGenerator",
    "ScreenEyedropperManager",
}


def _gallery_tree() -> ast.Module:
    return ast.parse(GALLERY_MAIN.read_text(encoding="utf-8"), GALLERY_MAIN.name)


def _qml_property_array(source: str, property_name: str) -> str:
    match = re.search(
        rf"property var {property_name}:\s*\[(.*?)\n\s*\]",
        source,
        re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def test_gallery_uses_complete_public_runtime_registration():
    tree = _gallery_tree()
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "register_types"
    ]

    # App owns the complete public registration now; Gallery must not duplicate
    # the engine wiring in its business entry point.
    # 现在由 App 统一负责完整公开注册；Gallery 业务入口不得重复装配引擎。
    assert calls == []
    source = GALLERY_MAIN.read_text(encoding="utf-8")
    assert "app = App(" in source
    runtime_source = (
        ROOT / "prismqml" / "python" / "runtime" / "engine.py"
    ).read_text(encoding="utf-8")
    assert "register_types(" in runtime_source


def test_gallery_disables_debug_logging_by_default():
    source = GALLERY_MAIN.read_text(encoding="utf-8")

    level_setup = "getLogger().set_level(Logger.INFO)"
    assert level_setup in source
    assert source.index(level_setup) < source.index("app = App(")


def test_gallery_uses_direct3d11_as_its_only_graphics_backend():
    source = GALLERY_MAIN.read_text(encoding="utf-8")

    runtime_source = (
        ROOT / "prismqml" / "python" / "runtime" / "application.py"
    ).read_text(encoding="utf-8")
    assert "QSGRendererInterface.GraphicsApi.Direct3D11" in runtime_source
    assert "QSGRendererInterface.OpenGL" not in source
    assert "GraphicsApi.OpenGL" not in source


def test_gallery_startup_benchmark_requires_real_direct3d11_and_real_home_page():
    source = GALLERY_STARTUP_BENCHMARK.read_text(encoding="utf-8")

    assert 'requested_graphics_api": "direct3d11"' in source
    assert 'actual_api_name != "Direct3D11"' in source
    assert '"--graphics-api"' not in source
    assert "stack.pageLoaded.connect(self._page_loaded)" in source
    assert 'class_name != "ButtonPage"' in source
    assert "pending.extend(item.childItems())" in source
    assert 'output["visual_item_class_counts"]' in source
    assert 'output["object_class_counts"]' not in source


def test_gallery_does_not_duplicate_public_context_or_lazy_providers():
    tree = _gallery_tree()
    context_names = set()
    provider_names = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "setContextProperty" and node.args:
            name = node.args[0]
            if isinstance(name, ast.Constant) and isinstance(name.value, str):
                context_names.add(name.value)
        if node.func.attr == "addImageProvider" and node.args:
            name = node.args[0]
            if isinstance(name, ast.Constant) and isinstance(name.value, str):
                provider_names.add(name.value)

    assert context_names.isdisjoint(PUBLIC_CONTEXT_NAMES)
    assert provider_names.isdisjoint({"acrylic", "qrcode"})


def test_gallery_does_not_override_persisted_language():
    source = GALLERY_QML.read_text(encoding="utf-8")

    assert "Fluent.Translator.setLanguage(" not in source
    assert "ConfigManager.setLanguage(" not in source


def test_gallery_navigation_order_matches_page_sources():
    source = GALLERY_QML.read_text(encoding="utf-8")
    expected_navigation = [
        ("gallery_ad1c50c9367c756d", "ButtonPage.qml"),
        ("gallery_2087c777c06fefe5", "InputPage.qml"),
        ("gallery_1d0fd5f9336d9103", "LabelPage.qml"),
        ("gallery_6d23f04b26967d64", "ContainerPage.qml"),
        ("gallery_fb5640f8e12e3337", "CardPage.qml"),
        ("gallery_85f05ecc2a4f3f5d", "CarouselPage.qml"),
        ("gallery_8cb443ab83797881", "ChartPage.qml"),
        ("gallery_4ce4cafdd0561280", "MenuPage.qml"),
        ("gallery_e72622fe470d04bc", "NavigationPage.qml"),
        ("gallery_8b2106ca13719cb2", "FeedbackPage.qml"),
        ("gallery_0d720eeea26466dd", "IconPage.qml"),
        ("gallery_8829dbcbcfce6e54", "EffectsPage.qml"),
        ("gallery_736cff237d7d9255", "AutoUpdatePage.qml"),
    ]

    navigation_source = _qml_property_array(source, "navItems")
    page_source = _qml_property_array(source, "pagePaths")
    translation_keys = re.findall(
        r'Fluent\.Translator\.tr\("([^"]+)"', navigation_source
    )
    page_names = re.findall(r'pages/([^"]+\.qml)', page_source)

    expected_page_names = [page_name for _, page_name in expected_navigation]
    assert translation_keys == [key for key, _ in expected_navigation]
    assert page_names == expected_page_names + ["SettingsPage.qml"]


def test_gallery_settings_keep_window_and_application_order():
    source = GALLERY_SETTINGS_PAGE.read_text(encoding="utf-8")
    ordered_tokens = [
        'Fluent.Translator.tr("gallery_248c888b290d234f"',
        'objectName: "windowTypeSettingsCard"',
        'objectName: "dpiScaleSettingsCard"',
        'Fluent.Translator.tr("gallery_491d8a1d801bb51f"',
        'Fluent.Translator.tr("gallery_1001f6a8b689600b"',
        'Fluent.Translator.tr("gallery_a1a42cd9b16e2162"',
        'objectName: "themeSettingsCard"',
        'objectName: "accentColorSettingsCard"',
        'objectName: "skinSettingsCard"',
        'objectName: "languageSettingsCard"',
        'Fluent.Translator.tr("gallery_d05c55bc5b9d134b"',
    ]

    positions = [source.index(token) for token in ordered_tokens]
    assert positions == sorted(positions)


def test_gallery_applies_lazy_loading_changes_after_restart():
    qml_source = GALLERY_QML.read_text(encoding="utf-8")
    settings_source = GALLERY_SETTINGS_PAGE.read_text(encoding="utf-8")
    snapshot_assignment = (
        "_startupLazyLoading = ConfigManager ? ConfigManager.lazyLoading : true"
    )
    window_creation = "windowInstance = windowComponent.createObject(null)"

    assert "property bool _startupLazyLoading: true" in qml_source
    assert "readonly property bool lazyLoading: _startupLazyLoading" in qml_source
    assert snapshot_assignment in qml_source
    assert qml_source.index(snapshot_assignment) < qml_source.index(window_creation)
    assert (
        "readonly property bool lazyLoading: ConfigManager" not in qml_source
    )
    assert "ConfigManager.setLazyLoading(isChecked)" in settings_source


def test_gallery_selects_and_persists_lazy_animation_type():
    qml_source = GALLERY_QML.read_text(encoding="utf-8")
    settings_source = GALLERY_SETTINGS_PAGE.read_text(encoding="utf-8")

    assert "property int lazyAnimationType: ConfigManager" in qml_source
    assert qml_source.count("lazyAnimationType: root.lazyAnimationType") == 3
    assert "ConfigManager.lazyAnimationTypeOptions" in settings_source
    assert "type: Fluent.Enums.settingCard.type_combobox" in settings_source
    assert "ConfigManager.setLazyAnimationType(selectedType)" in settings_source


def test_gallery_exposes_fractional_dpi_git_graph_timeline():
    menu_source = GALLERY_MENU_PAGE.read_text(encoding="utf-8")
    graph_source = GALLERY_GIT_GRAPH.read_text(encoding="utf-8")

    assert "TimelineGitGraphDemo {}" in menu_source
    assert 'objectName: "galleryGitGraphTimeline"' in graph_source
    assert "type: Fluent.Enums.timeline.type_graph" in graph_source
    assert "graphLaneCount: 3" in graph_source
    assert "startAtNode: true" in graph_source
    assert "endAtNode: true" in graph_source


def test_gallery_exposes_dry_and_real_auto_update_backends():
    main_source = GALLERY_MAIN.read_text(encoding="utf-8")
    qml_source = GALLERY_QML.read_text(encoding="utf-8")
    page_source = GALLERY_AUTO_UPDATE_PAGE.read_text(encoding="utf-8")
    dry_run_source = GALLERY_DRY_RUN_UPDATER.read_text(encoding="utf-8")

    assert "gallery_repository, prismqml.__version__, gallery_asset_keyword" in main_source
    assert 'setContextProperty("appUpdater", gallery_updater)' in main_source
    assert 'Fluent.Translator.tr("gallery_736cff237d7d9255"' in qml_source
    assert 'pages/AutoUpdatePage.qml' in qml_source
    assert "Fluent.AutoUpdater" in page_source
    assert "updater: root.activeUpdater" in page_source
    assert "GalleryInternal.GalleryDryRunUpdater" in page_source
    assert "onUpdateAvailable" in page_source
    assert "function checkForUpdate()" in dry_run_source
    assert "function downloadUpdate(token)" in dry_run_source
    assert "function runInstallerAndQuit(path, args)" in dry_run_source
    assert "function stageInstallerForNextLaunch(path, args)" in dry_run_source


def test_gallery_hyperlink_label_targets_github_repository():
    source = GALLERY_LABEL_PAGE.read_text(encoding="utf-8")

    assert 'Fluent.Translator.tr("gallery_8f9a5b6031177e4e"' in source
    assert 'url: "https://github.com/aki-riko/PrismQML"' in source
    assert 'url: "https://example.com"' not in source


def test_gallery_list_view_delegate_keeps_current_item_selected():
    source = GALLERY_MENU_PAGE.read_text(encoding="utf-8")

    assert "demoFluentListView.currentIndex === index" in source
    assert "Fluent.Enums.stateColor.selectedHover" in source
    assert "Fluent.Enums.stateColor.selected" in source
    assert "opacity: _lvDelegate._selected ? 1 : 0" in source
