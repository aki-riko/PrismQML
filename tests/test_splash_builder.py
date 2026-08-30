# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash configuration regressions. 启动画面配置回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml.python.window._splash_builder import (
    build_splash_properties,
    build_splash_template_values,
)
from prismqml.python.window.app import App
from prismqml.python.window.fast_splash import (
    FastSplashController,
    build_fast_splash_qml,
)
from prismqml.python.window.window_core import WindowCore


ROOT = Path(__file__).resolve().parents[1]


def test_fast_splash_normalizes_initial_icon_sources():
    """Initial fast-splash sources must remain valid in the isolated QML engine."""
    assert FastSplashController._qml_icon_source(":/app_icon.svg") == "qrc:/app_icon.svg"
    assert FastSplashController._qml_icon_source("qrc:/app_icon.svg") == "qrc:/app_icon.svg"
    assert FastSplashController._qml_icon_source("D:\\icons\\app.svg") == "file:///D:/icons/app.svg"


def test_fast_splash_template_uses_shared_subtitle_default_and_override():
    from prismqml.python.runtime.startup_defaults import DEFAULT_SPLASH_SUBTITLE

    assert DEFAULT_SPLASH_SUBTITLE in build_fast_splash_qml(False)
    assert "Loading..." in build_fast_splash_qml(False, 1200, 800, "Loading...")


def test_fast_splash_template_avoids_first_frame_icon_shadow_effect():
    source = build_fast_splash_qml(False)

    assert "import QtQuick.Effects" not in source
    assert "MultiEffect" not in source
    assert "layer.effect: MultiEffect" not in source


def test_fast_splash_does_not_take_over_attached_window_geometry():
    source = (ROOT / "prismqml/python/window/fast_splash.py").read_text(
        encoding="utf-8"
    )

    assert "_sync_window_size" not in source
    assert "_align_main_window_to_splash" not in source
    assert "main_window.setPosition" not in source


def test_fast_splash_keeps_explicit_initial_dimensions():
    source = build_fast_splash_qml(False, 980, 640)

    assert "width: 980; height: 640" in source


def _resolve_startup_sizes(monkeypatch, **kwargs):
    """Run App size resolution with Qt startup stubbed. 打桩 Qt 启动后解析尺寸。"""
    import prismqml.python.runtime as runtime
    from prismqml.python.window import app as app_module
    from prismqml.python.window import fast_splash as fast_splash_module

    recorded = {}

    class _RecordingController:
        def __init__(self, _app):
            pass

        def show(self, _icon, *, subtitle, splash_width, splash_height):
            recorded["splash_size"] = (splash_width, splash_height)
            return True

    monkeypatch.setattr(runtime, "create_qt_application", lambda _argv: (None, False))
    monkeypatch.setattr(runtime, "install_application_input_filter", lambda _app: None)
    monkeypatch.setattr(runtime, "install_application_dwm_filter", lambda: None)
    monkeypatch.setattr(
        fast_splash_module, "FastSplashController", _RecordingController
    )

    owner = SimpleNamespace()
    app_module._create_qt_application(owner, [], **kwargs)
    recorded["window_size"] = (owner._window_width, owner._window_height)
    return recorded


def test_app_window_size_drives_splash_and_window_together(monkeypatch):
    """One App setting must size both startup surfaces. 一次设定同时决定两个表面。"""
    sizes = _resolve_startup_sizes(monkeypatch, window_width=1150, window_height=780)

    assert sizes["window_size"] == (1150, 780)
    assert sizes["splash_size"] == (1150, 780)


def test_app_splash_size_stays_overridable(monkeypatch):
    """Explicit splash geometry must survive the shared default."""
    sizes = _resolve_startup_sizes(
        monkeypatch,
        window_width=1150,
        window_height=780,
        splash_width=640,
        splash_height=480,
    )

    assert sizes["window_size"] == (1150, 780)
    assert sizes["splash_size"] == (640, 480)


def test_app_window_size_defaults_to_shared_constants(monkeypatch):
    from prismqml.python.runtime.startup_defaults import (
        DEFAULT_WINDOW_HEIGHT,
        DEFAULT_WINDOW_WIDTH,
    )

    sizes = _resolve_startup_sizes(monkeypatch)

    assert sizes["window_size"] == (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    assert sizes["splash_size"] == (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1150"])
def test_app_rejects_invalid_window_dimensions(monkeypatch, value):
    with pytest.raises(ValueError):
        _resolve_startup_sizes(monkeypatch, window_width=value)


def test_window_size_falls_back_to_defaults_without_app():
    """A bare WindowCore must not require App. 裸 WindowCore 不应强依赖 App。"""
    from prismqml.python.runtime.startup_defaults import (
        DEFAULT_WINDOW_HEIGHT,
        DEFAULT_WINDOW_WIDTH,
    )
    from prismqml.python.runtime.startup_defaults import (
        resolve_initial_window_size,
    )

    assert App._instance is None
    assert resolve_initial_window_size() == (
        DEFAULT_WINDOW_WIDTH,
        DEFAULT_WINDOW_HEIGHT,
    )


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "980"])
def test_fast_splash_rejects_invalid_dimensions(value):
    with pytest.raises(ValueError):
        FastSplashController._validate_dimension(value, "splash_width")


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("", True),
        ("python", True),
        ("pythonw", True),
        ("PrismQML Gallery", False),
    ],
)
def test_fast_splash_recognizes_unbranded_process_titles(title, expected):
    """Unbranded interpreter titles must not be committed as a first frame."""
    assert FastSplashController._is_default_process_title(title) is expected


class _PropertyObject:
    def __init__(self, **properties):
        self._properties = properties

    def property(self, name):
        return self._properties.get(name)


class _QmlVariant:
    def __init__(self, value):
        self._value = value

    def toVariant(self):
        return self._value


class _SplashSurface:
    def __init__(self):
        self.properties = {}
        self.shown = False

    def setProperty(self, name, value):
        self.properties[name] = value

    def property(self, name):
        return self.properties.get(name)

    def show(self):
        self.shown = True


class _ApplicationSurface:
    def __init__(self, *, display_name="", application_name="", application_icon=""):
        self._display_name = display_name
        self._application_name = application_name
        self.application_icon = application_icon

    def applicationDisplayName(self):
        return self._display_name

    def applicationName(self):
        return self._application_name


class _WindowSurface:
    def __init__(self, **properties):
        self._properties = properties

    def property(self, name):
        return self._properties.get(name)


def test_fast_splash_waits_for_python_page_readiness():
    """Python page containers must not satisfy the fast-splash readiness gate."""
    page = _PropertyObject()
    stack = _PropertyObject(
        currentWidget=page,
        currentIndex=0,
        _useSourceMode=False,
    )
    window = _PropertyObject(
        stackedWidget=stack,
        _pythonPageMode=True,
        _pythonReadyIndexes=[],
    )

    assert FastSplashController._page_ready(window) is False
    window._properties["_pythonReadyIndexes"] = [0]
    assert FastSplashController._page_ready(window) is True


def test_fast_splash_shows_after_legacy_title_and_icon_metadata():
    """Legacy metadata is cached until Window commits the final splash config."""
    controller = FastSplashController(None)
    controller._splash = _SplashSurface()
    controller._visibility_deferred = True

    controller.update_metadata(title="Kaleidos")
    assert controller._splash.shown is False
    assert controller._splash.properties["splashTitle"] == "Kaleidos"

    controller.update_metadata(icon=":/icons/kaleidos.svg")
    assert controller._splash.shown is False
    assert controller._splash.properties["splashTitle"] == "Kaleidos"
    assert controller._splash.properties["splashIcon"] == "qrc:/icons/kaleidos.svg"

    controller.mark_window_metadata_ready()
    assert controller._splash.shown is True


def test_fast_splash_commits_explicit_subtitle_before_first_show(qapp):
    """App-level splash metadata must be present before the surface becomes visible."""
    original_display_name = qapp.applicationDisplayName()
    controller = FastSplashController(qapp)
    try:
        qapp.setApplicationDisplayName("Kaleidos")
        assert controller.show(
            ":/icons/kaleidos.svg",
            subtitle="程序正在初始化，请稍候...",
        )
        assert controller.splash is not None
        assert controller.splash.property("splashSubtitle") == "程序正在初始化，请稍候..."
        assert controller.splash.isVisible() is True
    finally:
        controller.close()
        qapp.setApplicationDisplayName(original_display_name)


def test_window_show_splash_keeps_fast_surface_deferred_until_attach():
    """Window.showSplash only releases the fast surface after full metadata."""
    calls = []
    window = SimpleNamespace(
        _splash_enabled=False,
        _splash_icon="",
        _splash_title="",
        _splash_subtitle="",
        _update_fast_splash_metadata=lambda **metadata: calls.append(metadata),
        _mark_fast_splash_metadata_ready=lambda: calls.append("ready"),
    )

    WindowCore.showSplash(window, subtitle="Loading")

    assert calls == [{"title": None, "icon": None, "subtitle": "Loading"}]


def test_window_show_splash_releases_complete_fast_metadata():
    """A complete title/icon transaction can show before QML root creation."""
    calls = []
    window = SimpleNamespace(
        _splash_enabled=False,
        _splash_icon="",
        _splash_title="",
        _splash_subtitle="",
        _update_fast_splash_metadata=lambda **metadata: calls.append(metadata),
    )

    controller = SimpleNamespace(show_if_metadata_ready=lambda: calls.append("ready"))
    app = SimpleNamespace(_fast_splash=controller)
    original_instance = App._instance
    App._instance = app
    try:
        WindowCore.showSplash(
            window,
            icon=":/icons/kaleidos.svg",
            title="Kaleidos",
            subtitle="Loading",
        )
    finally:
        App._instance = original_instance

    assert calls == [
        {"title": "Kaleidos", "icon": ":/icons/kaleidos.svg", "subtitle": "Loading"},
        "ready",
    ]


def test_fast_splash_uses_legacy_application_name_when_display_name_is_empty():
    """The old applicationName API must brand the early surface."""
    app = _ApplicationSurface(application_name="Kaleidos")
    assert FastSplashController._application_title(app) == "Kaleidos"


def test_fast_splash_syncs_window_metadata_with_application_fallbacks():
    """Window attachment must fill missing legacy metadata from App state."""
    app = _ApplicationSurface(
        display_name="Kaleidos",
        application_icon=":/icons/kaleidos.svg",
    )
    controller = FastSplashController(None)
    controller._app = app
    controller._splash = _SplashSurface()
    controller._visibility_deferred = True

    controller._sync_window_metadata(_WindowSurface(splashSubtitle="Loading"))

    assert controller._splash.shown is True
    assert controller._splash.properties == {
        "splashTitle": "Kaleidos",
        "splashIcon": "qrc:/icons/kaleidos.svg",
        "splashSubtitle": "Loading",
    }


def test_fast_splash_ignores_metadata_after_close():
    """Late legacy setters must not resurrect a closed splash window."""
    controller = FastSplashController(None)
    controller._splash = _SplashSurface()
    controller._visibility_deferred = True
    controller.close()

    controller.update_metadata(title="Kaleidos", icon=":/icons/kaleidos.svg")

    assert controller._splash.shown is False
    assert controller._splash.properties == {}


def test_app_window_icon_forwards_legacy_qicon_to_fast_splash():
    """App.setWindowIcon(QIcon) must retain the legacy fast-splash contract."""
    calls = []
    app = object.__new__(App)
    app._app = SimpleNamespace(setWindowIcon=lambda icon: calls.append(("qt", icon)))
    app._update_fast_splash_metadata = lambda **metadata: calls.append(metadata)
    icon = QIcon()

    app.setWindowIcon(icon)

    assert calls[0] == ("qt", icon)
    assert calls[1] == {"icon": icon}


def test_fast_splash_converts_qml_ready_indexes_before_readiness_check():
    """QML property-var wrappers must participate in the readiness gate."""
    page = _PropertyObject()
    stack = _PropertyObject(
        currentWidget=page,
        currentIndex=0,
        _useSourceMode=False,
    )
    window = _PropertyObject(
        stackedWidget=stack,
        _pythonPageMode=True,
        _pythonReadyIndexes=_QmlVariant([0]),
    )

    assert FastSplashController._page_ready(window) is True


def test_fast_splash_reads_real_qml_ready_indexes(qapp):
    """A real QML property-var value must satisfy the Python readiness gate."""
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
Item {
    property bool _pythonPageMode: true
    property var _pythonReadyIndexes: [0]
    property var stackedWidget: stack

    Item {
        id: stack
        property int currentIndex: 0
        property var currentWidget: page
        property bool _useSourceMode: false
    }
    Item { id: page }
}
""",
        QUrl("fast-splash-readiness"),
    )
    window = component.create()
    assert window is not None, [error.toString() for error in component.errors()]
    ready_indexes = window.property("_pythonReadyIndexes")
    assert hasattr(ready_indexes, "toVariant")
    assert FastSplashController._page_ready(window) is True


def _builder(**overrides):
    resolved = []

    def resolve_icon(value):
        resolved.append(value)
        return "qrc" + value if value.startswith(":/") else value

    values = {
        "_splash_enabled": True,
        "_splash_icon": "",
        "_splash_title": "",
        "_splash_subtitle": "",
        "_resolve_icon_path": resolve_icon,
    }
    values.update(overrides)
    builder = SimpleNamespace(**values)
    builder.resolved = resolved
    return builder


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {},
            {
                "splashEnabled": True,
                "splashIcon": "",
                "splashTitle": "",
                "splashSubtitle": "",
            },
        ),
        (
            {
                "_splash_enabled": False,
                "_splash_icon": ":/icons/splash.svg",
                "_splash_title": 'Title "quoted" {brace}\nline',
                "_splash_subtitle": "Loading",
            },
            {
                "splashEnabled": False,
                "splashIcon": "qrc:/icons/splash.svg",
                "splashTitle": 'Title "quoted" {brace}\nline',
                "splashSubtitle": "Loading",
            },
        ),
    ],
)
def test_build_splash_properties(overrides, expected):
    builder = _builder(**overrides)
    assert build_splash_properties(builder) == expected
    expected_resolved = (
        [overrides["_splash_icon"]] if overrides.get("_splash_icon") else []
    )
    assert builder.resolved == expected_resolved


def test_build_splash_template_values_escapes_strings():
    builder = _builder(
        _splash_icon=":/icon.svg",
        _splash_title='Title "quoted"',
        _splash_subtitle="Loading",
    )
    escaped = build_splash_template_values(builder, lambda value: f"<{value}>")
    assert escaped == {
        "splash_enabled": "true",
        "splash_icon": "<qrc:/icon.svg>",
        "splash_title": '<Title "quoted">',
        "splash_subtitle": "<Loading>",
    }


def test_build_splash_properties_supports_bare_window_builder():
    builder = SimpleNamespace(_resolve_icon_path=lambda value: value)
    from prismqml.python.runtime.startup_defaults import DEFAULT_SPLASH_SUBTITLE

    assert build_splash_properties(builder) == {
        "splashEnabled": True,
        "splashIcon": "",
        "splashTitle": "",
        "splashSubtitle": DEFAULT_SPLASH_SUBTITLE,
    }


def test_splash_lifecycle_is_owned_by_navigation_window_core():
    qml_source = (ROOT / "prismqml/PrismQML/NavigationWindowCore.qml").read_text(
        encoding="utf-8"
    )
    python_source = (ROOT / "prismqml/python/window/_window_builder.py").read_text(
        encoding="utf-8"
    )
    window_core_source = (ROOT / "prismqml/python/window/window_core.py").read_text(
        encoding="utf-8"
    )
    cpp_source = (ROOT / "cpp/src/Window.cpp").read_text(encoding="utf-8")
    gallery_source = (ROOT / "examples/main.qml").read_text(encoding="utf-8")
    gallery_entry_source = (ROOT / "examples/main.py").read_text(encoding="utf-8")
    fast_splash_source = (
        ROOT / "prismqml/python/window/fast_splash.py"
    ).read_text(encoding="utf-8")
    lifecycle_source = (
        ROOT / "prismqml/python/window/_fast_splash_lifecycle.py"
    ).read_text(encoding="utf-8")

    assert "property bool splashEnabled: true" in qml_source
    assert "property bool _fastSplashExternalCover: false" in qml_source
    assert "visible: !window._fastSplashExternalCover" in qml_source
    assert "property int splashMinimumVisibleDuration:" in qml_source
    assert "_splashVisibleSinceMs = Date.now()" in qml_source
    assert "_splashTimer.restart()" in qml_source
    assert "property Component splashComponent:" in qml_source
    assert "readonly property bool _usesDefaultSplashComponent:" in qml_source
    assert "function _enableDeferredSplash()" in qml_source
    assert "app._attach_fast_splash(main_window)" not in gallery_entry_source
    assert "PrismQmlStartup.registerStartupWindow(window)" in qml_source
    assert "uses_default_splash" not in gallery_entry_source
    assert "PrismQmlFastStartupSplashEnabled" not in gallery_entry_source
    assert "fastStartupSplashEnabled" not in gallery_source
    assert "transition.setParentItem(root_item)" in fast_splash_source
    assert "transition.setParent(self)" in fast_splash_source
    assert "QQmlEngine.setObjectOwnership(" in fast_splash_source
    assert "QQmlEngine.ObjectOwnership.CppOwnership" in fast_splash_source
    assert "wintypes.HWND(0)" in lifecycle_source
    assert "HWND_TOPMOST" not in lifecycle_source
    assert "win.revealTransition.revealRadiusPixels" in fast_splash_source
    assert "self._reveal_component = component" in fast_splash_source
    reveal_qml = fast_splash_source.split("_REVEAL_QML = \"\"\"", 1)[1].split(
        "\"\"\"", 1
    )[0]
    assert "revealDuration: 400" in reveal_qml
    assert "transition.revealDone()" in reveal_qml
    assert "keepSourceHiddenOnExpand: true" in reveal_qml
    assert "PageTransition {" in reveal_qml
    assert "NavigationInternal.LazyPageCircleTransition" not in reveal_qml
    finish_reveal = fast_splash_source.split("    def _finish_reveal", 1)[1]
    assert "root_item.setProperty(\"visible\", False)" not in finish_reveal
    assert 'objectName: "windowSplashLoader"' in qml_source
    assert "build_splash_properties(self)" in python_source
    assert "self._mark_fast_splash_metadata_ready()" not in window_core_source
    assert "def mark_window_metadata_ready(self)" in fast_splash_source
    assert "self.mark_window_metadata_ready()" in fast_splash_source
    assert "create_splash" not in python_source
    assert "Window::createSplash" not in cpp_source
    assert "createSplash();" not in cpp_source
    assert "splashSubtitle:" in gallery_source
    assert 'property string splashSubtitle: "{splash_subtitle}"' in fast_splash_source
    assert "DEFAULT_SPLASH_SUBTITLE" in fast_splash_source
    assert "splashComponent.createObject" not in gallery_source
    splash_qml = fast_splash_source.split('_SPLASH_QML = """', 1)[1].split(
        '"""', 1
    )[0]
    assert "visible: false" in splash_qml
    assert "visible: true" not in splash_qml
    assert gallery_source.count("            visible: false") == 3
    assert gallery_source.count("            splashEnabled: false") == 3
    assert 'GALLERY_APPLICATION_TITLE = "PrismQML Gallery"' in gallery_entry_source
    assert "QGuiApplication.setApplicationDisplayName(GALLERY_APPLICATION_TITLE)" in gallery_entry_source
    assert 'splash.setProperty("splashTitle", str(application_title))' in fast_splash_source
    assert "self._show_qml_owned_window(main_window)" in fast_splash_source
    assert 'main_window.setProperty("_fastSplashExternalCover", True)' in fast_splash_source
    assert 'main_window.setProperty("_fastSplashExternalCover", False)' in lifecycle_source
    assert 'GALLERY_APPLICATION_ICON = "qrc:/app_icon.svg"' in gallery_entry_source
    assert "application_icon=GALLERY_APPLICATION_ICON" in gallery_entry_source
    assert "def show(" in fast_splash_source
    assert "splash_width: Optional[int] = None" in fast_splash_source
    assert "splash_height: Optional[int] = None" in fast_splash_source
    assert "initial_icon_ready = self._set_icon_metadata(initial_icon)" in fast_splash_source
    assert "self._icon_provider = FastSplashIconProvider()" in fast_splash_source
    app_source = (ROOT / "prismqml/python/window/app.py").read_text(encoding="utf-8")
    assert "splash_subtitle: Optional[str] = None" in app_source
