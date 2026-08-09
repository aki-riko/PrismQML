# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Native popup owner repair contracts. 原生弹层 owner 修复合同。"""

from PySide6.QtCore import Qt

from prismqml.python.core import _popup_owner, window_helper


class _FakePopupOwnerApi:
    def __init__(self, owner: int = 0, capture: int = 0) -> None:
        self.current_owner = owner
        self.current_capture = capture
        self.process_ids = {11: 700, 21: 700}
        self.calls = []
        self.set_owner_result = True
        self.raise_result = True
        self.mouse_down = False
        self.release_capture_result = True

    def process_id(self, hwnd: int) -> int:
        self.calls.append(("process", hwnd))
        return self.process_ids.get(hwnd, 0)

    def owner(self, hwnd: int) -> int:
        self.calls.append(("owner", hwnd))
        return self.current_owner

    def set_owner(self, popup_hwnd: int, owner_hwnd: int) -> bool:
        self.calls.append(("set_owner", popup_hwnd, owner_hwnd))
        if self.set_owner_result:
            self.current_owner = owner_hwnd
        return self.set_owner_result

    def capture(self) -> int:
        self.calls.append(("capture",))
        return self.current_capture

    def mouse_button_down(self) -> bool:
        self.calls.append(("mouse_button_down",))
        return self.mouse_down

    def release_capture(self) -> bool:
        self.calls.append(("release_capture",))
        if self.release_capture_result:
            self.current_capture = 0
        return self.release_capture_result

    def raise_popup(self, popup_hwnd: int) -> bool:
        self.calls.append(("raise", popup_hwnd))
        return self.raise_result


def test_missing_popup_owner_is_repaired_verified_and_raised():
    api = _FakePopupOwnerApi()

    assert _popup_owner._ensure_popup_owner_with_api(api, 11, 21, 700)

    assert api.current_owner == 21
    assert api.calls == [
        ("process", 11),
        ("process", 21),
        ("owner", 11),
        ("set_owner", 11, 21),
        ("owner", 11),
        ("raise", 11),
    ]


def test_existing_popup_owner_is_only_refreshed_in_z_order():
    api = _FakePopupOwnerApi(owner=21)

    assert _popup_owner._ensure_popup_owner_with_api(api, 11, 21, 700)

    assert ("set_owner", 11, 21) not in api.calls
    assert api.calls[-1] == ("raise", 11)


def test_popup_owner_repair_rejects_cross_process_or_invalid_handles():
    api = _FakePopupOwnerApi()
    api.process_ids[11] = 701

    assert not _popup_owner._ensure_popup_owner_with_api(api, 11, 21, 700)
    assert not _popup_owner._ensure_popup_owner_with_api(api, 0, 21, 700)
    assert not _popup_owner._ensure_popup_owner_with_api(api, 21, 21, 700)
    assert not any(call[0] == "set_owner" for call in api.calls)


def test_failed_or_unverified_owner_assignment_does_not_raise():
    failed_api = _FakePopupOwnerApi()
    failed_api.set_owner_result = False
    assert not _popup_owner._ensure_popup_owner_with_api(failed_api, 11, 21, 700)
    assert not any(call[0] == "raise" for call in failed_api.calls)

    unverified_api = _FakePopupOwnerApi()
    unverified_api.set_owner = lambda popup, owner: True
    assert not _popup_owner._ensure_popup_owner_with_api(
        unverified_api, 11, 21, 700
    )
    assert not any(call[0] == "raise" for call in unverified_api.calls)


def test_matching_popup_owner_is_cleared_and_verified():
    api = _FakePopupOwnerApi(owner=21)

    assert _popup_owner._clear_popup_owner_with_api(api, 11, 21, 700)

    assert api.current_owner == 0
    assert api.calls == [
        ("process", 11),
        ("process", 21),
        ("owner", 11),
        ("set_owner", 11, 0),
        ("owner", 11),
    ]


def test_popup_owner_clear_rejects_foreign_or_reassigned_windows():
    foreign_api = _FakePopupOwnerApi(owner=21)
    foreign_api.process_ids[11] = 701
    assert not _popup_owner._clear_popup_owner_with_api(foreign_api, 11, 21, 700)
    assert not any(call[0] == "set_owner" for call in foreign_api.calls)

    reassigned_api = _FakePopupOwnerApi(owner=31)
    assert not _popup_owner._clear_popup_owner_with_api(
        reassigned_api, 11, 21, 700
    )
    assert not any(call[0] == "set_owner" for call in reassigned_api.calls)


def test_already_unowned_popup_is_a_successful_no_op():
    api = _FakePopupOwnerApi()

    assert _popup_owner._clear_popup_owner_with_api(api, 11, 21, 700)

    assert not any(call[0] == "set_owner" for call in api.calls)


def test_idle_owner_capture_is_released_and_verified():
    api = _FakePopupOwnerApi(owner=21, capture=21)

    assert _popup_owner._release_stale_popup_capture_with_api(api, 11, 21, 700)

    assert api.current_capture == 0
    assert api.calls == [
        ("process", 11),
        ("process", 21),
        ("owner", 11),
        ("capture",),
        ("mouse_button_down",),
        ("release_capture",),
        ("capture",),
    ]


def test_active_or_unrelated_capture_is_preserved():
    active_api = _FakePopupOwnerApi(owner=21, capture=21)
    active_api.mouse_down = True
    assert not _popup_owner._release_stale_popup_capture_with_api(
        active_api, 11, 21, 700
    )
    assert ("release_capture",) not in active_api.calls

    unrelated_api = _FakePopupOwnerApi(owner=21, capture=31)
    assert not _popup_owner._release_stale_popup_capture_with_api(
        unrelated_api, 11, 21, 700
    )
    assert ("mouse_button_down",) not in unrelated_api.calls
    assert ("release_capture",) not in unrelated_api.calls


def test_failed_or_unverified_capture_release_is_rejected():
    failed_api = _FakePopupOwnerApi(owner=21, capture=21)
    failed_api.release_capture_result = False
    assert not _popup_owner._release_stale_popup_capture_with_api(
        failed_api, 11, 21, 700
    )
    assert failed_api.current_capture == 21

    unverified_api = _FakePopupOwnerApi(owner=21, capture=21)
    unverified_api.release_capture = lambda: True
    assert not _popup_owner._release_stale_popup_capture_with_api(
        unverified_api, 11, 21, 700
    )
    assert unverified_api.current_capture == 21


def test_popup_capture_release_rejects_invalid_ownership_or_process():
    unowned_api = _FakePopupOwnerApi(capture=21)
    assert not _popup_owner._release_stale_popup_capture_with_api(
        unowned_api, 11, 21, 700
    )
    assert ("release_capture",) not in unowned_api.calls

    foreign_api = _FakePopupOwnerApi(owner=21, capture=21)
    foreign_api.process_ids[11] = 701
    assert not _popup_owner._release_stale_popup_capture_with_api(
        foreign_api, 11, 21, 700
    )
    assert ("release_capture",) not in foreign_api.calls


class _FakeWindow:
    def __init__(self, hwnd: int, window_type: Qt.WindowType) -> None:
        self._hwnd = hwnd
        self._window_type = window_type

    def winId(self) -> int:
        return self._hwnd

    def flags(self):
        return self._window_type


def test_window_helper_accepts_only_qt_popup_windows(monkeypatch):
    ensure_calls = []
    clear_calls = []
    release_calls = []
    monkeypatch.setattr(
        window_helper,
        "ensure_popup_window_owner",
        lambda popup, owner: ensure_calls.append((popup, owner)) or True,
    )
    monkeypatch.setattr(
        window_helper,
        "clear_popup_window_owner",
        lambda popup, owner: clear_calls.append((popup, owner)) or True,
    )
    monkeypatch.setattr(
        window_helper,
        "release_stale_popup_capture",
        lambda popup, owner: release_calls.append((popup, owner)) or True,
    )
    monkeypatch.setattr(window_helper.WindowHelper, "_instance", None)
    helper = window_helper.WindowHelper()
    popup = _FakeWindow(11, Qt.WindowType.Popup)
    owner = _FakeWindow(21, Qt.WindowType.Window)

    assert helper.ensurePopupWindowOwner(popup, owner)
    assert ensure_calls == [(11, 21)]
    assert not helper.ensurePopupWindowOwner(owner, popup)
    assert ensure_calls == [(11, 21)]

    assert helper.clearPopupWindowOwner(popup, owner)
    assert clear_calls == [(11, 21)]
    assert not helper.clearPopupWindowOwner(owner, popup)
    assert clear_calls == [(11, 21)]

    assert helper.releasePopupWindowCapture(popup, owner)
    assert release_calls == [(11, 21)]
    assert not helper.releasePopupWindowCapture(owner, popup)
    assert release_calls == [(11, 21)]
