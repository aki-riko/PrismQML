# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from prismqml.python.config import SettingsCore, SettingEntry
from prismqml.python.config.config_manager import ConfigManager


class MockConfig(SettingsCore):
    """测试用配置类"""

    test_str = SettingEntry("TestGroup", "TestStr", "default")
    test_int = SettingEntry("TestGroup", "TestInt", 42)


@pytest.fixture
def temp_config_env():
    """提供一个隔离的配置环境"""
    with TemporaryDirectory() as d:
        config_path = Path(d) / "config.json"
        
        # 暂时替换单例（测试结束后恢复）
        original_instance = getattr(ConfigManager, "_instance", None)
        
        manager = MockConfig()
        manager.file = config_path
        
        # 手动重置所有选项到默认值
        manager.test_str.value = manager.test_str.default_value
        manager.test_int.value = manager.test_int.default_value
            
        yield manager, config_path
        
        # 恢复单例状态
        if original_instance is not None:
            ConfigManager._instance = original_instance


class TestSettingsBase:
    def test_save_atomic_write(self, temp_config_env):
        """测试 save 方法的原子写入机制"""
        manager, path = temp_config_env
        
        # 修改值
        manager.set(manager.test_str, "custom_value")
        manager.set(manager.test_int, 100)
        
        # 此时应创建了新文件
        assert path.exists()
        
        # 检查写入内容
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["TestGroup"]["TestStr"] == "custom_value"
            assert data["TestGroup"]["TestInt"] == 100

        # 由于 atomic write 先写 .tmp 然后 rename，最终临时文件不应存在
        tmp_path = path.with_suffix(".json.tmp")
        assert not tmp_path.exists()
        
    def test_load_config(self, temp_config_env):
        """测试配置加载逻辑"""
        manager, path = temp_config_env
        
        # 外部先创建一个合法的配置文件
        test_data = {"TestGroup": {"TestStr": "loaded_str", "TestInt": 999}}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
            
        # 触发加载
        manager.load()
        
        assert manager.get(manager.test_str) == "loaded_str"
        assert manager.get(manager.test_int) == 999
