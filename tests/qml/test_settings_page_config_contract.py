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
    themeChanged = Signal()
    skinChanged = Signal()
    languageChanged = Signal()
    accentColorChanged = Signal()
    persistencePendingChanged = Signal()

    def __init__(self, *, accept_updates=True, dpi_options=None):
        super().__init__()
        self._accept_updates = accept_updates
        self._dpi_options = dpi_options or [200, 0, 125]
        self._window_type = 0
        self._dpi_scale = 0
        self._theme = "auto"
        self._skin = "fluent"
        self._language = "auto"
        self._accent_color = "#0e5a9c"
        self.window_calls = []
        self.dpi_calls = []

    @Property(bool, notify=persistencePendingChanged)
    def persistencePending(self):
        return False

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
        return self._dpi_options

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

    @Property(str, notify=themeChanged)
    def theme(self):
        return self._theme

    @Property("QVariantList", constant=True)
    def themeOptions(self):
        return ["auto", "light", "dark"]

    @Slot(str)
    def setTheme(self, value):
        self._theme = value
        ThemeManager().setThemeFromQml(value)
        self.themeChanged.emit()

    @Property(str, notify=skinChanged)
    def skin(self):
        return self._skin

    @Property("QVariantList", constant=True)
    def skinOptions(self):
        return ["fluent", "neobrutalism", "vintage_ticket", "neumorphism"]

    @Slot(str)
    def setSkin(self, value):
        self._skin = value
        ThemeManager().setSkinFromQml(value)
        self.skinChanged.emit()

    @Property(str, notify=languageChanged)
    def language(self):
        return self._language

    @Property("QVariantList", constant=True)
    def languageOptions(self):
        return [
            "auto", "en", "zh_CN", "zh_TW", "hi", "es", "ar", "pt",
            "ru", "ja", "de", "fr", "ko", "it", "vi", "th", "id",
            "tr", "pl", "nl", "uk",
        ]

    @Slot(str)
    def setLanguage(self, value):
        self._language = value
        self.languageChanged.emit()

    @Property(str, notify=accentColorChanged)
    def accentColor(self):
        return self._accent_color

    @Slot(str)
    def setAccentColor(self, value):
        self._accent_color = value
        ThemeManager().setAccentColor(value)
        self.accentColorChanged.emit()


def _find_qml_descendant(root, qml_type):
    pending = list(root.children())
    while pending:
        child = pending.pop(0)
        class_name = child.metaObject().className()
        if class_name == qml_type or class_name.startswith(f"{qml_type}_QMLTYPE_"):
            return child
        pending.extend(child.children())
    raise AssertionError(f"未找到 QML 子对象: {qml_type}")


def _to_variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


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


def _appearance_cards(root):
    theme_card = root.findChild(QObject, "themeSettingsCard")
    skin_card = root.findChild(QObject, "skinSettingsCard")
    assert theme_card is not None
    assert skin_card is not None
    return theme_card, skin_card


def _skin_and_language_cards(root):
    skin_card = root.findChild(QObject, "skinSettingsCard")
    language_card = root.findChild(QObject, "languageSettingsCard")
    assert skin_card is not None
    assert language_card is not None
    return skin_card, language_card


def _follow_system_cards(root):
    theme_card = root.findChild(QObject, "themeSettingsCard")
    dpi_card = root.findChild(QObject, "dpiScaleSettingsCard")
    language_card = root.findChild(QObject, "languageSettingsCard")
    assert theme_card is not None
    assert dpi_card is not None
    assert language_card is not None
    return theme_card, dpi_card, language_card


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


def test_gallery_combo_examples_keep_local_selection_state(qapp):
    manager = _ConfigManagerFixture()
    with _settings_page(manager, qapp) as root:
        gallery_card = root.findChild(QObject, "galleryComboSettingsCard")
        grouped_gallery_card = root.findChild(
            QObject, "galleryGroupComboSettingsCard"
        )
        assert gallery_card is not None
        assert grouped_gallery_card is not None
        assert gallery_card.property("currentIndex") == 0
        assert grouped_gallery_card.property("currentIndex") == 0

        _emit_card_index_selected(gallery_card, 2)
        _emit_card_index_selected(grouped_gallery_card, 1)
        qapp.processEvents()

        assert gallery_card.property("currentIndex") == 2
        assert grouped_gallery_card.property("currentIndex") == 1


def test_appearance_cards_follow_selected_and_persisted_state(qapp):
    theme_manager = ThemeManager()
    previous_theme = theme_manager.theme
    previous_skin = theme_manager.skin
    theme_manager.setThemeFromQml("light")
    theme_manager.setSkinFromQml("fluent")
    manager = _ConfigManagerFixture()

    try:
        with _settings_page(manager, qapp) as root:
            theme_card, skin_card = _appearance_cards(root)
            theme_nodes = _activate_combo_index(theme_card, 2)
            skin_nodes = _activate_combo_index(skin_card, 2)
            qapp.processEvents()

            assert theme_manager.theme == "dark"
            assert theme_manager.skin == "vintage_ticket"
            _assert_combo_index(theme_card, *theme_nodes, 2)
            _assert_combo_index(skin_card, *skin_nodes, 2)

            manager.setSkin("neobrutalism")
            qapp.processEvents()
            _assert_combo_index(skin_card, *skin_nodes, 1)

            manager.setTheme("auto")
            manager.setSkin("fluent")
            qapp.processEvents()
            _assert_combo_index(theme_card, *theme_nodes, 0)
            _assert_combo_index(skin_card, *skin_nodes, 0)
    finally:
        theme_manager.setThemeFromQml(previous_theme)
        theme_manager.setSkinFromQml(previous_skin)


def test_skin_labels_follow_runtime_language_without_changing_values(qapp):
    manager = _ConfigManagerFixture()
    with _settings_page(manager, qapp) as root:
        skin_card, language_card = _skin_and_language_cards(root)

        _emit_card_index_selected(language_card, 1)
        qapp.processEvents()
        assert skin_card.property("title") == "Design Skin"
        assert skin_card.property("content") == "Switch design style"
        assert _to_variant(skin_card.property("model")) == [
            "Fluent Design",
            "Neobrutalism",
            "Vintage Ticket",
            "Neumorphism",
        ]

        _emit_card_index_selected(language_card, 2)
        qapp.processEvents()
        chinese_labels = _to_variant(skin_card.property("model"))
        assert skin_card.property("title") == "设计皮肤"
        assert skin_card.property("content") == "切换设计风格"
        assert chinese_labels == ["流畅设计", "新粗野主义", "复古票据", "新拟态"]
        assert all(not any(character.isascii() and character.isalpha()
                           for character in label)
                   for label in chinese_labels)
        assert _to_variant(skin_card.property("skinValues")) == [
            "fluent",
            "neobrutalism",
            "vintage_ticket",
            "neumorphism",
        ]


def test_gallery_defaults_theme_dpi_and_language_to_follow_system(qapp):
    theme_manager = ThemeManager()
    previous_theme = theme_manager.theme
    theme_manager.setThemeFromQml("auto")
    manager = _ConfigManagerFixture(dpi_options=[0, 100, 125])

    try:
        with _settings_page(manager, qapp) as root:
            for card in _follow_system_cards(root):
                entry = _find_qml_descendant(card, "ComboBoxEntry")
                inner = _find_qml_descendant(entry, "ComboBoxDefault")
                _assert_combo_index(card, entry, inner, 0)
    finally:
        theme_manager.setThemeFromQml(previous_theme)
