# 按钮

统一的 `Button` 控件，按内容自动识别类型（仅图标→工具按钮，图标+文字/纯文字→普通按钮），通过 `style` / `shape` / `feature` 三个正交维度组合。

## 基本用法

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "确定"
    style: Fluent.Enums.button.style_primary
    onClicked: console.log("clicked")
}
```

## 样式 style（7 种）

| 值 | 说明 |
|----|------|
| `style_default` | 默认（白底/描边） |
| `style_primary` | 主色填充（自动用主题色；neo 下为橙） |
| `style_transparent` | 透明 |
| `style_filled` | 状态色填充（按 `level` 取成功/危险等） |
| `style_text` | 纯文字 |
| `style_hyperlink` | 超链接 |
| `style_gradient` | 渐变 |

## 形状 shape

| 值 | 说明 |
|----|------|
| `shape_default` | 默认圆角（neo 下小圆角） |
| `shape_pill` | 药丸（全圆角） |

## 功能 feature（9 种）

进度条 / 进度环 / 不定态 / 开关（toggle）/ 下拉（dropdown）/ split / 倒计时等：

```qml
Fluent.Button {
    text: "下载"
    feature: Fluent.Enums.button.feature_progress_bar
}
```

`feature_none` · `feature_progress_bar` · `feature_progress_ring` · `feature_indeterminate_bar` · `feature_indeterminate_ring` · `feature_toggle` · `feature_dropdown` · `feature_split` · `feature_countdown`

## 皮肤适配

- **Fluent**：圆角 + 模糊阴影，hover 半透明叠加
- **新粗野**：粗黑边 + 硬阴影，按下时"压平"硬阴影；primary 橙、filled 用高饱和语义色（绿/红/琥珀）

切换皮肤无需改动按钮代码——`style_primary` 的填充色随 `accentColor` 自动变。
