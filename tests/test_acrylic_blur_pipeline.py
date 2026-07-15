# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic blur pipeline contracts. 亚克力模糊流水线合同。"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from prismqml.python.window import mica_window


_FAILURE_STAGES = (
    "image.is_null",
    "image.convert",
    "converted.width",
    "converted.height",
    "pixmap.from_image",
    "pixmap.source.scaled",
    "pixmap.small.scaled",
    "pixmap.result.to_image",
)


class _ImageProbe:
    def __init__(self, probe):
        self._probe = probe

    def isNull(self):
        self._probe.step("image.is_null")
        return self._probe.null_image

    def convertToFormat(self, image_format):
        self._probe.step("image.convert", image_format)
        return self._probe.converted


class _ConvertedProbe:
    def __init__(self, probe):
        self._probe = probe

    def width(self):
        self._probe.step("converted.width")
        return self._probe.width

    def height(self):
        self._probe.step("converted.height")
        return self._probe.height


class _PixmapProbe:
    def __init__(self, probe, name):
        self._probe = probe
        self._name = name

    def scaled(self, *arguments):
        self._probe.step(f"pixmap.{self._name}.scaled", *arguments)
        if self._name == "source":
            return self._probe.small_pixmap
        return self._probe.result_pixmap

    def toImage(self):
        self._probe.step(f"pixmap.{self._name}.to_image")
        return self._probe.output_image


class _BlurProbe:
    def __init__(self, width=17, height=11, null_image=False, failure=None):
        self.width = width
        self.height = height
        self.null_image = null_image
        self.failure = failure
        self.events = []
        self.image = _ImageProbe(self)
        self.converted = _ConvertedProbe(self)
        self.source_pixmap = _PixmapProbe(self, "source")
        self.small_pixmap = _PixmapProbe(self, "small")
        self.result_pixmap = _PixmapProbe(self, "result")
        self.output_image = object()

    def step(self, stage, *values):
        self.events.append((stage, *values))
        if self.failure and self.failure[0] == stage:
            raise self.failure[1]

    def from_image(self, image):
        self.step("pixmap.from_image", image)
        return self.source_pixmap

    def install(self, monkeypatch):
        pixmap_api = type("PixmapApi", (), {"fromImage": staticmethod(self.from_image)})
        monkeypatch.setattr(mica_window, "QPixmap", pixmap_api)


def _run(probe, monkeypatch, radius):
    probe.install(monkeypatch)
    return mica_window._gaussian_blur_image(probe.image, radius)


@pytest.mark.parametrize(
    ("radius", "width", "height", "small_size"),
    (
        (1, 17, 11, (8, 5)),
        (7, 17, 11, (8, 5)),
        (8, 17, 11, (8, 5)),
        (11, 17, 11, (8, 5)),
        (12, 17, 11, (5, 3)),
        (31, 17, 11, (2, 1)),
        (100, 3, 2, (1, 1)),
        (8, 1, 17, (1, 8)),
        (8, 17, 1, (8, 1)),
    ),
)
def test_blur_pipeline_preserves_scaling_order_and_arguments(
    monkeypatch, radius, width, height, small_size
):
    probe = _BlurProbe(width=width, height=height)

    result = _run(probe, monkeypatch, radius)

    scale_args = (
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    assert result is probe.output_image
    assert probe.events == [
        ("image.is_null",),
        ("image.convert", QImage.Format.Format_ARGB32),
        ("converted.width",),
        ("converted.height",),
        ("pixmap.from_image", probe.converted),
        ("pixmap.source.scaled", *small_size, *scale_args),
        ("pixmap.small.scaled", width, height, *scale_args),
        ("pixmap.result.to_image",),
    ]


@pytest.mark.parametrize(("null_image", "radius"), ((True, 8), (False, 0), (False, -1)))
def test_blur_guard_returns_original_image(monkeypatch, null_image, radius):
    probe = _BlurProbe(null_image=null_image)

    result = _run(probe, monkeypatch, radius)

    assert result is probe.image
    assert probe.events == [("image.is_null",)]


@pytest.mark.parametrize(("width", "height"), ((0, 11), (17, 0), (0, 0)))
def test_zero_converted_dimension_returns_original_image(
    monkeypatch, width, height
):
    probe = _BlurProbe(width=width, height=height)

    result = _run(probe, monkeypatch, 8)

    assert result is probe.image
    assert probe.events == [
        ("image.is_null",),
        ("image.convert", QImage.Format.Format_ARGB32),
        ("converted.width",),
        ("converted.height",),
    ]


@pytest.mark.parametrize("stage", _FAILURE_STAGES)
@pytest.mark.parametrize(
    "error_type", (ValueError, OSError, RuntimeError, KeyboardInterrupt, SystemExit)
)
def test_blur_pipeline_propagates_failures_by_identity(
    monkeypatch, stage, error_type
):
    failure = error_type(f"failure at {stage}")
    probe = _BlurProbe(failure=(stage, failure))

    with pytest.raises(error_type) as caught:
        _run(probe, monkeypatch, 8)

    assert caught.value is failure
    assert probe.events[-1][0] == stage
