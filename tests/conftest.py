# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""
pytest 共享 fixture。

提供自包含的 ``qapp`` fixture：PrismQML 是 GUI 库，部分测试（如 IconCore
的 _bake_pixmap）需要一个就绪的 QApplication 才能构造 QPainter / 烘焙
QPixmap。pytest-qt 插件本身会提供同名 ``qapp`` fixture，但当运行命令带
``-p no:pytest-qt`` 禁用插件时，该 fixture 会消失，导致这些测试在 setup
阶段报 ``fixture 'qapp' not found``（ERROR at setup，而非断言失败）。

pyproject.toml 在加载第三方插件前执行边界引导；这里自定义同名 fixture，
让统一 runner 入口下的测试套件不依赖 pytest-qt 也能拿到 QApplication。
"""

from scripts.test_process import prepare_automated_test_process

# Force automated tests to stay headless and suppress native crash dialogs.
# 强制自动化测试无界面运行，并禁止原生崩溃弹窗。
prepare_automated_test_process()

from prismqml import configure_qml_environment

# Enable local translation resources before the suite creates its first QML engine.
# 在测试套件创建首个 QML 引擎前启用本地翻译资源。
configure_qml_environment()

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
