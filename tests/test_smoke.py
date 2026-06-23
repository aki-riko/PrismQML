# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。

import prismqml


def test_import_prismqml():
    assert hasattr(prismqml, "__version__")


def test_qml_path_exists():
    from prismqml import qml_path

    path = qml_path()
    assert path.exists()
