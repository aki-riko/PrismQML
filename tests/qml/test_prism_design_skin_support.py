# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared helpers for the Prism Design skin smoke test."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


def rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


class SkinTestContext:
    """Own one engine and retain every component and object until test exit."""

    def __init__(self):
        self.engine = QQmlApplicationEngine()
        register_types(self.engine)
        self.keep = []

    @staticmethod
    def repo_path(*parts):
        return Path(__file__).resolve().parents[2].joinpath(*parts)

    def build(self, qml):
        component = QQmlComponent(self.engine)
        component.setData(qml, QUrl("inline"))
        assert not component.isError(), [
            error.toString() for error in component.errors()
        ]
        item = component.create(self.engine.rootContext())
        assert item is not None, [error.toString() for error in component.errors()]
        self.keep.append((component, item))
        return item

    def load(self, *parts):
        path = self.repo_path(*parts)
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(path)))
        assert not component.isError(), [
            error.toString() for error in component.errors()
        ]
        item = component.create(self.engine.rootContext())
        assert item is not None, [error.toString() for error in component.errors()]
        self.keep.append((component, item))
        return item
