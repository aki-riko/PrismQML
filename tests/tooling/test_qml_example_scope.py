# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Examples-only QML010 scanner scope regressions. examples 仅 QML010 扫描范围回归。"""

from pathlib import Path, PurePosixPath
import subprocess

from scripts import qml_conventions as scanner


ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments], cwd=root, check=True, text=True,
        encoding="utf-8", capture_output=True,
    )


def _initialize_repo(root: Path) -> Path:
    library = root / "prismqml" / "PrismQML" / "Valid.qml"
    example = root / "examples" / "Page.qml"
    library.parent.mkdir(parents=True)
    example.parent.mkdir(parents=True)
    library.write_text("import QtQuick\nItem {}\n", encoding="utf-8")
    example.write_text(
        "import QtQuick 2.15\nItem {\n    property int radius: 4\n}\n",
        encoding="utf-8",
    )
    _git(root, "init")
    _git(root, "config", "user.name", "PrismQML Test")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    return example


def test_repository_scans_examples_for_qml010_only(tmp_path):
    example = _initialize_repo(tmp_path)
    example.write_text(
        "import QtQuick 2.15\nItem {\n"
        "    property int radius: 4\n"
        "    color: \"#ffffff\"\n"
        "    Rectangle {}\n"
        "    property string late: \"\"\n"
        "}\n",
        encoding="utf-8",
    )

    violations = scanner.scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in violations] == [
        (PurePosixPath("examples/Page.qml"), "QML010")
    ]


def test_changed_mode_tracks_only_example_qml010_deltas(tmp_path):
    example = _initialize_repo(tmp_path)
    example.write_text(
        example.read_text(encoding="utf-8").replace(
            "Item {", 'Item {\n    color: "#ffffff"'
        ),
        encoding="utf-8",
    )

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert result.base_total == 0
    assert result.current_total == 1
    assert [(item.path, item.rule) for item in result.violations] == [
        (PurePosixPath("examples/Page.qml"), "QML010")
    ]


def test_changed_mode_scans_untracked_examples_with_the_same_scope(tmp_path):
    _initialize_repo(tmp_path)
    example = tmp_path / "examples" / "New.qml"
    example.write_text(
        "import QtQuick 2.15\nItem {\n"
        "    property int radius: 4\n"
        "    color: \"#ffffff\"\n"
        "}\n",
        encoding="utf-8",
    )

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert [(item.path, item.rule) for item in result.violations] == [
        (PurePosixPath("examples/New.qml"), "QML010")
    ]


def test_changed_mode_maps_renamed_example_baselines(tmp_path):
    example = _initialize_repo(tmp_path)
    example.write_text(
        example.read_text(encoding="utf-8").replace(
            "Item {", 'Item {\n    color: "#111111"'
        ),
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "example color baseline")
    renamed = example.with_name("Renamed.qml")
    _git(
        tmp_path, "mv",
        str(example.relative_to(tmp_path)), str(renamed.relative_to(tmp_path)),
    )
    renamed.write_text(
        renamed.read_text(encoding="utf-8").replace(
            '    color: "#111111"',
            '    color: "#111111"\n    border.color: "#222222"',
        ),
        encoding="utf-8",
    )

    result = scanner.scan_changed(tmp_path, "HEAD")

    assert result.changed_files == 1
    assert result.base_total == 1
    assert result.current_total == 2
    assert [(item.path, item.rule) for item in result.violations] == [
        (PurePosixPath("examples/Renamed.qml"), "QML010")
    ]


def test_repository_examples_have_no_qml010_inventory():
    violations = [
        item
        for item in scanner.scan_repository(ROOT)
        if item.path.parts and item.path.parts[0] == "examples"
    ]

    assert violations == []
