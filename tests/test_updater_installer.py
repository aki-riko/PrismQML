# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater 安装事务单测（不真启动进程）。 Updater install-transaction tests.
全部沿用原文件的 monkeypatch 假 ctypes / QProcess / QDesktopServices 注入，
不产生真实进程、网络或仓库外文件 I/O；共用假实现在 updater_shared.py。
"""

import pytest

import prismqml.python.core._updater_install as install_module
import prismqml.python.core.update_slots as slot_module
import prismqml.python.core.updater as updater_module

from prismqml.python.core.updater import Updater
from updater_shared import (
    _FakeShellExecute,
    _assert_shell_execute_contract,
    _patch_windows_shell,
)


# ==================== 安装(不真启动进程) ====================
class TestInstaller:
    def test_dual_slot_reports_ready_only_after_state_and_executable_match(
        self, qapp, tmp_path, monkeypatch
    ):
        target = tmp_path / "slot-b" / "Gitora.exe"
        target.parent.mkdir()
        target.write_bytes(b"new")
        finished = []
        up = Updater("owner/repo", "v1.0.3", install_strategy="dual_slot")
        up.installPreparationFinished.connect(lambda: finished.append(True))
        preparation = up._slot_preparation
        preparation._preparing = True
        preparation._target_slot = "B"
        preparation._deadline = slot_module.time.monotonic() + 60
        monkeypatch.setattr(slot_module, "read_launch_slot", lambda: "B")
        monkeypatch.setattr(
            slot_module, "executable_for_slot", lambda _slot: target
        )

        preparation._poll()

        assert finished == [True]
        assert preparation.next_launch_prepared is True
        assert preparation._preparing is False

    def test_dual_slot_stage_keeps_process_running_and_records_slot_argument(
        self, qapp, tmp_path, monkeypatch
    ):
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"dummy")
        calls = []
        monkeypatch.setattr(slot_module.sys, "platform", "win32")
        monkeypatch.setattr(slot_module, "current_update_slot", lambda: "A")
        monkeypatch.setattr(slot_module, "opposite_slot", lambda slot: "B")
        monkeypatch.setattr(
            slot_module,
            "launch_windows_installer",
            lambda path, args: calls.append((path, args)) or True,
        )
        monkeypatch.setattr(slot_module.QTimer, "start", lambda _timer: None)

        quits = []
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3", install_strategy="dual_slot")
        assert up.stageInstallerForNextLaunch(
            str(installer), "/VERYSILENT /PRISMCURRENTSLOT=B"
        ) is True
        assert calls == [(str(installer), ["/VERYSILENT", "/PRISMCURRENTSLOT=A"])]
        assert quits == []
        assert up.installStrategy == "dual_slot"

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
            install_module.QProcess,
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

    def test_failed_installer_launch_removes_completed_download(
        self, qapp, tmp_path, monkeypatch
    ):
        installer = tmp_path / "Setup.run"
        installer.write_bytes(b"dummy")
        monkeypatch.setattr(updater_module.sys, "platform", "linux")
        monkeypatch.setattr(
            install_module.QProcess,
            "startDetached",
            staticmethod(lambda *_args: (False, 0)),
        )
        updater = Updater("owner/repo", "v1.0.3")
        updater._download_path = str(installer)

        assert updater.runInstallerAndQuit(str(installer)) is False
        assert not installer.exists()

    def test_failed_installer_launch_preserves_unowned_file(
        self, qapp, tmp_path, monkeypatch
    ):
        tracked = tmp_path / "tracked.run"
        unowned = tmp_path / "unowned.run"
        tracked.write_bytes(b"tracked")
        unowned.write_bytes(b"unowned")
        monkeypatch.setattr(updater_module.sys, "platform", "linux")
        monkeypatch.setattr(
            install_module.QProcess,
            "startDetached",
            staticmethod(lambda *_args: (False, 0)),
        )
        updater = Updater("owner/repo", "v1.0.3")
        updater._download_path = str(tracked)

        assert updater.runInstallerAndQuit(str(unowned)) is False
        assert tracked.exists() and unowned.exists()

    def test_detached_success_tuple_quits_once(self, qapp, tmp_path, monkeypatch):
        installer = tmp_path / "Setup.pkg"
        installer.write_bytes(b"dummy")
        calls = []
        quits = []
        monkeypatch.setattr(updater_module.sys, "platform", "darwin")
        monkeypatch.setattr(
            install_module.QProcess,
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
        assert calls == [("/usr/bin/open", [str(installer)])]
        assert quits == [True]

    def test_linux_deb_uses_system_package_handler(self, qapp, tmp_path, monkeypatch):
        installer = tmp_path / "Setup.deb"
        installer.write_bytes(b"dummy")
        opened = []
        quits = []
        monkeypatch.setattr(updater_module.sys, "platform", "linux")
        monkeypatch.setattr(
            install_module.QDesktopServices,
            "openUrl",
            staticmethod(lambda url: opened.append(url.toLocalFile()) or True),
        )
        monkeypatch.setattr(
            updater_module.QCoreApplication,
            "quit",
            staticmethod(lambda: quits.append(True)),
        )

        up = Updater("owner/repo", "v1.0.3")
        assert up.runInstallerAndQuit(str(installer)) is True
        assert opened == [installer.as_posix()]
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
            install_module.QProcess,
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
        monkeypatch.setattr(install_module.logger, "exception", messages.append)
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
