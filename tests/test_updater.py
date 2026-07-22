# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 组件单元测试。

覆盖纯逻辑(版本比对 / asset 选择)与信号发射(注入假 JSON,不真连网)。
"""

import json
import inspect
import os
from types import SimpleNamespace

import pytest
from PySide6.QtNetwork import QNetworkRequest

import prismqml.python.core.updater as updater_module
from prismqml.python.core.updater import (
    Updater,
    _network_request,
    _parse_version,
    _is_newer,
    _pick_asset,
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


# ==================== asset 选择 ====================
class TestPickAsset:
    def test_empty(self):
        assert _pick_asset([], "Setup") is None

    def test_keyword_exe_first(self):
        assets = [
            {"name": "source.zip"},
            {"name": "Gitora-Setup-1.0.4.exe"},
            {"name": "other.exe"},
        ]
        a = _pick_asset(assets, "Setup")
        assert a["name"] == "Gitora-Setup-1.0.4.exe"

    def test_fallback_any_exe(self):
        assets = [{"name": "source.zip"}, {"name": "tool.exe"}]
        a = _pick_asset(assets, "Setup")
        assert a["name"] == "tool.exe"

    def test_fallback_first(self):
        assets = [{"name": "a.zip"}, {"name": "b.tar.gz"}]
        a = _pick_asset(assets, "Setup")
        assert a["name"] == "a.zip"

    def test_keyword_case_insensitive(self):
        assets = [{"name": "MyApp-setup-2.0.exe"}]
        a = _pick_asset(assets, "Setup")
        assert a["name"] == "MyApp-setup-2.0.exe"


# ==================== 信号(注入假数据,不连网) ====================
class TestSignals:
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
                 "browser_download_url": "https://example.com/Gitora-Setup-1.0.4.exe"},
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


# ==================== 安装(不真启动进程) ====================
class _FakeShellExecute:
    def __init__(self, result=42, error=None):
        self._result = result
        self._error = error
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if self._error is not None:
            raise self._error
        return self._result


def _patch_windows_shell(monkeypatch, shell_execute):
    wintypes = SimpleNamespace(
        HWND=object(),
        LPCWSTR=object(),
        HINSTANCE=object(),
    )
    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(
            shell32=SimpleNamespace(ShellExecuteW=shell_execute),
        ),
        wintypes=wintypes,
        c_int=object(),
        ArgumentError=type("ArgumentError", (Exception,), {}),
    )
    monkeypatch.setattr(updater_module.sys, "platform", "win32")
    monkeypatch.setattr(updater_module, "ctypes", fake_ctypes, raising=False)
    monkeypatch.setattr(updater_module, "wintypes", wintypes, raising=False)
    return fake_ctypes, wintypes


def _assert_shell_execute_contract(
    shell_execute,
    fake_ctypes,
    wintypes,
    installer,
):
    assert shell_execute.argtypes == [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        fake_ctypes.c_int,
    ]
    assert shell_execute.restype is wintypes.HINSTANCE
    assert shell_execute.calls == [(
        None, "open", str(installer), "/NORESTART", None, 1,
    )]


class TestInstaller:
    def test_run_installer_missing_file(self, qapp):
        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit("/non/existent/path.exe") is False

    def test_open_in_browser_empty(self, qapp):
        up = Updater("owner/repo", "v1.0.3")
        assert up.openInBrowser("") is False

    def test_detached_failure_tuple_does_not_quit(self, qapp, tmp_path, monkeypatch):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        quits = []
        monkeypatch.setattr(updater_module.sys, "platform", "linux")
        monkeypatch.setattr(
            updater_module.QProcess,
            "startDetached",
            staticmethod(lambda *_args: (False, 0)),
        )
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )
        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer)) is False
        assert quits == []

    def test_detached_success_tuple_quits_once(self, qapp, tmp_path, monkeypatch):
        installer = tmp_path / "Setup.pkg"
        installer.write_bytes(b"dummy")
        calls = []
        quits = []
        monkeypatch.setattr(updater_module.sys, "platform", "darwin")
        monkeypatch.setattr(
            updater_module.QProcess,
            "startDetached",
            staticmethod(lambda path, args: calls.append((path, args)) or (True, 1234)),
        )
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer), "--silent") is True
        assert calls == [(str(installer), ["--silent"])]
        assert quits == [True]

    @pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
    def test_detached_process_control_propagates_without_quit(
        self,
        qapp,
        tmp_path,
        monkeypatch,
        error_type,
    ):
        installer = tmp_path / "Setup.pkg"
        installer.write_bytes(b"dummy")
        quits = []

        def fail_start(*_args):
            raise error_type("stop")

        monkeypatch.setattr(updater_module.sys, "platform", "darwin")
        monkeypatch.setattr(
            updater_module.QProcess,
            "startDetached",
            staticmethod(fail_start),
        )
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        with pytest.raises(error_type, match="stop"):
            up.runInstallerAndQuit(str(installer))
        assert quits == []

    def test_windows_shell_execute_signature_and_success(
        self,
        qapp,
        tmp_path,
        monkeypatch,
    ):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        shell_execute = _FakeShellExecute()
        fake_ctypes, wintypes = _patch_windows_shell(monkeypatch, shell_execute)
        quits = []
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer), "/NORESTART") is True
        _assert_shell_execute_contract(
            shell_execute, fake_ctypes, wintypes, installer
        )
        assert quits == [True]

    @pytest.mark.parametrize("result", (None, 32))
    def test_windows_shell_execute_failure_does_not_quit(
        self,
        qapp,
        tmp_path,
        monkeypatch,
        result,
    ):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        _patch_windows_shell(monkeypatch, _FakeShellExecute(result=result))
        quits = []
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer)) is False
        assert quits == []

    @pytest.mark.parametrize("error_type", (KeyboardInterrupt, SystemExit))
    def test_windows_process_control_propagates_without_quit(
        self,
        qapp,
        tmp_path,
        monkeypatch,
        error_type,
    ):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        shell_execute = _FakeShellExecute(error=error_type("stop"))
        _patch_windows_shell(monkeypatch, shell_execute)
        quits = []
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        with pytest.raises(error_type, match="stop"):
            up.runInstallerAndQuit(str(installer))
        assert quits == []

    def test_windows_shell_execute_exception_keeps_traceback_route(
        self,
        qapp,
        tmp_path,
        monkeypatch,
    ):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        shell_execute = _FakeShellExecute(error=OSError("shell unavailable"))
        _patch_windows_shell(monkeypatch, shell_execute)
        messages = []
        quits = []
        monkeypatch.setattr(updater_module.logger, "exception", messages.append)
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer)) is False
        assert messages == [
            "[Updater] 启动安装包异常: OSError: shell unavailable"
        ]
        assert quits == []
