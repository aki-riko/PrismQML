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
        { color: "#e74c3c", text: "Banner 1" },
        { color: "#3498db", text: "Banner 2" },
        { color: "#2ecc71", text: "Banner 3" },
        { color: "#9b59b6", text: "Banner 4" }
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
                    text: "轮播图 & 分页指示器"
                    font.pixelSize: Fluent.Enums.typography.displayLarge
                    font.bold: true
                    color: Fluent.Enums.textColor.primary
                    font.family: Fluent.Enums.fontFamily 
                }
                Text { 
                    text: "Carousel + PipsPager - 统一轮播组件配合分页指示器"
                    font.pixelSize: Fluent.Enums.typography.caption
                    color: Fluent.Enums.textColor.secondary
                    font.family: Fluent.Enums.fontFamily 
                }
            }

            // ==================== PipsPager Section 分页指示器部分 ====================
            ExampleCard {
                title: "分页指示器 (PipsPager)"
                description: "HorizontalPipsPager / VerticalPipsPager - 支持翻页按钮、可见数量限制、平滑滚动"
                
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    Row {
                        spacing: Fluent.Enums.spacing.xxl
                        
                        ComponentCard {
                            label: "水平基础 (5点)"
                            HorizontalPipsPager {
                                count: 5
                                currentIndex: 2
                            }
                        }
                        
                        ComponentCard {
                            label: "垂直基础 (4点)"
                            VerticalPipsPager {
                                count: 4
                                currentIndex: 1
                            }
                        }
                        
                        ComponentCard {
                            label: "带按钮 (始终显示)"
                            HorizontalPipsPager {
                                count: 10
                                currentIndex: 3
                                maxVisible: 5
                                prevButtonMode: Fluent.Enums.pipsPager.button_always
                                nextButtonMode: Fluent.Enums.pipsPager.button_always
                            }
                        }
                        
                        ComponentCard {
                            label: "垂直带按钮"
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
                title: "露边轮播"
                description: "Carousel - orientation 水平/垂直 + 外部 PipsPager 联动"

                Row {
                    spacing: Fluent.Enums.spacing.xxl

                    ComponentCard {
                        label: "水平 (默认)"
                        Carousel {
                            width: 400
                            height: 180
                            model: ["qrc:/image/horizontal/1.jpg", "qrc:/image/horizontal/2.jpg", "qrc:/image/horizontal/3.jpg", "qrc:/image/horizontal/4.jpg"]
                            autoPlay: true
                            showNavButtons: true
                        }
                    }

                    ComponentCard {
                        label: "垂直 (orientation: Qt.Vertical)"
                        Carousel {
                            width: 200
                            height: 280
                            model: ["qrc:/image/vertical/1.jpg", "qrc:/image/vertical/2.jpg", "qrc:/image/vertical/3.jpg", "qrc:/image/vertical/4.jpg"]
                            orientation: Qt.Vertical
                            showNavButtons: true
                        }
                    }

                    ComponentCard {
                        label: "外部 PipsPager 联动 + loop"
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
                title: "普通滑动轮播"
                description: "Carousel - effect: effect_slide(整图滑动，无两侧 peek)"

                Row {
                    spacing: Fluent.Enums.spacing.xxl

                    ComponentCard {
                        label: "effect_slide (水平)"
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
                        label: "effect_slide + 垂直"
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
