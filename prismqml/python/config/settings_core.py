# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

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

类级 SettingEntry 只定义 schema prototype；每个 SettingsCore 实例持有独立克隆。
保存与加载都先在独立快照上完成，原子提交成功后才更新实例值和信号。
"""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Iterator, Tuple

from PySide6.QtCore import QObject, Signal

from .config_item import SettingEntry
from ..core import debug, info, warning, error, exception


def _merge_setting_entries(cls) -> dict:
    """按 C3 最终属性解析构造 schema,保留非条目 shadow。"""
    names = []
    for base in cls.__mro__[1:]:
        for attr in base.__dict__.get("_setting_entries", {}):
            if attr not in names:
                names.append(attr)
    for attr, candidate in cls.__dict__.items():
        if isinstance(candidate, SettingEntry) and attr not in names:
            names.append(attr)
    merged = {}
    for attr in names:
        candidate = next(
            base.__dict__[attr] for base in cls.__mro__ if attr in base.__dict__
        )
        if isinstance(candidate, SettingEntry):
            merged[attr] = candidate
    return merged


def _validate_setting_entries(entries: dict):
    """拒绝会让 JSON 无损往返不成立的 schema。"""
    keys = {}
    group_shapes = {}
    for attr, entry in entries.items():
        entry_type = type(entry)
        if entry_type.dump is not SettingEntry.dump:
            if entry_type.encode is SettingEntry.encode:
                raise TypeError(
                    f"{entry_type.__name__} 必须用 encode(value) 取代 dump() override"
                )
        if entry_type.load is not SettingEntry.load:
            if entry_type.decode is SettingEntry.decode:
                raise TypeError(
                    f"{entry_type.__name__} 必须用 decode(raw) 取代 load() override"
                )
        schema_key = (entry.group, entry.name)
        if schema_key in keys:
            raise TypeError(
                f"配置 schema 重复 key {entry.key!r}: {keys[schema_key]!r}, {attr!r}"
            )
        keys[schema_key] = attr
        shape = "nested" if entry.name else "flat"
        previous = group_shapes.setdefault(entry.group, shape)
        if previous != shape:
            raise TypeError(
                f"配置 group {entry.group!r} 不能混用 flat 与 nested 条目"
            )


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
        merged = _merge_setting_entries(cls)
        _validate_setting_entries(merged)
        cls._setting_entries = merged

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file: Path = None
        self._entries = {}
        self._entry_lookup = {}
        for attr, prototype in type(self)._setting_entries.items():
            try:
                bound = prototype.clone(parent=self)
            except TypeError as exc:
                raise TypeError(
                    f"{type(self).__name__}.{attr} 无法绑定独立 SettingEntry; "
                    "自定义构造器必须 override clone(parent)"
                ) from exc
            bound._replace_value(self._isolate(bound, bound.default_value), False)
            self._entries[attr] = bound
            self._entry_lookup[prototype] = bound
            self._entry_lookup[bound] = bound

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

        只返回当前实例绑定的独立条目,不暴露类级 schema prototype。
        """
        yield from self._entries.items()

    # ---------- get / set ----------

    def entry(self, entry: SettingEntry) -> SettingEntry:
        """把 schema prototype 或本实例条目解析为绑定条目。"""
        try:
            return self._entry_lookup[entry]
        except (KeyError, TypeError) as exc:
            raise ValueError("SettingEntry 不属于当前 SettingsCore 实例") from exc

    def get(self, entry: SettingEntry):
        """读取单个条目的当前值。"""
        return self.entry(entry).value

    def set(self, entry: SettingEntry, value, save: bool = True) -> bool:
        """写入单个条目。

        候选值与信号参数先完整准备。save=True 时只有原子替换成功才
        提交实例值并发信号;失败时实例值从未改变。
        """
        current = self.entry(entry)
        codec = current.clone()
        candidate = codec.prepare(self._isolate(current, value))
        prepared = current._prepare_commit(candidate)
        if prepared.stored == current.value:
            # 经 coerce 后与旧值一致(含入参本就相等的情形),不落盘不通知。
            return True

        if save and not self._persist({current: prepared.stored}):
            return False

        current._apply_prepared(prepared)
        if current.restart:
            self.restartRequested.emit()

        self.configChanged.emit()
        return True

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

    def _to_mapping(self, persist: bool = True, overrides=None) -> dict:
        """把所有 SettingEntry 折叠成嵌套 dict。

        persist=True (默认) 走 entry.encode(value),允许自定义持久化形态;
        persist=False 直接读 .value,适合调试 / 内存快照。

        schema 冲突已在类定义阶段拒绝,因此这里不会静默丢字段。
        """
        overrides = overrides or {}
        result: dict = {}
        for _, entry in self._iter_entries():
            value = overrides.get(entry, entry.value)
            if persist:
                codec = entry.clone()
                payload = codec.encode(self._isolate(entry, value))
            else:
                payload = value

            if entry.name:
                bucket = result.setdefault(entry.group, {})
                bucket[entry.name] = payload
            else:
                result[entry.group] = payload
        return result

    @staticmethod
    def _cleanup_atomic_write(tmp_fd, tmp_path):
        """清理未被 fdopen 接管的句柄与未完成替换的临时文件。"""
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError as exc:
                debug(f"关闭配置临时文件句柄失败: {exc}")
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError as exc:
                warning(f"清理配置临时文件失败: {tmp_path}: {exc}")

    def _write_mapping(self, mapping: dict):
        """写入完整快照;os.replace 是唯一持久化提交点。"""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self._file.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fp:
                tmp_fd = None
                json.dump(mapping, fp, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._file)
            tmp_path = None
        finally:
            self._cleanup_atomic_write(tmp_fd, tmp_path)

    def _persist(self, overrides=None) -> bool:
        """序列化并原子提交快照;普通扩展异常保留 traceback。"""
        if not self._file:
            warning("未设置配置文件路径 Config file path not set")
            return False
        try:
            self._write_mapping(self._to_mapping(overrides=overrides))
        except Exception as exc:
            exception(f"保存失败 Save failed: {exc}")
            return False
        return True

    def save(self) -> bool:
        """原子保存当前实例的完整配置快照。"""
        return self._persist()

    def _read_mapping(self):
        """读取并验证配置文件根映射;已知输入错误返回 None。"""
        try:
            with open(self._file, encoding="utf-8") as fp:
                payload = json.load(fp)
        except FileNotFoundError:
            info(
                f"配置文件不存在,使用默认值 Config file not found, using defaults: {self._file}"
            )
            return None
        except (OSError, UnicodeError, ValueError, RecursionError) as exc:
            error(f"加载失败 Load failed: {exc}")
            return None

        if not isinstance(payload, dict):
            error(
                f"配置文件根节点非 dict Config file root is not dict: {self._file}"
            )
            return None
        return payload

    def _stage_mapping(self, payload):
        """在提交前完成全部 decode 与值/信号快照复制。"""
        staged = {}
        for _, current in self._iter_entries():
            if current.group not in payload:
                continue
            group_payload = payload[current.group]
            if current.name:
                if not isinstance(group_payload, dict):
                    raise ValueError(
                        f"配置 group {current.group!r} 必须是对象"
                    )
                if current.name not in group_payload:
                    continue
                raw = group_payload[current.name]
            else:
                raw = group_payload
            codec = current.clone()
            decoded = codec.decode(self._isolate(current, raw))
            staged[current] = current._prepare_commit(decoded)
        return staged

    def _commit_staged(self, staged):
        """先写齐全部实例值,再统一发 changed-entry 信号。"""
        changes = []
        for current, prepared in staged.items():
            if prepared.stored != current.value:
                changes.append(current)
        for current, prepared in staged.items():
            current._apply_prepared(prepared, False)
        for current in changes:
            current.valueUpdated.emit(staged[current].signal)

    def load(self, file=None) -> bool:
        """从磁盘装入 JSON,逐条灌进对应 SettingEntry。"""
        if file:
            self._file = Path(file)

        if not self._file:
            info("配置文件不存在,使用默认值 Config file not found, using defaults")
            return False

        payload = self._read_mapping()
        if payload is None:
            return False
        try:
            staged = self._stage_mapping(payload)
        except (TypeError, ValueError, OverflowError, RecursionError) as exc:
            error(f"配置字段无效 Invalid configuration field: {exc}")
            return False
        self._commit_staged(staged)

        self.configChanged.emit()
        return True


__all__ = ["SettingsCore"]
