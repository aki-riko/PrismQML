# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""FluentQML Python bindings"""

import os

# Suppress Qt font database warnings
if "QT_LOGGING_RULES" not in os.environ:
    os.environ["QT_LOGGING_RULES"] = "qt.text.font.db=false"
