# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import os
from pathlib import Path
import subprocess
import sys

import prismqml

SUBPROCESS_TIMEOUT_SECONDS = 30
PROJECT_CONFIG = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _project_version():
    section = ""
    for line in PROJECT_CONFIG.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        if section == "[project]" and stripped.startswith("version"):
            _, value = stripped.split("=", 1)
            return value.strip().strip('"')
    raise AssertionError("pyproject.toml [project].version is missing")


def test_import_prismqml():
    assert hasattr(prismqml, "__version__")


def test_source_version_matches_project_version():
    assert prismqml.__version__ == _project_version()


def test_import_prismqml_does_not_scan_distribution_metadata():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import prismqml; "
            "raise SystemExit(2 if 'importlib.metadata' in sys.modules else 0)",
        ],
        cwd=os.fspath(Path(__file__).resolve().parents[1]),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_qml_path_exists():
    from prismqml import qml_path

    path = qml_path()
    assert path.exists()


def test_import_prismqml_does_not_enable_local_qml_xhr():
    environment = os.environ.copy()
    environment.pop("QML_XHR_ALLOW_FILE_READ", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scripts.test_process import prepare_automated_test_process; "
            "prepare_automated_test_process(); import os; import prismqml; "
            "print(repr(os.environ.get('QML_XHR_ALLOW_FILE_READ')))",
        ],
        cwd=os.fspath(os.path.dirname(os.path.dirname(__file__))),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "None"


def test_configure_qml_environment_is_explicit(monkeypatch):
    from prismqml import configure_qml_environment
    from PySide6.QtQuick import QQuickWindow

    monkeypatch.delenv("QML_XHR_ALLOW_FILE_READ", raising=False)
    original_alpha_buffer = QQuickWindow.hasDefaultAlphaBuffer()
    QQuickWindow.setDefaultAlphaBuffer(False)
    try:
        configure_qml_environment()
        assert os.environ["QML_XHR_ALLOW_FILE_READ"] == "1"
        assert QQuickWindow.hasDefaultAlphaBuffer()

        configure_qml_environment(False)
        assert os.environ["QML_XHR_ALLOW_FILE_READ"] == "0"
        assert QQuickWindow.hasDefaultAlphaBuffer()
    finally:
        QQuickWindow.setDefaultAlphaBuffer(original_alpha_buffer)


def test_app_initialization_enables_local_qml_xhr():
    environment = os.environ.copy()
    environment.pop("QML_XHR_ALLOW_FILE_READ", None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scripts.test_process import prepare_automated_test_process; "
            "prepare_automated_test_process(); import os; "
            "from prismqml import App; app = App([]); "
            "enabled = os.environ.get('QML_XHR_ALLOW_FILE_READ') == '1'; "
            "App._reset(); raise SystemExit(0 if enabled else 2)",
        ],
        cwd=os.fspath(os.path.dirname(os.path.dirname(__file__))),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_app_initialization_loads_translator():
    environment = os.environ.copy()
    environment.pop("QML_XHR_ALLOW_FILE_READ", None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    script = """
from scripts.test_process import prepare_automated_test_process

prepare_automated_test_process()

from PySide6.QtCore import QEventLoop, QTimer
from prismqml import App

app = App([])
app.engine.loadData(b'''import QtQuick
import PrismQML
QtObject {
    property string translated: ""
    Component.onCompleted: Qt.callLater(function() {
        Translator.setLanguage("en")
        translated = Translator.tr("ok")
    })
}
''')

# Poll until the translation resolves instead of waiting a fixed 100 ms. A fixed
# sleep is a race: the callLater callback plus Translator.setLanguage can take
# longer than the budget on a loaded CI machine, and the assertion then reads an
# unresolved value and fails for reasons unrelated to the code under test.
# 轮询到翻译就绪, 而不是死等固定 100ms。固定等待是竞态: 在负载高的 CI 机器上
# callLater 回调加 Translator.setLanguage 可能超过该预算, 断言就会读到未解析的值,
# 因与本测试目标无关的原因失败。
deadline = 5000.0
elapsed = 0.0
step = 10.0
translated = None
while elapsed < deadline:
    loop = QEventLoop()
    QTimer.singleShot(int(step), loop.quit)
    loop.exec()
    elapsed += step
    roots = app.engine.rootObjects()
    candidate = roots[-1].property("translated") if roots else None
    if candidate:
        translated = candidate
        break
App._reset()
raise SystemExit(0 if translated == "OK" else 3)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.fspath(os.path.dirname(os.path.dirname(__file__))),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
