# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket preview entrypoint contracts. 复古票据预览入口合同。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "demo_vintage_ticket.py"
PREVIEW = ROOT / "examples" / "vintage_ticket_preview.qml"


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_vintage_ticket_preview_uses_the_real_skin_and_d3d11():
    source = ENTRYPOINT.read_text(encoding="utf-8")

    assert "setSkin(Skin.VINTAGE_TICKET)" in source
    assert "QSGRendererInterface.GraphicsApi.Direct3D11" in source
    assert 'actual_api != "Direct3D11"' in source
    assert source.index("QQuickWindow.setGraphicsApi") < source.index("QApplication(sys.argv)")
    assert "QSGRendererInterface.OpenGL" not in source
    assert "GraphicsApi.OpenGL" not in source
    assert "demo_neo" not in source
    assert "print(" not in source


def test_vintage_ticket_preview_is_an_independent_ticket_specimen():
    source = PREVIEW.read_text(encoding="utf-8")

    assert "TicketPaper" in source
    assert "PRISMQML RAILWAY BUREAU" in source
    assert "Perforation 撕票虚线" in source
    assert "Detachable stub 副券" in source
    assert "Enums.ticket" in source
    assert "Enums.isNeobrutalism" not in source


def test_vintage_ticket_preview_creates_without_qml_warnings(qapp):
    previous_skin = getSkin()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setSkin(Skin.VINTAGE_TICKET)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    engine.load(QUrl.fromLocalFile(str(PREVIEW)))
    _pump(80)
    roots = engine.rootObjects()

    try:
        assert len(roots) == 1
        assert isinstance(roots[0], QQuickWindow)
        assert roots[0].property("title") == "PrismQML - Vintage Ticket Preview"
        assert warnings == []
    finally:
        for root in roots:
            root.close()
            root.deleteLater()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        setSkin(previous_skin)
        _pump()
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
