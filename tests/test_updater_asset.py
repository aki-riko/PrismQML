# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 安装资产选择单测。 Updater release-asset selection tests."""

import pytest

from prismqml.python.core.updater import _pick_asset


# ==================== asset 选择 ====================
class TestPickAsset:
    def test_empty(self):
        assert _pick_asset([], "Setup") is None

    def test_keyword_exe_first(self):
        assets = [
            {"name": "source.zip"},
            {"name": "Gitora-Setup-1.0.4.exe", "browser_download_url": "https://x/a.exe"},
            {"name": "other.exe", "browser_download_url": "https://x/b.exe"},
        ]
        a = _pick_asset(assets, "Setup", "win32")
        assert a["name"] == "Gitora-Setup-1.0.4.exe"

    def test_fallback_any_exe(self):
        assets = [{"name": "source.zip"}, {"name": "tool.exe", "browser_download_url": "https://x/tool.exe"}]
        a = _pick_asset(assets, "Setup", "win32")
        assert a["name"] == "tool.exe"

    def test_no_installer_asset(self):
        assets = [{"name": "a.zip", "browser_download_url": "https://x/a.zip"},
                  {"name": "b.tar.gz", "browser_download_url": "https://x/b.tar.gz"}]
        assert _pick_asset(assets, "Setup") is None

    def test_keyword_case_insensitive(self):
        assets = [{"name": "MyApp-setup-2.0.exe", "browser_download_url": "https://x/a.exe"}]
        a = _pick_asset(assets, "Setup", "win32")
        assert a["name"] == "MyApp-setup-2.0.exe"

    @pytest.mark.parametrize(
        ("platform_name", "asset_name"),
        [("win32", "App.exe"), ("darwin", "App.dmg"), ("linux", "App.AppImage")],
    )
    def test_platform_installer_filter(self, platform_name, asset_name):
        assets = [
            {"name": "Wrong.zip", "browser_download_url": "https://x/wrong.zip"},
            {"name": asset_name, "browser_download_url": "https://x/installer"},
        ]

        assert _pick_asset(assets, "", platform_name)["name"] == asset_name

    def test_unsupported_platform_has_no_installer_fallback(self):
        assets = [{"name": "App.exe", "browser_download_url": "https://x/a.exe"}]

        assert _pick_asset(assets, "", "android") is None

    def test_empty_download_url_never_shadows_valid_asset(self):
        assets = [
            {"name": "Preferred-Setup.exe", "browser_download_url": ""},
            {"name": "Fallback.exe", "browser_download_url": "https://x/fallback.exe"},
        ]

        assert _pick_asset(assets, "Setup", "win32")["name"] == "Fallback.exe"
