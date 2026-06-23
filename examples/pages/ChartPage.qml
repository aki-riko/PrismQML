// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML as Fluent
import "../../fluentqml/FluentQML/controls/data"
import "../../fluentqml/FluentQML/controls/containers"

// Chart components page - Fluent Design style 图表组件页面 - Fluent Design 风格
Item {
    id: root
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../fluentqml/FluentQML/controls/icons/fluent/" + name + ".svg")
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
                Text { text: "图表组件"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "fluentqml.controls.data - Fluent Design Style"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // ==================== Bar Chart - Multi Series 柱状图 - 多系列 ====================
            ExampleCard {
                title: "柱状图 (Bar Chart)"
                description: "ChartView - Multi-series bar chart"
                ComponentCard {
                    label: "type_bar"
                    ChartView {
                        width: 600; height: 320
                        chartType: Fluent.Enums.chart.type_bar
                        title: "Rainfall vs Evaporation"
                        subtitle: "Fake Data"
                        showAverage: true
                        showMinMax: true
                        showBarGradient: true
                        chartData: [
                            {label: "Jan"}, {label: "Feb"}, {label: "Mar"}, {label: "Apr"},
                            {label: "May"}, {label: "Jun"}, {label: "Jul"}, {label: "Aug"},
                            {label: "Sep"}, {label: "Oct"}, {label: "Nov"}, {label: "Dec"}
                        ]
                        series: [
                            {name: "Rainfall", values: [2, 4.9, 7, 23.2, 25.6, 76.7, 135.6, 162.2, 32.6, 20, 6.4, 3.3], color: "#0078d4"},
                            {name: "Evaporation", values: [2.6, 5.9, 9, 26.4, 28.7, 70.7, 175.6, 182.2, 48.7, 18.8, 6, 2.3], color: "#107c10"}
                        ]
                    }
                }
            }
            
            // ==================== Horizontal Bar Chart 水平柱状图 ====================
            ExampleCard {
                title: "水平柱状图 (Horizontal Bar Chart)"
                description: "ChartView - barOrientation: orientation_horizontal"
                ComponentCard {
                    label: "horizontal"
                    ChartView {
                        width: 420; height: 220
                        chartType: Fluent.Enums.chart.type_bar
                        barOrientation: Fluent.Enums.chart.orientation_horizontal
                        title: "销售排名"
                        chartData: [
                            {label: "产品A", value: 120, color: Fluent.Enums.demoPalette.blue},
                            {label: "产品B", value: 98, color: Fluent.Enums.demoPalette.green},
                            {label: "产品C", value: 85, color: Fluent.Enums.demoPalette.orange},
                            {label: "产品D", value: 72, color: Fluent.Enums.demoPalette.purple},
                            {label: "产品E", value: 65, color: Fluent.Enums.demoPalette.red}
                        ]
                    }
                }
            }

            // ==================== Line Chart - Multi Series 折线图 - 多系列 ====================
            ExampleCard {
                title: "折线图 (Line Chart)"
                description: "ChartView - Multi-series line chart with area gradient"
                ComponentCard {
                    label: "type_line"
                    ChartView {
                        width: 560; height: 300
                        chartType: Fluent.Enums.chart.type_line
                        title: "Temperature Change in the Coming Week"
                        boundaryGap: false
                        showAreaGradient: true
                        yAxisSuffix: " °C"
                        showAverage: true
                        showMinMax: true
                        chartData: [
                            {label: "Mon"}, {label: "Tue"}, {label: "Wed"},
                            {label: "Thu"}, {label: "Fri"}, {label: "Sat"}, {label: "Sun"}
                        ]
                        series: [
                            {name: "Highest", values: [10, 11, 13, 11, 12, 12, 9], color: "#0078d4"},
                            {name: "Lowest", values: [1, -2, 2, 5, 3, 2, 0], color: "#107c10"}
                        ]
                    }
                }
            }
            
            // ==================== Stacked Area Chart 堆叠面积图 ====================
            ExampleCard {
                title: "堆叠面积图 (Stacked Area Chart)"
                description: "ChartView - stacked: true"
                ComponentCard {
                    label: "stacked"
                    ChartView {
                        width: 600; height: 320
                        chartType: Fluent.Enums.chart.type_line
                        title: "Stacked Area Chart"
                        boundaryGap: false
                        stacked: true
                        chartData: [
                            {label: "Mon"}, {label: "Tue"}, {label: "Wed"},
                            {label: "Thu"}, {label: "Fri"}, {label: "Sat"}, {label: "Sun"}
                        ]
                        series: [
                            {name: "Email", values: [120, 132, 101, 134, 90, 230, 210], color: "#0078d4"},
                            {name: "Union Ads", values: [220, 182, 191, 234, 290, 330, 310], color: "#107c10"},
                            {name: "Video Ads", values: [150, 232, 201, 154, 190, 330, 410], color: "#ffb900"},
                            {name: "Direct", values: [320, 332, 301, 334, 390, 330, 320], color: "#d13438"},
                            {name: "Search Engine", values: [820, 932, 901, 934, 1290, 1330, 1320], color: "#00b7c3"}
                        ]
                    }
                }
            }
            
            // ==================== Pie Chart 饼图 ====================
            ExampleCard {
                title: "饼图 (Pie Chart)"
                description: "ChartView - Pie chart with hover effect"
                ComponentCard {
                    label: "type_pie"
                    ChartView {
                        width: 420; height: 280
                        chartType: Fluent.Enums.chart.type_pie
                        title: "Referer of a Website"
                        subtitle: "Fake Data"
                        chartData: [
                            {label: "Search Engine", value: 1048, color: "#0078d4"},
                            {label: "Direct", value: 735, color: "#107c10"},
                            {label: "Email", value: 580, color: "#ffb900"},
                            {label: "Union Ads", value: 484, color: "#d13438"},
                            {label: "Video Ads", value: 300, color: "#00b7c3"}
                        ]
                    }
                }
            }
            
            // ==================== Donut Chart 环形图 ====================
            ExampleCard {
                title: "环形图 (Donut Chart)"
                description: "ChartView - isDonut: true"
                ComponentCard {
                    label: "type_donut"
                    ChartView {
                        width: 420; height: 280
                        chartType: Fluent.Enums.chart.type_pie
                        title: "Traffic Sources"
                        isDonut: true
                        donutRatio: 0.55
                        donutCenterText: "3147"
                        donutCenterSubtext: "Total"
                        chartData: [
                            {label: "Search Engine", value: 1048, color: "#0078d4"},
                            {label: "Direct", value: 735, color: "#107c10"},
                            {label: "Email", value: 580, color: "#ffb900"},
                            {label: "Union Ads", value: 484, color: "#d13438"},
                            {label: "Video Ads", value: 300, color: "#00b7c3"}
                        ]
                    }
                }
            }
            
            // ==================== Donut Chart with Emphasis Center 带中心强调的环形图 ====================
            ExampleCard {
                title: "环形图 - 中心强调 (Emphasis Center)"
                description: "ChartView - emphasisCenter: true (hover to see effect)"
                ComponentCard {
                    label: "emphasisCenter"
                    ChartView {
                        width: 420; height: 300
                        chartType: Fluent.Enums.chart.type_pie
                        title: "Access From"
                        isDonut: true
                        donutRatio: 0.5
                        emphasisCenter: true
                        chartData: [
                            {label: "Search Engine", value: 1048, color: "#0078d4"},
                            {label: "Direct", value: 735, color: "#107c10"},
                            {label: "Email", value: 580, color: "#ffb900"},
                            {label: "Union Ads", value: 484, color: "#d13438"},
                            {label: "Video Ads", value: 300, color: "#00b7c3"}
                        ]
                    }
                }
            }
            
            // ==================== Scatter Chart 散点图 ====================
            ExampleCard {
                title: "散点图 (Scatter Chart)"
                description: "ChartView - Scatter plot with outlier detection"
                ComponentCard {
                    label: "type_scatter"
                    ChartView {
                        width: 500; height: 320
                        chartType: Fluent.Enums.chart.type_scatter
                        title: "Outlier Detection"
                        series: [
                            // effectScatter: highlighted outliers with ripple 高亮异常点带涟漪
                            {name: "Outliers", type: "effectScatter", symbolSize: 20, data: [[172.7, 105.2], [153.4, 42]], color: "#d13438"},
                            // scatter: normal data points 普通数据点
                            {name: "Normal", type: "scatter", symbolSize: 8, data: [
                                [161.2, 51.6], [167.5, 59], [159.5, 49.2], [157, 63], [155.8, 53.6],
                                [170, 59], [159.1, 47.6], [166, 69.8], [176.2, 66.8], [160.2, 75.2],
                                [172.5, 55.2], [170.9, 54.2], [172.9, 62.5], [160, 50], [147.2, 49.8],
                                [168.2, 49.2], [175, 73.2], [157, 47.8], [167.6, 68.8], [159.5, 50.6],
                                [175, 82.5], [166.8, 57.2], [176.5, 87.8], [170.2, 72.8], [174, 54.5],
                                [173, 59.8], [179.9, 67.3], [170.5, 67.8], [160, 47], [154.4, 46.2],
                                [162, 55], [176.5, 83], [160, 54.4], [152, 45.8], [162.1, 53.6]
                            ], color: "#0078d4"}
                        ]
                    }
                }
            }
            
            // ==================== Radar Chart 雷达图 ====================
            ExampleCard {
                title: "雷达图 (Radar Chart)"
                description: "ChartView - Multi-indicator radar chart"
                ComponentCard {
                    label: "type_radar"
                    ChartView {
                        width: 480; height: 340
                        chartType: Fluent.Enums.chart.type_radar
                        title: "Basic Radar Chart"
                        indicators: [
                            {name: "Sales", max: 6500},
                            {name: "Administration", max: 16000},
                            {name: "Information Technology", max: 30000},
                            {name: "Customer Support", max: 38000},
                            {name: "Development", max: 52000},
                            {name: "Marketing", max: 25000}
                        ]
                        series: [
                            {name: "Allocated Budget", values: [4200, 3000, 20000, 35000, 50000, 18000], color: "#0078d4"},
                            {name: "Actual Spending", values: [5000, 14000, 28000, 26000, 42000, 21000], color: "#107c10"}
                        ]
                    }
                }
            }
            
            // ==================== Boxplot Chart 箱线图 ====================
            ExampleCard {
                title: "箱线图 (Boxplot Chart)"
                description: "ChartView - Statistical distribution"
                ComponentCard {
                    label: "type_boxplot"
                    ChartView {
                        width: 560; height: 340
                        chartType: Fluent.Enums.chart.type_boxplot
                        title: "Michelson-Morley Experiment"
                        subtitle: "Speed of Light Data"
                        boxplotData: [
                            {label: "Exp 1", min: 650, q1: 850, median: 930, q3: 980, max: 1070, outliers: []},
                            {label: "Exp 2", min: 760, q1: 800, median: 850, q3: 900, max: 960, outliers: []},
                            {label: "Exp 3", min: 620, q1: 840, median: 860, q3: 880, max: 970, outliers: []},
                            {label: "Exp 4", min: 720, q1: 770, median: 810, q3: 880, max: 920, outliers: []},
                            {label: "Exp 5", min: 740, q1: 800, median: 820, q3: 870, max: 950, outliers: []}
                        ]
                    }
                }
            }
            
            // ==================== Boxplot with Outliers 带异常点的箱线图 ====================
            ExampleCard {
                title: "箱线图 - 带异常点 (Boxplot with Outliers)"
                description: "ChartView - Boxplot showing outlier detection"
                ComponentCard {
                    label: "outliers"
                    ChartView {
                        width: 480; height: 300
                        chartType: Fluent.Enums.chart.type_boxplot
                        title: "Test Scores Distribution"
                        boxplotData: [
                            {label: "Class A", min: 55, q1: 70, median: 78, q3: 85, max: 95, outliers: [35, 42]},
                            {label: "Class B", min: 60, q1: 72, median: 80, q3: 88, max: 98, outliers: [45]},
                            {label: "Class C", min: 50, q1: 65, median: 75, q3: 82, max: 92, outliers: [30, 100]},
                            {label: "Class D", min: 58, q1: 68, median: 76, q3: 84, max: 94, outliers: []}
                        ]
                    }
                }
            }
            
            // ==================== Audio Waveform 音频波形 ====================
            ExampleCard {
                title: "音频波形 (AudioWaveform)"
                description: "AudioWaveform"
                ComponentCard {
                    label: "AudioWaveform"
                    AudioWaveform { width: 320; height: 70 }
                }
            }
        }
    }
}
