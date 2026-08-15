# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Optional provider runtime contracts. 可选 provider runtime 合同。"""


def test_qrcode_generator_facade_delegates_to_provider(monkeypatch):
    from prismqml.python.providers import qrcode_generator
    from prismqml.python.runtime.provider_services import get_qrcode_generator

    sentinel = object()
    monkeypatch.setattr(qrcode_generator, "get_qrcode_generator", lambda: sentinel)

    assert get_qrcode_generator() is sentinel


def test_qrcode_provider_facade_delegates_to_provider(monkeypatch):
    from prismqml.python.providers import qrcode_generator
    from prismqml.python.runtime.provider_services import get_qrcode_provider

    sentinel = object()
    monkeypatch.setattr(qrcode_generator, "get_qrcode_provider", lambda: sentinel)

    assert get_qrcode_provider() is sentinel


def test_screen_eyedropper_facade_delegates_to_provider(monkeypatch):
    from prismqml.python.providers import screen_eyedropper
    from prismqml.python.runtime.provider_services import (
        get_screen_eyedropper_manager,
    )

    sentinel = object()
    monkeypatch.setattr(
        screen_eyedropper,
        "get_screen_eyedropper_manager",
        lambda: sentinel,
    )

    assert get_screen_eyedropper_manager() is sentinel


def test_svg_provider_facade_delegates_to_provider(monkeypatch):
    from prismqml.python.providers import svg_provider
    from prismqml.python.runtime.provider_services import get_svg_provider

    sentinel = object()
    monkeypatch.setattr(svg_provider, "get_svg_provider", lambda: sentinel)

    assert get_svg_provider() is sentinel
