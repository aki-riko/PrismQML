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
            title: "Git graph · 150% DPI",
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
                    text: "fix: 修复提交图边界像素",
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
                    text: "test: 增加分数滚动像素门禁",
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
                    text: "同步 feature/timeline",
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
                    text: "refactor: 整理 Timeline 数据模型",
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
                    text: "feat: 创建 gallery 分支",
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
                    text: "style: 调整 Gallery 展示密度",
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
                    text: "chore: 初始化提交图示例",
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
