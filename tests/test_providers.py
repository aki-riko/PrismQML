# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from prismqml.python.providers.qrcode_generator import QRCodeImageProvider
from prismqml.python.providers.svg_provider import SvgImageProvider


class TestImageProviders:
    
    def test_qrcode_cache_eviction(self):
        """测试 QRCodeImageProvider 缓存最大限制及 LRU 驱逐策略 (P0-5)"""
        provider = QRCodeImageProvider()
        QR_MAX = provider.MAX_CACHE_SIZE
        
        # 模拟频繁请求，突破缓存大小限制
        for i in range(QR_MAX + 10):
            req_id = f"test_data_{i}"
            # requestImage 内部会将结果存入 _cache
            img = provider.requestImage(req_id, QSize(), QSize())
            assert isinstance(img, QImage)
            assert not img.isNull()
            
        # 校验：触发了 > MAX_CACHE_SIZE 后的删减机制，当前容量应该约为最大值的一半 (这里设计上如果是每次超出时删除一半)
        assert len(provider._cache) <= QR_MAX
        
        # 确保最新请求的值还在缓存中
        assert f"test_data_{QR_MAX + 9}|150|#000000|#ffffff|M" in provider._cache
        
        # 极早的值应该已经被清理掉了
        assert "test_data_0|150|#000000|#ffffff|M" not in provider._cache


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
