# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from __future__ import annotations

from collections import OrderedDict
from typing import Optional


class PageCache:
    """LRU page cache for SqlListModel."""

    def __init__(self, capacity: int) -> None:
        self._capacity = max(1, int(capacity))
        self._pages: "OrderedDict[int, tuple[list, Optional[list]]]" = OrderedDict()

    def clear(self) -> None:
        self._pages.clear()

    def get(self, page_idx: int) -> Optional[tuple[list, Optional[list]]]:
        cached = self._pages.get(page_idx)
        if cached is not None:
            self._pages.move_to_end(page_idx)
        return cached

    def put(self, page_idx: int, rows: list, end_cursor: Optional[list]) -> None:
        self._pages[page_idx] = (rows, end_cursor)
        self._pages.move_to_end(page_idx)
        while len(self._pages) > self._capacity:
            self._pages.popitem(last=False)

    def previous_cursor(self, page_idx: int) -> Optional[list]:
        if page_idx <= 0:
            return None
        previous = self._pages.get(page_idx - 1)
        if previous is None:
            return None
        _rows, end_cursor = previous
        return end_cursor
