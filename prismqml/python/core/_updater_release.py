# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Strict GitHub release payload parsing. GitHub release 严格解析。"""

from __future__ import annotations

import json
import sys
from typing import Optional
from urllib.parse import urlsplit


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
            "digest": _optional_release_string(asset, "digest"),
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


def is_safe_update_url(url: str, *, allow_local_http: bool = True) -> bool:
    """Accept only HTTPS, or loopback HTTP for local tests. 仅允许安全更新地址。"""
    try:
        parsed = urlsplit((url or "").strip())
    except ValueError:
        return False
    if parsed.username or parsed.password or not parsed.hostname:
        return False
    if parsed.scheme.lower() == "https":
        return True
    return (
        allow_local_http
        and parsed.scheme.lower() == "http"
        and parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
    )


def is_sha256_digest(digest: str) -> bool:
    """Validate a GitHub ``sha256:<hex>`` digest. 校验摘要格式。"""
    algorithm, separator, expected = (digest or "").partition(":")
    if not separator or algorithm.lower() != "sha256" or len(expected) != 64:
        return False
    try:
        int(expected, 16)
    except ValueError:
        return False
    return True


def _platform_suffixes(platform_name: Optional[str] = None) -> tuple[str, ...]:
    """Return launchable installer suffixes for one platform. 返回平台安装包后缀。"""
    name = platform_name or sys.platform
    if name == "win32":
        return (".exe",)
    if name == "darwin":
        return (".dmg", ".pkg")
    if name.startswith("linux"):
        return (".appimage", ".run", ".deb")
    return ()


def pick_asset(
    assets: list,
    keyword: str,
    platform_name: Optional[str] = None,
) -> Optional[dict]:
    """Pick a valid platform installer. 选择带地址的平台安装包。"""
    candidates = [
        asset for asset in assets
        if asset.get("browser_download_url")
        and asset.get("name", "").lower().endswith(_platform_suffixes(platform_name))
    ]
    if not candidates:
        return None
    normalized_keyword = (keyword or "").lower()
    if normalized_keyword:
        for asset in candidates:
            if normalized_keyword in asset["name"].lower():
                return asset
    return candidates[0]
