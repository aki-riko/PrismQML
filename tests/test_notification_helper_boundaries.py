# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Notification helper boundary contracts. 通知 helper 边界合同。"""

from types import SimpleNamespace

import pytest

from prismqml.python.runtime import notification


_DEFAULT = object()
_CACHE_STAGES = ("get_engine", "objectName", "parent")
_CONTROL_EXCEPTIONS = (ValueError, KeyboardInterrupt, SystemExit)
_DOWNSTREAM_EXCEPTIONS = (ValueError, RuntimeError, KeyboardInterrupt, SystemExit)
_DOWNSTREAM_STAGES = (
    "component_ctor",
    "qurl_ctor",
    "setData",
    "isError",
    "errorString",
    "rootContext",
    "create",
    "setParent",
)
_STAGE_EVENTS = {
    "get_engine": ["get_engine"],
    "objectName": ["get_engine", "objectName"],
    "parent": ["get_engine", "objectName", "parent"],
    "component_ctor": ["get_engine", "component_ctor"],
    "qurl_ctor": ["get_engine", "component_ctor", "qurl_ctor"],
    "setData": ["get_engine", "component_ctor", "qurl_ctor", "setData"],
    "isError": ["get_engine", "component_ctor", "qurl_ctor", "setData", "isError"],
    "errorString": [
        "get_engine", "component_ctor", "qurl_ctor", "setData", "isError",
        "errorString",
    ],
    "rootContext": [
        "get_engine", "component_ctor", "qurl_ctor", "setData", "isError",
        "rootContext",
    ],
    "create": [
        "get_engine", "component_ctor", "qurl_ctor", "setData", "isError",
        "rootContext", "create",
    ],
    "setParent": [
        "get_engine", "component_ctor", "qurl_ctor", "setData", "isError",
        "rootContext", "create", "setParent",
    ],
}
_SUCCESS_EVENTS = _STAGE_EVENTS["setParent"]


class _FakeHelper:
    """Configurable helper QObject substitute. 可配置 helper QObject 替身。"""

    def __init__(self, scenario):
        self._scenario = scenario
        self.parent_value = None

    def objectName(self):
        self._scenario.hit("objectName")
        return "notification-helper"

    def parent(self):
        self._scenario.hit("parent")
        return self.parent_value

    def setParent(self, parent):
        self._scenario.set_parent_arg = parent
        self._scenario.hit("setParent")
        self.parent_value = parent


class _FakeEngine:
    """Engine substitute exposing only rootContext. 仅暴露 rootContext 的引擎替身。"""

    def __init__(self, scenario):
        self._scenario = scenario

    def rootContext(self):
        self._scenario.hit("rootContext")
        return self._scenario.context


class _EqualButDistinctEngine(_FakeEngine):
    """Engine that compares equal without identity. 相等但非同一对象的引擎。"""

    def __eq__(self, _other):
        return True


class _FakeComponent:
    """QQmlComponent substitute with injectable outcomes. 可注入结果的组件替身。"""

    def __init__(self, scenario):
        self._scenario = scenario

    def setData(self, data, url):
        self._scenario.set_data_args = (data, url)
        self._scenario.hit("setData")

    def isError(self):
        self._scenario.hit("isError")
        return self._scenario.is_error

    def errorString(self):
        self._scenario.hit("errorString")
        return self._scenario.error_string

    def create(self, context):
        self._scenario.create_context = context
        self._scenario.hit("create")
        if self._scenario.create_result is _DEFAULT:
            return self._scenario.created_helper
        return self._scenario.create_result


class _FakeLogger:
    """Logger substitute recording message order. 记录消息顺序的日志替身。"""

    def __init__(self, scenario):
        self._scenario = scenario

    def warning(self, message):
        self._scenario.log_messages.append(("warning", message))
        self._scenario.hit("warning")

    def error(self, message):
        self._scenario.log_messages.append(("error", message))
        self._scenario.hit("error")


class _Scenario:
    """Shared fake graph and trace. 共享 fake 对象图与调用轨迹。"""

    def __init__(self):
        self.events = []
        self.cache_states = []
        self.errors = {}
        self.log_messages = []
        self.context = object()
        self.url = object()
        self.engine_result = _DEFAULT
        self.create_result = _DEFAULT
        self.is_error = False
        self.error_string = "synthetic compile error"
        self.set_data_args = None
        self.component_engine = None
        self.create_context = None
        self.set_parent_arg = None
        self.engine = _FakeEngine(self)
        self.other_engine = _FakeEngine(self)
        self.cached_helper = _FakeHelper(self)
        self.created_helper = _FakeHelper(self)
        self.component = _FakeComponent(self)
        self.logger = _FakeLogger(self)

    def hit(self, name):
        self.events.append(name)
        self.cache_states.append(notification._helper)
        error = self.errors.get(name)
        if error is not None:
            raise error

    def get_engine(self):
        self.hit("get_engine")
        if self.engine_result is _DEFAULT:
            return self.engine
        return self.engine_result

    def component_ctor(self, engine):
        self.component_engine = engine
        self.hit("component_ctor")
        return self.component

    def qurl_ctor(self):
        self.hit("qurl_ctor")
        return self.url


@pytest.fixture(autouse=True)
def _restore_notification_helper():
    """Restore the module cache after every contract. 每条合同后恢复模块缓存。"""
    previous = notification._helper
    notification._helper = None
    yield
    notification._helper = previous


@pytest.fixture
def scenario(monkeypatch):
    """Install a pure fake dependency graph. 安装纯 fake 依赖图。"""
    current = _Scenario()
    engine_manager = SimpleNamespace(get_engine=current.get_engine)
    monkeypatch.setattr(notification, "EngineManager", engine_manager)
    monkeypatch.setattr(notification, "QQmlComponent", current.component_ctor)
    monkeypatch.setattr(notification, "QUrl", current.qurl_ctor)
    monkeypatch.setattr(notification, "_logger", current.logger)
    return current


def _cache_state_at(scenario, event):
    """Return cache state at one traced event. 返回指定事件发生时的缓存状态。"""
    return scenario.cache_states[scenario.events.index(event)]


def _clear_trace(scenario):
    """Clear observations without changing outcomes. 清空观察值但不改变结果。"""
    scenario.events.clear()
    scenario.cache_states.clear()
    scenario.log_messages.clear()


def _prepare_exception_stage(scenario, stage):
    """Prepare the minimum state needed to reach one stage. 准备抵达阶段的最小状态。"""
    if stage in _CACHE_STAGES:
        scenario.cached_helper.parent_value = scenario.engine
        notification._helper = scenario.cached_helper
        return scenario.cached_helper
    if stage == "errorString":
        scenario.is_error = True
    return None


def _prepare_logger_case(scenario, case):
    """Prepare one logging edge and expected partial state. 准备日志边界及部分状态。"""
    if case == "engine_lookup":
        notification._helper = scenario.cached_helper
        scenario.errors["get_engine"] = RuntimeError("engine")
        return "warning", scenario.cached_helper, ["get_engine", "warning"]
    if case in {"invalid_object", "invalid_parent"}:
        notification._helper = scenario.cached_helper
        stage = "objectName" if case == "invalid_object" else "parent"
        scenario.cached_helper.parent_value = scenario.engine
        scenario.errors[stage] = RuntimeError("deleted")
        events = ["get_engine", "objectName"]
        if stage == "parent":
            events.append("parent")
        return "warning", scenario.cached_helper, events + ["warning"]
    if case == "changed_engine":
        notification._helper = scenario.cached_helper
        scenario.cached_helper.parent_value = scenario.other_engine
        return "warning", None, ["get_engine", "objectName", "parent", "warning"]
    if case == "compile_error":
        scenario.is_error = True
        return "error", None, _STAGE_EVENTS["errorString"] + ["error"]
    scenario.create_result = None
    return "error", None, _STAGE_EVENTS["create"] + ["error"]


def test_engine_runtime_error_warns_without_reading_cache(scenario):
    """RuntimeError means unavailable engine. RuntimeError 表示引擎不可用。"""
    cached = scenario.cached_helper
    error = RuntimeError("not initialized")
    notification._helper = cached
    scenario.errors["get_engine"] = error

    result = notification._get_helper()

    assert result is None
    assert notification._helper is cached
    assert scenario.events == ["get_engine", "warning"]
    assert scenario.log_messages == [
        ("warning", "Engine 未初始化, 通知 helper 不可用"),
    ]


def test_engine_none_is_silent_without_reading_cache(scenario):
    """None engine must silently block cache access. None 引擎必须静默阻断缓存访问。"""
    cached = scenario.cached_helper
    notification._helper = cached
    scenario.engine_result = None

    result = notification._get_helper()

    assert result is None
    assert notification._helper is cached
    assert scenario.events == ["get_engine"]
    assert scenario.log_messages == []


def test_same_engine_returns_cached_helper_before_component_work(scenario):
    """A live matching cache bypasses component work. 存活且匹配的缓存跳过组件工作。"""
    cached = scenario.cached_helper
    cached.parent_value = scenario.engine
    notification._helper = cached

    result = notification._get_helper()

    assert result is cached
    assert notification._helper is cached
    assert scenario.events == ["get_engine", "objectName", "parent"]
    assert scenario.log_messages == []


def test_equal_but_distinct_engine_rebuilds_cached_helper(scenario):
    """Cache ownership requires identity, not equality. 缓存所有权必须使用对象身份。"""
    cached = scenario.cached_helper
    cached.parent_value = _EqualButDistinctEngine(scenario)
    notification._helper = cached

    result = notification._get_helper()

    assert result is scenario.created_helper
    assert notification._helper is scenario.created_helper
    assert scenario.events == [
        "get_engine", "objectName", "parent", "warning", *_SUCCESS_EVENTS[1:]
    ]


@pytest.mark.parametrize("stage", ("objectName", "parent"))
def test_deleted_cache_runtime_error_logs_then_rebuilds(scenario, stage):
    """Deleted cache probes log before clearing and rebuilding. 失效缓存先记录再清理重建。"""
    cached = scenario.cached_helper
    cached.parent_value = scenario.engine
    notification._helper = cached
    scenario.errors[stage] = RuntimeError(stage)
    prefix = ["get_engine", "objectName"]
    if stage == "parent":
        prefix.append("parent")

    result = notification._get_helper()

    assert result is scenario.created_helper
    assert scenario.events == prefix + ["warning"] + _SUCCESS_EVENTS[1:]
    assert _cache_state_at(scenario, "warning") is cached
    assert _cache_state_at(scenario, "component_ctor") is None


def test_changed_engine_clears_cache_before_logging_and_rebuilds(scenario):
    """Engine mismatch clears before warning and rebuild. 引擎不匹配先清缓存再警告重建。"""
    cached = scenario.cached_helper
    cached.parent_value = scenario.other_engine
    notification._helper = cached

    result = notification._get_helper()

    assert result is scenario.created_helper
    assert scenario.events == [
        "get_engine", "objectName", "parent", "warning", *_SUCCESS_EVENTS[1:],
    ]
    assert _cache_state_at(scenario, "warning") is None
    assert notification._helper is scenario.created_helper


def test_successful_creation_publishes_only_after_parenting(scenario):
    """Publish only after complete construction and parenting. 完整构造并挂载后才发布缓存。"""
    result = notification._get_helper()

    assert result is scenario.created_helper
    assert scenario.events == _SUCCESS_EVENTS
    assert scenario.component_engine is scenario.engine
    assert scenario.set_data_args == (
        notification._HELPER_QML.encode("utf-8"), scenario.url,
    )
    assert scenario.create_context is scenario.context
    assert scenario.set_parent_arg is scenario.engine
    assert _cache_state_at(scenario, "setParent") is None
    assert notification._helper is scenario.created_helper


def test_compile_error_returns_none_and_retries(scenario):
    """Compile failure is logged and remains retryable. 编译失败记录日志且保持可重试。"""
    scenario.is_error = True

    first = notification._get_helper()

    assert first is None
    assert notification._helper is None
    assert scenario.events == _STAGE_EVENTS["errorString"] + ["error"]
    assert scenario.log_messages == [
        ("error", "Notification helper QML 编译失败: synthetic compile error"),
    ]
    _clear_trace(scenario)
    scenario.is_error = False
    second = notification._get_helper()
    assert second is scenario.created_helper
    assert scenario.events == _SUCCESS_EVENTS


def test_create_none_returns_none_and_retries(scenario):
    """Instantiation failure is logged and remains retryable. 实例化失败记录日志且保持可重试。"""
    scenario.create_result = None

    first = notification._get_helper()

    assert first is None
    assert notification._helper is None
    assert scenario.events == _STAGE_EVENTS["create"] + ["error"]
    assert scenario.log_messages == [
        ("error", "Notification helper QML 实例化失败"),
    ]
    _clear_trace(scenario)
    scenario.create_result = _DEFAULT
    second = notification._get_helper()
    assert second is scenario.created_helper
    assert scenario.events == _SUCCESS_EVENTS


def test_set_parent_failure_does_not_publish_and_can_retry(scenario):
    """Parenting failure propagates without publishing. 挂载失败传播且不得发布缓存。"""
    error = RuntimeError("setParent failed")
    scenario.errors["setParent"] = error

    with pytest.raises(RuntimeError) as caught:
        notification._get_helper()

    assert caught.value is error
    assert notification._helper is None
    assert scenario.events == _STAGE_EVENTS["setParent"]
    scenario.errors.pop("setParent")
    _clear_trace(scenario)
    assert notification._get_helper() is scenario.created_helper
    assert scenario.events == _SUCCESS_EVENTS


@pytest.mark.parametrize("stage", _CACHE_STAGES)
@pytest.mark.parametrize("error_type", _CONTROL_EXCEPTIONS)
def test_cache_stage_non_runtime_errors_propagate_identity(
    scenario, stage, error_type,
):
    """Uncaught cache-stage failures preserve identity and state. 缓存阶段未捕获失败保留身份与状态。"""
    expected_cache = _prepare_exception_stage(scenario, stage)
    error = error_type(stage)
    scenario.errors[stage] = error

    with pytest.raises(error_type) as caught:
        notification._get_helper()

    assert caught.value is error
    assert notification._helper is expected_cache
    assert scenario.events == _STAGE_EVENTS[stage]


@pytest.mark.parametrize("stage", _DOWNSTREAM_STAGES)
@pytest.mark.parametrize("error_type", _DOWNSTREAM_EXCEPTIONS)
def test_downstream_errors_propagate_identity_without_publishing(
    scenario, stage, error_type,
):
    """Construction failures propagate without publishing. 构造阶段失败传播且不得发布。"""
    _prepare_exception_stage(scenario, stage)
    error = error_type(stage)
    scenario.errors[stage] = error

    with pytest.raises(error_type) as caught:
        notification._get_helper()

    assert caught.value is error
    assert notification._helper is None
    assert scenario.events == _STAGE_EVENTS[stage]


@pytest.mark.parametrize(
    "case",
    (
        "engine_lookup",
        "invalid_object",
        "invalid_parent",
        "changed_engine",
        "compile_error",
        "create_none",
    ),
)
@pytest.mark.parametrize("error_type", _DOWNSTREAM_EXCEPTIONS)
def test_logger_errors_preserve_current_partial_state(
    scenario, case, error_type,
):
    """Logger failures preserve current ordering and partial state. 日志失败保留当前顺序与部分状态。"""
    log_stage, expected_cache, expected_events = _prepare_logger_case(scenario, case)
    error = error_type(case)
    scenario.errors[log_stage] = error

    with pytest.raises(error_type) as caught:
        notification._get_helper()

    assert caught.value is error
    assert notification._helper is expected_cache
    assert scenario.events == expected_events
