# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Parse native failure-fixture markers. 解析原生失败夹具标记。"""

from __future__ import annotations

import json
import re

from scripts._test_support.windows.result import BOUNDARY_RESULT_PREFIX


FAILURE_PREFIX = "PRISM_NATIVE_FAILURE "
SPAWN_PREFIX = "PRISM_NATIVE_SPAWN "
TRIGGER_PREFIX = "PRISM_NATIVE_TRIGGER "
QT_MESSAGE_PREFIX = "PRISM_NATIVE_QT_MESSAGE "
FAILURE_PATTERN = re.compile(
    r"PRISM_NATIVE_FAILURE mode=(?P<mode>\S+) pid=(?P<pid>\d+) "
    r"desktop=(?P<desktop>\S+) job=(?P<job>\S+) "
    r"in_job=(?P<in_job>[01]) error_mode=0x(?P<error_mode>[0-9A-Fa-f]+)"
)
SPAWN_PATTERN = re.compile(
    r"PRISM_NATIVE_SPAWN parent_pid=(?P<parent_pid>\d+) "
    r"child_pid=(?P<child_pid>\d+) requested_desktop=(?P<desktop>\S+) "
    r"job=(?P<job>\S+) child_in_job=(?P<child_in_job>[01])"
)
TRIGGER_PATTERN = re.compile(
    r"PRISM_NATIVE_TRIGGER mode=(?P<mode>\S+) pid=(?P<pid>\d+)"
)
QT_MESSAGE_PATTERN = re.compile(
    r"PRISM_NATIVE_QT_MESSAGE type=(?P<type>\S+) pid=(?P<pid>\d+) "
    r"message=(?P<message>.*)"
)


def parsed_markers(stderr: str, prefix: str, pattern: re.Pattern) -> list[dict]:
    markers = []
    for line in stderr.splitlines():
        if not line.startswith(prefix):
            continue
        match = pattern.fullmatch(line)
        if match is None:
            raise AssertionError(f"malformed native marker: {line!r}")
        markers.append(match.groupdict())
    return markers


def failure_markers(stderr: str) -> list[dict]:
    markers = parsed_markers(stderr, FAILURE_PREFIX, FAILURE_PATTERN)
    for marker in markers:
        for field in ("pid", "in_job"):
            marker[field] = int(marker[field])
        marker["error_mode"] = int(marker["error_mode"], 16)
    return markers


def spawn_markers(stderr: str) -> list[dict]:
    markers = parsed_markers(stderr, SPAWN_PREFIX, SPAWN_PATTERN)
    for marker in markers:
        for field in ("parent_pid", "child_pid", "child_in_job"):
            marker[field] = int(marker[field])
    return markers


def trigger_markers(stderr: str) -> list[dict]:
    markers = parsed_markers(stderr, TRIGGER_PREFIX, TRIGGER_PATTERN)
    for marker in markers:
        marker["pid"] = int(marker["pid"])
    return markers


def qt_message_markers(stderr: str) -> list[dict]:
    markers = parsed_markers(stderr, QT_MESSAGE_PREFIX, QT_MESSAGE_PATTERN)
    for marker in markers:
        marker["pid"] = int(marker["pid"])
    return markers


def only_marker(markers: list[dict], label: str) -> dict:
    if len(markers) != 1:
        raise AssertionError(f"expected one {label}, got {markers!r}")
    return markers[0]


def boundary_result(stderr: str) -> dict:
    records = [
        json.loads(line[len(BOUNDARY_RESULT_PREFIX) :])
        for line in stderr.splitlines()
        if line.startswith(BOUNDARY_RESULT_PREFIX)
    ]
    if len(records) != 1:
        raise AssertionError(f"expected one boundary result, got {records!r}")
    return records[0]


def verify_boundary(result) -> dict:
    boundary = boundary_result(result.stderr)
    desktop_prefix = "PrismQMLTest-"
    if not boundary["desktop"].startswith(desktop_prefix):
        raise AssertionError(boundary)
    if boundary["root_process_id"] <= 0:
        raise AssertionError(boundary)
    expected_job = "PrismQMLTestJob-" + boundary["desktop"].removeprefix(
        desktop_prefix
    )
    if boundary["job"] != expected_job:
        raise AssertionError(boundary)
    if boundary["final_active_processes"] != 0:
        raise AssertionError(boundary)
    if not boundary["cleanup_succeeded"]:
        raise AssertionError(boundary)
    if boundary["exit_code"] != result.returncode:
        raise AssertionError((boundary, result.returncode))
    if "visible_windows=0 / job_active_processes=0" not in result.stderr:
        raise AssertionError(result.stderr)
    return boundary
