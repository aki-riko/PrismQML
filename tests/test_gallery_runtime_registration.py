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
