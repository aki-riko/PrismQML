# 输入

文本输入、选择、开关等表单控件。

## LineEdit 输入框

```qml
import PrismQML as Fluent

Fluent.LineEdit {
    placeholderText: "请输入"
    width: 240
}
```

支持清除按钮、密码模式、标签（LineEditLabel）、标签输入（TagLineEdit）等变体。

## ComboBox 下拉框

!!! warning "导入方式"
    `ComboBox` 与 QtQuick 同名，需子模块导入：
    ```qml
    import "../prismqml/PrismQML/controls/inputs/ComboBox"
    ComboBoxDefault { model: ["选项一", "选项二", "选项三"] }
    ```

## Slider 滑块

```qml
import "../prismqml/PrismQML/controls/inputs/Slider"
SliderCore { value: 60; from: 0; to: 100 }
```

## 勾选类

- `CheckBox` — 复选框（支持三态）
- `RadioButton` — 单选
- `ToggleSwitch` — 开关

```qml
Fluent.CheckBox { text: "记住我"; checked: true }
Fluent.RadioButton { text: "选项 A" }
Fluent.ToggleSwitch { text: "启用"; checked: true }
```

## 其他

- `SpinBox` — 数字步进
- `PinInput` — 验证码/PIN 分格输入
- `BeforeAfterSlider` — 图片对比滑块

## 皮肤适配

新粗野下：输入框白底黑粗边，**聚焦时边框 + 硬阴影转橙**；复选框/单选/开关为黑粗边 + 橙选中态。
