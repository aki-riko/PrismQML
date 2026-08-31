# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""C++ Gallery startup configuration contracts. C++ Gallery 启动配置合同。"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CPP_GALLERY_MAIN = ROOT / "cpp" / "gallery" / "main.cpp"
WINDOW_HEADER = ROOT / "cpp" / "include" / "prism" / "Window.h"


def test_cpp_gallery_restores_persisted_window_type():
    source = CPP_GALLERY_MAIN.read_text(encoding="utf-8")
    window_header = WINDOW_HEADER.read_text(encoding="utf-8")

    assert "enum class WindowType { Split = 0, Bar = 1, Filled = 2 };" in window_header
    assert "ConfigManager::instance()->windowType()" in source
    assert "app.createWindow(WindowType::Bar)" not in source


def test_cpp_gallery_presents_generic_caption_action_without_owning_semantics():
    source = CPP_GALLERY_MAIN.read_text(encoding="utf-8")
    window_header = WINDOW_HEADER.read_text(encoding="utf-8")

    assert "setCaptionAction(QStringLiteral(\"Bot\")" in source
    assert "onCaptionActionTriggered([]()" in source
    assert "void setCaptionAction(" in window_header
    assert "void onCaptionActionTriggered(std::function<void()> cb);" in window_header
