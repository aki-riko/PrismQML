# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 信号发射单测（注入假 JSON，不连网）。
Updater signal emission tests: fake release JSON only, no real network I/O.
"""

import json

import pytest

import prismqml.python.core.updater as updater_module

from prismqml.python.core.updater import Updater


# ==================== 信号(注入假数据,不连网) ====================
class TestSignals:
    @pytest.fixture(autouse=True)
    def _select_windows_assets(self, monkeypatch):
        pick_asset = updater_module._pick_asset
        monkeypatch.setattr(
            updater_module,
            "_pick_asset",
            lambda assets, keyword: pick_asset(assets, keyword, "win32"),
        )

    def _make(self):
        return Updater("owner/repo", "v1.0.3", asset_keyword="Setup")

    def test_update_available(self, qapp):
        up = self._make()
        received = {}

        def on_avail(version, notes, dl, html):
            received.update(version=version, notes=notes, dl=dl, html=html)

        up.updateAvailable.connect(on_avail)

        fake = {
            "tag_name": "v1.0.4",
            "body": "新功能",
            "html_url": "https://github.com/owner/repo/releases/tag/v1.0.4",
            "assets": [
                {"name": "Gitora-Setup-1.0.4.exe",
                 "browser_download_url": "https://example.com/Gitora-Setup-1.0.4.exe",
                 "digest": "sha256:" + "0" * 64},
            ],
        }
        up._inject_release_for_test(json.dumps(fake).encode("utf-8"))

        assert received["version"] == "v1.0.4"
        assert received["notes"] == "新功能"
        assert received["dl"].endswith("Gitora-Setup-1.0.4.exe")
        assert "releases/tag" in received["html"]

    def test_up_to_date(self, qapp):
        up = self._make()
        seen = {}
        up.upToDate.connect(lambda v: seen.update(v=v))
        up._inject_release_for_test(json.dumps({"tag_name": "v1.0.3"}).encode("utf-8"))
        assert seen["v"] == "v1.0.3"

    def test_up_to_date_when_older_remote(self, qapp):
        up = self._make()
        seen = {}
        up.upToDate.connect(lambda v: seen.update(v=v))
        up._inject_release_for_test(json.dumps({"tag_name": "v1.0.0"}).encode("utf-8"))
        assert seen["v"] == "v1.0.3"

    def test_check_failed_bad_json(self, qapp):
        up = self._make()
        seen = {}
        up.checkFailed.connect(lambda m: seen.update(m=m))
        up._inject_release_for_test(b"not json {{{")
        assert "m" in seen

    def test_check_failed_no_tag(self, qapp):
        up = self._make()
        seen = {}
        up.checkFailed.connect(lambda m: seen.update(m=m))
        up._inject_release_for_test(json.dumps({"name": "no tag here"}).encode("utf-8"))
        assert "m" in seen

    def test_missing_asset_digest_fails_closed(self, qapp):
        up = self._make()
        failures = []
        successes = []
        up.checkFailed.connect(failures.append)
        up.updateAvailable.connect(lambda *args: successes.append(args))
        payload = {
            "tag_name": "v1.0.4",
            "assets": [{
                "name": "App-Setup.exe",
                "browser_download_url": "https://example.test/App-Setup.exe",
            }],
        }

        up._inject_release_for_test(json.dumps(payload).encode("utf-8"))

        assert failures == ["更新资产缺少有效 SHA-256 摘要"]
        assert successes == []

    def test_unsafe_asset_url_fails_before_confirmation(self, qapp):
        up = self._make()
        failures = []
        up.checkFailed.connect(failures.append)
        payload = {
            "tag_name": "v1.0.4",
            "assets": [{
                "name": "App-Setup.exe",
                "browser_download_url": "http://downloads.example/App-Setup.exe",
                "digest": "sha256:" + "0" * 64,
            }],
        }

        up._inject_release_for_test(json.dumps(payload).encode("utf-8"))

        assert failures == ["更新资产下载地址不安全"]

    def test_direct_download_without_release_digest_is_rejected(self, qapp):
        up = self._make()
        failures = []
        up.downloadFailed.connect(failures.append)

        up.downloadUpdate("https://example.test/App-Setup.exe")

        assert failures == ["下载地址未绑定有效 SHA-256 摘要"]
