# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""App-level application icon contracts. App 级应用图标合同。"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import struct
import sys
from types import SimpleNamespace

import pytest
from PySide6.QtGui import QColor, QImage

from prismqml.python.window.app import App


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = REPO_ROOT / "scripts" / "test_process.py"


class _FakeWindow:
    def __init__(self, window_type=None):
        self.window_type = window_type
        self.icon_calls = []

    def setWindowIcon(self, icon: str, colored: bool = True) -> None:
        self.icon_calls.append((icon, colored))


def _bare_app(windows=None):
    app = object.__new__(App)
    app._windows = list(windows or [])
    app._application_icon = ""
    app._application_icon_colored = True
    return app


def test_set_application_icon_publishes_and_updates_existing_windows(monkeypatch):
    """One App call must update Qt and every managed window. 一次调用同步全局与托管窗口。"""
    helper = SimpleNamespace(calls=[])
    helper.setAppIcon = helper.calls.append
    monkeypatch.setattr(
        "prismqml.python.core.window_helper.get_window_helper",
        lambda: helper,
    )
    first = _FakeWindow()
    second = _FakeWindow()
    app = _bare_app([first, second])

    app.set_application_icon(Path("assets/app.png"), colored=False)

    expected = str(Path("assets/app.png"))
    assert app.application_icon == expected
    assert app.application_icon_colored is False
    assert helper.calls == [expected]
    assert first.icon_calls == [(expected, False)]
    assert second.icon_calls == [(expected, False)]


def test_create_window_inherits_configured_application_icon(monkeypatch):
    """Every later window must inherit App branding automatically. 后建窗口自动继承品牌图标。"""
    monkeypatch.setattr(
        "prismqml.python.window.fluent_window.Window",
        _FakeWindow,
    )
    app = _bare_app()
    app._application_icon = ":/branding/app.svg"
    app._application_icon_colored = False

    window = app.create_window(window_type=2)

    assert window.window_type == 2
    assert window.icon_calls == [(":/branding/app.svg", False)]
    assert app.windows == [window]


def test_create_window_inherits_app_splash_subtitle(monkeypatch):
    """Python windows must inherit the App-level startup subtitle."""
    monkeypatch.setattr(
        "prismqml.python.window.fluent_window.Window",
        _FakeWindow,
    )
    app = _bare_app()
    app._splash_subtitle = "Loading..."

    window = app.create_window()

    assert window._splash_subtitle == "Loading..."


def test_application_icon_rejects_empty_source():
    """An empty source cannot silently retain a stale Qt icon. 空来源不得静默保留旧图标。"""
    app = _bare_app()

    try:
        app.set_application_icon("")
    except ValueError as error:
        assert "application_icon" in str(error)
    else:
        raise AssertionError("empty application_icon must fail")


def test_app_constructor_publishes_icon_before_window_creation(tmp_path):
    """Constructor branding must reach Qt before any window exists. 构造配置须先于窗口生效。"""
    source = tmp_path / "constructor.png"
    _write_source_png(source)
    script = f"""
from scripts.test_process import prepare_automated_test_process
prepare_automated_test_process()
import shiboken6
from prismqml import App
app = App([], application_icon={str(source)!r}, application_icon_colored=False)
window = app.create_window()
assert app.application_icon == {str(source)!r}
assert app.application_icon_colored is False
assert window._icon == {str(source).replace(chr(92), '/')!r}
assert not app.qapp.windowIcon().isNull()
qapp = app.qapp
app.shutdown()
App._reset()
shiboken6.delete(qapp)
print('APP_ICON_CONSTRUCTOR_OK')
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(TEST_PROCESS),
            "--qt-platform",
            "offscreen",
            "--timeout",
            "90",
            "--",
            sys.executable,
            "-c",
            script,
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "APP_ICON_CONSTRUCTOR_OK" in completed.stdout


def _write_source_png(path: Path) -> None:
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2080d0"))
    assert image.save(str(path), "PNG")


def test_prepare_windows_icon_builds_a_multisize_ico(tmp_path):
    """The build helper must derive a real multi-size ICO. 构建辅助生成真实多尺寸 ICO。"""
    from prismqml import prepare_windows_icon

    source = tmp_path / "brand.png"
    output = tmp_path / "generated" / "app.ico"
    _write_source_png(source)

    result = prepare_windows_icon(source, output)

    data = result.read_bytes()
    reserved, icon_type, count = struct.unpack_from("<HHH", data)
    assert result == output.resolve()
    assert (reserved, icon_type, count) == (0, 1, 7)
    assert len(data) > 6 + count * 16


@pytest.mark.parametrize(
    ("platform_name", "option_name", "expected_suffix"),
    [
        ("win32", "--windows-icon-from-ico=", "app_icon.ico"),
        ("darwin", "--macos-app-icon=", "brand.png"),
        ("linux", "--linux-icon=", "brand.png"),
    ],
)
def test_nuitka_icon_options_use_one_source_across_platforms(
    tmp_path,
    platform_name,
    option_name,
    expected_suffix,
):
    """One source image must produce the verified Nuitka platform option. 单源生成平台参数。"""
    from prismqml import nuitka_icon_options

    source = tmp_path / "brand.png"
    _write_source_png(source)

    options = nuitka_icon_options(
        source,
        tmp_path / "generated",
        platform_name=platform_name,
    )

    assert len(options) == 1
    assert options[0].startswith(option_name)
    assert options[0].endswith(expected_suffix)


def test_prepare_windows_icon_rejects_invalid_input(tmp_path):
    """Invalid image input must fail before packaging. 无效图片必须在打包前失败。"""
    from prismqml import prepare_windows_icon

    invalid = tmp_path / "invalid.png"
    invalid.write_text("not an image", encoding="utf-8")

    with pytest.raises(ValueError, match="application icon"):
        prepare_windows_icon(invalid, tmp_path / "app.ico")
