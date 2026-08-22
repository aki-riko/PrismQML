# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FlowLayout modularity gates. FlowLayout 模块化门禁。"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FLOW_LAYOUT = (
    REPO_ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Layout"
    / "FlowLayout.qml"
)
FLOW_ENGINE = FLOW_LAYOUT.with_name("FlowLayoutEngine.js")
FLOW_GEOMETRY = FLOW_LAYOUT.with_name("FlowLayoutGeometry.js")


def test_flow_layout_keeps_entry_and_engine_below_size_limit():
    assert len(FLOW_LAYOUT.read_text(encoding="utf-8").splitlines()) < 500
    assert len(FLOW_ENGINE.read_text(encoding="utf-8").splitlines()) < 500


def test_flow_layout_preserves_qml_proxy_contract():
    source = FLOW_LAYOUT.read_text(encoding="utf-8")
    engine_source = FLOW_ENGINE.read_text(encoding="utf-8")

    assert 'import "FlowLayoutEngine.js" as FlowLayoutEngine' in source
    for method in (
        "_placeDefaultItem",
        "_performLayout",
        "_layoutDefault",
        "_findBestPosition",
        "_usesSlidingWindow",
        "_layoutHorizontal",
        "_calculateRows",
        "_layoutVertical",
        "_calculateAutoColumnCount",
    ):
        assert f"function {method}(" in source
    assert "function _getEngineState(name)" in source
    assert "function _setEngineState(name, value)" in source
    assert "function getState(layout, name)" in engine_source
    assert "function setState(layout, name, value)" in engine_source
    assert "FlowLayoutGeometry.js" not in source


def test_flow_layout_geometry_stays_deleted():
    """滑窗几何只允许留在 FlowLayoutEngine.js 里。

    The sliding-window geometry has exactly one home: FlowLayoutEngine.js. The
    removed FlowLayoutGeometry.js duplicated it with no consumer, so this gate
    keeps the dead copy from coming back.
    """
    assert not FLOW_GEOMETRY.exists()

    engine_source = FLOW_ENGINE.read_text(encoding="utf-8")
    assert "function findBestSlidingPosition(" in engine_source

    for path in FLOW_LAYOUT.parent.rglob("*"):
        if path.is_file():
            assert path.name != "FlowLayoutGeometry.js"
