# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SVG rewrite boundary contracts. SVG 重写边界合同。"""

import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest
from PySide6.QtCore import QFile, QResource
from PySide6.QtSvg import QSvgRenderer

from prismqml.python.core.icon_core import _rewrite_svg_attrs


_GALLERY_RCC = Path(__file__).parents[1] / "examples" / "resources" / "gallery.rcc"


@pytest.mark.parametrize(
    "malformed",
    [
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/>',
        '<svg xmlns="http://www.w3.org/2000/svg"><g></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" fill="a" fill="b"/>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="&missing;"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"/><extra/>',
    ],
)
def test_malformed_svg_never_returns_partial_output(tmp_path, malformed):
    """Malformed XML must fail loudly. 畸形 XML 不得静默泄漏半截输出。"""
    svg_file = tmp_path / "malformed.svg"
    svg_file.write_text(malformed, encoding="utf-8")

    with pytest.raises(ValueError) as caught:
        _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})

    message = str(caught.value)
    assert svg_file.name in message
    assert "line=" in message
    assert "column=" in message
    svg_file.unlink()


def test_prefixed_svg_elements_keep_their_namespace(tmp_path):
    """Qualified SVG elements keep identity. 带前缀 SVG 元素保持命名空间身份。"""
    namespace = "http://www.w3.org/2000/svg"
    svg_file = tmp_path / "prefixed.svg"
    svg_file.write_text(
        '<s:svg xmlns:s="http://www.w3.org/2000/svg" '
        'viewBox="0 0 10 10" width="10" height="10">'
        '<s:path d="M0 0 H10 V10 H0 Z" fill="#000000"/>'
        '</s:svg>',
        encoding="utf-8",
    )

    rewritten = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})

    root = ElementTree.fromstring(rewritten)
    assert root.tag == f"{{{namespace}}}svg"
    assert root[0].tag == f"{{{namespace}}}path"
    assert root[0].attrib["fill"] == "#ff0000"
    assert QSvgRenderer(rewritten.encode("utf-8")).isValid()


def test_foreign_path_does_not_consume_svg_path_index(tmp_path):
    """Only SVG paths are indexed. 外部命名空间 path 不得占用 SVG 序号。"""
    svg_namespace = "http://www.w3.org/2000/svg"
    metadata_namespace = "urn:prismqml:test-metadata"
    svg_file = tmp_path / "foreign-path.svg"
    svg_file.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:m="urn:prismqml:test-metadata">'
        '<m:path fill="metadata"/>'
        '<path id="first" fill="first"/>'
        '<path id="second" fill="second"/>'
        '</svg>',
        encoding="utf-8",
    )

    rewritten = _rewrite_svg_attrs(
        str(svg_file),
        {"fill": "#ff0000"},
        only_paths=[0],
    )

    children = list(ElementTree.fromstring(rewritten))
    assert [child.tag for child in children] == [
        f"{{{metadata_namespace}}}path",
        f"{{{svg_namespace}}}path",
        f"{{{svg_namespace}}}path",
    ]
    assert [child.attrib["fill"] for child in children] == [
        "metadata",
        "#ff0000",
        "second",
    ]


def test_explicit_empty_namespace_path_does_not_consume_svg_index(tmp_path):
    """Namespace reset paths stay foreign. 显式清空命名空间的 path 保持外部身份。"""
    svg_file = tmp_path / "empty-namespace-path.svg"
    svg_file.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<g xmlns=""><path id="foreign" fill="metadata"/></g>'
        '<path id="svg" fill="original"/>'
        '</svg>',
        encoding="utf-8",
    )

    rewritten = _rewrite_svg_attrs(
        str(svg_file),
        {"fill": "#ff0000"},
        only_paths=[0],
    )

    root = ElementTree.fromstring(rewritten)
    foreign_path = root[0][0]
    svg_path = root[1]
    assert foreign_path.tag == "path"
    assert foreign_path.attrib["fill"] == "metadata"
    assert svg_path.tag == "{http://www.w3.org/2000/svg}path"
    assert svg_path.attrib["fill"] == "#ff0000"


def test_legacy_unnamespaced_svg_paths_remain_rewritable(tmp_path):
    """Legacy SVGs without xmlns remain supported. 无 xmlns 的旧 SVG 仍可重写。"""
    svg_file = tmp_path / "legacy.svg"
    svg_file.write_text(
        '<svg viewBox="0 0 1 1"><path fill="original"/></svg>',
        encoding="utf-8",
    )

    rewritten = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})

    root = ElementTree.fromstring(rewritten)
    assert root.tag == "svg"
    assert root[0].tag == "path"
    assert root[0].attrib["fill"] == "#ff0000"


def test_qrc_url_rewrites_registered_svg_resource():
    """Documented qrc paths stay readable. 文档声明的 qrc 路径可正常重写。"""
    assert QResource.registerResource(str(_GALLERY_RCC))
    try:
        assert QFile.exists(":/app_icon.svg")

        rewritten = _rewrite_svg_attrs(
            "qrc:/app_icon.svg",
            {"fill": "#ff0000"},
        )

        assert "#ff0000" in rewritten
        assert QSvgRenderer(rewritten.encode("utf-8")).isValid()
    finally:
        assert QResource.unregisterResource(str(_GALLERY_RCC))
