# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
pytest 共享 fixture。

提供自包含的 ``qapp`` fixture：PrismQML 是 GUI 库，部分测试（如 IconBase
的 _bake_pixmap）需要一个就绪的 QApplication 才能构造 QPainter / 烘焙
QPixmap。pytest-qt 插件本身会提供同名 ``qapp`` fixture，但当运行命令带
``-p no:pytest-qt`` 禁用插件时，该 fixture 会消失，导致这些测试在 setup
阶段报 ``fixture 'qapp' not found``（ERROR at setup，而非断言失败）。

这里在 conftest 自定义同名 fixture 后，无论 pytest-qt 是否启用都能拿到
QApplication，从而让测试套件自包含、运行命令无关。
"""

import pytest


@pytest.fixture(scope="session")
def qapp():
    """返回进程内唯一的 QApplication 实例（已存在则复用）。

    QApplication 单进程单例，session 级保证全程只创建一次；不主动调用
    quit()，交由进程退出时自然回收，避免提前销毁影响其它用例。
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
