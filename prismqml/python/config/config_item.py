# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""设置条目 — Setting Entry types

每个 SettingEntry 对应一条可持久化的设置:
  group  (str)  :  逻辑分组,通常对应 JSON 顶层节点
  name   (str)  :  分组内的键,留空表示该组只承载一个标量
  default       :  初始值,会先经过 validator.coerce 收敛
  validator     :  Validator 实例,默认 passthrough()
  restart       :  True 表示修改后需要重启进程才能完全生效

构造完毕后,SettingEntry 暴露:
  entry.value   读 / 写当前值 (写入会先 coerce 再发 valueUpdated)
  entry.encode(v) / decode(v) 纯序列化 hook,不得修改 entry 自身状态
  entry.dump() / load(v)       当前值的便利包装
  entry.clone(parent)          为 SettingsCore 构造独立 QObject 实例
  entry.key     "Group.Name" 或单独 "Group" 的扁平键

RangedEntry / EnumEntry 在 SettingEntry 之上各自暴露 .range / .options,
让 UI 层 (滑块、下拉) 能直接拿到约束元数据。
"""

from copy import deepcopy
from typing import NamedTuple

from PySide6.QtCore import QObject, Signal

from .validators import Validator


def _compose_key(group: str, name: str) -> str:
    """把 (group, name) 拼成 SettingsCore 持久化使用的扁平键。"""
    return f"{group}.{name}" if name else group


def _copy_value(value):
    """复制普通配置值;不可复制的 Qt 对象保留原引用。"""
    try:
        return deepcopy(value)
    except (TypeError, AttributeError):
        return value


class _PreparedValue(NamedTuple):
    stored: object
    signal: object


class SettingEntry(QObject):
    """A persisted setting backed by a validator and a Qt signal."""

    valueUpdated = Signal(object)

    def __init__(
        self,
        group: str,
        name: str,
        default,
        validator: Validator = None,
        *,
        restart: bool = False,
        parent=None,
        **kwargs,
    ):
        # 显式拒绝任何未知关键字, 比静默落入 **kwargs 错位好得多。
        if kwargs:
            raise TypeError(
                f"SettingEntry 收到未知关键字参数 unexpected kwargs: {sorted(kwargs)}"
            )

        super().__init__(parent)
        self.group = group
        self.name = name
        self.validator = validator or Validator.passthrough()
        self.restart = restart
        self.default_value = _copy_value(self.validator.coerce(default))
        self._value = _copy_value(self.default_value)

    def __get__(self, instance, owner):
        """类访问返回 schema prototype,实例访问返回绑定条目。"""
        if instance is None:
            return self
        return instance.entry(self)

    def clone(self, parent=None):
        """调用真实构造器克隆 QObject;自定义构造签名必须覆写本方法。"""
        try:
            cloned = type(self)(
                group=self.group,
                name=self.name,
                default=_copy_value(self.default_value),
                validator=self.validator,
                restart=self.restart,
                parent=parent,
            )
        except TypeError as exc:
            raise TypeError(
                f"{type(self).__name__} 使用自定义构造器时必须覆写 clone(parent)"
            ) from exc
        cloned._replace_value(self._value, False)
        return cloned

    # ---------- 取值/赋值 ----------

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, incoming):
        coerced = self.prepare(incoming)
        self._set_prepared(coerced)

    def prepare(self, incoming):
        """把 Python/QML 输入收敛为合法内存值。"""
        return self.validator.coerce(incoming)

    def _prepare_commit(self, prepared) -> _PreparedValue:
        """在提交点前完成存储值与信号值的全部复制。"""
        stored = _copy_value(prepared)
        return _PreparedValue(stored, _copy_value(stored))

    def _apply_prepared(self, prepared: _PreparedValue, notify: bool = True):
        """仅赋值已准备快照;本方法不得调用 hook 或 deepcopy。"""
        self._value = prepared.stored
        if notify:
            self.valueUpdated.emit(prepared.signal)

    def _replace_value(self, prepared, notify: bool = True):
        """提交已校验值,供 SettingsCore 事务最终提交使用。"""
        self._apply_prepared(self._prepare_commit(prepared), notify)

    def _set_prepared(self, prepared, notify: bool = True) -> bool:
        """去重后提交已校验值并按需通知。"""
        if self._value == prepared:
            return False
        self._replace_value(prepared, notify)
        return True

    # ---------- 持久化 hook ----------

    def encode(self, value):
        """把候选内存值编码为 JSON 值;实现必须是纯函数。"""
        return value

    def decode(self, raw):
        """把 JSON 值解码为合法内存值;实现必须是纯函数。"""
        return self.prepare(raw)

    def dump(self):
        """返回当前值的 JSON 表示。"""
        return self.encode(self.value)

    def load(self, raw):
        """解码并提交外部值,适合脱离 SettingsCore 的直接使用。"""
        self._set_prepared(self.decode(raw))

    # ---------- 元信息 ----------

    @property
    def key(self) -> str:
        return _compose_key(self.group, self.name)


class RangedEntry(SettingEntry):
    """带数值闭区间约束的设置条目;range 元组直接来自 validator。"""

    @property
    def range(self):
        return self.validator.range


class EnumEntry(SettingEntry):
    """带候选集合约束的设置条目;options 列表直接来自 validator。"""

    @property
    def options(self):
        return self.validator.options


__all__ = [
    "SettingEntry",
    "RangedEntry",
    "EnumEntry",
    "_compose_key",
]
