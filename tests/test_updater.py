# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 网络入口与请求策略单测（注入假数据，不真连网）。
Updater API base url / request policy unit tests (fake payloads, no real network).
"""

import pytest
from PySide6.QtNetwork import QNetworkRequest

import prismqml.python.core.updater as updater_module

from prismqml.python.core._updater_release import is_safe_update_url
from prismqml.python.core.updater import (
    Updater,
    _network_request,
)


class TestApiBaseUrl:
    def test_explicit_environment_and_default_precedence(self, monkeypatch):
        monkeypatch.delenv("PRISMQML_UPDATER_API_BASE_URL", raising=False)
        assert updater_module._resolve_api_base_url(None) == "https://api.github.com"

        monkeypatch.setenv(
            "PRISMQML_UPDATER_API_BASE_URL", "https://updates.example/api/v3/"
        )
        assert updater_module._resolve_api_base_url(None) == "https://updates.example/api/v3"
        assert updater_module._resolve_api_base_url("") == "https://updates.example/api/v3"
        assert updater_module._resolve_api_base_url(" / ") == "https://updates.example/api/v3"
        assert updater_module._resolve_api_base_url(" https://explicit.example/ ") == (
            "https://explicit.example"
        )

        monkeypatch.setenv("PRISMQML_UPDATER_API_BASE_URL", " / ")
        assert updater_module._resolve_api_base_url(None) == "https://api.github.com"

    def test_latest_release_url_and_updater_property(self, qapp, monkeypatch):
        monkeypatch.setenv("PRISMQML_UPDATER_API_BASE_URL", "https://env.example/api/")
        updater = Updater(
            "owner/repo",
            "v1.0.3",
            api_base_url="https://explicit.example/api/v3/",
        )

        assert updater.api_base_url == "https://explicit.example/api/v3"
        assert updater_module._latest_release_url(
            "owner/repo", updater.api_base_url
        ) == "https://explicit.example/api/v3/repos/owner/repo/releases/latest"

    def test_network_request_does_not_cache_idle_https_connection(self):
        request = _network_request(
            "https://api.github.com/repos/owner/repo/releases/latest"
        )

        expiry = request.attribute(
            QNetworkRequest.Attribute.ConnectionCacheExpiryTimeoutSecondsAttribute
        )
        assert expiry == 0
        assert request.attribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute
        ) == QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://updates.example/release", True),
            ("http://127.0.0.1:8080/release", True),
            ("http://localhost/release", True),
            ("http://updates.example/release", False),
            ("https://user:secret@updates.example/release", False),
            ("not-a-url", False),
        ],
    )
    def test_update_url_security_policy(self, url, expected):
        assert is_safe_update_url(url) is expected

    def test_qml_metadata_properties(self, qapp):
        updater = Updater("owner/repo", "v1.2.3")

        assert updater.repository == "owner/repo"
        assert updater.currentVersion == "v1.2.3"
        assert updater.requireArtifactDigest is True
        with pytest.raises(AttributeError):
            updater.requireArtifactDigest = False

    def test_download_progress_preserves_qint64_byte_counts(self, qapp):
        updater = Updater("owner/repo", "v1.2.3")
        progress = []
        updater.downloadProgress.connect(
            lambda received, total: progress.append((received, total))
        )

        updater.downloadProgress.emit(3_000_000_000, 4_000_000_000)

        assert progress == [(3_000_000_000, 4_000_000_000)]

    def test_busy_transactions_emit_terminal_failures(self, qapp):
        updater = Updater("owner/repo", "v1.2.3")
        check_failures = []
        download_failures = []
        updater.checkFailed.connect(check_failures.append)
        updater.downloadFailed.connect(download_failures.append)

        updater._check_reply = object()
        updater.checkForUpdate()
        updater.downloadUpdate("https://example.test/App-Setup.exe")
        updater._check_reply = None
        updater._download_reply = object()
        updater.checkForUpdate()
        updater.downloadUpdate("https://example.test/App-Setup.exe")

        assert check_failures == ["更新检查已在进行", "更新检查已在进行"]
        assert download_failures == ["更新检查已在进行", "下载已在进行"]
