# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater download transaction contracts. 更新下载事务合同。"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtNetwork import QNetworkReply

import prismqml.python.core._updater_download as download_module
from prismqml.python.core.updater import Updater


class _SignalStub:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for callback in tuple(self._callbacks):
            callback(*args)


class _ReplyStub:
    def __init__(self):
        self.downloadProgress = _SignalStub()
        self.readyRead = _SignalStub()
        self.finished = _SignalStub()
        self._data = b""
        self._error = QNetworkReply.NetworkError.NoError
        self.deleted = False
        self.aborted = False
        self.abort_error = None

    def feed(self, data: bytes):
        self._data += data

    def readAll(self):
        data, self._data = self._data, b""
        return data

    def error(self):
        return self._error

    def errorString(self):
        return "network failure"

    def abort(self):
        if self.abort_error is not None:
            raise self.abort_error
        self.aborted = True

    def deleteLater(self):
        self.deleted = True


class _NetworkManagerStub:
    def __init__(self):
        self.replies = []

    def get(self, _request):
        reply = _ReplyStub()
        self.replies.append(reply)
        return reply


class _FaultyFile:
    def __init__(self, wrapped, stage, error_type=OSError):
        self._wrapped = wrapped
        self._stage = stage
        self._error_type = error_type

    @property
    def closed(self):
        return self._wrapped.closed

    def write(self, payload):
        if self._stage == "write":
            return max(0, len(payload) - 1)
        if self._stage == "write-control":
            raise self._error_type("stop")
        return self._wrapped.write(payload)

    def flush(self):
        if self._stage == "flush":
            raise OSError("flush failed")
        return self._wrapped.flush()

    def fileno(self):
        return self._wrapped.fileno()

    def close(self):
        self._wrapped.close()
        if self._stage == "close":
            raise OSError("close failed")


def _finish_download(updater, manager, payload: bytes):
    reply = manager.replies[-1]
    reply.feed(payload)
    reply.readyRead.emit()
    reply.finished.emit()


def test_same_url_downloads_keep_distinct_completed_files(qapp):
    first = Updater("owner/repo", "v1.0.0")
    second = Updater("owner/repo", "v1.0.0")
    first_manager = _NetworkManagerStub()
    second_manager = _NetworkManagerStub()
    first._nam = first_manager
    second._nam = second_manager
    paths = []
    first.downloadFinished.connect(paths.append)
    second.downloadFinished.connect(paths.append)

    try:
        first.downloadUpdate("https://example.test/App-Setup.exe")
        _finish_download(first, first_manager, b"first")
        second.downloadUpdate("https://example.test/App-Setup.exe")
        _finish_download(second, second_manager, b"second")

        assert len(paths) == 2
        assert paths[0] != paths[1]
        assert Path(paths[0]).read_bytes() == b"first"
        assert Path(paths[1]).read_bytes() == b"second"
    finally:
        for path in set(paths):
            Path(path).unlink(missing_ok=True)


def test_finished_callback_commits_tail_without_ready_read(qapp):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    paths = []
    updater.downloadFinished.connect(paths.append)
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    reply = manager.replies[-1]
    reply.feed(b"tail-only")

    try:
        reply.finished.emit()

        assert len(paths) == 1
        assert Path(paths[0]).suffix == ".exe"
        assert Path(paths[0]).read_bytes() == b"tail-only"
    finally:
        for path in paths:
            Path(path).unlink(missing_ok=True)


def test_real_read_only_handle_write_failure_never_reports_success(qapp):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    failures = []
    successes = []
    updater.downloadFailed.connect(failures.append)
    updater.downloadFinished.connect(successes.append)

    updater.downloadUpdate("https://example.test/App-Setup.exe")
    path = Path(updater._download_path)
    try:
        updater._download_file.close()
        path.write_bytes(b"existing")
        updater._download_file = path.open("rb")
        _finish_download(updater, manager, b"new-data")

        assert len(failures) == 1
        assert successes == []
        assert not path.exists()
    finally:
        if updater._download_file is not None and not updater._download_file.closed:
            updater._download_file.close()
        path.unlink(missing_ok=True)


def test_write_failure_with_abort_failure_still_cleans_and_fails(qapp):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    failures = []
    updater.downloadFailed.connect(failures.append)
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    reply = manager.replies[-1]
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)
    updater._download_file = _FaultyFile(updater._download_file, "write")
    reply.abort_error = RuntimeError("abort failed")
    reply.feed(b"payload")

    reply.readyRead.emit()

    assert len(failures) == 1
    assert reply.deleted
    assert not partial_path.exists()
    assert not final_path.exists()


def test_duplicate_download_call_does_not_replace_active_reply(qapp):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager

    try:
        updater.downloadUpdate("https://example.test/first.exe")
        first_reply = updater._download_reply
        first_path = updater._download_path
        updater.downloadUpdate("https://example.test/second.exe")

        assert manager.replies == [first_reply]
        assert updater._download_reply is first_reply
        assert updater._download_path == first_path
    finally:
        if updater._download_file is not None:
            updater._download_file.close()
        Path(updater._download_path).unlink(missing_ok=True)


@pytest.mark.parametrize("stage", ["write", "flush", "close"])
def test_file_stage_failure_cleans_every_path(qapp, stage):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    failures = []
    successes = []
    updater.downloadFailed.connect(failures.append)
    updater.downloadFinished.connect(successes.append)
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)
    updater._download_file = _FaultyFile(updater._download_file, stage)

    _finish_download(updater, manager, b"payload")

    assert len(failures) == 1
    assert successes == []
    assert not partial_path.exists()
    assert not final_path.exists()


def test_atomic_publish_failure_cleans_partial_and_final(qapp, monkeypatch):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    failures = []
    updater.downloadFailed.connect(failures.append)
    monkeypatch.setattr(
        download_module.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(OSError("replace failed")),
    )
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)

    _finish_download(updater, manager, b"payload")

    assert len(failures) == 1
    assert not partial_path.exists()
    assert not final_path.exists()


@pytest.mark.parametrize("payload", [b"", b"payload"])
def test_network_or_empty_file_failure_never_leaves_artifact(qapp, payload):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    failures = []
    updater.downloadFailed.connect(failures.append)
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)
    if payload:
        manager.replies[-1]._error = QNetworkReply.NetworkError.ConnectionRefusedError

    _finish_download(updater, manager, payload)

    assert len(failures) == 1
    assert not partial_path.exists()
    assert not final_path.exists()


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_request_process_control_cleans_transaction_and_propagates(qapp, error_type):
    updater = Updater("owner/repo", "v1.0.0")
    updater._nam = type("FailingManager", (), {
        "get": lambda *_args: (_ for _ in ()).throw(error_type("stop")),
    })()

    with pytest.raises(error_type, match="stop"):
        updater.downloadUpdate("https://example.test/App-Setup.exe")

    assert updater._download_reply is None
    assert updater._download_file is None
    assert updater._download_partial_path == ""
    assert not Path(updater._download_path).exists()


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_write_process_control_cleans_transaction_and_propagates(qapp, error_type):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    reply = manager.replies[-1]
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)
    updater._download_file = _FaultyFile(
        updater._download_file, "write-control", error_type
    )
    reply.feed(b"payload")

    with pytest.raises(error_type, match="stop"):
        reply.readyRead.emit()

    assert updater._download_reply is None
    assert reply.aborted and reply.deleted
    assert not partial_path.exists()
    assert not final_path.exists()


def test_request_creation_failure_emits_once_and_cleans(qapp):
    updater = Updater("owner/repo", "v1.0.0")
    updater._nam = type("FailingManager", (), {
        "get": lambda *_args: (_ for _ in ()).throw(OSError("get failed")),
    })()
    failures = []
    updater.downloadFailed.connect(failures.append)

    updater.downloadUpdate("https://example.test/App-Setup.exe")

    assert len(failures) == 1
    assert updater._download_reply is None
    assert updater._download_file is None
    assert updater._download_partial_path == ""
    assert not Path(updater._download_path).exists()


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_commit_process_control_cleans_transaction_and_propagates(
    qapp,
    monkeypatch,
    error_type,
):
    updater = Updater("owner/repo", "v1.0.0")
    manager = _NetworkManagerStub()
    updater._nam = manager
    updater.downloadUpdate("https://example.test/App-Setup.exe")
    reply = manager.replies[-1]
    partial_path = Path(updater._download_partial_path)
    final_path = Path(updater._download_path)
    monkeypatch.setattr(
        download_module.os,
        "replace",
        lambda *_args: (_ for _ in ()).throw(error_type("stop")),
    )
    reply.feed(b"payload")

    with pytest.raises(error_type, match="stop"):
        reply.finished.emit()

    assert reply.deleted
    assert not partial_path.exists()
    assert not final_path.exists()
