# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Outside Drawer native-window contracts. 外侧抽屉原生窗口合同。"""

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Drawer"
    / "Drawer.qml"
)


def test_drawer_source_follows_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_drawer_source_uses_clipped_native_window_following():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "Qt.NoFluentShadowWindowHint" not in source
    assert "Qt.NoDropShadowWindowHint" not in source
    assert "_outsideShadowExtent" not in source
    assert 'objectName: "outsideDrawerShadow"' not in source
    assert "ShadowManager.enableShadowForWindow(outsideDrawerWindow)" in source
    assert "MicaManager.setWindowCorner(outsideDrawerWindow, true)" in source
    assert "id: outsideOpeningTimer" not in source
    assert "id: outsideVisibilityTimer" not in source
    assert "Behavior on width" not in source
    assert "Behavior on height" not in source
    assert 'id: outsideGeometryAnimation' in source
    assert 'property: "_outsideExtent"' in source
    assert 'objectName: "outsideDrawerViewport"' in source
    assert "clip: true" in source
    assert "on_OutsideExtentChanged" not in source
    assert "control._syncOutsideWindowGeometry()" not in source
    assert source.count("WindowHelper.updateWindowFollowerGeometry(") == 1
    assert "WindowHelper.registerWindowFollower(" in source
    assert "WindowHelper.unregisterWindowFollower(outsideDrawerWindow)" in source
    assert "ShadowManager.disableShadowForWindow(outsideDrawerWindow)" in source


def test_drawer_source_keeps_native_window_behind_host_without_overlap():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "transientParent: null" in source
    assert "outsideDrawerWindow.requestActivate()" not in source
    assert "_outsideSeamOverlap" not in source
    assert "? Enums.radius.large" in source
    assert "topLeftRadius:" in source
    assert "topRightRadius:" in source
    assert "bottomLeftRadius:" in source
    assert "bottomRightRadius:" in source


def test_drawer_source_guards_native_window_during_destruction():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "if (outsideDrawerWindow" in source
    assert "|| !outsideDrawerWindow" in source
    assert "outsideDrawerWindow ? outsideDrawerWindow.width : 0" in source
    assert "outsideDrawerWindow ? outsideDrawerWindow.height : 0" in source
    assert "outsideDrawerViewport ? -outsideDrawerViewport.x : 0" in source
    assert "outsideDrawerViewport ? -outsideDrawerViewport.y : 0" in source


def test_drawer_source_reveals_from_the_corresponding_edge():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "x: control.position === Enums.position.left\n                ? 0\n                : (outsideDrawerWindow" in source
    assert "y: control.position === Enums.position.top\n                ? 0\n                : (outsideDrawerWindow" in source
