# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Exercise a native popup scrollbar with real Windows input. 使用真实 Windows 输入验证原生弹层滚动条。"""

from __future__ import annotations

import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPointF, QTimer, QUrl
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication

import prismqml
from prismqml import register_types
from prismqml.python.core.utils import qml_path


MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


class Rect(ctypes.Structure):
    """Win32 RECT. Win32 矩形。"""

    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class GuiThreadInfo(ctypes.Structure):
    """Win32 GUI thread state. Win32 GUI 线程状态。"""

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", Rect),
    ]


QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    property int selectedIndex: -1
    property string selectedText: ""

    width: 520
    height: 360

    ButtonCore {
        id: menuButton
        objectName: "menuButton"
        x: 60
        y: 50
        width: 300
        text: "Servers"
        feature: Enums.button.feature_dropdown
        menuItems: [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta",
            "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu",
            "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma"
        ]
        onMenuItemClicked: function(index, text) {
            selectedIndex = index
            selectedText = text
        }
    }
}
"""


class NativePopupProbe:
    """Drive one popup and collect native input evidence. 驱动一次弹层并采集原生输入证据。"""

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._configure_user32()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.engine = QQmlApplicationEngine()
        self.engine.addImportPath(str(qml_path().parent))
        register_types(self.engine)
        self.component = QQmlComponent(self.engine)
        source_url = QUrl.fromLocalFile(str(Path(__file__).resolve()))
        self.component.setData(QML_SOURCE, source_url)
        if self.component.status() != QQmlComponent.Status.Ready:
            raise RuntimeError(
                "; ".join(error.toString() for error in self.component.errors())
            )
        self.root = self.component.create(self.engine.rootContext())
        if self.root is None:
            raise RuntimeError("QML root creation failed")
        self.window = QQuickWindow()
        self.window.setTitle("PrismQML native popup SendInput probe")
        self.window.setGeometry(240, 180, 520, 360)
        self.root.setParentItem(self.window.contentItem())
        self.button = self.root.findChild(QObject, "menuButton")
        if self.button is None:
            raise RuntimeError("menuButton not found")
        self.trace: list[dict[str, object]] = []
        self.finished = False
        self.final_content_y = 0.0
        self.success = False

    def _configure_user32(self) -> None:
        self.user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.GetGUIThreadInfo.argtypes = [
            wintypes.DWORD,
            ctypes.POINTER(GuiThreadInfo),
        ]
        self.user32.GetGUIThreadInfo.restype = wintypes.BOOL
        self.user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self.user32.SetCursorPos.restype = wintypes.BOOL
        self.user32.mouse_event.argtypes = [
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self.user32.SetForegroundWindow.restype = wintypes.BOOL
        self.user32.GetCapture.restype = wintypes.HWND
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short

    @staticmethod
    def _hwnd_value(value: int | None) -> int:
        return int(value or 0)

    def _gui_state(self, label: str) -> None:
        process_id = wintypes.DWORD()
        thread_id = self.user32.GetWindowThreadProcessId(
            wintypes.HWND(int(self.window.winId())),
            ctypes.byref(process_id),
        )
        info = GuiThreadInfo()
        info.cbSize = ctypes.sizeof(GuiThreadInfo)
        ok = bool(self.user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)))
        self.trace.append(
            {
                "label": label,
                "ok": ok,
                "active": self._hwnd_value(info.hwndActive),
                "focus": self._hwnd_value(info.hwndFocus),
                "capture": self._hwnd_value(info.hwndCapture),
                "menu_owner": self._hwnd_value(info.hwndMenuOwner),
            }
        )

    def _window_snapshot(self, label: str) -> None:
        windows = []
        for window in QGuiApplication.allWindows():
            windows.append(
                {
                    "class": window.metaObject().className(),
                    "title": window.title(),
                    "visible": window.isVisible(),
                    "active": window.isActive(),
                    "win_id": int(window.winId()),
                    "flags": int(window.flags()),
                }
            )
        self.trace.append({"label": label, "windows": windows})

    def _popup_snapshot(self, label: str) -> None:
        popups = []
        popup = self._popup_core()
        if popup is not None:
            popups.append(
                {
                    "class": popup.metaObject().className(),
                    "is_open": bool(popup.property("isOpen")),
                    "is_closing": bool(popup.property("isClosing")),
                    "surface_visible": bool(popup.property("_surfaceVisible")),
                    "scale": popup.property("_scale"),
                    "qt_window": bool(popup.property("useQtPopupWindow")),
                }
            )
        descendants = list(self._object_descendants(self.button))
        self.trace.append(
            {
                "label": label,
                "popups": popups,
                "button_descendants": [
                    candidate.metaObject().className()
                    for candidate in descendants[:80]
                ],
            }
        )

    @staticmethod
    def _object_descendants(root):
        pending = list(root.children())
        while pending:
            child = pending.pop()
            yield child
            pending.extend(child.children())

    def _popup_core(self):
        dropdowns = [
            candidate
            for candidate in self._object_descendants(self.button)
            if candidate.metaObject().indexOfProperty("isMenuOpen") >= 0
            and candidate.metaObject().indexOfProperty("mainHovered") >= 0
        ]
        for dropdown in dropdowns:
            for candidate in self._object_descendants(dropdown):
                if (
                    candidate.metaObject().indexOfProperty("_itemsHeight") >= 0
                    and candidate.metaObject().indexOfProperty("_prewarmed") >= 0
                ):
                    return candidate
        return None

    def _all_objects(self):
        seen: set[int] = set()
        roots = [self.root]
        for window in QGuiApplication.allWindows():
            roots.append(window)
            content_item = getattr(window, "contentItem", lambda: None)()
            if content_item is not None:
                roots.append(content_item)
        for root in roots:
            candidates = [
                root,
                *root.findChildren(QObject),
                *self._visual_descendants(root),
            ]
            for candidate in candidates:
                identity = id(candidate)
                if identity in seen:
                    continue
                seen.add(identity)
                yield candidate

    def _visual_descendants(self, root):
        """Yield visual children because QML visual parents may differ from QObject parents. 枚举视觉子项以覆盖 QML 视觉父级。"""
        child_items = getattr(root, "childItems", lambda: [])()
        for child in child_items:
            yield child
            yield from self._visual_descendants(child)

    def _find_menu_item(self, text: str):
        popup = self._popup_core()
        if popup is not None:
            popup_content = popup.findChild(QQuickItem, "_popupContent")
            if popup_content is not None:
                for candidate in self._visual_descendants(popup_content):
                    if (
                        candidate.metaObject().indexOfProperty("isSeparator") >= 0
                        and candidate.property("text") == text
                    ):
                        return candidate
        matches = []
        for candidate in self._all_objects():
            if (
                candidate.metaObject().indexOfProperty("isSeparator") >= 0
                and candidate.property("text") == text
            ):
                candidate_window = candidate.window()
                matches.append(
                    {
                        "item": candidate,
                        "window_visible": bool(
                            candidate_window and candidate_window.isVisible()
                        ),
                        "window_class": candidate_window.metaObject().className()
                        if candidate_window
                        else "",
                        "window_id": int(candidate_window.winId())
                        if candidate_window
                        else 0,
                    }
                )
        self.trace.append(
            {
                "label": "menu_item_candidates",
                "items": [
                    {key: value for key, value in match.items() if key != "item"}
                    for match in matches
                ],
            }
        )
        for match in matches:
            if match["window_visible"]:
                return match["item"]
        return matches[0]["item"] if matches else None

    def _move(self, point: QPointF) -> None:
        QCursor.setPos(point.toPoint())

    def _mouse_down(self, point: QPointF) -> None:
        self._move(point)
        self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)

    def _mouse_up(self, point: QPointF) -> None:
        self._move(point)
        self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)

    def start(self) -> int:
        self.window.show()
        self.window.requestActivate()
        QTimer.singleShot(250, self._open_programmatically)
        QTimer.singleShot(3000, self._finish)
        self.app.exec()
        return 0 if self.success else 1

    def _open_programmatically(self) -> None:
        dropdowns = [
            candidate
            for candidate in self._object_descendants(self.button)
            if candidate.metaObject().indexOfProperty("isMenuOpen") >= 0
            and candidate.metaObject().indexOfMethod("openMenu()") >= 0
        ]
        if len(dropdowns) != 1:
            self.trace.append(
                {"label": "unexpected_dropdowns", "count": len(dropdowns)}
            )
            self._finish()
            return
        if not QMetaObject.invokeMethod(dropdowns[0], "openMenu"):
            self.trace.append({"label": "open_menu_invoke_failed"})
            self._finish()
            return
        QTimer.singleShot(600, self._scroll_down)

    def _hover_button(self) -> None:
        self.user32.SetForegroundWindow(wintypes.HWND(int(self.window.winId())))
        point = self.button.mapToGlobal(
            QPointF(self.button.width() / 2, self.button.height() / 2)
        )
        self.trace.append(
            {"label": "button_point", "x": point.x(), "y": point.y()}
        )
        self._move(point)
        QTimer.singleShot(250, lambda: self._open_down(point))

    def _open_down(self, point: QPointF) -> None:
        self._gui_state("before_open_down")
        self._mouse_down(point)
        self._gui_state("after_open_down")
        QTimer.singleShot(60, lambda: self._open_up(point))

    def _open_up(self, point: QPointF) -> None:
        self._mouse_up(point)
        self._gui_state("after_open_up")
        QTimer.singleShot(500, self._scroll_down)

    def _find_scrollbar(self):
        matches = [
            candidate
            for candidate in self._all_objects()
            if candidate.metaObject().indexOfProperty("minThumbSize") >= 0
            and candidate.metaObject().indexOfProperty("flickable") >= 0
            and bool(candidate.property("visible"))
        ]
        self.trace.append(
            {
                "label": "scrollbar_candidates",
                "count": len(matches),
                "classes": [match.metaObject().className() for match in matches],
            }
        )
        return matches[0] if matches else None

    def _scroll_snapshot(
        self, label: str, scrollbar, flickable, thumb, input_layer, handler
    ) -> None:
        popup_window = input_layer.window()
        grabber = (
            popup_window.mouseGrabberItem()
            if popup_window and hasattr(popup_window, "mouseGrabberItem")
            else None
        )
        self.trace.append(
            {
                "label": label,
                "content_y": flickable.property("contentY"),
                "content_height": flickable.property("contentHeight"),
                "view_height": flickable.property("height"),
                "thumb_y": thumb.property("y"),
                "thumb_height": thumb.property("height"),
                "input_y": input_layer.property("y"),
                "handler_active": bool(handler.property("active")),
                "capture": self._hwnd_value(self.user32.GetCapture()),
                "async_lbutton_down": bool(
                    self.user32.GetAsyncKeyState(0x01) & 0x8000
                ),
                "mouse_grabber": (
                    grabber.metaObject().className() if grabber else ""
                ),
            }
        )

    def _scroll_down(self) -> None:
        self._window_snapshot("after_open_windows")
        self._popup_snapshot("after_open_popups")
        scrollbar = self._find_scrollbar()
        if scrollbar is None:
            self._finish()
            return
        flickables = [
            candidate
            for candidate in self._all_objects()
            if "Flickable" in candidate.metaObject().className()
            and bool(candidate.property("visible"))
        ]
        if len(flickables) != 1:
            self.trace.append(
                {"label": "unexpected_flickables", "count": len(flickables)}
            )
            self._finish()
            return
        flickable = flickables[0]
        scrollbar.valueChanged.connect(
            lambda value: self.trace.append(
                {"label": "scrollbar_value_changed", "value": value}
            )
        )
        scrollbar.sliderMoved.connect(
            lambda: self.trace.append({"label": "scrollbar_slider_moved"})
        )
        scrollbar.sliderReleased.connect(
            lambda: self.trace.append({"label": "scrollbar_slider_released"})
        )
        thumbs = [
            child
            for child in scrollbar.childItems()
            if child.metaObject().className().startswith("QQuickRectangle")
            and child.height() < scrollbar.height()
        ]
        if len(thumbs) != 1:
            self.trace.append({"label": "unexpected_thumbs", "count": len(thumbs)})
            self._finish()
            return
        thumb = thumbs[0]
        input_layers = []
        for child in scrollbar.childItems():
            handlers = [
                handler
                for handler in child.children()
                if "PointHandler" in handler.metaObject().className()
            ]
            if handlers:
                input_layers.append((child, handlers[0]))
        if len(input_layers) != 1:
            self.trace.append(
                {"label": "unexpected_input_layers", "count": len(input_layers)}
            )
            self._finish()
            return
        input_layer, handler = input_layers[0]
        handler.grabChanged.connect(
            lambda transition, _point: self.trace.append(
                {
                    "label": "thumb_handler_grab_changed",
                    "transition": str(transition),
                    "transition_value": int(
                        getattr(transition, "value", transition)
                    ),
                }
            )
        )
        handler.activeChanged.connect(
            lambda: self.trace.append(
                {
                    "label": "thumb_handler_active_changed",
                    "active": bool(handler.property("active")),
                }
            )
        )
        point = thumb.mapToGlobal(QPointF(thumb.width() / 2, thumb.height() / 2))
        self.trace.append({"label": "scroll_point", "x": point.x(), "y": point.y()})
        self._scroll_snapshot(
            "before_scroll_down", scrollbar, flickable, thumb, input_layer, handler
        )
        self._mouse_down(point)
        QTimer.singleShot(
            100,
            lambda: self._scroll_move(
                scrollbar, flickable, thumb, input_layer, handler, point, 1
            ),
        )

    def _scroll_move(
        self, scrollbar, flickable, thumb, input_layer, handler, start, step: int
    ) -> None:
        self._scroll_snapshot(
            f"before_scroll_move_{step}",
            scrollbar,
            flickable,
            thumb,
            input_layer,
            handler,
        )
        point = QPointF(start.x(), start.y() + step * 24)
        self._move(point)
        if step < 6:
            QTimer.singleShot(
                100,
                lambda: self._scroll_move(
                    scrollbar,
                    flickable,
                    thumb,
                    input_layer,
                    handler,
                    start,
                    step + 1,
                ),
            )
            return
        QTimer.singleShot(
            100,
            lambda: self._scroll_up(
                scrollbar, flickable, thumb, input_layer, handler, point
            ),
        )

    def _scroll_up(
        self, scrollbar, flickable, thumb, input_layer, handler, point
    ) -> None:
        self._scroll_snapshot(
            "before_scroll_up", scrollbar, flickable, thumb, input_layer, handler
        )
        self._mouse_up(point)
        QTimer.singleShot(
            200,
            lambda: self._scroll_finished(
                scrollbar, flickable, thumb, input_layer, handler
            ),
        )

    def _scroll_finished(
        self, scrollbar, flickable, thumb, input_layer, handler
    ) -> None:
        self._scroll_snapshot(
            "after_scroll_up", scrollbar, flickable, thumb, input_layer, handler
        )
        self.final_content_y = float(flickable.property("contentY"))
        value_changes = [
            event
            for event in self.trace
            if event.get("label") == "scrollbar_value_changed"
        ]
        drag_snapshots = [
            event
            for event in self.trace
            if str(event.get("label", "")).startswith("before_scroll_move_")
            or event.get("label") == "before_scroll_up"
        ]
        release_snapshots = [
            event for event in self.trace if event.get("label") == "after_scroll_up"
        ]
        self.success = bool(
            self.final_content_y > 200
            and len(value_changes) >= 4
            and drag_snapshots
            and all(event.get("async_lbutton_down") for event in drag_snapshots)
            and release_snapshots
            and release_snapshots[-1].get("capture") == 0
            and not release_snapshots[-1].get("handler_active")
        )
        self._finish()

    def _item_down(self) -> None:
        self._window_snapshot("after_open_windows")
        self._popup_snapshot("after_open_popups")
        item = self._find_menu_item("Beta")
        if item is None:
            self.trace.append({"label": "beta_not_found"})
            self._finish()
            return
        point = item.mapToGlobal(QPointF(item.width() / 2, item.height() / 2))
        self.trace.append(
            {
                "label": "beta_point",
                "x": point.x(),
                "y": point.y(),
                "window": int(item.window().winId()) if item.window() else 0,
            }
        )
        self._gui_state("before_item_down")
        self._mouse_down(point)
        self._gui_state("after_item_down")
        QTimer.singleShot(100, lambda: self._item_up(point))

    def _item_up(self, point: QPointF) -> None:
        self._mouse_up(point)
        self._gui_state("after_item_up")
        QTimer.singleShot(300, self._finish)

    def _finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        result = {
            "prismqml_file": prismqml.__file__,
            "prismqml_version": prismqml.__version__,
            "selected_index": self.root.property("selectedIndex"),
            "selected_text": self.root.property("selectedText"),
            "graphics_api": str(self.window.rendererInterface().graphicsApi()),
            "success": self.success,
            "trace": self.trace,
        }
        print(json.dumps(result, ensure_ascii=False))
        self.window.close()
        self.app.quit()


def main() -> int:
    """Run the visible native input probe. 运行可见原生输入探针。"""
    QQuickWindow.setGraphicsApi(
        QSGRendererInterface.GraphicsApi.Direct3D11
    )
    probe = NativePopupProbe()
    return probe.start()


if __name__ == "__main__":
    raise SystemExit(main())
