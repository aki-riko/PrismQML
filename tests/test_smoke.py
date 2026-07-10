# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import os
import subprocess
import sys

import prismqml


def test_import_prismqml():
    assert hasattr(prismqml, "__version__")


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
            "import os; import prismqml; "
            "print(repr(os.environ.get('QML_XHR_ALLOW_FILE_READ')))",
        ],
        cwd=os.fspath(os.path.dirname(os.path.dirname(__file__))),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
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
            "import os; from prismqml import App; app = App([]); "
            "enabled = os.environ.get('QML_XHR_ALLOW_FILE_READ') == '1'; "
            "App._reset(); raise SystemExit(0 if enabled else 2)",
        ],
        cwd=os.fspath(os.path.dirname(os.path.dirname(__file__))),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_app_initialization_loads_translator():
    environment = os.environ.copy()
    environment.pop("QML_XHR_ALLOW_FILE_READ", None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    script = """
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
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
