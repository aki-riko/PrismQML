# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""实际 SettingsPage 必须按运行时候选值映射下拉索引。"""

from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    Property,
    Q_ARG,
    QMetaObject,
    QUrl,
    Signal,
    Slot,
    Qt,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml.python.core.theme import ThemeManager


ROOT = Path(__file__).resolve().parents[2]


class _ConfigManagerFixture(QObject):
    windowTypeChanged = Signal()
    dpiScaleChanged = Signal()

    def __init__(self, *, accept_updates=True):
        super().__init__()
        self._accept_updates = accept_updates
        self._window_type = 0
        self._dpi_scale = 0
        self.window_calls = []
        self.dpi_calls = []

    @Property("QVariantList", constant=True)
    def windowTypeOptions(self):
        return [2, 0, 1]

    @Property(int, notify=windowTypeChanged)
    def windowType(self):
        return self._window_type

    @Slot("QVariant")
    def setWindowType(self, value):
        self.window_calls.append(value)
        if not self._accept_updates:
            return
        self._window_type = value
        self.windowTypeChanged.emit()

    @Property("QVariantList", constant=True)
    def dpiScaleOptions(self):
        return [200, 0, 125]

    @Property(int, notify=dpiScaleChanged)
    def dpiScale(self):
        return self._dpi_scale

    @Slot("QVariant")
    def setDpiScale(self, value):
        self.dpi_calls.append(value)
        if not self._accept_updates:
            return
        self._dpi_scale = value
        self.dpiScaleChanged.emit()

    @Property(bool, constant=True)
    def micaEnabled(self):
        return False

    @Property(bool, constant=True)
    def dwmShadow(self):
        return True

    @Property(bool, constant=True)
    def lazyLoading(self):
        return True

    @Slot(bool)
    def setMicaEnabled(self, _value):
        pass

    @Slot(bool)
    def setDwmShadow(self, _value):
        pass

    @Slot(bool)
    def setLazyLoading(self, _value):
        pass


def _find_qml_descendant(root, qml_type):
    pending = list(root.children())
    while pending:
        child = pending.pop(0)
        class_name = child.metaObject().className()
        if class_name == qml_type or class_name.startswith(f"{qml_type}_QMLTYPE_"):
            return child
        pending.extend(child.children())
    raise AssertionError(f"未找到 QML 子对象: {qml_type}")


def _activate_combo_index(card, index):
    entry = _find_qml_descendant(card, "ComboBoxEntry")
    inner = _find_qml_descendant(entry, "ComboBoxDefault")
    assert inner.setProperty("currentIndex", index)
    assert QMetaObject.invokeMethod(
        inner,
        "activated",
        Qt.ConnectionType.DirectConnection,
        Q_ARG(int, index),
    )
    return entry, inner


def _emit_card_index_selected(card, index):
    assert QMetaObject.invokeMethod(
        card,
        "indexSelected",
        Qt.ConnectionType.DirectConnection,
        Q_ARG(int, index),
    )


def _create_settings_page(manager, engine, qapp):
    engine.addImportPath(str(ROOT / "prismqml"))
    context = engine.rootContext()
    context.setContextProperty("ThemeManager", ThemeManager())
    context.setContextProperty("ConfigManager", manager)
    component = QQmlComponent(engine)
    component.loadUrl(
        QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "SettingsPage.qml"))
    )
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        qapp.processEvents()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    return component, root


@contextmanager
def _settings_page(manager, qapp):
    engine = QQmlEngine()
    component = None
    root = None
    try:
        component, root = _create_settings_page(manager, engine, qapp)
        yield root
    finally:
        if root is not None:
            root.deleteLater()
        if component is not None:
            component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def _settings_cards(root):
    window_card = root.findChild(QObject, "windowTypeSettingsCard")
    dpi_card = root.findChild(QObject, "dpiScaleSettingsCard")
    assert window_card is not None
    assert dpi_card is not None
    return window_card, dpi_card


def _activate_cards(window_card, dpi_card, qapp):
    window_nodes = _activate_combo_index(window_card, 0)
    dpi_nodes = _activate_combo_index(dpi_card, 2)
    qapp.processEvents()
    return window_nodes, dpi_nodes


def _assert_combo_index(card, entry, inner, index):
    assert card.property("currentIndex") == index
    assert entry.property("currentIndex") == index
    assert inner.property("currentIndex") == index


def _set_backend_values(manager, window_type, dpi_scale, qapp):
    manager._window_type = window_type
    manager.windowTypeChanged.emit()
    manager._dpi_scale = dpi_scale
    manager.dpiScaleChanged.emit()
    qapp.processEvents()


def test_settings_page_maps_real_selection_to_reordered_values(qapp):
    manager = _ConfigManagerFixture()
    with _settings_page(manager, qapp) as root:
        window_card, dpi_card = _settings_cards(root)
        assert window_card.property("currentIndex") == 1
        assert dpi_card.property("currentIndex") == 1

        window_nodes, dpi_nodes = _activate_cards(window_card, dpi_card, qapp)
        assert manager.window_calls == [2]
        assert manager.dpi_calls == [125]
        _assert_combo_index(window_card, *window_nodes, 0)
        _assert_combo_index(dpi_card, *dpi_nodes, 2)

        _emit_card_index_selected(window_card, -1)
        _emit_card_index_selected(window_card, 3)
        _emit_card_index_selected(dpi_card, -1)
        _emit_card_index_selected(dpi_card, 3)
        assert manager.window_calls == [2]
        assert manager.dpi_calls == [125]


def test_settings_page_keeps_binding_after_real_selection(qapp):
    manager = _ConfigManagerFixture()
    with _settings_page(manager, qapp) as root:
        window_card, dpi_card = _settings_cards(root)
        window_nodes, dpi_nodes = _activate_cards(window_card, dpi_card, qapp)

        _set_backend_values(manager, 1, 200, qapp)
        _assert_combo_index(window_card, *window_nodes, 2)
        _assert_combo_index(dpi_card, *dpi_nodes, 0)

        _set_backend_values(manager, 99, 999, qapp)
        _assert_combo_index(window_card, *window_nodes, -1)
        _assert_combo_index(dpi_card, *dpi_nodes, -1)


def test_settings_page_reverts_selection_when_backend_rejects_update(qapp):
    manager = _ConfigManagerFixture(accept_updates=False)
    with _settings_page(manager, qapp) as root:
        window_card, dpi_card = _settings_cards(root)
        window_nodes, dpi_nodes = _activate_cards(window_card, dpi_card, qapp)

        assert manager.window_calls == [2]
        assert manager.dpi_calls == [125]
        assert manager.property("windowType") == 0
        assert manager.property("dpiScale") == 0
        _assert_combo_index(window_card, *window_nodes, 1)
        _assert_combo_index(dpi_card, *dpi_nodes, 1)
