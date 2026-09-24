# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""OpacityMask wiring contract. OpacityMask 接线合同。

Qt 6.11.2 实测: MultiEffect 遮罩经 layer.effect 安装时静默失效 —— 四种接线
(内联子项 / 属性赋值 / ShaderEffectSource / 停靠分层遮罩) 对真实渲染像素验证过,
输出与完全不挂遮罩一致。因此禁止再用 layer.effect 安装遮罩: 它不会报错, 只会
悄悄什么也不做。需要遮罩时必须改用独立写法 (source + 可见且开启 layer.enabled
的硬边遮罩), 并且连续 alpha 渐变不会产生按比例淡出。
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
OPACITY_MASK_PATH = QML_ROOT / "effects" / "OpacityMask.qml"
BROKEN_WIRING = "layer.effect: OpacityMask"
BROKEN_WIRING_COMPACT = "layer.effect:OpacityMask"


def _qml_sources():
    return sorted(QML_ROOT.rglob("*.qml"))


def test_no_qml_installs_opacity_mask_through_layer_effect():
    offenders = []
    for path in _qml_sources():
        source = path.read_text(encoding="utf-8")
        if BROKEN_WIRING in source or BROKEN_WIRING_COMPACT in source:
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == [], (
        "layer.effect: OpacityMask is a silent no-op in Qt 6.11 "
        "(no masking, no warning). Use a standalone MultiEffect with source instead. "
        "Offenders 违规文件: " + ", ".join(offenders)
    )


def test_opacity_mask_documents_the_verified_limit():
    source = OPACITY_MASK_PATH.read_text(encoding="utf-8")

    assert "VERIFIED LIMIT (Qt 6.11.2)" in source
    assert "silent no-op" in source
    assert "layer.enabled" in source
    assert "NOT SUPPORTED" in source


def test_opacity_mask_keeps_binary_threshold_defaults():
    source = OPACITY_MASK_PATH.read_text(encoding="utf-8")

    # The verified working configuration for hard-edged masks.
    assert "maskEnabled: root.mask !== null" in source
    assert "maskSource: root.mask" in source
    assert "maskThresholdMin: root.invert ? 0.5 : 0.0" in source
    assert "maskSpreadAtMin: 1.0" in source
