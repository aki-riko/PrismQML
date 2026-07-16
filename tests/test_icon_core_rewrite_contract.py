# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SVG rewrite boundary contracts. SVG 重写边界合同。"""

import inspect
import re
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Iterable, Optional, get_type_hints

import pytest
from PySide6.QtCore import QFile, QResource, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from prismqml.python.core import icon_core
from prismqml.python.core.icon_core import _rewrite_svg_attrs


_GALLERY_RCC = Path(__file__).parents[1] / "examples" / "resources" / "gallery.rcc"


class _FileScenario:
    """Injectable QFile trace. 可注入 QFile 调用轨迹。"""

    def __init__(self):
        self.events = []
        self.payload = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
        self.open_result = True
        self.read_failure = None
        self.close_failure = None
        self.closed = False


class _FakeQFile:
    """QFile substitute backed by one scenario. 由场景驱动的 QFile 替身。"""

    ReadOnly = object()
    scenario = None

    def __init__(self, path):
        self._scenario = type(self).scenario
        self._scenario.events.append(("init", path))

    def open(self, mode):
        assert mode is self.ReadOnly
        self._scenario.events.append(("open", mode))
        return self._scenario.open_result

    def readAll(self):
        self._scenario.events.append(("readAll", None))
        if self._scenario.read_failure is not None:
            raise self._scenario.read_failure
        return self._scenario.payload

    def close(self):
        self._scenario.events.append(("close", None))
        self._scenario.closed = True
        if self._scenario.close_failure is not None:
            raise self._scenario.close_failure


class _OneShotIterable:
    """One-shot iterable with lifecycle checks. 带生命周期检查的一次性迭代器。"""

    def __init__(self, values=(), *, scenario=None, failure=None):
        self.values = values
        self.scenario = scenario
        self.failure = failure
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        assert self.iterations == 1
        if self.scenario is not None:
            assert self.scenario.closed
        if self.failure is not None:
            raise self.failure
        return iter(self.values)


class _RaisingItemsMapping:
    """Mapping whose items lookup raises. items 查询抛错的映射。"""

    def __init__(self, scenario, failure):
        self.scenario = scenario
        self.failure = failure

    def items(self):
        assert self.scenario.closed
        raise self.failure


class _Stringable:
    """Object exposing one controlled string form. 暴露受控字符串形式的对象。"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


@pytest.fixture
def file_scenario(monkeypatch):
    """Install an injectable QFile. 安装可注入 QFile。"""
    scenario = _FileScenario()
    _FakeQFile.scenario = scenario
    monkeypatch.setattr(icon_core, "QFile", _FakeQFile)
    return scenario


def _write_svg(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def _render_svg(source):
    renderer = QSvgRenderer(source.encode("utf-8"))
    image = QImage(12, 12, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()
    return renderer, image


def test_rewrite_signature_stays_stable():
    """Internal call shape stays explicit. 内部调用形状保持明确。"""
    signature = inspect.signature(_rewrite_svg_attrs)
    parameters = list(signature.parameters.values())

    assert [parameter.name for parameter in parameters] == [
        "svg_path",
        "overrides",
        "only_paths",
    ]
    assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[2].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters[2].default is None
    assert get_type_hints(_rewrite_svg_attrs) == {
        "svg_path": str,
        "overrides": dict,
        "only_paths": Optional[Iterable[int]],
        "return": str,
    }


def test_non_svg_returns_without_constructing_qfile(monkeypatch):
    """Non-SVG inputs short-circuit before I/O. 非 SVG 输入在 I/O 前短路。"""
    def forbidden_qfile(_path):
        raise AssertionError("QFile must not be constructed")

    monkeypatch.setattr(icon_core, "QFile", forbidden_qfile)

    assert _rewrite_svg_attrs("icon.png", {"fill": "red"}) == ""


def test_unopenable_svg_returns_without_reading(file_scenario):
    """Open failure keeps the empty sentinel. 打开失败保持空串哨兵。"""
    file_scenario.open_result = False

    assert _rewrite_svg_attrs("missing.SVG", {}) == ""
    event_names = [event[0] for event in file_scenario.events]
    assert event_names[:2] == ["init", "open"]
    assert "readAll" not in event_names
    assert file_scenario.events[0][1] == "missing.SVG"


def test_file_closes_before_selection_and_parsing(file_scenario):
    """Input closes before downstream work. 输入文件在后续处理前关闭。"""
    indexes = _OneShotIterable([], scenario=file_scenario)

    rewritten = _rewrite_svg_attrs("valid.svg", {}, only_paths=indexes)

    assert rewritten
    assert indexes.iterations == 1
    assert [event[0] for event in file_scenario.events] == [
        "init",
        "open",
        "readAll",
        "close",
    ]


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_read_failure_propagates_same_object_and_closes(file_scenario, exception_type):
    """Read failures preserve identity and close. 读取失败保持身份并关闭。"""
    failure = exception_type("read failure")
    file_scenario.read_failure = failure

    with pytest.raises(exception_type) as caught:
        _rewrite_svg_attrs("failure.svg", {})

    assert caught.value is failure
    assert file_scenario.closed
    assert [event[0] for event in file_scenario.events] == [
        "init",
        "open",
        "readAll",
        "close",
    ]


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_close_failure_propagates_same_object(file_scenario, exception_type):
    """Close failures preserve identity. 关闭失败保持原异常身份。"""
    failure = exception_type("close failure")
    file_scenario.close_failure = failure

    with pytest.raises(exception_type) as caught:
        _rewrite_svg_attrs("failure.svg", {})

    assert caught.value is failure
    assert file_scenario.closed


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_selection_failure_propagates_after_close(file_scenario, exception_type):
    """Selection failures occur after close. path 选择失败发生在关闭之后。"""
    failure = exception_type("selection failure")
    indexes = _OneShotIterable(scenario=file_scenario, failure=failure)

    with pytest.raises(exception_type) as caught:
        _rewrite_svg_attrs("failure.svg", {}, only_paths=indexes)

    assert caught.value is failure
    assert indexes.iterations == 1


@pytest.mark.parametrize("exception_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_override_failure_propagates_after_close(file_scenario, exception_type):
    """Override failures occur after close. 属性映射失败发生在关闭之后。"""
    failure = exception_type("override failure")
    overrides = _RaisingItemsMapping(file_scenario, failure)

    with pytest.raises(exception_type) as caught:
        _rewrite_svg_attrs("failure.svg", overrides)

    assert caught.value is failure


def test_global_path_selection_and_attribute_order(tmp_path):
    """Path indexes and attribute order stay stable. path 序号与属性顺序保持稳定。"""
    svg_file = _write_svg(
        tmp_path,
        "ordered.svg",
        '<svg xmlns="http://www.w3.org/2000/svg"><defs>'
        '<path id="zero" fill="zero" stroke="zero-stroke" d="M0 0"/>'
        '</defs><g><path id="one" fill="one" d="M1 1"/></g>'
        '<path id="two" fill="two" stroke="two-stroke" d="M2 2"/>'
        '</svg>',
    )
    indexes = _OneShotIterable([2, 0, 2])

    rewritten = _rewrite_svg_attrs(
        str(svg_file),
        {"stroke": "new-stroke", "opacity": "0.5", "fill": "new-fill"},
        only_paths=indexes,
    )

    tags = re.findall(r"<path\b[^>]*", rewritten)
    assert (indexes.iterations, len(tags)) == (1, 3)
    expected = ('fill="new-fill"', 'stroke="new-stroke"', 'opacity="0.5"')
    assert all(value in tags[0] for value in expected)
    positions = [
        tags[0].index(f' {name}="')
        for name in ("fill", "stroke", "d", "opacity")
    ]
    assert positions == sorted(positions)
    assert 'fill="one"' in tags[1] and "opacity=" not in tags[1]
    assert all(value in tags[2] for value in expected)


def test_override_keys_and_values_are_stringified(tmp_path):
    """Override objects use their string forms. 属性对象使用其字符串形式。"""
    svg_file = _write_svg(
        tmp_path,
        "stringify.svg",
        '<svg xmlns="http://www.w3.org/2000/svg"><path/></svg>',
    )

    rewritten = _rewrite_svg_attrs(
        str(svg_file),
        {_Stringable("data-count"): _Stringable("7")},
    )

    root = ElementTree.fromstring(rewritten)
    assert root[0].attrib["data-count"] == "7"


def test_processing_tokens_and_internal_entity_semantics(tmp_path):
    """Supported XML tokens retain order and meaning. XML token 保持顺序与语义。"""
    svg_file = _write_svg(
        tmp_path,
        "tokens.svg",
        '<?xml version="1.0"?><?probe mode="keep"?>'
        '<!DOCTYPE svg [<!ENTITY marker "A &amp; B">]>'
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<!--keep--><style><![CDATA[A < B & C]]></style>'
        '<path data-note="&marker;" fill="old"/>'
        '</svg>',
    )

    rewritten = _rewrite_svg_attrs(str(svg_file), {"fill": "new"})

    tokens = [
        '<?probe mode="keep"?>',
        "<!DOCTYPE svg",
        "<!--keep-->",
        "<![CDATA[A < B & C]]>",
    ]
    assert all(token in rewritten for token in tokens)
    assert [rewritten.index(token) for token in tokens] == sorted(
        rewritten.index(token) for token in tokens
    )
    root = ElementTree.fromstring(rewritten)
    assert root[-1].attrib["data-note"] == "A & B"
    assert root[-1].attrib["fill"] == "new"


def test_namespaced_use_renders_rewritten_pixels(tmp_path, qapp):
    """Rewritten SVG renders real pixels. 重写 SVG 可真实渲染目标像素。"""
    del qapp
    svg_file = _write_svg(
        tmp_path,
        "render.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 12 12">'
        '<defs><path id="shape" d="M2 2 H10 V10 H2 Z" fill="#000000"/></defs>'
        '<use xlink:href="#shape"/></svg>',
    )

    rewritten = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})
    root = ElementTree.fromstring(rewritten)
    use = root[-1]
    renderer, image = _render_svg(rewritten)

    assert use.attrib["{http://www.w3.org/1999/xlink}href"] == "#shape"
    assert renderer.isValid()
    assert image.pixelColor(6, 6) == QColor("#ff0000")
    assert image.pixelColor(0, 0).alpha() == 0


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
    svg_file = _write_svg(
        tmp_path,
        "foreign-path.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:m="urn:prismqml:test-metadata">'
        '<m:path fill="metadata"/>'
        '<path id="first" fill="first"/>'
        '<path id="second" fill="second"/>'
        '</svg>',
    )

    rewritten = _rewrite_svg_attrs(
        str(svg_file), {"fill": "#ff0000"}, only_paths=[0]
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
