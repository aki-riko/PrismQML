# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MapControl lazy creation and layer contracts. MapControl 延迟创建与图层合同。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "map-control-scene.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/media"

Item {
    width: 480
    height: 360

    QtObject {
        id: probe
        property int failureCount: 0
    }

    MapControl {
        id: mapControl
        objectName: "mapControl"
        pluginName: "osm"
        pluginParameters: [
            { "name": "osm.mapping.highdpi_tiles", "value": true }
        ]
    }

    Connections {
        function onAvailabilityFailed(message) { probe.failureCount += 1 }

        target: mapControl
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 5_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _evaluate(instance: QObject, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def _invoke(instance: QObject, source: str) -> None:
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    expression.evaluate()
    assert not expression.hasError(), expression.error().toString()


def _class_names(root: QQuickItem) -> list[str]:
    return sorted({child.metaObject().className() for child in root.findChildren(QObject)})


def _geo_maps(root: QQuickItem) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if child.metaObject().className() == "QDeclarativeGeoMap"
    ]


def _loaded_surface(control: QQuickItem) -> QQuickItem:
    """Return the incubated surface item of one control. 返回控件已孵化的表面对象。"""
    items = [
        loader.property("item")
        for loader in control.childItems()
        if loader.metaObject().className().startswith("QQuickLoader")
    ]
    loaded = [item for item in items if isinstance(item, QQuickItem)]
    assert len(loaded) == 1, _class_names(control)
    return loaded[0]


def _create_scene():
    engine = QQmlEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root, warnings


def _dispose(engine, component, root) -> None:
    for obj in (root, component, engine):
        if obj is not None:
            obj.deleteLater()
    _pump(1)


def test_map_control_does_not_create_the_geoservices_plugin(qapp):
    """Construction must not create the map or its plugin. 构造期不得创建地图与插件。"""
    engine, component, root, warnings = _create_scene()
    try:
        control = root.findChild(QQuickItem, "mapControl")
        assert control is not None

        assert control.property("active") is False
        assert control.property("surfaceCreated") is False
        assert control.property("available") is False
        assert control.property("degraded") is False
        assert control.property("mapReady") is False
        assert control.property("availabilityState") == _evaluate(
            control, "Enums.media.availability_unknown"
        )
        assert control.property("layerCount") == 0
        assert _geo_maps(control) == [], _class_names(control)

        # Availability probing compiles the surface without creating it
        # 可用性探测只编译表面，不创建实例
        _invoke(control, "probeAvailability()")
        assert _wait_for(lambda: control.property("available") is True)
        assert control.property("surfaceCreated") is False
        assert _geo_maps(control) == [], _class_names(control)
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_map_control_activates_with_injected_provider(qapp):
    """activate() incubates the map with the injected provider. activate() 用注入提供方孵化地图。"""
    engine, component, root, warnings = _create_scene()
    try:
        control = root.findChild(QQuickItem, "mapControl")
        assert control is not None

        _invoke(control, "activate()")
        assert _wait_for(lambda: control.property("surfaceCreated") is True), _class_names(
            control
        )
        assert control.property("active") is True
        assert control.property("available") is True
        assert control.property("degraded") is False
        assert _geo_maps(control) != [], _class_names(control)
        surface = _loaded_surface(control)

        # Injected provider name and parameters reach the Qt plugin
        # 注入的提供方名称与参数到达 Qt 插件
        assert _evaluate(surface, "mapItem.plugin.name") == "osm"
        assert (
            _evaluate(surface, "mapItem.plugin.parameters[0].name")
            == "osm.mapping.highdpi_tiles"
        )
        assert _evaluate(surface, "mapItem.plugin.parameters[0].value") is True
        assert _evaluate(surface, "mapItem.copyrightsVisible") is True
        assert abs(
            float(_evaluate(surface, "mapItem.zoomLevel"))
            - float(_evaluate(control, "Enums.media.map_default_zoom"))
        ) < 0.001
        # mapReady is forwarded from the Qt map; tile readiness needs network and is
        # not asserted here. mapReady 由 Qt 地图转发；瓦片就绪依赖网络，此处不断言。
        _pump(50)
        assert control.property("mapReady") == _evaluate(surface, "mapItem.mapReady")
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_map_scheduler_gate_defers_surface_activation(qapp):
    """Scheduler gating defers map surface creation. 调度门控延迟地图表面创建。"""
    engine, component, root, warnings = _create_scene()
    try:
        control = root.findChild(QQuickItem, "mapControl")
        assert control is not None
        control.setProperty("schedulerActive", False)
        _invoke(control, "activate()")
        assert control.property("surfaceCreated") is False

        control.setProperty("schedulerActive", True)
        assert _wait_for(lambda: control.property("surfaceCreated"))
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_map_control_layers_and_viewport(qapp):
    """Layers, centre and zoom stay in sync with the map. 图层、中心与缩放与地图同步。"""
    engine, component, root, warnings = _create_scene()
    try:
        control = root.findChild(QQuickItem, "mapControl")
        assert control is not None
        _invoke(control, "activate()")
        assert _wait_for(lambda: control.property("surfaceCreated") is True)
        surface = _loaded_surface(control)

        _invoke(control, "addMarker(31.23, 121.47, 'Shanghai')")
        assert control.property("layerCount") == 1
        assert _wait_for(
            lambda: _evaluate(surface, "markerView.mapItems.length") == 1
        ), _evaluate(surface, "markerView.mapItems.length")

        _invoke(
            control,
            "addPolyline([{ 'latitude': 31.0, 'longitude': 121.0 },"
            " { 'latitude': 31.1, 'longitude': 121.1 }])",
        )
        assert control.property("layerCount") == 2
        assert _wait_for(
            lambda: _evaluate(surface, "polylineView.mapItems.length") == 1
        )

        _invoke(control, "addCircle(31.3, 121.5, 500.0)")
        assert control.property("layerCount") == 3
        assert _wait_for(
            lambda: _evaluate(surface, "circleView.mapItems.length") == 1
        )

        _invoke(control, "removeMarkerAt(0)")
        assert control.property("layerCount") == 2
        assert _wait_for(
            lambda: _evaluate(surface, "markerView.mapItems.length") == 0
        )

        _invoke(control, "clearLayers()")
        assert control.property("layerCount") == 0
        assert _evaluate(control, "markers.length") == 0
        assert _evaluate(control, "polylines.length") == 0
        assert _evaluate(control, "circles.length") == 0

        # Viewport control 视口控制
        _invoke(control, "setCenter(31.23, 121.47)")
        assert control.property("center") is None
        assert abs(float(control.property("latitude")) - 31.23) < 0.001
        assert abs(float(control.property("longitude")) - 121.47) < 0.001
        assert _wait_for(
            lambda: abs(float(_evaluate(surface, "mapItem.center.latitude")) - 31.23)
            < 0.001
        )

        before = float(control.property("zoomLevel"))
        _invoke(control, "zoomIn()")
        assert float(control.property("zoomLevel")) > before
        assert _wait_for(
            lambda: abs(
                float(_evaluate(surface, "mapItem.zoomLevel"))
                - float(control.property("zoomLevel"))
            )
            < 0.001
        )
        _invoke(control, "zoomOut()")
        assert abs(float(control.property("zoomLevel")) - before) < 0.001
        assert warnings == []
    finally:
        _dispose(engine, component, root)


def test_map_sources_contain_no_injected_endpoints():
    """Map QML must not hardcode tile URLs or credentials. 地图 QML 不得硬编码瓦片 URL 或凭据。"""
    media_root = ROOT / "prismqml" / "PrismQML" / "controls" / "media"
    offenders = []
    for path in sorted(media_root.rglob("*.qml")):
        text = path.read_text(encoding="utf-8")
        for token in ("http://", "https://", "apiKey", "api_key", "accessToken"):
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert offenders == []
