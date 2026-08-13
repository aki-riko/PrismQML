// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML
import PrismQML as Fluent

// FeedbackTeachingTourExample - TeachingTour gallery example 新手指引示例
ExampleCard {
    id: control

    title: Fluent.Translator.tr("gallery_83b9b08586d026b8", Fluent.Translator._v)
    description: Fluent.Translator.tr("gallery_ee8f78daf20350be", Fluent.Translator._v)

    // ==================== Content 内容 ====================
    Row {
        spacing: Fluent.Enums.spacing.l

        Button {
            objectName: "galleryTeachingTourStartButton"
            text: Fluent.Translator.tr("gallery_12db2da005b7030b", Fluent.Translator._v)
            style: Fluent.Enums.button.style_primary
            onClicked: teachingTour.start()
        }

        Button {
            id: firstTarget

            text: Fluent.Translator.tr("gallery_b94d13a45ea21152", Fluent.Translator._v)
        }

        Button {
            id: secondTarget

            text: Fluent.Translator.tr("gallery_247ca01ae2808bf7", Fluent.Translator._v)
        }
    }

    TeachingTour {
        id: teachingTour

        objectName: "galleryTeachingTour"
        steps: [
            {
                "target": firstTarget,
                "title": Fluent.Translator.tr("gallery_2dfed5d0b87e02ab", Fluent.Translator._v),
                "content": Fluent.Translator.tr("gallery_8ee5b78a1115f5ca", Fluent.Translator._v),
                "anchorPosition": Fluent.Enums.teachingTip.anchor_bottom
            },
            {
                "target": secondTarget,
                "title": Fluent.Translator.tr("gallery_248c17d5af3c53c1", Fluent.Translator._v),
                "content": Fluent.Translator.tr("gallery_d88f21dbfa7ea97d", Fluent.Translator._v),
                "anchorPosition": Fluent.Enums.teachingTip.anchor_bottom
            }
        ]
    }
}
