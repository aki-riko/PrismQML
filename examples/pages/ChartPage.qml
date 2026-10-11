// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Chart components page - Fluent Design style 图表组件页面 - Fluent Design 风格
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_519ccb00791b0b9f", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }
            
            // ==================== Bar Chart - Multi Series 柱状图 - 多系列 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_e5b63006a73c1640", Fluent.Translator._v)
                description: "ChartView - Multi-series bar chart"
                ComponentCard {
                    label: "type_bar"
                    ChartView {
                        width: 600; height: 320
                        chartType: Fluent.Enums.chart.type_bar
                        title: Fluent.Translator.tr("gallery_ce2a040dc533453c", Fluent.Translator._v)
                        subtitle: Fluent.Translator.tr("gallery_bad84c328f619c41", Fluent.Translator._v)
                        showAverage: true
                        showMinMax: true
                        showBarGradient: true
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_3e750612b1506eb7", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_42d5f1ff3cb96317", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_720a8da4588d9c9f", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_1b6e21a2413c3704", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_295d12c47765d225", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_bc3e874c55e6d8b6", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_e610f3af850fd30f", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_397be3b504637b99", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_0bc8c1a9a3b8f442", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_fa5042c9a31ef928", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_53c19ce5c76fdd69", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_2a3da8a22b970422", Fluent.Translator._v)}
                        ]
                        series: [
                            {name: Fluent.Translator.tr("gallery_6ccc4701014c58cc", Fluent.Translator._v), values: [2, 4.9, 7, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20, 6.4, 3.3], color: Fluent.Enums.chartColors.palette[0]},
                            {name: Fluent.Translator.tr("gallery_975f602e49c1038f", Fluent.Translator._v), values: [2.6, 5.9, 9, 26.4, 28.7, 70.7, 175.6, 182.2, 48.7, 18.8, 6, 2.3], color: Fluent.Enums.chartColors.palette[1]}
                        ]
                    }
                }
            }
            
            // ==================== Horizontal Bar Chart 水平柱状图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_859edeb6b0ef412d", Fluent.Translator._v)
                description: "ChartView - barOrientation: orientation_horizontal"
                ComponentCard {
                    label: "horizontal"
                    ChartView {
                        width: 420; height: 220
                        chartType: Fluent.Enums.chart.type_bar
                        barOrientation: Fluent.Enums.chart.orientation_horizontal
                        title: Fluent.Translator.tr("gallery_3a84ef1fd6c433e4", Fluent.Translator._v)
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_bc89675cb97d885b", Fluent.Translator._v), value: 120, color: Fluent.Enums.chartColors.palette[0]},
                            {label: Fluent.Translator.tr("gallery_37a41cac23af4aca", Fluent.Translator._v), value: 98, color: Fluent.Enums.chartColors.palette[1]},
                            {label: Fluent.Translator.tr("gallery_14ae1ed5ea1092e3", Fluent.Translator._v), value: 85, color: Fluent.Enums.chartColors.palette[2]},
                            {label: Fluent.Translator.tr("gallery_2fc2cfbe651c8f7a", Fluent.Translator._v), value: 72, color: Fluent.Enums.chartColors.palette[3]},
                            {label: Fluent.Translator.tr("gallery_d00568f458f0dfd1", Fluent.Translator._v), value: 65, color: Fluent.Enums.chartColors.palette[4]}
                        ]
                    }
                }
            }

            // ==================== Line Chart - Multi Series 折线图 - 多系列 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_963916ba956b4ff3", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_30b7e0a0252a9ac8", Fluent.Translator._v)
                ComponentCard {
                    label: "type_line"
                    ChartView {
                        width: 560; height: 300
                        chartType: Fluent.Enums.chart.type_line
                        title: Fluent.Translator.tr("gallery_049c44589b5b21ee", Fluent.Translator._v)
                        boundaryGap: false
                        showAreaGradient: true
                        yAxisSuffix: " °C"
                        showAverage: true
                        showMinMax: true
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_c430f4c12eaa146a", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_d1378a68e620b1cc", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_2961168962be301a", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_e9d3b01a5a00f1af", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_572388f3b096b817", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_f9aa11dbb15ce647", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_ee239f3943293f87", Fluent.Translator._v)}
                        ]
                        series: [
                            {name: Fluent.Translator.tr("gallery_8672864e90417138", Fluent.Translator._v), values: [10, 11, 13, 11, 12, 12, 9], color: Fluent.Enums.chartColors.palette[0]},
                            {name: Fluent.Translator.tr("gallery_8b5f2a61b79721aa", Fluent.Translator._v), values: [1, -2, 2, 5, 3, 2, 0], color: Fluent.Enums.chartColors.palette[1]}
                        ]
                    }
                }
            }
            
            // ==================== Stacked Area Chart 堆叠面积图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_abb744eaa0c954a7", Fluent.Translator._v)
                description: "ChartView - stacked: true"
                ComponentCard {
                    label: "stacked"
                    ChartView {
                        width: 600; height: 320
                        chartType: Fluent.Enums.chart.type_line
                        title: Fluent.Translator.tr("gallery_dd1d6f23c154550f", Fluent.Translator._v)
                        boundaryGap: false
                        stacked: true
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_c430f4c12eaa146a", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_d1378a68e620b1cc", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_2961168962be301a", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_e9d3b01a5a00f1af", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_572388f3b096b817", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_f9aa11dbb15ce647", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_ee239f3943293f87", Fluent.Translator._v)}
                        ]
                        series: [
                            {name: Fluent.Translator.tr("gallery_1b2714b812d42f77", Fluent.Translator._v), values: [120, 132, 101, 134, 90, 230, 210], color: Fluent.Enums.chartColors.palette[0]},
                            {name: Fluent.Translator.tr("gallery_7a2879c781b005ef", Fluent.Translator._v), values: [220, 182, 191, 234, 290, 330, 310], color: Fluent.Enums.chartColors.palette[1]},
                            {name: Fluent.Translator.tr("gallery_bd81a9b7948fa055", Fluent.Translator._v), values: [150, 232, 201, 154, 190, 330, 410], color: Fluent.Enums.chartColors.palette[2]},
                            {name: Fluent.Translator.tr("gallery_762cd9c2de69577b", Fluent.Translator._v), values: [320, 332, 301, 334, 390, 330, 320], color: Fluent.Enums.chartColors.palette[3]},
                            {name: Fluent.Translator.tr("gallery_82cbe72ab9d93e0a", Fluent.Translator._v), values: [820, 932, 901, 934, 1290, 1330, 1320], color: Fluent.Enums.chartColors.palette[5]}
                        ]
                    }
                }
            }
            
            // ==================== Pie Chart 饼图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ff1dc8827e7acaf2", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d039b5cdb1c90520", Fluent.Translator._v)
                ComponentCard {
                    label: "type_pie"
                    ChartView {
                        width: 420; height: 280
                        chartType: Fluent.Enums.chart.type_pie
                        title: Fluent.Translator.tr("gallery_1a4996debbffffb8", Fluent.Translator._v)
                        subtitle: Fluent.Translator.tr("gallery_bad84c328f619c41", Fluent.Translator._v)
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_82cbe72ab9d93e0a", Fluent.Translator._v), value: 1048, color: Fluent.Enums.chartColors.palette[0]},
                            {label: Fluent.Translator.tr("gallery_762cd9c2de69577b", Fluent.Translator._v), value: 735, color: Fluent.Enums.chartColors.palette[1]},
                            {label: Fluent.Translator.tr("gallery_1b2714b812d42f77", Fluent.Translator._v), value: 580, color: Fluent.Enums.chartColors.palette[2]},
                            {label: Fluent.Translator.tr("gallery_7a2879c781b005ef", Fluent.Translator._v), value: 484, color: Fluent.Enums.chartColors.palette[3]},
                            {label: Fluent.Translator.tr("gallery_bd81a9b7948fa055", Fluent.Translator._v), value: 300, color: Fluent.Enums.chartColors.palette[5]}
                        ]
                    }
                }
            }
            
            // ==================== Donut Chart 环形图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_37f9b294197d0733", Fluent.Translator._v)
                description: "ChartView - isDonut: true"
                ComponentCard {
                    label: "type_donut"
                    ChartView {
                        width: 420; height: 280
                        chartType: Fluent.Enums.chart.type_pie
                        title: Fluent.Translator.tr("gallery_6e8e4afc3398408b", Fluent.Translator._v)
                        isDonut: true
                        donutRatio: 0.55
                        donutCenterText: "3147"
                        donutCenterSubtext: Fluent.Translator.tr("gallery_e8dc871a7fdee23b", Fluent.Translator._v)
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_82cbe72ab9d93e0a", Fluent.Translator._v), value: 1048, color: Fluent.Enums.chartColors.palette[0]},
                            {label: Fluent.Translator.tr("gallery_762cd9c2de69577b", Fluent.Translator._v), value: 735, color: Fluent.Enums.chartColors.palette[1]},
                            {label: Fluent.Translator.tr("gallery_1b2714b812d42f77", Fluent.Translator._v), value: 580, color: Fluent.Enums.chartColors.palette[2]},
                            {label: Fluent.Translator.tr("gallery_7a2879c781b005ef", Fluent.Translator._v), value: 484, color: Fluent.Enums.chartColors.palette[3]},
                            {label: Fluent.Translator.tr("gallery_bd81a9b7948fa055", Fluent.Translator._v), value: 300, color: Fluent.Enums.chartColors.palette[5]}
                        ]
                    }
                }
            }
            
            // ==================== Donut Chart with Emphasis Center 带中心强调的环形图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3cf407787b79ad97", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_95cde7e1ba90e7ce", Fluent.Translator._v)
                ComponentCard {
                    label: "emphasisCenter"
                    ChartView {
                        width: 420; height: 300
                        chartType: Fluent.Enums.chart.type_pie
                        title: Fluent.Translator.tr("gallery_c8f60588710668cc", Fluent.Translator._v)
                        isDonut: true
                        donutRatio: 0.5
                        emphasisCenter: true
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_82cbe72ab9d93e0a", Fluent.Translator._v), value: 1048, color: Fluent.Enums.chartColors.palette[0]},
                            {label: Fluent.Translator.tr("gallery_762cd9c2de69577b", Fluent.Translator._v), value: 735, color: Fluent.Enums.chartColors.palette[1]},
                            {label: Fluent.Translator.tr("gallery_1b2714b812d42f77", Fluent.Translator._v), value: 580, color: Fluent.Enums.chartColors.palette[2]},
                            {label: Fluent.Translator.tr("gallery_7a2879c781b005ef", Fluent.Translator._v), value: 484, color: Fluent.Enums.chartColors.palette[3]},
                            {label: Fluent.Translator.tr("gallery_bd81a9b7948fa055", Fluent.Translator._v), value: 300, color: Fluent.Enums.chartColors.palette[5]}
                        ]
                    }
                }
            }
            
            // ==================== Scatter Chart 散点图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_36af541acfbcd432", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_4182f4043194566b", Fluent.Translator._v)
                ComponentCard {
                    label: "type_scatter"
                    ChartView {
                        width: 500; height: 320
                        chartType: Fluent.Enums.chart.type_scatter
                        title: Fluent.Translator.tr("gallery_8ae0d7e7e42468f3", Fluent.Translator._v)
                        series: [
                            // effectScatter: highlighted outliers with ripple 高亮异常点带涟漪
                            {name: Fluent.Translator.tr("gallery_eb02176db2ba5e00", Fluent.Translator._v), type: "effectScatter", symbolSize: 20, data: [[172.7, 105.2], [153.4, 42]], color: Fluent.Enums.chartColors.palette[3]},
                            // scatter: normal data points 普通数据点
                            {name: Fluent.Translator.tr("gallery_296de0e31f8c22d9", Fluent.Translator._v), type: "scatter", symbolSize: 8, data: [
                                [161.2, 51.6], [167.5, 59], [159.5, 49.2], [157, 63], [155.8, 53.6],
                                [170, 59], [159.1, 47.6], [166, 69.8], [176.2, 66.8], [160.2, 75.2],
                                [172.5, 55.2], [170.9, 54.2], [172.9, 62.5], [160, 50], [147.2, 49.8],
                                [168.2, 49.2], [175, 73.2], [157, 47.8], [167.6, 68.8], [159.5, 50.6],
                                [175, 82.5], [166.8, 57.2], [176.5, 87.8], [170.2, 72.8], [174, 54.5],
                                [173, 59.8], [179.9, 67.3], [170.5, 67.8], [160, 47], [154.4, 46.2],
                                [162, 55], [176.5, 83], [160, 54.4], [152, 45.8], [162.1, 53.6]
                            ], color: Fluent.Enums.chartColors.palette[0]}
                        ]
                    }
                }
            }
            
            // ==================== Radar Chart 雷达图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1d35f107645d5a6c", Fluent.Translator._v)
                description: "ChartView - Multi-indicator radar chart"
                ComponentCard {
                    label: "type_radar"
                    ChartView {
                        width: 480; height: 340
                        chartType: Fluent.Enums.chart.type_radar
                        title: Fluent.Translator.tr("gallery_546942f8b48814d1", Fluent.Translator._v)
                        indicators: [
                            {name: Fluent.Translator.tr("gallery_faf3aa3bca537fe8", Fluent.Translator._v), max: 6500},
                            {name: Fluent.Translator.tr("gallery_e79890c96ee6f0c5", Fluent.Translator._v), max: 16000},
                            {name: Fluent.Translator.tr("gallery_bea5df18ef44c9e8", Fluent.Translator._v), max: 30000},
                            {name: Fluent.Translator.tr("gallery_73c20614bb204536", Fluent.Translator._v), max: 38000},
                            {name: Fluent.Translator.tr("gallery_cb086d66cd715fa8", Fluent.Translator._v), max: 52000},
                            {name: Fluent.Translator.tr("gallery_9c1e8bd22488de3b", Fluent.Translator._v), max: 25000}
                        ]
                        series: [
                            {name: Fluent.Translator.tr("gallery_12418479a66de3a4", Fluent.Translator._v), values: [4200, 3000, 20000, 35000, 50000, 18000], color: Fluent.Enums.chartColors.palette[0]},
                            {name: Fluent.Translator.tr("gallery_27e510bb25443ce4", Fluent.Translator._v), values: [5000, 14000, 28000, 26000, 42000, 21000], color: Fluent.Enums.chartColors.palette[1]}
                        ]
                    }
                }
            }
            
            // ==================== Boxplot Chart 箱线图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_430076d0d0890898", Fluent.Translator._v)
                description: "ChartView - Statistical distribution"
                ComponentCard {
                    label: "type_boxplot"
                    ChartView {
                        width: 560; height: 340
                        chartType: Fluent.Enums.chart.type_boxplot
                        title: Fluent.Translator.tr("gallery_0ac3b54e9e564baa", Fluent.Translator._v)
                        subtitle: Fluent.Translator.tr("gallery_35e4ba3d73ec8af5", Fluent.Translator._v)
                        boxplotData: [
                            {label: Fluent.Translator.tr("gallery_9cb3046e6db1b8d3", Fluent.Translator._v), min: 650, q1: 850, median: 930, q3: 980, max: 1070, outliers: []},
                            {label: Fluent.Translator.tr("gallery_680af39b3e465362", Fluent.Translator._v), min: 760, q1: 800, median: 850, q3: 900, max: 960, outliers: []},
                            {label: Fluent.Translator.tr("gallery_4c84bb65bdec9d5c", Fluent.Translator._v), min: 620, q1: 840, median: 860, q3: 880, max: 970, outliers: []},
                            {label: Fluent.Translator.tr("gallery_970634c639b07f5b", Fluent.Translator._v), min: 720, q1: 770, median: 810, q3: 880, max: 920, outliers: []},
                            {label: Fluent.Translator.tr("gallery_b1a8d67fee8ffeff", Fluent.Translator._v), min: 740, q1: 800, median: 820, q3: 870, max: 950, outliers: []}
                        ]
                    }
                }
            }
            
            // ==================== Boxplot with Outliers 带异常点的箱线图 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a4888ea5661fa13a", Fluent.Translator._v)
                description: "ChartView - Boxplot showing outlier detection"
                ComponentCard {
                    label: "outliers"
                    ChartView {
                        width: 480; height: 300
                        chartType: Fluent.Enums.chart.type_boxplot
                        title: Fluent.Translator.tr("gallery_3172c3a3fcdfd371", Fluent.Translator._v)
                        boxplotData: [
                            {label: Fluent.Translator.tr("gallery_6d34dad76233be0e", Fluent.Translator._v), min: 55, q1: 70, median: 78, q3: 85, max: 95, outliers: [35, 42]},
                            {label: Fluent.Translator.tr("gallery_fc93ce190ade25d3", Fluent.Translator._v), min: 60, q1: 72, median: 80, q3: 88, max: 98, outliers: [45]},
                            {label: Fluent.Translator.tr("gallery_f5b0c4e951d68cf0", Fluent.Translator._v), min: 50, q1: 65, median: 75, q3: 82, max: 92, outliers: [30, 100]},
                            {label: Fluent.Translator.tr("gallery_b76796b0dfd34fea", Fluent.Translator._v), min: 58, q1: 68, median: 76, q3: 84, max: 94, outliers: []}
                        ]
                    }
                }
            }
            
            // ==================== Audio Waveform 音频波形 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_8e2a8035d8dc6368", Fluent.Translator._v)
                description: "AudioWaveform"
                ComponentCard {
                    label: "AudioWaveform"
                    AudioWaveform { width: 320; height: 70 }
                }
            }

            // ==================== Circular Gauge 环形仪表盘 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_55507e1dd15f61bd", Fluent.Translator._v)
                description: "value / minValue / maxValue / unit"
                GalleryFlow {
                    ComponentCard { label: Fluent.Translator.tr("gallery_d971a7856d2becfc", Fluent.Translator._v); CircularGauge { width: 110; height: 110; value: 60; unit: "%" } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_d0d8bf9e3c5b8515", Fluent.Translator._v); CircularGauge { width: 110; height: 110; value: 85; unit: "%" } }
                    ComponentCard { label: Fluent.Translator.tr("gallery_7f0873fec2a1ac3f", Fluent.Translator._v); CircularGauge { width: 110; height: 110; value: 7; maxValue: 10 } }
                }
            }

            // ==================== Chart Data Zoom 图表视窗缩放 ====================
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1f0b5c05e2e3077d", Fluent.Translator._v)
                description: "viewportStart / viewportEnd (dual-handle selector)"
                ComponentCard {
                    label: "viewport 0.2 - 0.8"
                    ChartDataZoom {
                        width: 460
                        height: 96
                        chartData: [
                            {label: Fluent.Translator.tr("gallery_3e750612b1506eb7", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_42d5f1ff3cb96317", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_720a8da4588d9c9f", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_1b6e21a2413c3704", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_295d12c47765d225", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_bc3e874c55e6d8b6", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_e610f3af850fd30f", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_397be3b504637b99", Fluent.Translator._v)},
                            {label: Fluent.Translator.tr("gallery_0bc8c1a9a3b8f442", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_fa5042c9a31ef928", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_53c19ce5c76fdd69", Fluent.Translator._v)}, {label: Fluent.Translator.tr("gallery_2a3da8a22b970422", Fluent.Translator._v)}
                        ]
                        series: [
                            {name: Fluent.Translator.tr("gallery_6ccc4701014c58cc", Fluent.Translator._v), values: [2, 4.9, 7, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20, 6.4, 3.3], color: Fluent.Enums.chartColors.palette[0]}
                        ]
                        viewportStart: 0.2
                        viewportEnd: 0.8
                    }
                }
            }
        }
    }
}
