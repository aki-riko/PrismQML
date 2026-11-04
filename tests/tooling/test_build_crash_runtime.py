# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Contracts for the crash runtime build script. 崩溃运行时构建脚本契约。"""

import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import build_crash_runtime as crash_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PINNED_COMMIT = "af9e9367913edf07f54e4f2f9655ce96af0c1681"


def _layout(tmp_path: Path) -> crash_runtime.Layout:
    return crash_runtime.resolve_layout({crash_runtime.ARTIFACT_ROOT_ENV: str(tmp_path)})


class _FakeGit:
    """Record commands and answer git queries. 记录命令并应答 git 查询。"""

    def __init__(self, head: str = PINNED_COMMIT, submodules: str = "") -> None:
        self.head = head
        self.submodules = submodules
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(list(command))
        if command[:2] == ["git", "clone"]:
            Path(command[-1]).mkdir(parents=True)
        stdout = ""
        if "rev-parse" in command:
            stdout = self.head + "\n"
        elif "submodule" in command:
            stdout = self.submodules
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")


def test_pin_file_records_full_commit():
    pin = crash_runtime.load_pin()
    assert pin.repository == "https://github.com/getsentry/sentry-native.git"
    assert pin.tag == "0.17.5"
    assert pin.commit == PINNED_COMMIT


def test_pin_rejects_abbreviated_commit(tmp_path):
    pin_file = tmp_path / "pin.json"
    pin_file.write_text('{"repository": "r", "tag": "t", "commit": "af9e936"}', encoding="utf-8")
    with pytest.raises(ValueError, match="full lowercase sha1"):
        crash_runtime.load_pin(pin_file)


def test_layout_defaults_under_repo_artifacts():
    layout = crash_runtime.resolve_layout({})
    base = PROJECT_ROOT / ".artifacts" / "cpp" / "sentry-native"
    assert layout.artifact_root == PROJECT_ROOT / ".artifacts"
    assert (layout.source, layout.build, layout.install, layout.runtime) == (
        base / "src", base / "build", base / "install", base / "runtime"
    )


def test_layout_honours_artifact_root_override(tmp_path):
    layout = _layout(tmp_path)
    assert layout.runtime == tmp_path / "cpp" / "sentry-native" / "runtime"


def test_cmake_command_honours_override():
    assert crash_runtime.cmake_command({}) == "cmake"
    assert crash_runtime.cmake_command({crash_runtime.CMAKE_COMMAND_ENV: "C:/cm.exe"}) == "C:/cm.exe"


def test_build_commands_use_crashpad_without_transport(tmp_path):
    layout = _layout(tmp_path)
    configure, build, install = crash_runtime.build_commands(layout, "cmake")
    assert "-DSENTRY_BACKEND=crashpad" in configure
    assert "-DSENTRY_TRANSPORT=none" in configure
    assert "-DCRASHPAD_ZLIB_SYSTEM=OFF" in configure
    assert "-DSENTRY_BUILD_SHARED_LIBS=ON" in configure
    assert f"-DCMAKE_INSTALL_PREFIX={layout.install}" in configure
    assert configure[configure.index("-B") + 1] == str(layout.build)
    assert build[build.index("--config") + 1] == crash_runtime.BUILD_CONFIG
    assert install[install.index("--config") + 1] == crash_runtime.BUILD_CONFIG


def test_windows_build_links_the_crt_statically(tmp_path):
    layout = _layout(tmp_path)
    windows, _, _ = crash_runtime.build_commands(layout, "cmake", "win32")
    linux, _, _ = crash_runtime.build_commands(layout, "cmake", "linux")
    assert "-DSENTRY_BUILD_RUNTIMESTATIC=ON" in windows
    assert not any("RUNTIMESTATIC" in option for option in linux)


def test_only_linux_strips_installed_binaries(tmp_path):
    layout = _layout(tmp_path)
    for platform, stripped in (("linux", True), ("darwin", False), ("win32", False)):
        _, _, install = crash_runtime.build_commands(layout, "cmake", platform)
        assert ("--strip" in install) is stripped, platform


def test_checkout_clones_pinned_tag_with_submodules(tmp_path):
    layout = _layout(tmp_path)
    git = _FakeGit()
    crash_runtime.ensure_checkout(crash_runtime.load_pin(), layout, git)
    clone = git.commands[0]
    assert clone[:2] == ["git", "clone"]
    assert clone[clone.index("--branch") + 1] == "0.17.5"
    assert "--recurse-submodules" in clone
    assert clone[-1] == str(layout.source)


def test_checkout_rejects_unpinned_head(tmp_path):
    layout = _layout(tmp_path)
    layout.source.mkdir(parents=True)
    git = _FakeGit(head="0" * 40)
    with pytest.raises(ValueError, match="expected pinned"):
        crash_runtime.ensure_checkout(crash_runtime.load_pin(), layout, git)
    assert not any(command[:2] == ["git", "clone"] for command in git.commands)


def test_checkout_rejects_uninitialized_submodules(tmp_path):
    layout = _layout(tmp_path)
    layout.source.mkdir(parents=True)
    git = _FakeGit(submodules=" 1234 external/ok (v1)\n-5678 external/crashpad\n")
    with pytest.raises(ValueError, match="external/crashpad"):
        crash_runtime.ensure_checkout(crash_runtime.load_pin(), layout, git)


@pytest.mark.parametrize("platform", sorted(crash_runtime.RUNTIME_FILES))
def test_stage_copies_platform_files_and_drops_stale_ones(tmp_path, platform):
    layout = _layout(tmp_path)
    for index, name in enumerate(crash_runtime.RUNTIME_FILES[platform]):
        source = layout.install / ("bin" if index % 2 else "lib") / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(name.encode("utf-8"))
    layout.runtime.mkdir(parents=True)
    (layout.runtime / "stale.bin").write_bytes(b"old")

    staged = crash_runtime.stage_runtime(layout, platform)

    assert sorted(path.name for path in layout.runtime.iterdir()) == sorted(
        crash_runtime.RUNTIME_FILES[platform]
    )
    for name, path in staged.items():
        assert path.read_bytes() == name.encode("utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits only")
def test_stage_marks_posix_handler_executable(tmp_path):
    layout = _layout(tmp_path)
    for name in crash_runtime.RUNTIME_FILES["linux"]:
        (layout.install / name).parent.mkdir(parents=True, exist_ok=True)
        (layout.install / name).write_bytes(b"x")
    staged = crash_runtime.stage_runtime(layout, "linux")
    assert staged["crashpad_handler"].stat().st_mode & stat.S_IXUSR


def test_stage_rejects_missing_file(tmp_path):
    layout = _layout(tmp_path)
    (layout.install / "bin").mkdir(parents=True)
    (layout.install / "bin" / "sentry.dll").write_bytes(b"x")
    with pytest.raises(FileNotFoundError, match="crashpad_handler.exe"):
        crash_runtime.stage_runtime(layout, "win32")


def test_stage_rejects_duplicate_file(tmp_path):
    layout = _layout(tmp_path)
    for folder in ("bin", "lib"):
        for name in crash_runtime.RUNTIME_FILES["linux"]:
            (layout.install / folder).mkdir(parents=True, exist_ok=True)
            (layout.install / folder / name).write_bytes(b"x")
    with pytest.raises(FileNotFoundError, match="exactly one"):
        crash_runtime.stage_runtime(layout, "linux")


def test_stage_rejects_unknown_platform(tmp_path):
    with pytest.raises(ValueError, match="unsupported platform"):
        crash_runtime.stage_runtime(_layout(tmp_path), "sunos5")


def test_stage_refuses_runtime_outside_artifact_root(tmp_path):
    layout = _layout(tmp_path / "artifacts")
    outside = crash_runtime.Layout(
        layout.artifact_root, layout.source, layout.build, layout.install, tmp_path / "elsewhere"
    )
    for name in crash_runtime.RUNTIME_FILES["linux"]:
        (outside.install / name).parent.mkdir(parents=True, exist_ok=True)
        (outside.install / name).write_bytes(b"x")
    with pytest.raises(ValueError, match="outside"):
        crash_runtime.stage_runtime(outside, "linux")
    assert not (tmp_path / "elsewhere").exists()


def test_main_reports_failed_command(monkeypatch, caplog):
    def fail():
        raise subprocess.CalledProcessError(2, ["cmake", "--build"])

    monkeypatch.setattr(crash_runtime, "build_runtime", fail)
    assert crash_runtime.main([]) == 1
    assert "exit code 2" in caplog.text
