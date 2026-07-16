# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Strict GitHub release payload parsing. GitHub release 严格解析。"""

from __future__ import annotations

import json
from typing import Optional


def _optional_release_string(data: dict, key: str) -> str:
    """Read a nullable optional string field. 读取可空的可选字符串字段。"""
    value = data.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"release field {key!r} must be a string or null")
    return value


def _validated_release_assets(data: dict) -> list[dict]:
    """Validate and normalize release assets. 校验并归一化 release assets。"""
    assets = data.get("assets")
    if assets is None:
        return []
    if not isinstance(assets, list):
        raise ValueError("release field 'assets' must be an array or null")
    normalized = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("each release asset must be an object")
        normalized.append({
            "name": _optional_release_string(asset, "name"),
            "browser_download_url": _optional_release_string(
                asset, "browser_download_url"
            ),
        })
    return normalized


def decode_release_payload(raw: bytes) -> dict:
    """Decode a strict UTF-8 release object. 解码严格 UTF-8 release 对象。"""
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("release JSON root must be an object")
    tag = data.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError("release field 'tag_name' must be a non-empty string")
    return {
        "tag_name": tag.strip(),
        "body": _optional_release_string(data, "body"),
        "html_url": _optional_release_string(data, "html_url"),
        "assets": _validated_release_assets(data),
    }


def pick_asset(assets: list, keyword: str) -> Optional[dict]:
    """Pick a preferred installer asset. 选择首选安装包资源。"""
    if not assets:
        return None
    normalized_keyword = (keyword or "").lower()
    executable_assets = [
        asset
        for asset in assets
        if asset["name"].lower().endswith(".exe")
    ]
    if normalized_keyword:
        for asset in executable_assets:
            if normalized_keyword in asset["name"].lower():
                return asset
    if executable_assets:
        return executable_assets[0]
    return assets[0]
