# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Early pytest boundary bootstrap. pytest 早期进程边界引导。"""

from scripts.test_process import prepare_automated_test_process


# Loaded through pytest addopts before third-party pytest11 entry points.
# 由 pytest addopts 在第三方 pytest11 入口插件之前加载。
prepare_automated_test_process()
