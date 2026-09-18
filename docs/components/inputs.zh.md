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

```qml
import PrismQML as Fluent
Fluent.ComboBoxDefault { model: ["选项一", "选项二", "选项三"] }
```

## Slider 滑块

```qml
import PrismQML as Fluent
Fluent.Slider { value: 60; from: 0; to: 100 }
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

三态值统一通过 `Enums.toggle` 访问：`state_unchecked`、`state_partially_checked`、`state_checked`。`checked` 与 `checkState` 双向同步；部分勾选态对应 `checked: false`。

```qml
Fluent.CheckBox {
    text: "部分选择"
    tristate: true
    checkState: Fluent.Enums.toggle.state_partially_checked
}
```

## SpinBox 数字步进

```qml
import PrismQML as Fluent

Fluent.SpinBox {
    minimum: 0
    maximum: 100
    value: 42
}
```

`type` 选择变体：`Enums.input.spinbox_normal`、`spinbox_double`、`spinbox_compact`、`spinbox_compact_double`；`prefix` / `suffix` 提供文本单位。

单位也可以直接是图标：`prefixIcon` / `suffixIcon` 接受 Fluent 图标名、emoji 或图片路径（svg/png/qrc/file），紧贴数值两侧显示，`iconSize` 控制尺寸（默认 `Enums.iconSize.s`）。图标默认用控件文字色着色；彩色原图请设 `iconThemeAware: false` 保留原色。

```qml
Fluent.SpinBox {
    value: 42
    prefixIcon: Fluent.Enums.icon.wallet
    suffixIcon: "qrc:/app/images/gold_brick.svg"
    iconThemeAware: false
}
```

## 其他

- `SpinBox` — 数字步进
- `PinInput` — 验证码/PIN 分格输入
- `BeforeAfterSlider` — 图片对比滑块

## 皮肤适配

新粗野下：输入框白底黑粗边，**聚焦时边框 + 硬阴影转橙**；复选框/单选/开关为黑粗边 + 橙选中态。
