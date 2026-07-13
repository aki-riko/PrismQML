# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window compatibility error-boundary regressions. 窗口兼容错误边界回归。"""

import pytest


@pytest.mark.parametrize("phase", ["invoke", "fallback"])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_restore_visible_state_process_control_propagates(
    monkeypatch, phase, error_type
):
    import PySide6.QtCore as qt_core
    from prismqml.python.window._window_compat import WindowCompatMixin

    class FakeMetaObject:
        @staticmethod
        def invokeMethod(_window, _method):
            if phase == "invoke":
                raise error_type("stop")
            return True

    class FakeWindow:
        def setOpacity(self, _value):
            raise error_type("stop")

        def setProperty(self, _name, _value):
            return True

        def update(self):
            return None

    monkeypatch.setattr(qt_core, "QMetaObject", FakeMetaObject)
    compat = WindowCompatMixin()
    compat._window = FakeWindow()
    with pytest.raises(error_type, match="stop"):
        compat._restore_visible_state()
