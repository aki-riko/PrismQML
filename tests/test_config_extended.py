# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
PrismQML 配置系统扩展单元测试

覆盖：
- 验证器边界测试（Validator: passthrough / between / choice / boolean）
- ConfigManager 单例行为
- SettingsCore.load 完成后 configChanged 信号
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from prismqml.python.config.validators import Validator, ValidationKind
from prismqml.python.config.config_item import SettingEntry, RangedEntry, EnumEntry
from prismqml.python.config.settings_base import SettingsCore
from prismqml.python.config.config_manager import ConfigManager


# ==================== 验证器测试 ====================


class TestValidatorPassthrough:
    """passthrough() 验证器测试"""

    def test_accepts_anything(self):
        """passthrough 应接受任何值"""
        v = Validator.passthrough()
        assert v.accepts(42) is True
        assert v.accepts("text") is True
        assert v.accepts(None) is True

    def test_coerce_returns_original(self):
        """passthrough 应原样返回"""
        v = Validator.passthrough()
        assert v.coerce(42) == 42
        assert v.coerce("text") == "text"

    def test_kind_is_passthrough(self):
        """kind 应为 PASSTHROUGH"""
        v = Validator.passthrough()
        assert v.kind is ValidationKind.PASSTHROUGH


class TestValidatorBetween:
    """between(lo, hi) 验证器测试"""

    def test_boundary_lo(self):
        """下界值应通过"""
        v = Validator.between(0, 100)
        assert v.accepts(0) is True

    def test_boundary_hi(self):
        """上界值应通过"""
        v = Validator.between(0, 100)
        assert v.accepts(100) is True

    def test_inside_range(self):
        """范围内的值应通过"""
        v = Validator.between(0, 100)
        assert v.accepts(50) is True

    def test_below_lo(self):
        """低于下界应失败"""
        v = Validator.between(0, 100)
        assert v.accepts(-1) is False

    def test_above_hi(self):
        """高于上界应失败"""
        v = Validator.between(0, 100)
        assert v.accepts(101) is False

    def test_coerce_clamps_low(self):
        """低于下界应收敛为下界"""
        v = Validator.between(10, 50)
        assert v.coerce(5) == 10

    def test_coerce_clamps_high(self):
        """高于上界应收敛为上界"""
        v = Validator.between(10, 50)
        assert v.coerce(100) == 50

    def test_coerce_in_range(self):
        """范围内的值应原样返回"""
        v = Validator.between(10, 50)
        assert v.coerce(25) == 25

    def test_range_property(self):
        """range 属性应返回 (lo, hi) 元组"""
        v = Validator.between(0, 200)
        assert v.range == (0, 200)

    def test_invalid_lo_gt_hi_raises(self):
        """lo > hi 应抛 ValueError"""
        with pytest.raises(ValueError):
            Validator.between(10, 5)

    def test_kind_is_range(self):
        """kind 应为 RANGE"""
        v = Validator.between(0, 100)
        assert v.kind is ValidationKind.RANGE


class TestValidatorChoice:
    """choice([...]) 验证器测试"""

    def test_valid_option(self):
        """合法选项应通过"""
        v = Validator.choice([1, 2, 3])
        assert v.accepts(1) is True

    def test_invalid_option(self):
        """非法选项应失败"""
        v = Validator.choice([1, 2, 3])
        assert v.accepts(4) is False

    def test_coerce_invalid_to_first(self):
        """非法值应收敛为第一个候选"""
        v = Validator.choice(["a", "b", "c"])
        assert v.coerce("x") == "a"

    def test_coerce_valid_unchanged(self):
        """合法值应原样返回"""
        v = Validator.choice(["a", "b", "c"])
        assert v.coerce("b") == "b"

    def test_empty_options_raises(self):
        """空候选集合应抛 ValueError"""
        with pytest.raises(ValueError):
            Validator.choice([])

    def test_options_property_returns_copy(self):
        """options 属性应返回独立副本"""
        original = [1, 2, 3]
        v = Validator.choice(original)
        assert v.options == [1, 2, 3]
        # 修改返回副本不影响内部状态
        v.options.append(99)
        assert v.options == [1, 2, 3]

    def test_kind_is_choice(self):
        """kind 应为 CHOICE"""
        v = Validator.choice([1, 2])
        assert v.kind is ValidationKind.CHOICE


class TestValidatorBoolean:
    """boolean() 验证器测试"""

    def test_true_valid(self):
        v = Validator.boolean()
        assert v.accepts(True) is True

    def test_false_valid(self):
        v = Validator.boolean()
        assert v.accepts(False) is True

    def test_non_bool_invalid(self):
        v = Validator.boolean()
        assert v.accepts("true") is False
        assert v.accepts(None) is False
        assert v.accepts(2) is False
        # 严格语义: 0/1 也不是 bool (用 isinstance 判定, 而非 in [True, False])

    def test_coerce_invalid_to_true(self):
        """非法布尔值应收敛为 True（候选列表第一个）"""
        v = Validator.boolean()
        assert v.coerce("invalid") is True

    def test_coerce_keeps_bool(self):
        """合法布尔值应原样返回"""
        v = Validator.boolean()
        assert v.coerce(True) is True
        assert v.coerce(False) is False

    def test_kind_is_boolean(self):
        v = Validator.boolean()
        assert v.kind is ValidationKind.BOOLEAN


# ==================== SettingEntry 测试 ====================


class TestSettingEntrySignal:
    """SettingEntry 信号测试"""

    def test_value_changed_signal(self):
        """修改值应触发 valueUpdated 信号"""
        item = SettingEntry("TestGroup", "TestKey", "default")
        changes = []
        item.valueUpdated.connect(lambda v: changes.append(v))

        item.value = "new_value"
        assert changes == ["new_value"]

    def test_same_value_no_signal(self):
        """相同值不应触发信号"""
        item = SettingEntry("TestGroup", "TestKey", 42)
        changes = []
        item.valueUpdated.connect(lambda v: changes.append(v))

        item.value = 42  # 值相同
        assert changes == []

    def test_key_with_name(self):
        """有名称的配置项 key 格式应为 group.name"""
        item = SettingEntry("Window", "LazyLoading", True)
        assert item.key == "Window.LazyLoading"

    def test_key_without_name(self):
        """无名称的配置项 key 应为 group"""
        item = SettingEntry("Window", "", True)
        assert item.key == "Window"

    def test_ranged_entry(self):
        """RangedEntry 应正确暴露 range"""
        item = RangedEntry("Test", "Range", 50, Validator.between(0, 100))
        assert item.range == (0, 100)

    def test_enum_entry(self):
        """EnumEntry 应正确暴露 options"""
        item = EnumEntry("Test", "Opt", 1, Validator.choice([0, 1, 2]))
        assert item.options == [0, 1, 2]


# ==================== SettingsCore.load 信号测试 ====================


class MockConfig(SettingsCore):
    """测试用配置类"""
    test_str = SettingEntry("TestGroup", "TestStr", "default")
    test_int = SettingEntry("TestGroup", "TestInt", 42)


class TestSettingsBaseLoadSignal:
    """SettingsCore.load 完成后应发射 configChanged 信号"""

    def test_load_emits_config_changed(self):
        """加载配置文件后应触发 configChanged"""
        with TemporaryDirectory() as d:
            config_path = Path(d) / "test.json"
            test_data = {"TestGroup": {"TestStr": "loaded", "TestInt": 99}}
            config_path.write_text(json.dumps(test_data), encoding="utf-8")

            cfg = MockConfig()
            cfg.file = config_path

            # 手动重置到默认值
            MockConfig.test_str._value = MockConfig.test_str.default_value
            MockConfig.test_int._value = MockConfig.test_int.default_value

            signals = []
            cfg.configChanged.connect(lambda: signals.append(True))

            cfg.load()
            assert len(signals) == 1
            assert cfg.get(MockConfig.test_str) == "loaded"

    def test_load_missing_file_no_signal(self):
        """加载不存在的文件不应触发 configChanged"""
        cfg = MockConfig()
        cfg.file = Path("/nonexistent/path/config.json")

        # 手动重置到默认值
        MockConfig.test_str._value = MockConfig.test_str.default_value
        MockConfig.test_int._value = MockConfig.test_int.default_value

        signals = []
        cfg.configChanged.connect(lambda: signals.append(True))

        cfg.load()
        assert len(signals) == 0


# ==================== ConfigManager 单例测试 ====================


class TestConfigManagerSingleton:
    """ConfigManager 单例行为测试"""

    def setup_method(self):
        """每个测试前重置单例"""
        ConfigManager._instance = None
        ConfigManager._instance = None

    def teardown_method(self):
        """每个测试后重置单例"""
        ConfigManager._instance = None

    def test_returns_same_instance(self):
        """多次实例化应返回同一对象"""
        with TemporaryDirectory() as d:
            config_path = Path(d) / "app.json"

            a = ConfigManager(str(config_path))
            b = ConfigManager(str(config_path))
            assert a is b


# ==================== 边角行为测试 ====================


class _RestartConfig(SettingsCore):
    """带 restart=True 条目的测试容器。"""

    normal_flag = SettingEntry("Test", "NormalFlag", False, Validator.boolean())
    restart_flag = SettingEntry(
        "Test", "RestartFlag", False, Validator.boolean(), restart=True,
    )


class TestRestartRequestedSignal:
    """SettingsCore.set 在 restart=True 条目变更时应发射 restartRequested"""

    def test_restart_signal_fires_for_restart_entry(self):
        with TemporaryDirectory() as d:
            cfg = _RestartConfig()
            cfg.file = Path(d) / "r.json"
            _RestartConfig.restart_flag._value = _RestartConfig.restart_flag.default_value

            fired = []
            cfg.restartRequested.connect(lambda: fired.append(True))

            cfg.set(_RestartConfig.restart_flag, True, save=False)
            assert fired == [True]

    def test_restart_signal_silent_for_normal_entry(self):
        with TemporaryDirectory() as d:
            cfg = _RestartConfig()
            cfg.file = Path(d) / "r.json"
            _RestartConfig.normal_flag._value = _RestartConfig.normal_flag.default_value

            fired = []
            cfg.restartRequested.connect(lambda: fired.append(True))

            cfg.set(_RestartConfig.normal_flag, True, save=False)
            assert fired == []


class _SnapshotConfig(SettingsCore):
    """混合一个标量条目和一个嵌套条目的容器,用于测 _to_mapping 两条路径。"""

    nested = SettingEntry("Group", "Inner", "default")
    flat = SettingEntry("FlatGroup", "", 42)


class TestToMappingModes:
    """_to_mapping 的 persist=True / False 两条路径"""

    def test_persist_true_calls_dump(self):
        cfg = _SnapshotConfig()
        _SnapshotConfig.nested._value = "live"
        _SnapshotConfig.flat._value = 100

        out = cfg._to_mapping(persist=True)
        assert out == {"Group": {"Inner": "live"}, "FlatGroup": 100}

    def test_persist_false_reads_value_directly(self):
        cfg = _SnapshotConfig()
        _SnapshotConfig.nested._value = "live2"
        _SnapshotConfig.flat._value = 200

        out = cfg._to_mapping(persist=False)
        assert out == {"Group": {"Inner": "live2"}, "FlatGroup": 200}


class _OrderedConfig(SettingsCore):
    """属性名乱序声明,用于验证 _iter_entries 迭代顺序稳定 (定义序)。"""

    zebra = SettingEntry("Z", "Zebra", 1)
    alpha = SettingEntry("A", "Alpha", 2)
    middle = SettingEntry("M", "Middle", 3)


class TestIterEntriesOrder:
    """_iter_entries 应按"声明顺序"稳定迭代。

    条目集合在类定义阶段由 __init_subclass__ 扫 cls.__dict__ 固化,
    Py3.7+ 的 dict 保留插入顺序, 因此迭代顺序 == 源码里的声明顺序,
    比旧的 dir() 字母序更可预测 (也不再依赖 dir() 的隐式排序)。
    """

    def test_iteration_follows_declaration_order(self):
        cfg = _OrderedConfig()
        names = [name for name, _ in cfg._iter_entries()]
        # 声明顺序: zebra -> alpha -> middle
        assert names == ["zebra", "alpha", "middle"]

    def test_iteration_is_stable(self):
        """同一类多次迭代顺序一致 (稳定性, 与具体顺序无关)。"""
        cfg = _OrderedConfig()
        first = [name for name, _ in cfg._iter_entries()]
        second = [name for name, _ in cfg._iter_entries()]
        assert first == second


class _MixedGroupConfig(SettingsCore):
    """同一 group 下挂 1 个嵌套 + 1 个扁平条目,触发 _to_mapping 防御。"""

    nested_in_x = SettingEntry("X", "Sub", "nested_value")
    flat_in_x = SettingEntry("X", "", "flat_value")


class TestToMappingMixedGroupConflict:
    """同 group 内同时存在嵌套子项 + 扁平条目时,_to_mapping 不应崩,跳后者并 warn"""

    def test_no_typeerror_on_mixed_group(self):
        cfg = _MixedGroupConfig()
        # 不应抛 TypeError
        out = cfg._to_mapping(persist=True)
        # 不论字母序如何,group "X" 总会出现 (一种形态)
        assert "X" in out
