# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import importlib.metadata
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

import prismqml

SUBPROCESS_TIMEOUT_SECONDS = 30
PACKAGE_INIT = Path(__file__).resolve().parents[1] / "prismqml" / "__init__.py"
PROJECT_CONFIG = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _metadata_failure(error):
    def fail(_distribution_name):
        raise error

    return fail


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


def test_missing_distribution_uses_source_version_fallback(monkeypatch):
    missing = importlib.metadata.PackageNotFoundError("prismqml")
    monkeypatch.setattr(importlib.metadata, "version", _metadata_failure(missing))

    namespace = runpy.run_path(str(PACKAGE_INIT))

    assert namespace["__version__"] == _project_version()


def test_metadata_backend_failure_is_not_hidden_as_missing_package(monkeypatch):
    failure = RuntimeError("metadata backend failed")
    monkeypatch.setattr(importlib.metadata, "version", _metadata_failure(failure))

    with pytest.raises(RuntimeError, match="metadata backend failed"):
        runpy.run_path(str(PACKAGE_INIT))


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

    monkeypatch.delenv("QML_XHR_ALLOW_FILE_READ", raising=False)
    configure_qml_environment()
    assert os.environ["QML_XHR_ALLOW_FILE_READ"] == "1"

    configure_qml_environment(False)
    assert os.environ["QML_XHR_ALLOW_FILE_READ"] == "0"


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
loop = QEventLoop()
QTimer.singleShot(100, loop.quit)
loop.exec()
roots = app.engine.rootObjects()
translated = roots[-1].property("translated") if roots else None
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
