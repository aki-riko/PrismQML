# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater release response schema contracts. 更新响应 schema 合同。"""

from __future__ import annotations

import json

import pytest

from prismqml.python.core.updater import Updater


def _encoded(value) -> bytes:
    if isinstance(value, bytes):
        return value
    return json.dumps(value).encode("utf-8")


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"tag_name": 104},
        {"tag_name": "   "},
        {"tag_name": "v1.0.4", "body": []},
        {"tag_name": "v1.0.4", "html_url": {}},
        {"tag_name": "v1.0.4", "assets": {}},
        {"tag_name": "v1.0.4", "assets": ["not-an-object"]},
        {"tag_name": "v1.0.4", "assets": [{"name": []}]},
        {"tag_name": "v1.0.4", "assets": [{"browser_download_url": 7}]},
        b'{"tag_name":"v1.0.4"}\xff',
    ],
)
def test_invalid_release_schema_fails_once_without_success(qapp, payload):
    updater = Updater("owner/repo", "v1.0.3")
    failures = []
    successes = []
    updater.checkFailed.connect(failures.append)
    updater.updateAvailable.connect(lambda *args: successes.append(args))
    updater.upToDate.connect(successes.append)

    updater._inject_release_for_test(_encoded(payload))

    assert len(failures) == 1
    assert successes == []


def test_null_optional_release_fields_are_normalized(qapp):
    updater = Updater("owner/repo", "v1.0.3")
    received = []
    updater.updateAvailable.connect(lambda *args: received.append(args))

    updater._inject_release_for_test(_encoded({
        "tag_name": "v1.0.4",
        "body": None,
        "html_url": None,
        "assets": None,
    }))

    assert received == [("v1.0.4", "", "", "")]
