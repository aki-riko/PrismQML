// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import "../../fluentqml/PrismQML/controls/buttons"
import "../../fluentqml/PrismQML/controls/inputs"
import "../../fluentqml/PrismQML/controls/inputs/ColorPicker/_internal"
import "../../fluentqml/PrismQML/controls/containers"
import "../../fluentqml/PrismQML/controls/containers/ScrollBar"
import "../../fluentqml/PrismQML/controls/data"

// 输入组件展示页面
Item {
    id: root
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../fluentqml/PrismQML/controls/icons/fluent/" + name + ".svg")
    }
    
    ScrollArea {
        id: scrollArea
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Enums.spacing.xxl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Enums.spacing.xs
                Text { text: "输入组件"; font.pixelSize: Enums.typography.displayLarge; font.bold: true; color: Enums.textColor.primary; font.family: Enums.fontFamily }
                Text { text: "fluentqml.controls.inputs"; font.pixelSize: Enums.typography.caption; color: Enums.textColor.secondary; font.family: Enums.fontFamily }
            }
            
            // 文本输入
            ExampleCard {
                title: "文本输入"
                description: "LineEdit / TextEdit"
                Column {
                    spacing: Enums.spacing.l
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_normal"; LineEdit { placeholderText: "LineEdit"; width: 180 } }
                        ComponentCard { label: "type_password"; LineEdit { inputType: Enums.input.type_password; placeholderText: "密码"; width: 180 } }
                        ComponentCard { label: "type_search"; LineEdit { inputType: Enums.input.type_search; placeholderText: "搜索"; width: 180 } }
                        ComponentCard { label: "collapsible"; LineEdit { inputType: Enums.input.type_search; collapsible: true; placeholderText: "搜索"; expandedWidth: 200 } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_label"; LineEdit { inputType: Enums.input.type_label; label: "用户名"; width: 200 } }
                        ComponentCard { label: "type_tag"; LineEdit { inputType: Enums.input.type_tag; placeholderText: "添加标签..."; width: 280; maxTags: 5; suggestions: ["测试", "测试2", "选项A", "选项B", "标签1", "标签2"] } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        // 差异化能力: 校验回调(长度≥2才接受) + 逗号/分号粘贴拆分
                        ComponentCard {
                            label: "tag_validate"
                            LineEdit {
                                inputType: Enums.input.type_tag
                                placeholderText: "≥2字, 逗号分隔"
                                width: 280
                                extraSeparators: [",", ";"]
                                validateTag: (t) => t.length >= 2
                            }
                        }
                        // 差异化能力: 按标签着色
                        ComponentCard {
                            label: "tag_colors"
                            LineEdit {
                                inputType: Enums.input.type_tag
                                placeholderText: "彩色标签"
                                width: 280
                                tags: ["紧急", "普通", "完成"]
                                tagColors: ({ "紧急": "#D13438", "普通": "#0078D4", "完成": "#107C10" })
                            }
                        }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "multiline_plain"; TextEdit { multilineType: Enums.input.multiline_plain; placeholderText: "PlainTextEdit"; width: 200; height: 60 } }
                        ComponentCard { label: "multiline_browser"; TextEdit { multilineType: Enums.input.multiline_browser; width: 200; height: 60; text: "<b>支持</b>富文本<i>显示</i>" } }
                    }
                }
            }
            
            // 下拉选择
            ExampleCard {
                title: "下拉选择"
                description: "ComboBox - type/style/feature"
                Column {
                    spacing: Enums.spacing.l
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "默认"; ComboBox { model: ["选项1", "选项2", "选项3", "选项4", "选项5", "选项6", "选项7", "选项8", "选项9", "选项10"]; width: 140 } }
                        ComponentCard { label: "style_primary"; ComboBox { style: Enums.comboBox.style_primary; model: ["Primary1", "Primary2"]; width: 140 } }
                        ComponentCard { label: "style_transparent"; ComboBox { style: Enums.comboBox.style_transparent; model: ["透明1", "透明2"]; width: 140 } }
                        ComponentCard { label: "feature_editable"; ComboBox { feature: Enums.comboBox.feature_editable; model: ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安", "重庆"]; placeholderText: "输入城市..."; width: 140 } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_multi"; ComboBox { type: Enums.comboBox.type_multi; model: ["多选1", "多选2", "多选3", "多选4", "多选5", "多选6", "多选7", "多选8", "多选9", "多选10", "多选11", "多选12", "多选13", "多选14", "多选15", "多选16", "多选17", "多选18", "多选19", "多选20", "多选21", "多选22", "多选23", "多选24", "多选25", "多选26", "多选27", "多选28", "多选29", "多选30"]; width: 180 } }
                        ComponentCard { 
                            label: "type_multi_tree"
                            ComboBoxMultiTree { 
                                width: 220
                                placeholderText: "请选择"
                                selectedPaths: [["华东地区", "江苏省", "南京市"], ["华东地区", "浙江省", "杭州市"]]
                                model: [
                                    {
                                        text: "华东地区",
                                        children: [
                                            { text: "上海市", children: [{ text: "黄浦区" }, { text: "浦东新区" }] },
                                            { text: "江苏省", children: [{ text: "南京市" }, { text: "苏州市" }] },
                                            { text: "浙江省", children: [{ text: "杭州市" }, { text: "宁波市" }, { text: "温州市" }] }
                                        ]
                                    },
                                    {
                                        text: "华南地区",
                                        children: [
                                            { text: "广东省", children: [{ text: "广州市" }, { text: "深圳市" }, { text: "珠海市" }] }
                                        ]
                                    }
                                ]
                            } 
                        }
                        ComponentCard { 
                            label: "type_tree"
                            ComboBox { 
                                type: Enums.comboBox.type_tree
                                width: 200
                                placeholderText: "请选择"
                                showPathFromRoot: false
                                model: [
                                    {
                                        text: "华东地区",
                                        children: [
                                            { text: "上海市", children: [{ text: "黄浦区" }, { text: "浦东新区" }, { text: "徐汇区" }] },
                                            { text: "江苏省", children: [{ text: "南京市" }, { text: "苏州市" }, { text: "无锡市" }] },
                                            { text: "浙江省", children: [{ text: "杭州市" }, { text: "宁波市" }, { text: "温州市" }, { text: "绍兴市" }, { text: "嘉兴市" }] }
                                        ]
                                    },
                                    {
                                        text: "华南地区",
                                        children: [
                                            { text: "广东省", children: [{ text: "广州市" }, { text: "深圳市" }, { text: "珠海市" }, { text: "佛山市" }, { text: "东莞市" }] }
                                        ]
                                    }
                                ]
                            } 
                        }
                        ComponentCard { label: "type_font"; ComboBox { type: Enums.comboBox.type_font; width: 160 } }
                    }
                }
            }
            
            
            // 数值输入
            ExampleCard {
                title: "数值输入"
                description: "SpinBox (type: normal / double / compact / compact_double)"
                Column {
                    spacing: Enums.spacing.l
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: "SpinBox"; SpinBox { value: 50 } }
                        ComponentCard { label: "SpinBox (double)"; SpinBox { type: Enums.input.spinbox_double; value: 2.84 } }
                    }
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: "SpinBox (compact)"; SpinBox { type: Enums.input.spinbox_compact; value: 10 } }
                        ComponentCard { label: "SpinBox (compact_double)"; SpinBox { type: Enums.input.spinbox_compact_double; value: 3.14 } }
                    }
                }
            }
            
            // Toggle 切换控件
            ExampleCard {
                title: "Toggle 切换控件"
                description: "Toggle (controlType: checkbox / radio / switch, type: default / indicator / subtitle)"
                Column {
                    spacing: Enums.spacing.l
                    
                    // CheckBox
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_checkbox"; Toggle { controlType: Enums.toggle.control_checkbox; text: "Toggle" } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_checkbox; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_checkbox; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: "说明文字" } }
                    }
                    
                    // RadioButton
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_radio"; Toggle { controlType: Enums.toggle.control_radio; text: "Toggle"; checked: true } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_radio; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_radio; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: "说明文字" } }
                    }
                    
                    // ToggleSwitch
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_switch"; Toggle { controlType: Enums.toggle.control_switch; text: "Toggle" } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_switch; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_switch; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: "说明文字" } }
                    }
                }
            }
            
            // 滑块
            ExampleCard {
                title: "滑块"
                description: "Slider"
                Column {
                    spacing: Enums.spacing.xl
                    ComponentCard { label: "type_default"; Slider { width: 300; value: 50 } }
                    ComponentCard { label: "type_range"; Slider { width: 300; type: Enums.slider.type_range } }
                }
            }
            
            // 日期时间选择器（统一组件）
            ExampleCard {
                title: "日期时间选择器"
                description: "DateTimePicker - 统一滚轮选择器，自动本地化"
                Column {
                    spacing: Enums.spacing.xl
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: "日期"; DateTimePicker { type: Enums.picker.type_date } }
                        ComponentCard { label: "时间"; DateTimePicker { type: Enums.picker.type_time } }
                        ComponentCard { label: "时间(秒)"; DateTimePicker { type: Enums.picker.type_time; timePrecision: Enums.picker.time_second } }
                    }
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: "12小时制"; DateTimePicker { type: Enums.picker.type_time; timeFormat: Enums.picker.format_12h } }
                        ComponentCard { label: "日期+时间"; DateTimePicker { type: Enums.picker.type_datetime } }
                    }
                }
            }
            
            // 日历选择器
            ExampleCard {
                title: "日历选择器"
                description: "CalendarPicker / CalendarPickerCore"
                Row {
                    spacing: Enums.spacing.xl
                    ComponentCard { label: "CalendarPicker"; CalendarPicker { } }
                    ComponentCard { label: "CalendarPicker (Range)"; CalendarPicker { type: Enums.calendarPicker.type_range } }
                    ComponentCard { label: "CalendarPickerCore"; CalendarPickerCore { } }
                }
            }
            
            // 特殊输入
            ExampleCard {
                title: "特殊输入"
                description: "PinInput / Rating"
                Row {
                    spacing: Enums.spacing.xxl
                    ComponentCard { label: "PinInput"; PinInput { length: 4 } }
                    ComponentCard { label: "Rating"; Rating { value: Enums.demoMetrics.ratingDefaultValue } }
                }
            }
            
            // 图片相关
            ExampleCard {
                title: "图片"
                description: "BeforeAfterSlider / ImageCropper (Dialog / Overlay)"
                Row {
                    spacing: Enums.spacing.xl
                    ComponentCard { label: "BeforeAfterSlider"; BeforeAfterSlider { width: 200; height: 120; leftImage: "qrc:/image/horizontal/1.jpg"; rightImage: "qrc:/image/horizontal/2.jpg" } }
                    ComponentCard { label: "ImageCropper (Dialog)"; ImageCropper { type: Enums.imageCropper.type_dialog; width: 120; height: 80 } }
                    ComponentCard { label: "ImageCropper (Overlay)"; ImageCropper { type: Enums.imageCropper.type_overlay; width: 120; height: 80 } }
                }
            }
            
            // 过滤器
            ExampleCard {
                title: "过滤器"
                description: "FilterBar (text / icon / icon+text)"
                Column {
                    spacing: Enums.spacing.xl
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: "纯文本"; 
                            font.pixelSize: Enums.typography.body; 
                            font.family: Enums.fontFamily
                            color: Enums.textColor.primary
                            width: 80
                            topPadding: Enums.spacing.s
                        }
                        FilterBar { items: ["All", "Apps", "Document", "Web", "People", "IMG"]; currentIndex: 2 }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: "纯图标"; 
                            font.pixelSize: Enums.typography.body; 
                            font.family: Enums.fontFamily
                            color: Enums.textColor.primary
                            width: 80
                            topPadding: Enums.spacing.s
                        }
                        FilterBar { items: ["Home", "Apps", "Document", "Globe", "People", "Image"]; currentIndex: 0 }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: "图标+文本"; 
                            font.pixelSize: Enums.typography.body; 
                            font.family: Enums.fontFamily
                            color: Enums.textColor.primary
                            width: 80
                            topPadding: Enums.spacing.s
                        }
                        FilterBar {
                            items: [
                                { icon: "Home", text: "首页" },
                                { icon: "Apps", text: "应用" },
                                { icon: "Document", text: "文档" },
                                { icon: "Globe", text: "网页" }
                            ]
                            currentIndex: 1
                        }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: "多选混搭"; 
                            font.pixelSize: Enums.typography.body; 
                            font.family: Enums.fontFamily
                            color: Enums.textColor.primary
                            width: 80
                            topPadding: Enums.spacing.s
                        }
                        FilterBar {
                            exclusive: false
                            items: [
                                "All",
                                { icon: "Image", text: "图片" },
                                { icon: "Video", text: "视频" },
                                { icon: "MusicNote1", text: "音乐" }
                            ]
                            selectedIndices: [0, 1]
                        }
                    }
                }
            }
            
            // 平滑滚动条
            ExampleCard {
                title: "平滑滚动条"
                description: "ScrollBar (垂直/水平)"
                Row {
                    spacing: Enums.spacing.xxxl
                    
                    // 垂直滚动条 - 带实际内容
                    ComponentCard {
                        label: "垂直"
                        Rectangle {
                            width: 150
                            height: 100
                            color: Enums.stateColor.bgMedium
                            radius: Enums.radius.small
                            clip: true
                            
                            Flickable {
                                id: vFlickable
                                anchors.fill: parent
                                anchors.rightMargin: Enums.demoMetrics.scrollBarMargin
                                contentHeight: vContent.height
                                clip: true
                                
                                Column {
                                    id: vContent
                                    width: parent.width
                                    spacing: Enums.spacing.xs
                                    Repeater {
                                        model: 15
                                        Text { 
                                            text: "Item " + (index + 1)
                                            color: Enums.textColor.primary
                                            font.pixelSize: Enums.typography.caption
                                            leftPadding: 8
                                        }
                                    }
                                }
                            }
                            
                            ScrollBarEntry {
                                flickable: vFlickable
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: Enums.demoMetrics.scrollBarThickness
                            }
                        }
                    }
                    
                    // 水平滚动条
                    ComponentCard {
                        label: "水平"
                        Rectangle {
                            width: 150
                            height: 80
                            color: Enums.stateColor.bgMedium
                            radius: Enums.radius.small
                            clip: true
                            
                            ScrollArea {
                                id: hScrollArea
                                anchors.fill: parent
                                orientation: Qt.Horizontal
                                
                                Row {
                                    id: hContent
                                    spacing: Enums.spacing.m
                                    Repeater {
                                        model: 10
                                        Rectangle {
                                            width: 50
                                            height: 40
                                            radius: Enums.radius.small
                                            color: Enums.accentColor
                                            Text {
                                                anchors.centerIn: parent
                                                text: index + 1
                                                color: Enums.accentForeground
                                                font.bold: true
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            
            // 颜色选择器
            ExampleCard {
                title: "颜色选择器"
                description: "ColorPicker (type: picker/palette/circle/screen/dialog)"
                Column {
                    spacing: Enums.spacing.m
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_picker"; ColorPicker { type: Enums.colorPicker.type_picker } }
                        ComponentCard { label: "type_palette"; ColorPicker { type: Enums.colorPicker.type_palette } }
                        ComponentCard { 
                            label: "ColorDialog"
                            Button { 
                                text: "打开颜色对话框"
                                onClicked: colorDialog.open()
                            }
                        }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_circle"; ColorPicker { type: Enums.colorPicker.type_circle } }
                        ComponentCard { label: "type_screen"; ColorPicker { type: Enums.colorPicker.type_screen } }
                    }
                }
            }
            
            // 快捷键选择器
            ExampleCard {
                title: "快捷键选择器"
                description: "ShortcutEditor (allowSingleKey: 单键录入 / 组合键录入)"
                Row {
                    spacing: Enums.spacing.l
                    ComponentCard {
                        label: "组合键 (默认)"
                        ShortcutEditor { width: 200; shortcut: "Ctrl+S" }
                    }
                    ComponentCard {
                        label: "允许单键 allowSingleKey"
                        ShortcutEditor { width: 200; allowSingleKey: true }
                    }
                }
            }
            
        }
    }
    
    // ColorDialog instance 颜色对话框实例
    // overlayTarget设置为scrollArea，覆盖页面内容区域而非整个窗口
    ColorPickerDialog {
        id: colorDialog
        title: "选择背景颜色"
        selectedColor: Enums.accentColor
        overlayTarget: scrollArea  // 覆盖ScrollArea
        onColorAccepted: (c) => console.log("选择的颜色:", c)
    }
}
