# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 版本比对纯逻辑单测。 Pure version-compare logic tests for the updater."""

import inspect

import pytest

from prismqml.python.core.updater import (
    _is_newer,
    _parse_version,
)


# ==================== 版本比对 ====================
class TestVersionCompare:
    def test_strip_v_prefix(self):
        assert _parse_version("v1.0.3") == _parse_version("1.0.3")
        assert _parse_version("V2.1.0") == _parse_version("2.1.0")

    def test_newer_basic(self):
        assert _is_newer("v1.0.4", "v1.0.3")
        assert _is_newer("v1.1.0", "v1.0.9")
        assert _is_newer("v2.0.0", "v1.9.9")

    def test_not_newer_equal(self):
        assert not _is_newer("v1.0.3", "v1.0.3")

    def test_not_newer_older(self):
        assert not _is_newer("v1.0.2", "v1.0.3")
        assert not _is_newer("v1.0.0", "v1.1.0")

    def test_release_newer_than_prerelease(self):
        # 1.0.0 应比 1.0.0-beta 新(数字段 > 字符串段)
        assert _is_newer("v1.0.0", "v1.0.0-beta")

    def test_empty_is_smallest(self):
        assert _parse_version("") == ()
        assert _is_newer("v0.0.1", "")
        assert not _is_newer("", "v0.0.1")

    def test_different_length(self):
        # 1.0.1 > 1.0
        assert _is_newer("v1.0.1", "v1.0")
        # 1.0 不比 1.0.0 新(段比较,1.0 的元组更短)
        assert not _is_newer("v1.0", "v1.0.0")

    def test_four_part_version(self):
        assert _is_newer("v0.2.24.1", "v0.2.24")
        assert not _is_newer("v0.2.24", "v0.2.24.1")

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            ("v1.0.0+build.2", "v1.0.0+build.1"),
            ("v1.0.0-beta+build.2", "v1.0.0-beta+build.1"),
        ],
    )
    def test_build_metadata_does_not_change_precedence(self, left, right):
        assert _parse_version(left) == _parse_version(right)
        assert not _is_newer(left, right)
        assert not _is_newer(right, left)

    @pytest.mark.parametrize("tag", ["   ", "\t", "v", " V "])
    def test_blank_or_prefix_only_tag_is_empty(self, tag):
        assert _parse_version(tag) == ()

    def test_arbitrarily_large_numeric_prerelease_segments(self):
        assert _is_newer(
            "v1.0.0-alpha.1000000000000000000000000000000",
            "v1.0.0-alpha.999999999999999999999999999999",
        )

    def test_version_parser_stays_small_and_delegates(self):
        lines, _start_line = inspect.getsourcelines(_parse_version)
        source = "".join(lines)

        assert len(lines) <= 30
        assert "_normalize_version_tag(tag)" in source
        assert source.count("_parse_version_segments(") == 2
