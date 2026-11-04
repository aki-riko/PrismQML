# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Contracts for bundling the crash runtime into wheels. 崩溃运行时打包契约。"""

import importlib.util
import io
import logging
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts import build_crash_runtime as crash_runtime
from scripts import validate_dist


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSION = "0.7.2.2"
WHEEL_PLATFORMS = {
    "win32": "win_amd64",
    "linux": "manylinux_2_28_x86_64",
    "darwin": "macosx_11_0_arm64",
}


def _load_setup_hook():
    spec = importlib.util.spec_from_file_location("prismqml_setup_hook", PROJECT_ROOT / "setup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup_hook = _load_setup_hook()


def _write_wheel(tmp_path: Path, platform: str, runtime_files=(), handler_mode=0o755) -> Path:
    path = tmp_path / f"prismqml-{VERSION}-cp39-abi3-{WHEEL_PLATFORMS[platform]}.whl"
    extension = "prismqml_rs.pyd" if platform == "win32" else "prismqml_rs.abi3.so"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(extension, b"ext")
        for name in runtime_files:
            info = zipfile.ZipInfo(validate_dist.CRASH_RUNTIME_DIR + name)
            mode = handler_mode if name == validate_dist.POSIX_HANDLER else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, b"bin")
    return path


def _write_sdist(tmp_path: Path, extra=()) -> Path:
    root = f"prismqml-{VERSION}"
    path = tmp_path / f"{root}.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        for name in (*validate_dist.REQUIRED_SDIST_FILES, *extra):
            data = b"x"
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path


def test_setup_hook_reads_the_directory_the_build_script_writes(tmp_path):
    assert setup_hook.crash_runtime_dir({}) == crash_runtime.resolve_layout({}).runtime
    override = {setup_hook.ARTIFACT_ROOT_ENV: str(tmp_path)}
    assert setup_hook.crash_runtime_dir(override) == crash_runtime.resolve_layout(override).runtime


def test_validator_file_lists_match_build_script():
    tag_to_platform = {"win_": "win32", "manylinux": "linux", "macosx_": "darwin"}
    assert {
        tag_to_platform[tag]: files for tag, files in validate_dist.CRASH_RUNTIME_FILES.items()
    } == dict(crash_runtime.RUNTIME_FILES)


def test_copy_bundles_staged_files_and_drops_stale_ones(tmp_path):
    source = tmp_path / "runtime"
    source.mkdir()
    (source / "sentry.dll").write_bytes(b"lib")
    (source / "crashpad_handler.exe").write_bytes(b"exe")
    build_lib = tmp_path / "build_lib"
    stale = build_lib.joinpath(*setup_hook.RUNTIME_PACKAGE_DIR) / "old.dll"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old")

    copied = setup_hook.copy_crash_runtime(source, build_lib, required=True)

    assert sorted(path.name for path in copied) == ["crashpad_handler.exe", "sentry.dll"]
    assert sorted(path.name for path in stale.parent.iterdir()) == [
        "crashpad_handler.exe", "sentry.dll"
    ]


def test_copy_warns_and_clears_when_runtime_missing(tmp_path, caplog):
    build_lib = tmp_path / "build_lib"
    stale = build_lib.joinpath(*setup_hook.RUNTIME_PACKAGE_DIR) / "old.dll"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old")
    with caplog.at_level(logging.WARNING, logger="prismqml.build"):
        copied = setup_hook.copy_crash_runtime(tmp_path / "missing", build_lib, required=False)
    assert copied == []
    assert not stale.parent.exists()
    assert "will not include crash reporting" in caplog.text


def test_copy_fails_when_runtime_required_but_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="build_crash_runtime.py"):
        setup_hook.copy_crash_runtime(tmp_path / "missing", tmp_path / "build_lib", required=True)


@pytest.mark.parametrize("platform", sorted(WHEEL_PLATFORMS))
def test_wheel_with_complete_runtime_passes(tmp_path, platform):
    wheel = _write_wheel(tmp_path, platform, crash_runtime.RUNTIME_FILES[platform])
    validate_dist.validate_wheel(wheel, expect_crash_runtime=True)


def test_wheel_without_runtime_passes_unless_required(tmp_path):
    wheel = _write_wheel(tmp_path, "win32")
    validate_dist.validate_wheel(wheel)
    with pytest.raises(ValueError, match="expected crash runtime"):
        validate_dist.validate_wheel(wheel, expect_crash_runtime=True)


def test_wheel_with_partial_runtime_fails_even_when_not_required(tmp_path):
    wheel = _write_wheel(tmp_path, "linux", ("libsentry.so",))
    with pytest.raises(ValueError, match="expected crash runtime"):
        validate_dist.validate_wheel(wheel)


def test_posix_wheel_requires_executable_handler(tmp_path):
    wheel = _write_wheel(tmp_path, "linux", crash_runtime.RUNTIME_FILES["linux"], 0o644)
    with pytest.raises(ValueError, match="not executable"):
        validate_dist.validate_wheel(wheel, expect_crash_runtime=True)


def test_sdist_rejects_build_artifacts(tmp_path):
    validate_dist.validate_sdist(_write_sdist(tmp_path, ("prismqml/builder.py",)))
    for index, name in enumerate((".artifacts/cpp/x.dll", "build/lib/a.py", "dist/a.whl",
                                  "prismqml/_native/crash/sentry.dll")):
        case_dir = tmp_path / f"case{index}"
        case_dir.mkdir()
        with pytest.raises(ValueError, match="build artifacts"):
            validate_dist.validate_sdist(_write_sdist(case_dir, (name,)))
