# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
FluentQML 配置项验证器

设计要点：
- 单一类 Validator + ValidationKind 枚举，工厂方法分发
- 与 FluentQML 其他模块的 Enum 范式对齐
  (Theme / ShadowMode / Position / WindowType / Icon 同风格)
- 验证接口:
    accepts(value) -> bool   是否允许该值
    coerce(value)  -> Any    强制把值收敛到合法集合内
- 工厂入口:
    Validator.passthrough()         # 不约束
    Validator.between(lo, hi)       # 数值闭区间 [lo, hi]
    Validator.choice([...])         # 离散候选
    Validator.boolean()             # True / False
"""

from enum import Enum
from typing import Any, Iterable, List, Tuple


class ValidationKind(Enum):
    """配置项验证类型"""
    PASSTHROUGH = "passthrough"  # 不约束
    RANGE = "range"              # 数值闭区间
    CHOICE = "choice"            # 离散候选
    BOOLEAN = "boolean"          # True / False


class Validator:
    """配置项验证器（单类 + 枚举分发）

    不要直接调用 ``__init__``，请使用工厂方法构造：

        v = Validator.passthrough()
        v = Validator.between(0, 100)
        v = Validator.choice(['low', 'mid', 'high'])
        v = Validator.boolean()

    然后用：

        v.accepts(value)  # 是否允许
        v.coerce(value)   # 收敛到允许集合
    """

    __slots__ = ("kind", "_lo", "_hi", "_options")

    def __init__(
        self,
        kind: ValidationKind,
        *,
        lo: Any = None,
        hi: Any = None,
        options: List = None,
    ):
        self.kind = kind
        self._lo = lo
        self._hi = hi
        self._options = options

    # ---------- 工厂方法 ----------

    @classmethod
    def passthrough(cls) -> "Validator":
        """不约束的验证器（任何值都通过）"""
        return cls(ValidationKind.PASSTHROUGH)

    @classmethod
    def between(cls, lo: Any, hi: Any) -> "Validator":
        """数值闭区间 [lo, hi]"""
        if lo > hi:
            raise ValueError(
                f"Validator.between: lo({lo}) 必须 <= hi({hi})"
            )
        return cls(ValidationKind.RANGE, lo=lo, hi=hi)

    @classmethod
    def choice(cls, options: Iterable) -> "Validator":
        """离散候选集合"""
        opts = list(options)
        if not opts:
            raise ValueError("Validator.choice: 候选集合不能为空")
        return cls(ValidationKind.CHOICE, options=opts)

    @classmethod
    def boolean(cls) -> "Validator":
        """布尔候选(True / False)，coerce 默认到 True"""
        return cls(ValidationKind.BOOLEAN, options=[True, False])

    # ---------- 兼容只读属性 ----------
    # RangedEntry / EnumEntry 通过这两个属性把约束暴露给 UI 层
    # （例如滑块需要知道 lo/hi、下拉框需要知道 options）

    @property
    def range(self) -> Tuple:
        """RANGE 时返回 (lo, hi)，其余返回 ()"""
        if self.kind is ValidationKind.RANGE:
            return (self._lo, self._hi)
        return ()

    @property
    def options(self) -> List:
        """CHOICE / BOOLEAN 时返回候选列表的拷贝，其余返回 []"""
        if self._options is None:
            return []
        return list(self._options)

    # ---------- 验证接口 ----------

    def accepts(self, value: Any) -> bool:
        """该值是否被允许"""
        kind = self.kind
        if kind is ValidationKind.PASSTHROUGH:
            return True
        if kind is ValidationKind.RANGE:
            try:
                return self._lo <= value <= self._hi
            except TypeError:
                return False
        if kind is ValidationKind.BOOLEAN:
            # 严格匹配 True/False(过滤掉 0/1/None/"true" 等假阳性)
            return isinstance(value, bool)
        if kind is ValidationKind.CHOICE:
            return value in self._options
        return False

    def coerce(self, value: Any) -> Any:
        """把值收敛到允许集合内"""
        kind = self.kind
        if kind is ValidationKind.PASSTHROUGH:
            return value
        if kind is ValidationKind.RANGE:
            try:
                if value < self._lo:
                    return self._lo
                if value > self._hi:
                    return self._hi
                return value
            except TypeError:
                return self._lo
        if kind is ValidationKind.BOOLEAN:
            # 非 bool 一律收敛到 True(候选列表第一个)
            return value if isinstance(value, bool) else self._options[0]
        if kind is ValidationKind.CHOICE:
            return value if value in self._options else self._options[0]
        return value

    # ---------- 调试友好 ----------

    def __repr__(self) -> str:
        if self.kind is ValidationKind.RANGE:
            return f"Validator.between({self._lo}, {self._hi})"
        if self.kind is ValidationKind.CHOICE:
            return f"Validator.choice({self._options!r})"
        if self.kind is ValidationKind.BOOLEAN:
            return "Validator.boolean()"
        return "Validator.passthrough()"


__all__ = ["Validator", "ValidationKind"]
