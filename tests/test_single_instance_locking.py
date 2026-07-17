# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SingleInstance lock-path characterization. 单实例锁路径特征回归。"""

from __future__ import annotations

import importlib.util
import platform
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest


SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "prismqml"
    / "python"
    / "core"
    / "single_instance.py"
)


class _FakeKernel:
    def __init__(self, handle, last_error):
        self.handle = handle
        self.last_error = last_error
        self.closed = []

    def CreateMutexW(self, _attributes, _owner, _name):
        return self.handle

    def GetLastError(self):
        return self.last_error

    def CloseHandle(self, handle):
        self.closed.append(handle)
        return True


class _FakeSemaphore:
    def __init__(self):
        self.events = []

    def acquire(self):
        self.events.append("acquire")

    def release(self):
        self.events.append("release")


class _FakeSharedMemory:
    def __init__(self, attach_results, create_result=False):
        self.attach_results = list(attach_results)
        self.create_result = create_result
        self.detach_count = 0
        self.create_sizes = []

    def attach(self):
        return self.attach_results.pop(0)

    def create(self, size):
        self.create_sizes.append(size)
        return self.create_result

    def detach(self):
        self.detach_count += 1
        return True


class _FakeSocket:
    def __init__(self, *, connected=True, ready=True, reply=b"ok", read_error=None):
        self.connected = connected
        self.ready = ready
        self.reply = reply
        self.read_error = read_error
        self.events = []
        self._state = 1

    def connectToServer(self, name):
        self.events.append(("connect", name))

    def waitForConnected(self, timeout):
        self.events.append(("wait_connected", timeout))
        return self.connected

    def write(self, payload):
        self.events.append(("write", payload))
        return len(payload)

    def flush(self):
        self.events.append(("flush",))
        return True

    def waitForBytesWritten(self, timeout):
        self.events.append(("wait_written", timeout))
        return True

    def waitForReadyRead(self, timeout):
        self.events.append(("wait_ready", timeout))
        return self.ready

    def readAll(self):
        self.events.append(("read",))
        if self.read_error is not None:
            raise self.read_error
        return self.reply

    def disconnectFromServer(self):
        self.events.append(("disconnect",))
        self._state = 0

    def state(self):
        return self._state

    def waitForDisconnected(self, timeout):
        self.events.append(("wait_disconnected", timeout))
        self._state = 0
        return True


def _load_module(monkeypatch, system_name: str):
    monkeypatch.setattr(platform, "system", lambda: system_name)
    name = f"prismqml.python.core._single_instance_test_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, SOURCE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _instrument(instance, *, alive: bool):
    events = []
    instance._notify_primary = lambda: events.append("notify") or alive
    instance._start_server = lambda: events.append("server")
    instance._on_second_instance = lambda: events.append("callback")
    return events


def _windows_instance(monkeypatch, *, handle, last_error, alive=False):
    module = _load_module(monkeypatch, "Windows")
    kernel = _FakeKernel(handle, last_error)
    monkeypatch.setattr(module, "kernel32", kernel)
    warnings = []
    monkeypatch.setattr(module.logger, "warning", warnings.append)
    instance = module.SingleInstance(f"LockTest.{uuid4().hex}")
    events = _instrument(instance, alive=alive)
    return module, instance, kernel, events, warnings


def _non_windows_instance(
    monkeypatch, *, attach_results, create_result=False, alive=False
):
    module = _load_module(monkeypatch, "Linux")
    shared = _FakeSharedMemory(attach_results, create_result)
    semaphore = _FakeSemaphore()
    monkeypatch.setattr(module, "QSharedMemory", lambda _name: shared)
    monkeypatch.setattr(module, "QSystemSemaphore", lambda *_args: semaphore)
    monkeypatch.setattr(module.SingleInstance, "_fix_crash_residue", lambda _self: None)
    warnings = []
    monkeypatch.setattr(module.logger, "warning", warnings.append)
    instance = module.SingleInstance(f"LockTest.{uuid4().hex}")
    events = _instrument(instance, alive=alive)
    return instance, shared, semaphore, events, warnings


def test_windows_new_mutex_claims_lock_and_starts_server(monkeypatch):
    _module, instance, kernel, events, warnings = _windows_instance(
        monkeypatch, handle=101, last_error=0
    )
    assert instance.try_lock() is True
    assert instance._is_locked is True
    assert instance._mutex_handle == 101
    assert events == ["server"]
    assert kernel.closed == []
    assert warnings == []


def test_windows_live_mutex_notifies_callback_and_closes_handle(monkeypatch):
    module, instance, kernel, events, warnings = _windows_instance(
        monkeypatch, handle=202, last_error=183, alive=True
    )
    assert module.ERROR_ALREADY_EXISTS == 183
    assert instance.try_lock() is False
    assert instance._is_locked is False
    assert instance._mutex_handle is None
    assert events == ["notify", "callback"]
    assert kernel.closed == [202]
    assert warnings == []


def test_windows_stale_mutex_keeps_handle_and_takes_over(monkeypatch):
    _module, instance, kernel, events, warnings = _windows_instance(
        monkeypatch, handle=303, last_error=183, alive=False
    )
    assert instance.try_lock() is True
    assert instance._is_locked is True
    assert instance._mutex_handle == 303
    assert events == ["notify", "server"]
    assert kernel.closed == []
    assert len(warnings) == 1


@pytest.mark.parametrize(
    ("alive", "expected", "detach_count", "events", "warning_count"),
    (
        (True, False, 1, ["notify", "callback"], 0),
        (False, True, 0, ["notify", "server"], 1),
    ),
)
def test_non_windows_existing_segment_distinguishes_live_and_stale(
    monkeypatch, alive, expected, detach_count, events, warning_count
):
    instance, shared, semaphore, actual_events, warnings = _non_windows_instance(
        monkeypatch, attach_results=[True], alive=alive
    )
    assert instance.try_lock() is expected
    assert instance._is_locked is expected
    assert shared.detach_count == detach_count
    assert semaphore.events == ["acquire", "release"]
    assert actual_events == events
    assert len(warnings) == warning_count


@pytest.mark.parametrize(
    ("attach_results", "create_result", "expected", "events", "detach_count"),
    (
        ([False], True, True, ["server"], 0),
        ([False, True], False, False, ["notify", "callback"], 1),
        ([False, False], False, False, [], 0),
    ),
)
def test_non_windows_create_and_race_paths_preserve_current_contract(
    monkeypatch, attach_results, create_result, expected, events, detach_count
):
    instance, shared, semaphore, actual_events, warnings = _non_windows_instance(
        monkeypatch,
        attach_results=attach_results,
        create_result=create_result,
        alive=False,
    )
    assert instance.try_lock() is expected
    assert instance._is_locked is expected
    assert shared.create_sizes == [1]
    assert shared.detach_count == detach_count
    assert semaphore.events == ["acquire", "release"]
    assert actual_events == events
    assert warnings == []


@pytest.mark.parametrize(
    ("connected", "ready", "reply", "read_error", "expected"),
    (
        (False, False, b"", None, False),
        (True, False, b"", None, False),
        (True, True, b"ok", None, True),
        (True, True, b"other", None, False),
        (True, True, b"", OSError("read failed"), False),
    ),
)
def test_notify_primary_ack_matrix(
    monkeypatch, connected, ready, reply, read_error, expected
):
    module = _load_module(monkeypatch, "Windows")
    socket = _FakeSocket(
        connected=connected, ready=ready, reply=reply, read_error=read_error
    )

    class _SocketType:
        LocalSocketState = SimpleNamespace(UnconnectedState=0)

        def __new__(cls):
            return socket

    import PySide6.QtNetwork as qt_network

    monkeypatch.setattr(qt_network, "QLocalSocket", _SocketType)
    instance = module.SingleInstance(f"NotifyTest.{uuid4().hex}")
    assert instance._notify_primary() is expected
    if connected:
        assert ("write", b"activate") in socket.events
        assert ("disconnect",) in socket.events
    else:
        assert socket.events == [
            ("connect", instance._server_name()),
            ("wait_connected", 500),
        ]
