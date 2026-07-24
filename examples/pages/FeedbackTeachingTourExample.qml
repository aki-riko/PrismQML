// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// FeedbackTeachingTourExample - TeachingTour gallery example 新手指引示例
ExampleCard {
    id: control

    title: "TeachingTour 新手指引"
    description: "全窗口遮罩聚焦目标区域，支持下一步、完成与跳过"

    // ==================== Content 内容 ====================
    Row {
        spacing: Fluent.Enums.spacing.l

        Button {
            text: "开始新手指引"
            style: Fluent.Enums.button.style_primary
            onClicked: teachingTour.start()
        }

        Button {
            id: firstTarget

            text: "个人资料"
        }

        Button {
            id: secondTarget

            text: "通知设置"
        }
    }

    TeachingTour {
        id: teachingTour

        steps: [
            {
                "target": firstTarget,
                "title": "第一步",
                "content": "在这里编辑头像和个人信息。",
                "anchorPosition": Fluent.Enums.teachingTip.anchor_bottom
            },
            {
                "target": secondTarget,
                "title": "第二步",
                "content": "在这里选择需要接收的通知。",
                "anchorPosition": Fluent.Enums.teachingTip.anchor_bottom
            }
        ]
    }
}
