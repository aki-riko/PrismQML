# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Icon rewrite caller contracts. 图标重写调用方合同。"""

import pytest
from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QColor, QIcon

from prismqml.python.core import icon_core
from prismqml.python.core.theme import Theme


class _RecordingIcon(icon_core.IconCore):
    """IconCore recording requested themes. 记录主题请求的 IconCore。"""

    def __init__(self, asset_path):
        self.asset_path = asset_path
        self.themes = []

    def path(self, theme=Theme.AUTO):
        self.themes.append(theme)
        return self.asset_path


class _RecordingRenderer:
    """Renderer appending construction and render calls. 记录构造与渲染调用。"""

    calls = None

    def __init__(self, payload):
        self.calls.append(("init", payload))

    def render(self, painter, rect):
        self.calls.append(("render", painter, rect))


def test_make_icon_delegates_color_rewrite(monkeypatch, qapp):
    """make_icon delegates exact tint inputs. make_icon 精确委托着色输入。"""
    del qapp
    calls = []
    payload = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4">'
        '<path d="M0 0 H4 V4 H0 Z" fill="#fedcba"/></svg>'
    )

    def rewrite(path, overrides, *, only_paths=None):
        calls.append((path, overrides, only_paths))
        return payload

    monkeypatch.setattr(icon_core, "_rewrite_svg_attrs", rewrite)
    source = _RecordingIcon("asset.svg")

    result = icon_core.make_icon(source, Theme.DARK, QColor("#12ab34"))

    assert isinstance(result, QIcon)
    assert source.themes == [Theme.DARK]
    assert calls == [("asset.svg", {"fill": "#12ab34"}, None)]
    pixmap = result.pixmap(4, 4)
    assert not pixmap.isNull()
    assert pixmap.toImage().pixelColor(2, 2) == QColor("#fedcba")


def test_paint_icon_delegates_indexes_and_payload(monkeypatch):
    """paint_icon forwards indexes and UTF-8 payload. paint_icon 透传序号与载荷。"""
    rewrite_calls = []
    render_calls = []

    def rewrite(path, overrides, *, only_paths=None):
        rewrite_calls.append((path, overrides, only_paths))
        return "<svg/>"

    _RecordingRenderer.calls = render_calls
    monkeypatch.setattr(icon_core, "_rewrite_svg_attrs", rewrite)
    monkeypatch.setattr(icon_core, "QSvgRenderer", _RecordingRenderer)
    source = _RecordingIcon("asset.svg")
    indexes = iter([1])
    painter = object()
    rect = QRect(1, 2, 3, 4)

    icon_core.paint_icon(
        painter, rect, source, Theme.LIGHT,
        path_indexes=indexes, fill="#abcdef", stroke="#123456",
    )

    assert source.themes == [Theme.LIGHT]
    assert rewrite_calls == [
        ("asset.svg", {"fill": "#abcdef", "stroke": "#123456"}, indexes)
    ]
    assert render_calls == [
        ("init", b"<svg/>"),
        ("render", painter, QRectF(rect)),
    ]


@pytest.mark.parametrize("exception_type", [ValueError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("caller", ["make_icon", "paint_icon"])
def test_public_icon_callers_propagate_rewrite_failure(
    monkeypatch,
    exception_type,
    caller,
):
    """Public callers preserve rewrite errors. 公开调用方保留重写异常。"""
    failure = exception_type("rewrite failure")

    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(icon_core, "_rewrite_svg_attrs", fail)
    source = _RecordingIcon("broken.svg")

    with pytest.raises(exception_type) as caught:
        if caller == "make_icon":
            icon_core.make_icon(source, color=QColor("red"))
        else:
            icon_core.paint_icon(object(), QRect(0, 0, 1, 1), source, fill="red")

    assert caught.value is failure
