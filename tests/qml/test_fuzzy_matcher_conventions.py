# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Fuzzy matcher runtime contracts. 模糊匹配器运行时合同。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine


ROOT = Path(__file__).resolve().parents[2]
MATCHER_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "Search"
    / "_internal"
)
SOURCE_PATH = MATCHER_DIR / "FuzzyMatcher.js"
SOURCE_URL = QUrl.fromLocalFile(str(MATCHER_DIR / "fuzzy-matcher-contract.qml"))
SOURCE = b"""
import QtQuick
import "FuzzyMatcher.js" as FM

QtObject {
    function runMatch(query, text) {
        return FM.match(query, text)
    }

    function runSubstring(query, text) {
        return FM.substringMatch(query, text)
    }

    function runEntry(query, entry, useFuzzy) {
        return FM.matchEntry(
            query,
            entry,
            ["title", "subtitle", "section", "keywords"],
            undefined,
            useFuzzy
        )
    }

    function runFilter(query, entries, useFuzzy, maxResults) {
        return FM.filterAndRank(
            query,
            entries,
            ["title", "subtitle", "section", "keywords"],
            undefined,
            useFuzzy,
            maxResults
        )
    }
}
"""


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _create_matcher():
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(SOURCE, SOURCE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    matcher = component.create()
    assert matcher is not None, [error.toString() for error in component.errors()]
    return engine, component, matcher


def _dispose_matcher(engine, component, matcher) -> None:
    matcher.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_fuzzy_matcher_preserves_scores_ranges_and_case_folding(qapp):
    engine, component, matcher = _create_matcher()
    try:
        assert _variant(matcher.runMatch("CAT", "concatenate")) == {
            "score": 42,
            "ranges": [[0, 1], [4, 6]],
        }
        assert _variant(matcher.runSubstring("CAT", "concatenate")) == {
            "score": 30,
            "ranges": [[3, 6]],
        }
        assert _variant(matcher.runMatch("missing", "concatenate")) is None
        assert _variant(matcher.runMatch("", "concatenate")) == {
            "score": 0,
            "ranges": [],
        }
    finally:
        _dispose_matcher(engine, component, matcher)


def test_fuzzy_matcher_preserves_weighted_entry_and_filter_order(qapp):
    engine, component, matcher = _create_matcher()
    entries = [
        {
            "title": "Project",
            "subtitle": "Open project",
            "section": "General",
            "keywords": ["projection", "workspace"],
        },
        {
            "title": "Profile",
            "subtitle": "Edit account",
            "section": "General",
            "keywords": ["user"],
        },
        {
            "title": "Settings",
            "subtitle": "Configure project",
            "section": "General",
            "keywords": ["preferences"],
        },
    ]
    try:
        entry_match = _variant(matcher.runEntry("PRO", entries[0], True))
        assert entry_match == {
            "score": 262,
            "fieldRanges": {
                "title": [[0, 3]],
                "subtitle": [[1, 2], [6, 8]],
                "keywords": [[0, 3]],
            },
        }

        hits = _variant(matcher.runFilter("PRO", entries, True, 2))
        assert [hit["entry"]["title"] for hit in hits] == ["Project", "Profile"]
        assert [hit["score"] for hit in hits] == [262, 150]
        assert hits[0]["fieldRanges"] == entry_match["fieldRanges"]

        substring_hits = _variant(matcher.runFilter("PRO", entries, False, 3))
        assert [hit["entry"]["title"] for hit in substring_hits] == [
            "Project",
            "Profile",
            "Settings",
        ]
        assert [hit["score"] for hit in substring_hits] == [220, 120, 60]

        empty_hits = _variant(matcher.runFilter("", entries, True, 2))
        assert [hit["entry"]["title"] for hit in empty_hits] == [
            "Project",
            "Profile",
        ]
        assert [hit["score"] for hit in empty_hits] == [0, 0]
    finally:
        _dispose_matcher(engine, component, matcher)


def test_fuzzy_matcher_reuses_normalized_query_in_batch_filter():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "var normalizedQuery = _normalize(query)" in source
    assert "_matchEntryNormalized(" in source
    assert "normalizedQuery, entries[k]" in source
