# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
"""设置容器基类 — SettingsCore

每个 SettingsCore 子类把若干 SettingEntry 作为类属性挂出去,然后通过
get / set 读写,save / load 落盘 / 装载。 持久化格式是 JSON:

    {
        "Window": {              # SettingEntry.group
            "LazyLoading": true,    # SettingEntry.name -> entry.dump()
            "DwmShadow": true,
        }
    }

约定:
- group 不带 name 的条目会被序列化成 {"Group": value} 这种扁平形式
- 写盘走 (临时文件 + os.replace) 原子替换,中断不会留半截 JSON
- load 完成后发一次 configChanged,UI 层一次性刷新

实现层抽出两个内部 helper:
- _iter_entries(): 读类定义阶段固化的 _setting_entries 缓存, 列出所有 SettingEntry
- _compose_key():  与 SettingEntry.key 共享同一份键拼接逻辑
"""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Iterator, Tuple

from PySide6.QtCore import QObject, Signal

from .config_item import SettingEntry, _compose_key
from ..core import debug, info, warning, error


class SettingsCore(QObject):
    """配置容器基类 — 每个实例绑定一个独立 JSON 文件。"""

    # 修改了 restart=True 的条目时通知前端"建议重启",由 UI 决定怎么提示
    restartRequested = Signal()
    # 任何条目落盘 / load 完成后广播一次,适合做"配置已变化"全局刷新
    configChanged = Signal()

    # 每个子类在"类定义阶段"由 __init_subclass__ 填好的 {attr_name: SettingEntry}。
    # 用类创建钩子一次性固化, 取代运行时对 dir() 的反复反射扫描:
    # 条目集合在子类成形时就已确定, 没必要每次读写都重新枚举类属性。
    _setting_entries: dict = {}

    def __init_subclass__(cls, **kwargs):
        """子类一被定义就锁定它的 SettingEntry 集合。

        合并父链上已登记的条目 (支持配置类继承再扩展), 再叠加本类
        ``__dict__`` 里新声明的 SettingEntry, 存进 ``cls._setting_entries``。
        """
        super().__init_subclass__(**kwargs)
        merged: dict = {}
        for base in cls.__mro__[1:]:
            inherited = base.__dict__.get("_setting_entries")
            if inherited:
                merged.update(inherited)
        for attr, candidate in cls.__dict__.items():
            if isinstance(candidate, SettingEntry):
                merged[attr] = candidate
        cls._setting_entries = merged

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file: Path = None

    # ---------- 文件路径 ----------

    @property
    def file(self) -> Path:
        return self._file

    @file.setter
    def file(self, path):
        self._file = Path(path) if path else None

    # ---------- 内部条目出口 ----------

    def _iter_entries(self) -> Iterator[Tuple[str, SettingEntry]]:
        """Yield (attr_name, entry) for every SettingEntry defined on this class.

        直接读 :attr:`_setting_entries` 这份在类定义阶段固化的缓存,
        不再运行时反射, 既快又是唯一出口。
        """
        yield from type(self)._setting_entries.items()

    # ---------- get / set ----------

    def get(self, entry: SettingEntry):
        """读取单个条目的当前值。"""
        return entry.value

    def set(self, entry: SettingEntry, value, save: bool = True):
        """写入单个条目。

        实际写入交给 :class:`SettingEntry` 自身的 setter(内部负责 coerce、
        去重并发 ``valueUpdated``),本方法只在条目"确有变化"后再决定落盘
        与全局通知。据写入前后值是否相等判断变化,而非提前比对入参。
        """
        previous = entry.value
        entry.value = self._isolate(entry, value)
        if entry.value == previous:
            # 经 coerce 后与旧值一致(含入参本就相等的情形),不落盘不通知。
            return

        if save:
            self.save()

        if entry.restart:
            self.restartRequested.emit()

        self.configChanged.emit()

    @staticmethod
    def _isolate(entry: SettingEntry, value):
        """对可深拷贝的值做隔离副本;Qt 原生对象退化为原值。

        某些 Qt 对象 (QPixmap / QObject 子类等) 不支持 deepcopy,
        此时直接返回原值,仅失去隔离,值本身仍可用。
        """
        try:
            return deepcopy(value)
        except (TypeError, AttributeError) as exc:
            debug(f"deepcopy 不支持 {entry.key} 的值,直接赋值兜底: {exc}")
            return value

    # ---------- 序列化 / 反序列化 ----------

    def _to_mapping(self, persist: bool = True) -> dict:
        """把所有 SettingEntry 折叠成嵌套 dict。

        persist=True (默认) 走 entry.dump(),允许子类自定义持久化形态;
        persist=False 直接读 .value,适合调试 / 内存快照。

        约束: 同一个 group 下要么全部带 name (产出嵌套 dict),
        要么只挂一个 name="" 的扁平条目 (产出标量)。混用时跳过冲突项
        并打 warning,而不是 TypeError 崩溃。
        """
        result: dict = {}
        for _, entry in self._iter_entries():
            payload = entry.dump() if persist else entry.value

            if entry.name:
                # 嵌套写入: result[group][name] = payload
                bucket = result.setdefault(entry.group, {})
                if not isinstance(bucket, dict):
                    warning(
                        f"group={entry.group!r} 已被扁平条目占用为标量,"
                        f"跳过子项 {entry.key!r} 防止覆盖"
                    )
                    continue
                bucket[entry.name] = payload
            else:
                # 扁平写入: result[group] = payload
                if entry.group in result:
                    warning(
                        f"group={entry.group!r} 已存在嵌套子项,"
                        f"跳过扁平条目 {entry.key!r} 防止冲突"
                    )
                    continue
                result[entry.group] = payload
        return result

    def save(self):
        """原子写入配置文件:先写 .tmp,再 os.replace 一气换上。"""
        if not self._file:
            warning("未设置配置文件路径 Config file path not set")
            return

        tmp_fd = None
        tmp_path = None
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=str(self._file.parent), suffix=".tmp"
            )
            # 一旦 os.fdopen 接管了 fd,后面就不再由我们关闭
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fp:
                tmp_fd = None
                json.dump(self._to_mapping(), fp, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._file)
            tmp_path = None
            info(f"配置已保存 Config saved: {self._file}")
        except Exception as exc:
            error(f"保存失败 Save failed: {exc}")
        finally:
            # 兜底清理:os.fdopen 没接管的 fd / 没替换成功的 .tmp
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def load(self, file=None):
        """从磁盘装入 JSON,逐条灌进对应 SettingEntry。"""
        if file:
            self._file = Path(file)

        if not self._file or not self._file.exists():
            info(
                f"配置文件不存在,使用默认值 Config file not found, using defaults: {self._file}"
            )
            return

        try:
            with open(self._file, encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception as exc:
            error(f"加载失败 Load failed: {exc}")
            return

        if not isinstance(payload, dict):
            error(
                f"配置文件根节点非 dict Config file root is not dict: {self._file}"
            )
            return

        # 反射出 "key -> entry" 查找表
        index = {entry.key: entry for _, entry in self._iter_entries()}

        for group, group_payload in payload.items():
            if isinstance(group_payload, dict):
                for child, child_value in group_payload.items():
                    full = _compose_key(group, child)
                    if full in index:
                        index[full].load(child_value)
            else:
                # 整组就是一个标量(无 name 的扁平条目)
                if group in index:
                    index[group].load(group_payload)

        info(f"配置已加载 Config loaded: {self._file}")
        self.configChanged.emit()


__all__ = ["SettingsCore"]
