# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic capture public signature contract. 亚克力截图公开签名合同。"""

from inspect import Parameter, signature

from PySide6.QtGui import QWindow

from prismqml.python.window import mica_window


def test_public_slot_and_python_signature_are_preserved():
    sig = signature(mica_window.AcrylicHelper.grabAndBlur)
    params = tuple(sig.parameters.values())
    names = ("self", "window", "x", "y", "width", "height")

    assert tuple(param.name for param in params) == names
    assert all(param.kind is Parameter.POSITIONAL_OR_KEYWORD for param in params)
    assert tuple(param.annotation for param in params[1:]) == (
        QWindow, int, int, int, int
    )
    assert sig.return_annotation is str
    meta = mica_window.AcrylicHelper.staticMetaObject
    index = meta.indexOfMethod("grabAndBlur(QWindow*,int,int,int,int)")
    assert index >= 0
    assert meta.method(index).returnMetaType().name() == "QString"


def test_window_frame_slot_and_python_signature_are_exposed():
    sig = signature(mica_window.AcrylicHelper.grabWindowFrame)
    params = tuple(sig.parameters.values())
    names = ("self", "window", "x", "y", "width", "height")

    assert tuple(param.name for param in params) == names
    assert all(param.kind is Parameter.POSITIONAL_OR_KEYWORD for param in params)
    assert tuple(param.annotation for param in params[1:]) == (
        QWindow, int, int, int, int
    )
    assert sig.return_annotation is str
    meta = mica_window.AcrylicHelper.staticMetaObject
    index = meta.indexOfMethod("grabWindowFrame(QWindow*,int,int,int,int)")
    assert index >= 0
    assert meta.method(index).returnMetaType().name() == "QString"
