// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 输入组件展示页面
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
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
                Text { text: Fluent.Translator.tr("gallery_85b015684ed1a12c", Fluent.Translator._v); font.pixelSize: Enums.typography.displayLarge; font.bold: true; color: Enums.textColor.primary; font.family: Enums.fontFamily }
                Text { text: "prismqml.controls.inputs"; font.pixelSize: Enums.typography.caption; color: Enums.textColor.secondary; font.family: Enums.fontFamily }
            }
            
            // 文本输入
            ExampleCard {
                title: Fluent.Translator.tr("gallery_5420b6d872e828b9", Fluent.Translator._v)
                description: "LineEdit / TextEdit"
                Column {
                    spacing: Enums.spacing.l
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_normal"; LineEdit { placeholderText: "LineEdit"; width: 180 } }
                        ComponentCard { label: "type_password"; LineEdit { inputType: Enums.input.type_password; placeholderText: Fluent.Translator.tr("gallery_a621ab606db2a11f", Fluent.Translator._v); width: 180 } }
                        ComponentCard { label: "type_search"; LineEdit { inputType: Enums.input.type_search; placeholderText: Fluent.Translator.tr("gallery_44ce7ae909bbb28b", Fluent.Translator._v); width: 180 } }
                        ComponentCard { label: "collapsible"; LineEdit { inputType: Enums.input.type_search; collapsible: true; placeholderText: Fluent.Translator.tr("gallery_44ce7ae909bbb28b", Fluent.Translator._v); expandedWidth: 200 } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_label"; LineEdit { inputType: Enums.input.type_label; label: Fluent.Translator.tr("gallery_1a3f0617d6de8e52", Fluent.Translator._v); width: 200 } }
                        ComponentCard { label: "type_tag"; LineEdit { inputType: Enums.input.type_tag; placeholderText: Fluent.Translator.tr("gallery_01e6fe14b3dc3cf4", Fluent.Translator._v); width: 280; maxTags: 5; suggestions: [Fluent.Translator.tr("gallery_6aa8f49cc992dfd7", Fluent.Translator._v), Fluent.Translator.tr("gallery_cb647750b60eb6e9", Fluent.Translator._v), Fluent.Translator.tr("gallery_4c91d67075d07d9f", Fluent.Translator._v), Fluent.Translator.tr("gallery_0f722881d96fd668", Fluent.Translator._v), Fluent.Translator.tr("gallery_6c273ecc79d229ed", Fluent.Translator._v), Fluent.Translator.tr("gallery_8d7f8612a58f664d", Fluent.Translator._v)] } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        // 差异化能力: 校验回调(长度≥2才接受) + 逗号/分号粘贴拆分
                        ComponentCard {
                            label: "tag_validate"
                            LineEdit {
                                inputType: Enums.input.type_tag
                                placeholderText: Fluent.Translator.tr("gallery_555623c1af9dccfd", Fluent.Translator._v)
                                width: 280
                                extraSeparators: [",", ";"]
                                validateTag: (t) => t.length >= 2
                            }
                        }
                        // Per-tag outline colors 按标签设置描边颜色
                        ComponentCard {
                            label: "tag_colors"
                            LineEdit {
                                inputType: Enums.input.type_tag
                                placeholderText: Fluent.Translator.tr("gallery_df30a51e65e7062e", Fluent.Translator._v)
                                width: 280
                                tags: [Fluent.Translator.tr("gallery_0efa477b24b1f3c7", Fluent.Translator._v), Fluent.Translator.tr("gallery_de907d10df98b498", Fluent.Translator._v), Fluent.Translator.tr("gallery_c0b3fbff51ccc40b", Fluent.Translator._v)]
                                tagColors: ({
                                    Fluent.Translator.tr("gallery_0efa477b24b1f3c7", Fluent.Translator._v): Enums.chartColors.palette[3],
                                    Fluent.Translator.tr("gallery_de907d10df98b498", Fluent.Translator._v): Enums.chartColors.palette[0],
                                    Fluent.Translator.tr("gallery_c0b3fbff51ccc40b", Fluent.Translator._v): Enums.chartColors.palette[1]
                                })
                            }
                        }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "multiline_plain"; TextEdit { multilineType: Enums.input.multiline_plain; placeholderText: "PlainTextEdit"; width: 200; height: 60 } }
                        ComponentCard { label: "multiline_browser"; TextEdit { multilineType: Enums.input.multiline_browser; width: 200; height: 60; text: Fluent.Translator.tr("gallery_b97be57c7ccdf579", Fluent.Translator._v) } }
                    }
                }
            }
            
            // 下拉选择
            ExampleCard {
                title: Fluent.Translator.tr("gallery_095b751a68e708b2", Fluent.Translator._v)
                description: "ComboBox - type/style/feature"
                Column {
                    spacing: Enums.spacing.l
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); ComboBox { model: [Fluent.Translator.tr("gallery_96198518dab609f0", Fluent.Translator._v), Fluent.Translator.tr("gallery_5f04a01fe105bb4d", Fluent.Translator._v), Fluent.Translator.tr("gallery_74b97119bee5c66d", Fluent.Translator._v), Fluent.Translator.tr("gallery_400823a3d4340d25", Fluent.Translator._v), Fluent.Translator.tr("gallery_3b13a36cf3789cb7", Fluent.Translator._v), Fluent.Translator.tr("gallery_a827ea9a6cf89c08", Fluent.Translator._v), Fluent.Translator.tr("gallery_c16eb8a24ffc6ce9", Fluent.Translator._v), Fluent.Translator.tr("gallery_7ddc74635d0d5e24", Fluent.Translator._v), Fluent.Translator.tr("gallery_5a4c64fc826dfedf", Fluent.Translator._v), Fluent.Translator.tr("gallery_7881ad1b2622aae3", Fluent.Translator._v)]; width: 140 } }
                        ComponentCard { label: "style_primary"; ComboBox { style: Enums.comboBox.style_primary; model: ["Primary1", "Primary2"]; width: 140 } }
                        ComponentCard { label: "style_transparent"; ComboBox { style: Enums.comboBox.style_transparent; model: [Fluent.Translator.tr("gallery_d8efa593c9afae84", Fluent.Translator._v), Fluent.Translator.tr("gallery_c224e980b5cd88f2", Fluent.Translator._v)]; width: 140 } }
                        ComponentCard { label: "feature_editable"; ComboBox { feature: Enums.comboBox.feature_editable; model: [Fluent.Translator.tr("gallery_68c77e155132565e", Fluent.Translator._v), Fluent.Translator.tr("gallery_4906a49adc5c472b", Fluent.Translator._v), Fluent.Translator.tr("gallery_85da183b0683e5f7", Fluent.Translator._v), Fluent.Translator.tr("gallery_1bb5e3986433569c", Fluent.Translator._v), Fluent.Translator.tr("gallery_a8027f71a8e38bcb", Fluent.Translator._v), Fluent.Translator.tr("gallery_c690fe6240419c66", Fluent.Translator._v), Fluent.Translator.tr("gallery_d222587118255cbd", Fluent.Translator._v), Fluent.Translator.tr("gallery_48afd8d3b9269706", Fluent.Translator._v), Fluent.Translator.tr("gallery_e2d11378ac1898de", Fluent.Translator._v), Fluent.Translator.tr("gallery_ea31f4d6d27dd76d", Fluent.Translator._v)]; placeholderText: Fluent.Translator.tr("gallery_854f96221f84c69e", Fluent.Translator._v); width: 140 } }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        ComponentCard { label: "type_multi"; ComboBox { type: Enums.comboBox.type_multi; model: [Fluent.Translator.tr("gallery_f14e92b3ca94f9b1", Fluent.Translator._v), Fluent.Translator.tr("gallery_4b52fe9ca014ce17", Fluent.Translator._v), Fluent.Translator.tr("gallery_cbd3f762ab062eaf", Fluent.Translator._v), Fluent.Translator.tr("gallery_479d2d25532faf4f", Fluent.Translator._v), Fluent.Translator.tr("gallery_eca7d57c116f0045", Fluent.Translator._v), Fluent.Translator.tr("gallery_370e2a15bf17a364", Fluent.Translator._v), Fluent.Translator.tr("gallery_d4ed5df31880da18", Fluent.Translator._v), Fluent.Translator.tr("gallery_c7be748e4d27bdaf", Fluent.Translator._v), Fluent.Translator.tr("gallery_30f06e50bbd7be40", Fluent.Translator._v), Fluent.Translator.tr("gallery_28b8848421d707c2", Fluent.Translator._v), Fluent.Translator.tr("gallery_1c610efe7eaf2a2b", Fluent.Translator._v), Fluent.Translator.tr("gallery_2e51176514bb2ea3", Fluent.Translator._v), Fluent.Translator.tr("gallery_4819555b3d58110d", Fluent.Translator._v), Fluent.Translator.tr("gallery_74ebc830dbb4e309", Fluent.Translator._v), Fluent.Translator.tr("gallery_3ecdfaee94f24576", Fluent.Translator._v), Fluent.Translator.tr("gallery_b8e811e24395dc25", Fluent.Translator._v), Fluent.Translator.tr("gallery_40efddaf0ee898b9", Fluent.Translator._v), Fluent.Translator.tr("gallery_c06d62700d71e22e", Fluent.Translator._v), Fluent.Translator.tr("gallery_c87ddad2c91b256f", Fluent.Translator._v), Fluent.Translator.tr("gallery_798c85e0b474bf74", Fluent.Translator._v), Fluent.Translator.tr("gallery_1784ebb55ffa5b65", Fluent.Translator._v), Fluent.Translator.tr("gallery_6f7a3be34579b316", Fluent.Translator._v), Fluent.Translator.tr("gallery_be5b212d0ab9a9eb", Fluent.Translator._v), Fluent.Translator.tr("gallery_e49752e2be94493f", Fluent.Translator._v), Fluent.Translator.tr("gallery_2648657b4d98050e", Fluent.Translator._v), Fluent.Translator.tr("gallery_905b6866f5175b1a", Fluent.Translator._v), Fluent.Translator.tr("gallery_3717a12e06b9d4d7", Fluent.Translator._v), Fluent.Translator.tr("gallery_196f9bae9c07e8af", Fluent.Translator._v), Fluent.Translator.tr("gallery_795502c9f30ef515", Fluent.Translator._v), Fluent.Translator.tr("gallery_cda276fb07fc6f86", Fluent.Translator._v)]; width: 180 } }
                        ComponentCard { 
                            label: "type_multi_tree"
                            ComboBoxMultiTree { 
                                width: 220
                                placeholderText: Fluent.Translator.tr("gallery_da590a8fe3ce4de0", Fluent.Translator._v)
                                selectedPaths: [[Fluent.Translator.tr("gallery_780e5b757b2d7a5b", Fluent.Translator._v), Fluent.Translator.tr("gallery_ac7240a660d14397", Fluent.Translator._v), Fluent.Translator.tr("gallery_93413130d8fdae07", Fluent.Translator._v)], [Fluent.Translator.tr("gallery_780e5b757b2d7a5b", Fluent.Translator._v), Fluent.Translator.tr("gallery_5395aa56194876b9", Fluent.Translator._v), Fluent.Translator.tr("gallery_38150fb2d76a683e", Fluent.Translator._v)]]
                                model: [
                                    {
                                        text: Fluent.Translator.tr("gallery_780e5b757b2d7a5b", Fluent.Translator._v),
                                        children: [
                                            { text: Fluent.Translator.tr("gallery_2e9414cac2cae506", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_88bf5f4eea8d83fb", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_e7ce130eda090dc3", Fluent.Translator._v) }] },
                                            { text: Fluent.Translator.tr("gallery_ac7240a660d14397", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_93413130d8fdae07", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_6cf593f0fccdae21", Fluent.Translator._v) }] },
                                            { text: Fluent.Translator.tr("gallery_5395aa56194876b9", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_38150fb2d76a683e", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_3b79e1953b16287e", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_23e2e8acf2e9eead", Fluent.Translator._v) }] }
                                        ]
                                    },
                                    {
                                        text: Fluent.Translator.tr("gallery_5715f626316ce566", Fluent.Translator._v),
                                        children: [
                                            { text: Fluent.Translator.tr("gallery_ee410024807c0467", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_892d3dbc5120a794", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_70ac7d972dc46eaf", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_9d050b910649e5ae", Fluent.Translator._v) }] }
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
                                placeholderText: Fluent.Translator.tr("gallery_da590a8fe3ce4de0", Fluent.Translator._v)
                                showPathFromRoot: false
                                model: [
                                    {
                                        text: Fluent.Translator.tr("gallery_780e5b757b2d7a5b", Fluent.Translator._v),
                                        children: [
                                            { text: Fluent.Translator.tr("gallery_2e9414cac2cae506", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_88bf5f4eea8d83fb", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_e7ce130eda090dc3", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_f8900163cf9f19bc", Fluent.Translator._v) }] },
                                            { text: Fluent.Translator.tr("gallery_ac7240a660d14397", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_93413130d8fdae07", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_6cf593f0fccdae21", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_fe86bd150a840d95", Fluent.Translator._v) }] },
                                            { text: Fluent.Translator.tr("gallery_5395aa56194876b9", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_38150fb2d76a683e", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_3b79e1953b16287e", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_23e2e8acf2e9eead", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_a68ef6ab683bf681", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_351267ac91b3d871", Fluent.Translator._v) }] }
                                        ]
                                    },
                                    {
                                        text: Fluent.Translator.tr("gallery_5715f626316ce566", Fluent.Translator._v),
                                        children: [
                                            { text: Fluent.Translator.tr("gallery_ee410024807c0467", Fluent.Translator._v), children: [{ text: Fluent.Translator.tr("gallery_892d3dbc5120a794", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_70ac7d972dc46eaf", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_9d050b910649e5ae", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_34f32ac09a7f85b5", Fluent.Translator._v) }, { text: Fluent.Translator.tr("gallery_b90341e24a5fa6f7", Fluent.Translator._v) }] }
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
                title: Fluent.Translator.tr("gallery_cde4729fd9104c52", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_9aa66d632584eebb", Fluent.Translator._v)
                description: "Toggle (controlType: checkbox / radio / switch, type: default / indicator / subtitle)"
                Column {
                    spacing: Enums.spacing.l
                    
                    // CheckBox
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_checkbox"; Toggle { controlType: Enums.toggle.control_checkbox; text: "Toggle" } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_checkbox; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_checkbox; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: Fluent.Translator.tr("gallery_a75800abd20b81bd", Fluent.Translator._v) } }
                    }
                    
                    // RadioButton
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_radio"; Toggle { controlType: Enums.toggle.control_radio; text: "Toggle"; checked: true } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_radio; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_radio; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: Fluent.Translator.tr("gallery_a75800abd20b81bd", Fluent.Translator._v) } }
                    }
                    
                    // ToggleSwitch
                    Row {
                        spacing: Enums.spacing.xxl
                        ComponentCard { label: "control_switch"; Toggle { controlType: Enums.toggle.control_switch; text: "Toggle" } }
                        ComponentCard { label: "type_indicator"; Toggle { controlType: Enums.toggle.control_switch; type: Enums.toggle.type_indicator } }
                        ComponentCard { label: "type_subtitle"; Toggle { controlType: Enums.toggle.control_switch; type: Enums.toggle.type_subtitle; text: "Toggle"; subtitle: Fluent.Translator.tr("gallery_a75800abd20b81bd", Fluent.Translator._v) } }
                    }
                }
            }
            
            // 滑块
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a7c3e94cbb35a809", Fluent.Translator._v)
                description: "Slider"
                Column {
                    spacing: Enums.spacing.xl
                    ComponentCard { label: "type_default"; Slider { width: 300; value: 50 } }
                    ComponentCard { label: "type_range"; Slider { width: 300; type: Enums.slider.type_range } }
                }
            }
            
            // 日期时间选择器（统一组件）
            ExampleCard {
                title: Fluent.Translator.tr("gallery_b087092ffece72c8", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_a3845a3dee776402", Fluent.Translator._v)
                Column {
                    spacing: Enums.spacing.xl
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: Fluent.Translator.tr("gallery_70d0c1b33626ba4b", Fluent.Translator._v); DateTimePicker { type: Enums.picker.type_date } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_8b6ff498515bcc2f", Fluent.Translator._v); DateTimePicker { type: Enums.picker.type_time } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_bb901de8fdfa0a09", Fluent.Translator._v); DateTimePicker { type: Enums.picker.type_time; timePrecision: Enums.picker.time_second } }
                    }
                    Row {
                        spacing: Enums.spacing.xl
                        ComponentCard { label: Fluent.Translator.tr("gallery_a57f56726b3b5c0d", Fluent.Translator._v); DateTimePicker { type: Enums.picker.type_time; timeFormat: Enums.picker.format_12h } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_c3a9540159f53ded", Fluent.Translator._v); DateTimePicker { type: Enums.picker.type_datetime } }
                    }
                }
            }
            
            // 日历选择器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1e2f7daf79570e9c", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_3b1c70eca9718194", Fluent.Translator._v)
                description: "PinInput / Rating"
                Row {
                    spacing: Enums.spacing.xxl
                    ComponentCard { label: "PinInput"; PinInput { length: 4 } }
                    ComponentCard { label: "Rating"; Rating { value: Enums.demoMetrics.ratingDefaultValue } }
                }
            }
            
            // 图片相关
            ExampleCard {
                title: Fluent.Translator.tr("gallery_d24c10d37db0feea", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_4aaccba26873ebc2", Fluent.Translator._v)
                description: "FilterBar (text / icon / icon+text)"
                Column {
                    spacing: Enums.spacing.xl
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: Fluent.Translator.tr("gallery_f9124b40e8ccbeab", Fluent.Translator._v);
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
                            text: Fluent.Translator.tr("gallery_9232c621254bb0d8", Fluent.Translator._v);
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
                            text: Fluent.Translator.tr("gallery_8813a2458fd4724c", Fluent.Translator._v);
                            font.pixelSize: Enums.typography.body; 
                            font.family: Enums.fontFamily
                            color: Enums.textColor.primary
                            width: 80
                            topPadding: Enums.spacing.s
                        }
                        FilterBar {
                            items: [
                                { icon: "Home", text: Fluent.Translator.tr("gallery_203c08e0d44ac375", Fluent.Translator._v) },
                                { icon: "Apps", text: Fluent.Translator.tr("gallery_63c73c4730f4473e", Fluent.Translator._v) },
                                { icon: "Document", text: Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v) },
                                { icon: "Globe", text: Fluent.Translator.tr("gallery_005074b65962188c", Fluent.Translator._v) }
                            ]
                            currentIndex: 1
                        }
                    }
                    Row {
                        spacing: Enums.spacing.l
                        Text { 
                            text: Fluent.Translator.tr("gallery_0b03d8a35cda2f98", Fluent.Translator._v);
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
                                { icon: "Image", text: Fluent.Translator.tr("gallery_d24c10d37db0feea", Fluent.Translator._v) },
                                { icon: "Video", text: Fluent.Translator.tr("gallery_c20f7618d330a854", Fluent.Translator._v) },
                                { icon: "MusicNote1", text: Fluent.Translator.tr("gallery_db95142124934467", Fluent.Translator._v) }
                            ]
                            selectedIndices: [0, 1]
                        }
                    }
                }
            }
            
            // 平滑滚动条
            ExampleCard {
                title: Fluent.Translator.tr("gallery_dd5e3983be8e0f6e", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_b233049163c5e4c2", Fluent.Translator._v)
                Row {
                    spacing: Enums.spacing.xxxl
                    
                    // 垂直滚动条 - 带实际内容
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_1777a1e5f3a54dee", Fluent.Translator._v)
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
                        label: Fluent.Translator.tr("gallery_4995b90d72fc59f9", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_6b4298bb407fc598", Fluent.Translator._v)
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
                                text: Fluent.Translator.tr("gallery_b499c14cb63cd338", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_da0b8919b7ad7da3", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_6d9b62998a127d13", Fluent.Translator._v)
                Row {
                    spacing: Enums.spacing.l
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_491968b6105dd32f", Fluent.Translator._v)
                        ShortcutEditor { width: 200; shortcut: "Ctrl+S" }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_00e9d95ae98ff2bc", Fluent.Translator._v)
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
        title: Fluent.Translator.tr("gallery_53c8bd2fe9d60274", Fluent.Translator._v)
        selectedColor: Enums.accentColor
        overlayTarget: scrollArea  // 覆盖ScrollArea
        onColorAccepted: (c) => console.log(Fluent.Translator.tr("gallery_c80b23dc43aefe9f", Fluent.Translator._v), c)
    }
}
