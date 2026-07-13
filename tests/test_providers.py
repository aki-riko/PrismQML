# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import base64
from concurrent.futures import ThreadPoolExecutor

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from qrcode.exceptions import DataOverflowError
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

from prismqml.python.providers._qrcode_protocol import (
    MAX_CACHE_BYTES,
    create_request,
    encode_provider_id,
)
from prismqml.python.providers import qrcode_generator
from prismqml.python.providers.qrcode_generator import QRCodeImageProvider
from prismqml.python.providers.svg_provider import SvgImageProvider


class TestImageProviders:
    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            ("L", ERROR_CORRECT_L),
            ("M", ERROR_CORRECT_M),
            ("Q", ERROR_CORRECT_Q),
            ("H", ERROR_CORRECT_H),
        ],
    )
    def test_qrcode_error_levels_are_exact(self, monkeypatch, level, expected):
        """Keep all four public ECC levels exact. 精确保持四档纠错级别。"""
        captured = {}
        real_qrcode = qrcode_generator.qrcode.QRCode

        def create_qrcode(*args, **kwargs):
            captured["error_correction"] = kwargs["error_correction"]
            return real_qrcode(*args, **kwargs)

        monkeypatch.setattr(qrcode_generator.qrcode, "QRCode", create_qrcode)
        provider = QRCodeImageProvider()
        provider_id = encode_provider_id(
            create_request(f"ecc-{level}", 96, "#000000", "#ffffff", level)
        )
        assert provider.requestImage(provider_id, QSize(), QSize()).size() == QSize(96, 96)
        assert captured["error_correction"] == expected

    def test_qrcode_cache_eviction(self):
        """Verify entry-count LRU eviction. 验证条目数 LRU 驱逐。"""
        provider = QRCodeImageProvider()
        provider_ids = [
            encode_provider_id(
                create_request(f"test_data_{index}", 32, "#000000", "#ffffff", "M")
            )
            for index in range(provider.MAX_CACHE_SIZE + 1)
        ]
        for provider_id in provider_ids[: provider.MAX_CACHE_SIZE]:
            assert not provider.requestImage(provider_id, QSize(), QSize()).isNull()
        provider.requestImage(provider_ids[0], QSize(), QSize())
        provider.requestImage(provider_ids[-1], QSize(), QSize())

        assert len(provider._cache) == provider.MAX_CACHE_SIZE
        assert provider_ids[0] in provider._cache
        assert provider_ids[1] not in provider._cache
        assert provider_ids[-1] in provider._cache

    def test_qrcode_cache_respects_byte_budget(self):
        """Verify the 32 MiB cache budget. 验证 32 MiB 缓存预算。"""
        provider = QRCodeImageProvider()
        for index in range(9):
            provider_id = encode_provider_id(
                create_request(f"large-{index}", 1024, "#000000", "#ffffff", "M")
            )
            image = provider.requestImage(provider_id, QSize(), QSize())
            assert image.size() == QSize(1024, 1024)

        assert len(provider._cache) == 8
        assert provider._cache_bytes == MAX_CACHE_BYTES

    def test_qrcode_invalid_and_overflow_requests_stay_bounded(self, monkeypatch):
        """Reject hostile IDs and contain encoder overflow. 拒绝恶意 ID 并隔离溢出。"""
        provider = QRCodeImageProvider()
        invalid = provider.requestImage(
            "legacy|2147483647|#000000|#ffffff|M",
            QSize(),
            QSize(2_147_483_647, 2_147_483_647),
        )
        assert invalid.size() == QSize(128, 128)
        assert invalid.pixelColor(0, 0).alpha() == 0
        assert not provider._cache

        def raise_overflow(_request):
            raise DataOverflowError("forced overflow")

        monkeypatch.setattr(provider, "_generate_qrcode", raise_overflow)
        provider_id = encode_provider_id(
            create_request("overflow", 64, "#000000", "#ffffff", "H")
        )
        overflow = provider.requestImage(provider_id, QSize(), QSize(64, 64))
        assert overflow.size() == QSize(64, 64)
        assert overflow.pixelColor(0, 0).alpha() == 0
        assert not provider._cache

    def test_qrcode_deep_json_returns_a_bounded_placeholder(self):
        """Contain deeply nested JSON. 隔离深层 JSON。"""
        provider = QRCodeImageProvider()
        raw = b"[" * 3000 + b"0" + b"]" * 3000
        token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
        image = provider.requestImage(f"v1.{token}", QSize(), QSize(64, 64))

        assert image.size() == QSize(64, 64)
        assert image.pixelColor(0, 0).alpha() == 0
        assert not provider._cache

    def test_qrcode_provider_is_reentrant(self):
        """Exercise concurrent provider callbacks. 并发执行 provider 回调。"""
        provider = QRCodeImageProvider()
        provider_ids = [
            encode_provider_id(
                create_request(f"thread-{index % 4}", 96, "#000000", "#ffffff", "M")
            )
            for index in range(24)
        ]

        def request(provider_id):
            return provider.requestImage(provider_id, QSize(), QSize())

        with ThreadPoolExecutor(max_workers=8) as executor:
            images = list(executor.map(request, provider_ids))
        assert all(isinstance(image, QImage) and image.size() == QSize(96, 96) for image in images)
        assert len(provider._cache) == 4

    def test_qrcode_mixed_mode_content_matches_cpp_capacity(self):
        """Keep Python/C++ whole-text segmentation aligned. 对齐整串分段策略。"""
        provider = QRCodeImageProvider()
        provider_id = encode_provider_id(
            create_request("1" * 20 + "a", 32, "#000000", "#ffffff", "L")
        )
        image = provider.requestImage(provider_id, QSize(), QSize(32, 32))

        assert image.size() == QSize(32, 32)
        assert image.pixelColor(0, 0).alpha() == 0
        assert not provider._cache


    def test_svg_cache_eviction(self, tmp_path):
        """测试 SvgImageProvider 缓存最大限制 (P1-2)
        
        注意：QSvgRenderer 是矢量渲染器，缓存 key 是文件路径而非尺寸。
        因此必须使用不同的 SVG 文件路径来测试缓存驱逐机制。
        """
        provider = SvgImageProvider()
        SVG_MAX = provider.MAX_CACHE_SIZE
        svg_content = '<svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
        
        # 创建超过 MAX_CACHE_SIZE 个不同的 SVG 文件路径
        for i in range(SVG_MAX + 10):
            svg_file = tmp_path / f"test_{i}.svg"
            svg_file.write_text(svg_content)
            img = provider.requestImage(str(svg_file), QSize(), QSize(32, 32))
            assert isinstance(img, QImage)
            
        # 校验缓存驱逐机制：触发超限后，当前缓存应不超过最大值
        assert len(provider._cache) <= SVG_MAX
        
        # 最新请求的文件应仍在缓存中
        latest_file = str(tmp_path / f"test_{SVG_MAX + 9}.svg")
        assert latest_file in provider._cache
