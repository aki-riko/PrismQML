// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Carousel Page 轮播页面
Item {
    id: root
    
    // Test data 测试数据
    property var testModel: [
        { color: Fluent.Enums.examplePageColors.carouselRed, text: "Banner 1" },
        { color: Fluent.Enums.examplePageColors.carouselBlue, text: "Banner 2" },
        { color: Fluent.Enums.examplePageColors.carouselGreen, text: "Banner 3" },
        { color: Fluent.Enums.examplePageColors.carouselPurple, text: "Banner 4" }
    ]
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { 
                    text: Fluent.Translator.tr("gallery_8da557d5b8a7f49a", Fluent.Translator._v)
                    font.pixelSize: Fluent.Enums.typography.displayLarge
                    font.bold: true
                    color: Fluent.Enums.textColor.primary
                    font.family: Fluent.Enums.fontFamily 
                }
                Text { 
                    text: Fluent.Translator.tr("gallery_21d472b97eb91c0b", Fluent.Translator._v)
                    font.pixelSize: Fluent.Enums.typography.caption
                    color: Fluent.Enums.textColor.secondary
                    font.family: Fluent.Enums.fontFamily 
                }
            }

            // ==================== PipsPager Section 分页指示器部分 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_c5cf81e08f22e5d5", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_feed68ac96819f85", Fluent.Translator._v)
                
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_1671919a8d15b42a", Fluent.Translator._v)
                            HorizontalPipsPager {
                                count: 5
                                currentIndex: 2
                            }
                        }
                        
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_e0a3ea0c1284da73", Fluent.Translator._v)
                            VerticalPipsPager {
                                count: 4
                                currentIndex: 1
                            }
                        }
                        
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_50d8fc2f69be51e0", Fluent.Translator._v)
                            HorizontalPipsPager {
                                count: 10
                                currentIndex: 3
                                maxVisible: 5
                                prevButtonMode: Fluent.Enums.pipsPager.button_always
                                nextButtonMode: Fluent.Enums.pipsPager.button_always
                            }
                        }
                        
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_054b03a76cff840d", Fluent.Translator._v)
                            VerticalPipsPager {
                                count: 8
                                currentIndex: 2
                                maxVisible: 4
                                prevButtonMode: Fluent.Enums.pipsPager.button_always
                                nextButtonMode: Fluent.Enums.pipsPager.button_always
                            }
                        }
                    }
                }
            }
            
            // ==================== Peek Carousel 露边轮播 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_cce4c8c1bc7d34b4", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_9e17cc2bef9868b7", Fluent.Translator._v)

                Row {
                    spacing: Fluent.Enums.spacing.xxl

                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_3f72e872c52f702f", Fluent.Translator._v)
                        Carousel {
                            width: 400
                            height: 180
                            model: ["qrc:/image/horizontal/1.jpg", "qrc:/image/horizontal/2.jpg", "qrc:/image/horizontal/3.jpg", "qrc:/image/horizontal/4.jpg"]
                            autoPlay: true
                            showNavButtons: true
                        }
                    }

                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_414c4d713eeb6da0", Fluent.Translator._v)
                        Carousel {
                            width: 200
                            height: 280
                            model: ["qrc:/image/vertical/1.jpg", "qrc:/image/vertical/2.jpg", "qrc:/image/vertical/3.jpg", "qrc:/image/vertical/4.jpg"]
                            orientation: Qt.Vertical
                            showNavButtons: true
                        }
                    }

                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_8448d9ffc9f9fc92", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.s
                            Carousel {
                                id: hCarousel
                                width: 320
                                height: 180
                                model: ["qrc:/image/horizontal/1.jpg", "qrc:/image/horizontal/2.jpg", "qrc:/image/horizontal/3.jpg", "qrc:/image/horizontal/4.jpg"]
                                loop: true
                                showIndicator: false
                            }
                            HorizontalPipsPager {
                                anchors.horizontalCenter: parent.horizontalCenter
                                count: hCarousel.model.length
                                currentIndex: hCarousel.currentIndex
                                onIndexClicked: (idx) => hCarousel.goTo(idx)
                            }
                        }
                    }
                }
            }

            // ==================== Plain Slide Carousel 普通滑动轮播 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_22672541d05520ef", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_cc38c3b4060f1068", Fluent.Translator._v)

                Row {
                    spacing: Fluent.Enums.spacing.xxl

                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_93881536b744e50f", Fluent.Translator._v)
                        Carousel {
                            width: 400
                            height: 180
                            model: ["qrc:/image/horizontal/1.jpg", "qrc:/image/horizontal/2.jpg", "qrc:/image/horizontal/3.jpg", "qrc:/image/horizontal/4.jpg"]
                            effect: Fluent.Enums.carousel.effect_slide
                            autoPlay: true
                            showNavButtons: true
                        }
                    }

                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_22cb302040e89090", Fluent.Translator._v)
                        Carousel {
                            width: 200
                            height: 280
                            model: ["qrc:/image/vertical/1.jpg", "qrc:/image/vertical/2.jpg", "qrc:/image/vertical/3.jpg", "qrc:/image/vertical/4.jpg"]
                            effect: Fluent.Enums.carousel.effect_slide
                            orientation: Qt.Vertical
                            showNavButtons: true
                        }
                    }
                }
            }
        }
    }
}
