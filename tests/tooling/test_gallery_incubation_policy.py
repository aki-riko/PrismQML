# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery incubation policy contract. Gallery 孵化策略契约。"""

from pathlib import Path

from prismqml.python.core.incubation import asynchronous_page_loader_enabled


ROOT = Path(__file__).resolve().parents[2]
GALLERY_MAIN = ROOT / "examples" / "main.py"
RUNTIME_ENGINE = ROOT / "prismqml" / "python" / "runtime" / "engine.py"


def test_gallery_injects_safe_async_page_loader_policy():
    source = GALLERY_MAIN.read_text(encoding="utf-8")
    runtime_source = RUNTIME_ENGINE.read_text(encoding="utf-8")

    assert "asynchronous_page_loader_enabled" in source
    assert '"PrismQmlAsynchronousPageLoaderEnabled"' in source
    assert "asynchronous_page_loader_enabled()," in source
    assert "install_default_incubation_controller(engine)" in runtime_source
    assert source.index("PrismQmlAsynchronousPageLoaderEnabled") < source.index(
        "engine.load("
    )


def test_qt_611_windows_use_synchronous_gallery_page_loaders():
    assert not asynchronous_page_loader_enabled("6.11.1", "win32")
