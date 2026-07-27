# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Windows A/B slot resolution contracts. Windows A/B 槽解析合同。"""

from pathlib import Path

from prismqml.python.core import update_slots


def _install_tree(tmp_path: Path, launch_slot: str = "A"):
    root = tmp_path / "Gitora"
    slot_a = root / "slot-a"
    slot_b = root / "slot-b"
    slot_a.mkdir(parents=True)
    slot_b.mkdir()
    executable = slot_a / "Gitora.exe"
    executable.write_bytes(b"old")
    (slot_b / "Gitora.exe").write_bytes(b"new")
    (root / "prism-update-slot.ini").write_text(
        f"[Slots]\nLaunchSlot={launch_slot}\n", encoding="utf-8"
    )
    return root, executable


def test_slot_state_is_scoped_to_shared_install_root(tmp_path):
    root, executable = _install_tree(tmp_path, "B")

    assert update_slots.current_update_slot(executable) == "A"
    assert update_slots.update_root(executable) == root
    assert update_slots.read_launch_slot(executable) == "B"
    assert update_slots.executable_for_slot("B", executable) == (
        root / "slot-b" / "Gitora.exe"
    )


def test_redirect_starts_selected_slot_and_forwards_arguments(tmp_path, monkeypatch):
    _root, executable = _install_tree(tmp_path, "B")
    calls = []

    monkeypatch.setattr(update_slots.sys, "platform", "win32")
    monkeypatch.setattr(
        update_slots.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    assert update_slots.redirect_to_active_update_slot(
        ["--open", "file.txt"], executable
    ) is True
    assert calls == [(
        [str(executable.parent.parent / "slot-b" / "Gitora.exe"), "--open", "file.txt"],
        {
            "cwd": str(executable.parent.parent / "slot-b"),
            "close_fds": True,
            "creationflags": getattr(update_slots.subprocess, "DETACHED_PROCESS", 0)
            | getattr(update_slots.subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        },
    )]


def test_redirect_is_noop_when_state_selects_current_or_target_missing(tmp_path, monkeypatch):
    _root, executable = _install_tree(tmp_path, "A")
    monkeypatch.setattr(update_slots.sys, "platform", "win32")
    assert update_slots.redirect_to_active_update_slot([], executable) is False

    (executable.parent.parent / "slot-b" / "Gitora.exe").unlink()
    (executable.parent.parent / "prism-update-slot.ini").write_text(
        "[Slots]\nLaunchSlot=B\n", encoding="utf-8"
    )
    assert update_slots.redirect_to_active_update_slot([], executable) is False
