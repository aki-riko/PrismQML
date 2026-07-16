# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SQLite read-only connection helpers. SQLite 只读连接工具。"""

import os
import sqlite3
from urllib.parse import quote


def sqlite_read_only_uri(path: str) -> str:
    raw_path = str(path)
    if raw_path.startswith(("\\\\", "//")):
        normalized = raw_path.replace("\\", "/")
        encoded_path = quote(normalized, safe="/:")
        return f"file://{encoded_path}?mode=ro"
    if len(raw_path) >= 3 and raw_path[1] == ":" and raw_path[2] in "\\/":
        normalized = raw_path.replace("\\", "/")
        encoded_path = quote(normalized, safe="/:")
        return f"file:///{encoded_path}?mode=ro"
    if raw_path.startswith("/"):
        return f"file://{quote(raw_path, safe='/:')}?mode=ro"
    normalized = raw_path.replace("\\", "/") if os.name == "nt" else raw_path
    return f"file:{quote(normalized, safe='/:')}?mode=ro"


def open_read_only(path: str) -> sqlite3.Connection:
    uri = sqlite_read_only_uri(path)
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    connection.execute("PRAGMA busy_timeout=5000")
    return connection
