# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphic inset shader source regressions. 新拟态内阴影着色器源码回归。"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
LAYER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "effects"
    / "_internal"
    / "NeumorphicInsetLayer.qml"
)
SHADER_PATH = ROOT / "prismqml" / "PrismQML" / "shaders" / "neumorphic_inset.frag"
SHADER_BINARY_PATH = SHADER_PATH.with_suffix(".frag.qsb")


def test_inset_shadow_strength_uses_shared_subtle_opacity():
    metrics_source = METRICS_PATH.read_text(encoding="utf-8")
    assert "insetNormalSampleStep: root.spacing.micro" in metrics_source
    assert "insetDarkOpacity: root.opacity.light" in metrics_source
    assert "insetLightOpacity: root.opacity.light" in metrics_source


def test_inset_shader_uses_smooth_directional_falloff():
    shader_source = SHADER_PATH.read_text(encoding="utf-8")
    assert "shadowDepth + softness" in shader_source
    assert "1.0 - smoothstep(0.0, edgeRange, insideDepth)" in shader_source
    assert "dot(outwardNormal, lightDirection)" in shader_source
    assert "insideDepth > softness" not in shader_source
    assert "max(-outwardNormal.x, -outwardNormal.y)" not in shader_source


def test_inset_layer_binds_sample_step_and_precompiled_shader():
    layer_source = LAYER_PATH.read_text(encoding="utf-8")
    assert "property real normalSampleStep: Enums.neumorphism.insetNormalSampleStep" in layer_source
    assert 'fragmentShader: Qt.resolvedUrl("../../shaders/neumorphic_inset.frag.qsb")' in layer_source
    assert SHADER_BINARY_PATH.is_file()
    assert SHADER_BINARY_PATH.stat().st_size > 0
