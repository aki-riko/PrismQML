# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
"""设置条目 — Setting Entry types

每个 SettingEntry 对应一条可持久化的设置:
  group  (str)  :  逻辑分组,通常对应 JSON 顶层节点
  name   (str)  :  分组内的键,留空表示该组只承载一个标量
  default       :  初始值,会先经过 validator.coerce 收敛
  validator     :  Validator 实例,默认 passthrough()
  restart       :  True 表示修改后需要重启进程才能完全生效

构造完毕后,SettingEntry 暴露:
  entry.value   读 / 写当前值 (写入会先 coerce 再发 valueUpdated)
  entry.dump()  返回当前值 (留作后续 hook 自定义序列化)
  entry.load(v) 把外部值灌进 entry (走 setter,自动 coerce + 信号)
  entry.key     "Group.Name" 或单独 "Group" 的扁平键

RangedEntry / EnumEntry 在 SettingEntry 之上各自暴露 .range / .options,
让 UI 层 (滑块、下拉) 能直接拿到约束元数据。
"""

from PySide6.QtCore import QObject, Signal

from .validators import Validator


def _compose_key(group: str, name: str) -> str:
    """把 (group, name) 拼成 SettingsCore 持久化使用的扁平键。"""
    return f"{group}.{name}" if name else group


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
        **kwargs,
    ):
        # 显式拒绝任何未知关键字, 比静默落入 **kwargs 错位好得多。
        if kwargs:
            raise TypeError(
                f"SettingEntry 收到未知关键字参数 unexpected kwargs: {sorted(kwargs)}"
            )

        super().__init__()
        self.group = group
        self.name = name
        self.validator = validator or Validator.passthrough()
        self.restart = restart
        self.default_value = self.validator.coerce(default)
        self._value = self.default_value

    # ---------- 取值/赋值 ----------

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, incoming):
        coerced = self.validator.coerce(incoming)
        if self._value == coerced:
            return
        self._value = coerced
        self.valueUpdated.emit(coerced)

    # ---------- 持久化 hook ----------

    def dump(self):
        """返回应当写入配置文件的值,默认即当前 value。

        子类或下游可重写以自定义序列化形式 (例如把 Enum 转为成员名)。
        """
        return self.value

    def load(self, raw):
        """把外部 raw 灌入 entry,等价于走一次 setter (会 coerce + emit)。"""
        self.value = raw

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
