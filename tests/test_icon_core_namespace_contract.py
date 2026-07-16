# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SVG namespace attribute contracts. SVG 命名空间属性合同。"""

import xml.etree.ElementTree as ElementTree

from PySide6.QtSvg import QSvgRenderer

from prismqml.python.core.icon_core import _rewrite_svg_attrs


def test_rewritten_path_keeps_prefixed_attributes(tmp_path):
    """Target paths retain qualified attributes. 目标 path 保留限定属性。"""
    svg_file = tmp_path / "qualified-attribute.svg"
    svg_file.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:m="urn:prismqml:meta">'
        '<path m:note="keep" fill="old" d="M0 0"/>'
        '</svg>',
        encoding="utf-8",
    )

    rewritten = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})

    path = ElementTree.fromstring(rewritten)[0]
    assert path.attrib["{urn:prismqml:meta}note"] == "keep"
    assert path.attrib["fill"] == "#ff0000"
    assert QSvgRenderer(rewritten.encode("utf-8")).isValid()
