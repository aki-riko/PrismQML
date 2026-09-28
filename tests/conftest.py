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

import os
from pathlib import Path

from scripts.test_process import prepare_automated_test_process

# Force automated tests to stay headless and suppress native crash dialogs.
# 强制自动化测试无界面运行，并禁止原生崩溃弹窗。
prepare_automated_test_process(
    "windows" if os.environ.get("PRISMQML_ALLOW_VISIBLE_WINDOWS") == "1" else "offscreen"
)

import pytest


def pytest_addoption(parser):
    """Expose the explicit release gate without changing normal pytest usage.

    日常开发默认走快速回归；发布和 CI 用 ``--full-suite`` 显式恢复完整门禁。
    """
    parser.addoption(
        "--full-suite",
        action="store_true",
        default=False,
        help="运行包含发布级高成本回归在内的完整测试套件",
    )


def pytest_collection_modifyitems(config, items):
    """Keep expensive release gates opt-in for local development."""
    if config.getoption("--full-suite"):
        return
    skip_release = pytest.mark.skip(
        reason="发布级门禁默认跳过；使用 pytest --full-suite 显式运行"
    )
    for item in items:
        item_path = Path(str(item.fspath)).resolve()
        is_qml_runtime = (
            item_path.parent.name == "qml" and "qapp" in item.fixturenames
        )
        if "release" in item.keywords or is_qml_runtime:
            item.add_marker(skip_release)


@pytest.fixture(scope="session")
def qapp():
    """返回进程内唯一的 QApplication 实例（已存在则复用）。

    QApplication 单进程单例，session 级保证全程只创建一次；不主动调用
    quit()，交由进程退出时自然回收，避免提前销毁影响其它用例。
    """
    from prismqml import configure_qml_environment
    from PySide6.QtWidgets import QApplication

    # Enable local translations before the first QApplication or QML engine.
    # 在首个 QApplication 或 QML 引擎前启用本地翻译资源。
    configure_qml_environment()

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
