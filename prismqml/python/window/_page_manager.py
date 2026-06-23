# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""FluentQML Page Manager - 页面生命周期管理

负责懒加载、页面创建、异步加载等页面管理逻辑。
从 window_base.py 抽取，作为 Mixin 注入 WindowCore。
"""

from typing import Any, Dict, Optional, Type

from PySide6.QtCore import QObject, QTimer, QMetaObject, Q_ARG
from PySide6.QtQuick import QQuickItem

from ..core.logger import warning, info, error


class PageManagerMixin:
    """页面管理器 Mixin，提供懒加载和页面生命周期管理"""

    # ==================== 懒加载管理（统一入口） ====================
    # Lazy loading is fully managed by Python side
    # QML side only provides animation and UI rendering
    # 懒加载完全由Python侧管理，QML侧只负责动画和UI渲染

    def _ensure_page_created(self, index: int):
        """确保指定索引的页面已创建（同步）"""
        if index not in self._pages:
            self._create_page(index)

    def _create_page(self, index: int):
        """创建页面内容"""
        # 获取导航项（顶部+底部）
        all_items = self._nav_items + self._bottom_nav_items
        if index >= len(all_items):
            return

        item = all_items[index]

        if self._window is None:
            return

        # 查找对应的页面占位容器
        page_container = self._find_child_by_name(f"page_{index}")

        if page_container is None:
            warning(f"未找到页面容器: page_{index}")
            return
        
        # 检查是否已有实例（传入实例模式）或需要创建
        page_instance = None
        if item._page_instance is not None:
            page_instance = item._page_instance
        elif getattr(item, 'page_getter', None):
            # 使用page_getter获取页面实例（懒加载工厂模式）
            page_instance = item.page_getter()
            item._page_instance = page_instance
        elif item.page_class:
            # 使用page_class创建页面实例（懒加载模式）
            page_instance = item.page_class()
            item._page_instance = page_instance
        elif item.page_builder:
            # 兼容旧的page_builder模式，直接返回普通对象并在后续直接赋值
            class Wrapper(QObject):
                pass
            wrapper = Wrapper()
            wrapper._qml_item = page_container
            wrapper._parent = None
            wrapper._children = []
            wrapper._pending_properties = {}
            item._page_instance = item.page_builder(wrapper)
            self._pages[index] = wrapper
            info(f"创建页面: {item.text}")
            return
        else:
            return

        # 将页面的QML组件添加到占位容器中
        if page_instance._qml_item:
            page_instance._qml_item.setParentItem(page_container)

            # 通过信号绑定尺寸到父容器
            from shiboken6 import isValid

            def bind_size():
                if isValid(page_instance._qml_item) and isValid(page_container):
                    w = page_container.width()
                    h = page_container.height()
                    if w > 0 and h > 0:
                        page_instance._qml_item.setWidth(w)
                        page_instance._qml_item.setHeight(h)

            page_container.widthChanged.connect(bind_size)
            page_container.heightChanged.connect(bind_size)
            QTimer.singleShot(50, bind_size)
        else:
            warning(f"[_create_page] page_{index} _qml_item 为 None!")

        self._pages[index] = page_instance
        info(f"创建页面: {item.text}")

        # 检查页面是否有延迟创建队列
        if hasattr(page_instance, "_deferred_queue") and page_instance._deferred_queue:
            page_instance.startBatchCreation()


    def _find_child_by_name(self, name: str) -> Optional[QQuickItem]:
        """根据objectName查找子项"""
        if self._window is None:
            return None

        def find_recursive(item: QQuickItem) -> Optional[QQuickItem]:
            if item.objectName() == name:
                return item
            for child in item.childItems():
                result = find_recursive(child)
                if result:
                    return result
            return None

        return find_recursive(self._window.contentItem())

    def _on_nav_changed(self, index: int):
        """导航项切换回调（QML触发）"""
        self._current_index = index

        # Python侧懒加载：页面未创建时异步加载并显示loading
        if self._lazy_loading and index not in self._pages:
            self._start_async_page_load(index)
        else:
            self._switch_to_index(index)

        self.currentIndexChanged.emit(index)

    def _switch_to_index(self, index: int):
        """触发QML侧页面切换"""
        if self._window:
            try:
                QMetaObject.invokeMethod(
                    self._window, "navigateTo", Q_ARG("QVariant", index)
                )
            except RuntimeError as exc:
                warning(f"页面切换失败: {exc}")

    def _start_async_page_load(self, index: int):
        """异步加载页面（显示loading动画）

        流程：
        1. 显示QML侧的_pythonLoading覆盖层
        2. 延迟16ms让loading动画先渲染
        3. 创建页面实例
        4. 如果页面有_deferred_queue，启动分批创建
        5. 完成后隐藏loading覆盖层
        """
        from PySide6.QtWidgets import QApplication

        # 显示loading
        if self._window:
            try:
                QMetaObject.invokeMethod(
                    self._window, "_startPythonLoading", Q_ARG("QVariant", index)
                )
            except RuntimeError:
                # Method may not exist, ignore 方法可能不存在
                pass

        # 获取导航项
        all_items = self._nav_items + self._bottom_nav_items
        if index >= len(all_items):
            self._finish_loading()
            return

        item = all_items[index]
        page_container = self._find_child_by_name(f"page_{index}")

        has_loader = item.page_class is not None or getattr(item, 'page_getter', None) is not None or item._page_instance is not None
        if page_container is None or not has_loader:
            self._finish_loading()
            return

        def on_page_ready(page_instance):
            """页面创建完成回调"""
            if page_instance is None:
                self._finish_loading()
                return

            item._page_instance = page_instance

            # 将页面的QML组件添加到占位容器中
            if page_instance._qml_item:
                page_instance._qml_item.setParentItem(page_container)

                # 通过信号绑定尺寸到父容器
                # Python 无法直接访问 QQuickAnchors，使用信号绑定代替
                # Use signal binding since Python cannot access QQuickAnchors
                from shiboken6 import isValid

                def bind_size_async():
                    if isValid(page_instance._qml_item) and isValid(page_container):
                        w = page_container.width()
                        h = page_container.height()
                        if w > 0 and h > 0:
                            page_instance._qml_item.setWidth(w)
                            page_instance._qml_item.setHeight(h)
                            # 强制触发 widthChanged/heightChanged 信号
                            # 确保页面内部子组件（如 IconPage 的 _main Layout）能够正确更新
                            # Force emit widthChanged/heightChanged to ensure internal
                            # child components receive the size update
                            try:
                                page_instance._qml_item.widthChanged.emit()
                                page_instance._qml_item.heightChanged.emit()
                            except Exception as e:
                                warning(f"页面尺寸信号触发失败: {e}")

                page_container.widthChanged.connect(bind_size_async)
                page_container.heightChanged.connect(bind_size_async)
                # 延迟初始化，等待容器尺寸稳定
                QTimer.singleShot(50, bind_size_async)
                # 更长的延迟再试一次，确保布局完全稳定
                QTimer.singleShot(200, bind_size_async)

                # Hide page content during batch creation if has heavy widgets
                # 如果有重型组件，分批创建期间隐藏页面内容
                has_deferred = (
                    hasattr(page_instance, "_deferred_queue")
                    and page_instance._deferred_queue
                )
                if has_deferred:
                    page_instance._qml_item.setOpacity(0)

            self._pages[index] = page_instance
            info(f"异步创建页面: {item.text}")

            # Check if page has deferred widgets (heavy widgets auto-queued)
            # 检查页面是否有延迟组件（重型组件自动入队）
            has_deferred = (
                hasattr(page_instance, "_deferred_queue")
                and page_instance._deferred_queue
            )
            if has_deferred:
                # Start batch adding deferred widgets 开始分批添加延迟组件
                def on_batch_complete():
                    # Show page content after batch creation 分批创建完成后显示页面内容
                    if page_instance._qml_item:
                        page_instance._qml_item.setOpacity(1)
                    self._finish_loading_and_switch(index)

                page_instance.startBatchCreation(on_complete=on_batch_complete)
            else:
                # No deferred widgets, done immediately 无延迟组件，立即完成
                self._finish_loading_and_switch(index)

        def do_create():
            """延迟创建页面（让loading动画先显示）"""
            try:
                if getattr(item, 'page_getter', None):
                    page_instance = item.page_getter()
                elif item.page_class:
                    page_instance = item.page_class()
                elif item._page_instance:
                    page_instance = item._page_instance
                else:
                    page_instance = None
                on_page_ready(page_instance)
            except Exception as e:
                error(f"页面创建失败: {e}")
                on_page_ready(None)

        # 延迟到下一事件循环让 loading 动画先显示
        # singleShot(0) 跟随事件循环节拍, 不依赖 60fps 帧时长
        QTimer.singleShot(0, do_create)

    def _finish_loading_and_switch(self, index: int):
        """完成加载并切换到目标页面"""
        self._finish_loading()
        self._switch_to_index(index)

    def _finish_loading(self):
        """完成加载，隐藏loading动画"""
        if self._window:
            try:
                QMetaObject.invokeMethod(self._window, "_finishPythonLoading")
            except RuntimeError:
                # Method may not exist, ignore 方法可能不存在
                pass
