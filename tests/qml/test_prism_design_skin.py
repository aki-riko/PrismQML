# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design skin token and component smoke tests."""

from prismqml import Skin, Theme, setSkin, setTheme

from test_prism_design_skin_core import verify_light_core
from test_prism_design_skin_gallery import verify_dark_gallery, verify_light_gallery
from test_prism_design_skin_inputs import verify_light_inputs_and_surfaces
from test_prism_design_skin_support import SkinTestContext


def test_prism_design_skin_tokens_and_controls(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)
    context = SkinTestContext()

    try:
        verify_light_core(context)
        verify_light_inputs_and_surfaces(context)
        verify_light_gallery(context)
        setTheme(Theme.DARK)
        verify_dark_gallery(context)
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
