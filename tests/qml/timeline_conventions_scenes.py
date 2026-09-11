# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by timeline_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    property var virtualItems: makeItems(12)
    property var largeVirtualItems: makeLargeItems()
    readonly property int virtualFlatCount: virtualTimeline._flatRows.length
    readonly property string virtualFirstTitle:
        virtualTimeline._flatRows.length > 0 ? virtualTimeline._flatRows[0].title : ""
    readonly property string virtualFirstCardText:
        virtualTimeline._flatRows.length > 1 ? virtualTimeline._flatRows[1].text : ""
    readonly property int largeVirtualFlatCount: largeVirtualTimeline._flatRows.length
    readonly property int graphFlatCount: graphTimeline._flatRows.length
    readonly property real timelinePulseOpacity: timeline._pulseOpacity

    function makeItems(count) {
        var result = []
        for (var i = 0; i < count; i++) {
            result.push({
                "title": "Group " + i,
                "status": i % 2 ? "success" : "info",
                "cards": [
                    { "text": "Card " + i + "A", "commit": "a" + i },
                    { "text": "Card " + i + "B", "commit": "b" + i }
                ]
            })
        }
        return result
    }

    function appendVirtualGroup() {
        var next = virtualItems.slice()
        next.push({
            "title": "Appended",
            "status": "warning",
            "cards": [
                { "text": "Appended A", "commit": "append-a" },
                { "text": "Appended B", "commit": "append-b" }
            ]
        })
        virtualItems = next
    }

    function updateVirtualFirstGroupInPlace() {
        virtualItems[0].title = "Updated Group 0"
        virtualItems[0].cards[0].text = "Updated Card 0A"
        virtualItems = virtualItems.slice()
    }

    function makeLargeItems() {
        var result = []
        for (var groupIndex = 0; groupIndex < 3; groupIndex++) {
            var cards = []
            for (var cardIndex = 0; cardIndex < 30; cardIndex++) {
                var suffix = cardIndex % 5 === 0
                    ? " with a deliberately long summary that wraps onto multiple lines and changes delegate height"
                    : ""
                cards.push({
                    "text": "Commit " + groupIndex + "-" + cardIndex + suffix,
                    "commit": "large-" + groupIndex + "-" + cardIndex
                })
            }
            result.push({
                "title": "Large Group " + groupIndex,
                "status": groupIndex % 2 ? "success" : "info",
                "cards": cards
            })
        }
        return result
    }

    width: 1500
    height: 857
    visible: true

    TimelineCore {
        id: timeline
        objectName: "timeline"
        x: 20
        y: 20
        width: 320
        items: [
            {
                "title": "Plan",
                "dateKey": "2026-08-29",
                "status": "info",
                "cards": [
                    { "text": "One", "description": "First", "commit": "one" },
                    "Two"
                ]
            },
            {
                "title": "Done",
                "status": "success",
                "cards": [{ "text": "Three", "strikeOut": true }]
            }
        ]
    }

    TimelineCore {
        id: virtualTimeline
        objectName: "virtualTimeline"
        x: 380
        y: 20
        width: 340
        height: 220
        virtualized: true
        selectedRole: "commit"
        selectedKey: "b0"
        items: root.virtualItems
    }

    TimelineCore {
        id: largeVirtualTimeline
        objectName: "largeVirtualTimeline"
        x: 760
        y: 20
        width: 340
        height: 817
        virtualized: true
        items: root.largeVirtualItems
    }

    TimelineCore {
        id: graphTimeline
        objectName: "graphTimeline"
        x: 1120
        y: 20
        width: 360
        height: 360
        type: Enums.timeline.type_graph
        graphLaneCount: 3
        selectedRole: "commit"
        selectedKey: "merge"
        items: [
            {
                "title": "Graph",
                "graph": {
                    "segments": [
                        {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                        {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                    ]
                },
                "cards": [
                    {
                        "text": "Merge feature",
                        "time": "10:42",
                        "timePeriod": "AM",
                        "commit": "merge",
                        "labels": [{"text": "main", "status": Enums.statusLevel.info}],
                        "graph": {
                            "nodeLane": 0,
                            "nodeColorIndex": 0,
                            "segments": [
                                {"fromLane": 0, "toLane": 0, "colorIndex": 0,
                                    "endAtNode": true},
                                {"fromLane": 0, "toLane": 1, "colorIndex": 1,
                                    "startAtNode": true}
                            ]
                        }
                    },
                    {
                        "text": "Feature work",
                        "time": "13:18",
                        "timePeriod": "PM",
                        "commit": "feature",
                        "graph": {
                            "nodeLane": 1,
                            "nodeColorIndex": 1,
                            "segments": [
                                {"fromLane": 0, "toLane": 0, "colorIndex": 0},
                                {"fromLane": 1, "toLane": 1, "colorIndex": 1}
                            ]
                        }
                    }
                ]
            }
        ]
    }
}
"""
