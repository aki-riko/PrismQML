# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery runtime registration contracts. Gallery 运行时注册合同。"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GALLERY_MAIN = ROOT / "examples" / "main.py"
GALLERY_QML = ROOT / "examples" / "main.qml"
GALLERY_AUTO_UPDATE_PAGE = ROOT / "examples" / "pages" / "AutoUpdatePage.qml"
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


def test_gallery_uses_complete_public_runtime_registration():
    tree = _gallery_tree()
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "register_types"
    ]

    assert len(calls) == 1
    assert len(calls[0].args) == 1
    assert isinstance(calls[0].args[0], ast.Name)
    assert calls[0].args[0].id == "engine"


def test_gallery_disables_debug_logging_by_default():
    source = GALLERY_MAIN.read_text(encoding="utf-8")

    level_setup = "getLogger().set_level(Logger.INFO)"
    assert level_setup in source
    assert source.index(level_setup) < source.index("install_qt_message_handler()")


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


def test_gallery_defaults_language_to_follow_system():
    source = GALLERY_QML.read_text(encoding="utf-8")

    assert "Fluent.Translator.setLanguage(Fluent.Enums.lang.auto)" in source
    assert "Fluent.Translator.setLanguage(Fluent.Enums.lang.zh_CN)" not in source


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
    assert '"text": "自动更新"' in qml_source
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

    assert 'text: "超链接文本"; url: "https://github.com/aki-riko/PrismQML"' in source
    assert 'text: "超链接文本"; url: "https://example.com"' not in source
