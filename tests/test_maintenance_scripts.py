# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Regression tests for destructive maintenance scripts. 维护脚本回归测试。"""

import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts import copy_all_icons, extract_icons, extract_translations


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALID_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>'
BATCH_SCRIPTS = (
    "build.bat",
    "build_android.bat",
    "build_android_x64.bat",
    "build_android_apk.bat",
    "build_apk.bat",
)


def _write_svg(source_dir: Path, name: str, content: str = VALID_SVG) -> None:
    svg_dir = source_dir / name / "SVG"
    svg_dir.mkdir(parents=True)
    (svg_dir / f"{name}_20_regular.svg").write_text(content, encoding="utf-8")


def _existing_outputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    target = tmp_path / "output" / "fluent"
    target.mkdir(parents=True)
    (target / "Keep.svg").write_text(VALID_SVG, encoding="utf-8")
    python_output = tmp_path / "output" / "icons.py"
    qml_output = tmp_path / "output" / "Icons.qml"
    python_output.write_bytes(b"old python\n")
    qml_output.write_bytes(b"old qml\n")
    return target, python_output, qml_output


def _snapshot_path(path: Path):
    if path.is_file():
        return ("file", path.read_bytes())
    files = tuple(
        (item.relative_to(path).as_posix(), item.read_bytes())
        for item in sorted(path.rglob("*"))
        if item.is_file()
    )
    return ("dir", files)


def _snapshot_outputs(outputs: tuple[Path, Path, Path]):
    return tuple(_snapshot_path(path) for path in outputs)


def _sync(source: Path, outputs: tuple[Path, Path, Path], **kwargs) -> int:
    return copy_all_icons.sync_icons(
        source,
        outputs[0],
        outputs[1],
        outputs[2],
        minimum_icons=kwargs.pop("minimum_icons", 1),
        required_icons=kwargs.pop("required_icons", ()),
        **kwargs,
    )


def test_missing_icon_source_preserves_existing_outputs(tmp_path):
    outputs = _existing_outputs(tmp_path)
    before = _snapshot_outputs(outputs)

    with pytest.raises(FileNotFoundError):
        _sync(tmp_path / "missing", outputs)

    assert _snapshot_outputs(outputs) == before


def test_damaged_icon_source_preserves_existing_outputs(tmp_path):
    source = tmp_path / "assets"
    _write_svg(source, "Broken", "<svg><broken>")
    outputs = _existing_outputs(tmp_path)
    before = _snapshot_outputs(outputs)

    with pytest.raises(ValueError, match="invalid SVG XML"):
        _sync(source, outputs)

    assert _snapshot_outputs(outputs) == before


def test_interrupted_icon_copy_preserves_existing_outputs(tmp_path):
    source = tmp_path / "assets"
    _write_svg(source, "Interrupted")
    outputs = _existing_outputs(tmp_path)
    before = _snapshot_outputs(outputs)

    def interrupted_copy(_source: Path, _destination: Path):
        raise OSError("forced copy interruption")

    with pytest.raises(OSError, match="forced copy interruption"):
        _sync(source, outputs, copy_file=interrupted_copy)

    assert _snapshot_outputs(outputs) == before
    assert not list(outputs[0].parent.glob(".copy-all-icons-*"))


def test_commit_failure_rolls_back_all_icon_outputs(tmp_path):
    source = tmp_path / "assets"
    _write_svg(source, "Add")
    outputs = _existing_outputs(tmp_path)
    before = _snapshot_outputs(outputs)
    calls = 0

    def fail_once(source_path: Path, destination: Path):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise OSError("forced commit interruption")
        source_path.replace(destination)

    with pytest.raises(OSError, match="forced commit interruption"):
        _sync(source, outputs, mover=fail_once)

    assert _snapshot_outputs(outputs) == before
    assert not list(outputs[0].parent.rglob("*.backup-*"))
    assert not list(outputs[0].parent.glob(".copy-all-icons-*"))


def test_successful_icon_sync_replaces_all_outputs(tmp_path):
    source = tmp_path / "assets"
    _write_svg(source, "Add")
    _write_svg(source, "Search")
    outputs = _existing_outputs(tmp_path)

    count = _sync(source, outputs, minimum_icons=2, required_icons=("Add", "Search"))

    assert count == 2
    assert sorted(path.name for path in outputs[0].glob("*.svg")) == ["Add.svg", "Search.svg"]
    compile(outputs[1].read_text(encoding="utf-8"), str(outputs[1]), "exec")
    qml = outputs[2].read_text(encoding="utf-8")
    assert "import QtQuick\n" in qml
    assert "QtQuick 2.15" not in qml
    assert 'readonly property string search: "Search"' in qml


def test_icon_check_mode_reports_stale_outputs_without_writing(tmp_path):
    source = tmp_path / "assets"
    _write_svg(source, "Add")
    outputs = _existing_outputs(tmp_path)
    before = _snapshot_outputs(outputs)

    with pytest.raises(copy_all_icons.IconSyncMismatch):
        _sync(source, outputs, check=True)

    assert _snapshot_outputs(outputs) == before


def test_icon_generator_targets_current_prism_enum_path():
    qml = extract_icons.generate_qml_icons(["Add", "Search"])

    assert extract_icons.DEFAULT_QML_OUTPUT.parts[-2:] == ("PrismEnums", "Icons.qml")
    assert "FluentEnums" not in qml
    assert "QtQuick 2.15" not in qml


def test_icon_generator_rejects_invalid_and_case_colliding_names():
    with pytest.raises(ValueError, match="invalid Python enum"):
        extract_icons.validate_icon_names(["Bad-Name"])
    with pytest.raises(ValueError, match="duplicate"):
        extract_icons.validate_icon_names(["Add", "add"])


def test_current_translator_external_json_layout_is_valid():
    count = extract_translations.run(
        extract_translations.DEFAULT_QML_INPUT,
        extract_translations.DEFAULT_OUTPUT_DIR,
        check=True,
    )

    assert count == 20


def test_legacy_translation_extraction_is_atomic(tmp_path):
    qml_input = tmp_path / "LegacyTranslator.qml"
    output_dir = tmp_path / "i18n"
    qml_input.write_text(
        'readonly property var translations: ({\n'
        '  "en": {"hello": "Hello", "quoted": "A \\\"quote\\\""},\n'
        '  "zh_CN": {"hello": "你好", "quoted": "引号"}\n'
        '})\n',
        encoding="utf-8",
    )

    assert extract_translations.run(qml_input, output_dir) == 2
    assert '"quoted": "A \\\"quote\\\""' in (output_dir / "en.json").read_text(encoding="utf-8")
    assert extract_translations.run(qml_input, output_dir, check=True) == 2


def test_build_scripts_have_no_personal_absolute_paths():
    for name in BATCH_SCRIPTS:
        content = (PROJECT_ROOT / "cpp" / name).read_text(encoding="utf-8")
        assert re.search(r"[A-Za-z]:\\", content) is None
        assert "%~dp0" in content


def test_android_config_does_not_reparse_ninja_path_through_call():
    for name in ("build_android.bat", "build_android_x64.bat", "build_android_apk.bat"):
        content = (PROJECT_ROOT / "cpp" / name).read_text(encoding="utf-8")
        assert "CMAKE_MAKE_PROGRAM" not in content
        assert 'for %%I in ("%NINJA%") do set "PATH=%%~dpI;' in content


@pytest.mark.skipif(os.name != "nt", reason="Windows batch behavior")
def test_build_scripts_fail_when_required_environment_is_missing():
    environment = os.environ.copy()
    for name in ("PRISM_VCVARS64", "QT_HOST_PATH", "JAVA_HOME", "ANDROID_SDK_ROOT",
                 "ANDROID_NDK_ROOT", "QT_ANDROID_CMAKE", "NINJA"):
        environment.pop(name, None)
    for name in BATCH_SCRIPTS:
        completed = _run_batch(PROJECT_ROOT / "cpp" / name, environment)
        assert completed.returncode == 10
        assert "MISSING_ENV_" in completed.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows batch behavior")
def test_build_environment_accepts_paths_with_parentheses(tmp_path):
    tool = tmp_path / "Program Files (x86)" / "tool.bat"
    tool.parent.mkdir(parents=True)
    tool.write_text("@echo off\nexit /b 0\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["PRISM_TEST_TOOL"] = str(tool)

    completed = subprocess.run(
        ["cmd", "/d", "/c", str(PROJECT_ROOT / "cpp" / "build_env.bat"),
         "require-file", "PRISM_TEST_TOOL"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0


def _run_batch(path: Path, environment: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["cmd", "/d", "/c", str(path)],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=environment,
        check=False,
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows batch behavior")
def test_apk_scripts_propagate_build_failure(tmp_path):
    success = tmp_path / "success.bat"
    failure = tmp_path / "failure.bat"
    success.write_text("@echo off\nexit /b 0\n", encoding="utf-8")
    failure.write_text("@echo off\nexit /b 37\n", encoding="utf-8")
    environment = _fake_android_environment(tmp_path, success, failure)

    for name in ("build_android_x64.bat", "build_android_apk.bat", "build_apk.bat"):
        completed = _run_batch(PROJECT_ROOT / "cpp" / name, environment)
        assert completed.returncode == 12
        assert "BUILD_FAIL" in completed.stdout


def _fake_android_environment(
    tmp_path: Path, qt_cmake: Path, ninja: Path
) -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("java", "sdk", "ndk", "qt-host", "build"):
        (tmp_path / name).mkdir()
    environment.update(
        JAVA_HOME=str(tmp_path / "java"),
        ANDROID_SDK_ROOT=str(tmp_path / "sdk"),
        ANDROID_NDK_ROOT=str(tmp_path / "ndk"),
        QT_HOST_PATH=str(tmp_path / "qt-host"),
        QT_ANDROID_CMAKE=str(qt_cmake),
        NINJA=str(ninja),
        PRISM_ANDROID_BUILD_DIR=str(tmp_path / "build"),
    )
    return environment
