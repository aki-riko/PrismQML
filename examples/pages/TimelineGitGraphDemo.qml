// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML as Fluent

Fluent.Timeline {
    objectName: "galleryGitGraphTimeline"
    width: 500
    height: 620
    type: Fluent.Enums.timeline.type_graph
    virtualized: true
    graphLaneCount: 3
    selectedRole: "commit"
    selectedKey: "merge-feature"
    items: [
        {
            title: Fluent.Translator.tr("gallery_c1af7bcd8081939f", Fluent.Translator._v),
            graph: {
                segments: [
                    {fromLane: 0, toLane: 0, colorIndex: 0}
                ]
            },
            cards: [
                {
                    text: "Merge feature/timeline",
                    description: "9830e1b · main",
                    commit: "merge-feature",
                    labels: [
                        {text: "main", status: Fluent.Enums.statusLevel.info},
                        {text: "merge", status: Fluent.Enums.statusLevel.success}
                    ],
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0, endAtNode: true},
                            {fromLane: 0, toLane: 0, colorIndex: 0, startAtNode: true},
                            {fromLane: 0, toLane: 1, colorIndex: 1, startAtNode: true}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_ad8f635a6b81da15", Fluent.Translator._v),
                    description: "d9c1b5f · feature/timeline",
                    commit: "feature-fix",
                    graph: {
                        nodeLane: 1,
                        nodeColorIndex: 1,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0},
                            {fromLane: 1, toLane: 1, colorIndex: 1}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_117038fca5ff03f9", Fluent.Translator._v),
                    description: "7a6728d · feature/timeline",
                    commit: "feature-test",
                    graph: {
                        nodeLane: 1,
                        nodeColorIndex: 1,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0},
                            {fromLane: 1, toLane: 1, colorIndex: 1}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_886816422bf7b518", Fluent.Translator._v),
                    description: "cacec6e · main",
                    commit: "sync-feature",
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0, endAtNode: true},
                            {fromLane: 1, toLane: 0, colorIndex: 1, endAtNode: true},
                            {fromLane: 0, toLane: 0, colorIndex: 0, startAtNode: true}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_7a0249c9221b1e73", Fluent.Translator._v),
                    description: "e34acf8 · main",
                    commit: "main-refactor",
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_aa6961aea844cb9c", Fluent.Translator._v),
                    description: "be281d0 · main",
                    commit: "branch-gallery",
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0, endAtNode: true},
                            {fromLane: 0, toLane: 0, colorIndex: 0, startAtNode: true},
                            {fromLane: 0, toLane: 2, colorIndex: 2, startAtNode: true}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_a4bbb56e773b37b3", Fluent.Translator._v),
                    description: "fca8d6e · gallery",
                    commit: "gallery-style",
                    graph: {
                        nodeLane: 2,
                        nodeColorIndex: 2,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0},
                            {fromLane: 2, toLane: 2, colorIndex: 2}
                        ]
                    }
                },
                {
                    text: "Merge gallery preview",
                    description: "13ac741 · main",
                    commit: "merge-gallery",
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0, endAtNode: true},
                            {fromLane: 2, toLane: 0, colorIndex: 2, endAtNode: true},
                            {fromLane: 0, toLane: 0, colorIndex: 0, startAtNode: true}
                        ]
                    }
                },
                {
                    text: Fluent.Translator.tr("gallery_6a20fc431bc6bb3a", Fluent.Translator._v),
                    description: "65bf901 · main",
                    commit: "graph-base",
                    graph: {
                        nodeLane: 0,
                        nodeColorIndex: 0,
                        segments: [
                            {fromLane: 0, toLane: 0, colorIndex: 0}
                        ]
                    }
                }
            ]
        }
    ]
}
