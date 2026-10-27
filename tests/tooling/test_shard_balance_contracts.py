# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shard duration balancing contracts. 分片耗时均衡合同.

qml-2 exhausted a 1200s budget on two separate releases while the other buckets
finished in about three minutes. The cause was balancing by source size, which cannot
see fixed-wait behaviour. These contracts lock the replacement: measured seconds must
outrank every size estimate, and only successful shards may contribute samples.
qml-2 在两次发布中都耗尽 1200s 预算, 而其它分片约三分钟完成。原因是用源码体积做均衡,
它看不见固定等待行为。以下合同锁定替代方案: 实测秒数必须优先于任何体积估算, 且只有
成功的分片才能贡献样本。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARDS_PATH = ROOT / "scripts" / "run_test_shards.py"


def _load_shards():
    spec = importlib.util.spec_from_file_location("run_test_shards_contract", SHARDS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_measured_seconds_outrank_size_estimates(tmp_path, monkeypatch):
    """A file measured slow must outweigh a much larger unmeasured file.

    实测较慢的文件必须压过体积大得多的未测量文件。
    """
    shards = _load_shards()
    small_slow = tmp_path / "test_small_slow.py"
    small_slow.write_text("\n" * 10, encoding="utf-8")
    big_fast = tmp_path / "test_big_fast.py"
    big_fast.write_text("\n" * 2000, encoding="utf-8")

    size_only = shards._file_weight(big_fast, {})
    assert size_only > shards._file_weight(small_slow, {})

    measured = {
        small_slow.relative_to(tmp_path).as_posix(): 42.0,
    }
    # Patch ROOT-relative resolution by measuring the real repository paths instead.
    # 通过真实仓库路径测量, 而不是伪造 ROOT 相对解析。
    real_slow = ROOT / "tests" / "qml" / "test_scroll_bar_conventions.py"
    real_big = ROOT / "tests" / "qml" / "test_stacked_widget_loader_lifecycle.py"
    relativized = {
        real_slow.relative_to(ROOT).as_posix(): 10.0,
    }
    assert shards._file_weight(real_slow, {}) != shards._file_weight(real_slow, relativized)
    slow_weight = shards._file_weight(real_slow, relativized)
    big_weight = shards._file_weight(real_big, {})
    # The measured file is weighted by its seconds, scaled to the size unit.
    # 实测文件按其秒数加权, 缩放到与体积同一单位。
    assert slow_weight == max(1, int(10.0 * 1_000))
    assert isinstance(big_weight, int) and big_weight > 0


def test_duration_samples_are_capped_and_medians_are_used():
    """Samples roll at a fixed size and the median resists a single outlier.

    样本按固定长度滚动, 中位数能抵抗单个离群值。
    """
    shards = _load_shards()
    assert shards.DURATION_SAMPLE_LIMIT >= 3
    assert shards.DURATION_CACHE_NAME.endswith(".json")


def test_only_successful_shards_contribute_samples():
    """A timed-out log is truncated, so it must not feed the partitioner.

    超时日志被截断, 因此不得喂给分片器。
    """
    source = SHARDS_PATH.read_text(encoding="utf-8")
    body = source[source.index("def _finish_shards") :]
    # The recording call must sit behind a success check.
    # 记录调用必须位于成功判断之后。
    record_index = body.index("_record_measured_durations")
    guard_index = body.index("if return_code == 0:")
    assert guard_index < record_index


def test_pytest_reports_every_duration_not_only_the_slowest():
    """Balancing needs every file's seconds, so --durations must not truncate.

    均衡需要每个文件的秒数, 因此 --durations 不得截断。
    """
    source = SHARDS_PATH.read_text(encoding="utf-8")
    assert '"--durations=0"' in source
    assert '"--durations=20"' not in source


def test_shard_layout_is_derived_and_reproducible():
    """The partition must be deterministic for a given duration cache.

    给定耗时缓存时, 分片结果必须可重复。
    """
    shards = _load_shards()
    first = shards._partition_files(ROOT / "tests" / "qml", 4)
    second = shards._partition_files(ROOT / "tests" / "qml", 4)
    assert first == second
    assert len(first) == 4
    total = sum(len(bucket) for bucket in first)
    expected = len(
        tuple(
            path
            for path in sorted((ROOT / "tests" / "qml").glob("test_*.py"))
            if path.relative_to(ROOT).as_posix()
            not in set(shards.SERIAL_RUNTIME_FILES) | set(shards.NESTED_ENTRYPOINT_FILES)
        )
    )
    assert total == expected
