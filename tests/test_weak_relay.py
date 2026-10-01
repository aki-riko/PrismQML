# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Weak relay lifetime contracts. 弱引用中继生命周期合同。"""

import gc
import weakref

import pytest
import shiboken6
from PySide6.QtCore import QObject

from prismqml.python.core._weak_relay import WeakMethodRelay


class _Receiver(QObject):
    def __init__(self):
        super().__init__()
        self.values = []

    def receive(self, value):
        self.values.append(value)

    def fail(self):
        raise RuntimeError("relay target failure")


def test_relay_forwards_arguments_to_live_qobject():
    receiver = _Receiver()
    relay = WeakMethodRelay(receiver, "receive")

    relay("live")

    assert receiver.values == ["live"]


def test_relay_skips_deleted_qobject_with_live_python_wrapper():
    receiver = _Receiver()
    relay = WeakMethodRelay(receiver, "receive")
    shiboken6.delete(receiver)
    assert not shiboken6.isValid(receiver)

    relay("deleted")

    assert receiver.values == []


def test_relay_does_not_retain_receiver():
    receiver = _Receiver()
    reference = weakref.ref(receiver)
    relay = WeakMethodRelay(receiver, "receive")
    del receiver
    gc.collect()

    assert reference() is None
    relay("collected")


def test_relay_preserves_live_target_exceptions():
    receiver = _Receiver()
    relay = WeakMethodRelay(receiver, "fail")

    with pytest.raises(RuntimeError, match="relay target failure"):
        relay()
