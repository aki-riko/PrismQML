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

## 统一菜单入口

`feature_dropdown` 和 `feature_split` 都可以直接绑定 `PopupWindowCore` 契约的菜单对象（例如 `MenuCore`）。按钮会负责预热、定位、开关和箭头状态；`menuItems` 仍可用于简单菜单。

```qml
Fluent.MenuCore {
    id: actionMenu
    Fluent.Action { text: "打开" }
    Fluent.Action { text: "导出" }
}

Fluent.Button {
    text: "操作"
    feature: Fluent.Enums.button.feature_split
    menu: actionMenu
    onClicked: console.log("主按钮点击")
}
```

外部菜单需要提供 `isOpen`、`prewarm()`、`openAtControl(control)` 和 `close()`；不满足契约时会输出明确警告。

## 样式 style（7 种）

| 值 | 说明 |
|----|------|
| style_default | 默认（白底/描边） |
| style_primary | 主色填充（自动用主题色；neo 下为橙） |
| style_transparent | 透明 |
| style_filled | 状态色填充（按 level 取成功/危险等） |
| style_text | 纯文字 |
| style_hyperlink | 超链接 |
| style_gradient | 渐变 |

## 泛光 glow（正交维度）

泛光**不是**一种样式，而是与 style / shape / eature 并列的独立轴，可与任意组合叠加：

`qml
// 主色按钮 + 泛光
Fluent.Button {
    text: "开始"
    style: Fluent.Enums.button.style_primary
    glow: Fluent.Enums.glow.glow_accent
}

// 也可以叠在任何其它样式或功能上
Fluent.Button {
    text: "删除"
    style: Fluent.Enums.button.style_filled
    level: 3
    glow: Fluent.Enums.glow.glow_accent
}
`

| 值 | 说明 |
|----|------|
| glow_none | 无泛光（默认） |
| glow_accent | 跟随按钮面颜色的泛光 |

- 光晕取**当前样式已解析出的面色相**：主色按钮泛蓝、成功后填充泛绿、中性默认按钮泛浅灰，因此与所有填充样式都能协调组合。
- 由单个 RectangularShadow 绘制。Qt 6.9+ 用有符号距离场渲染且**无离屏图层**，这是 AGENTS.md 6.2 规定的矩形表面首选方案，也是真实显示器上唯一真正平滑的衰减。
- 尺寸按**按钮高度比例**（lurRatio 0.45 / spreadRatio 0.10），在 32~60px 按钮上观感一致。
- 惰性创建：只有 glow_accent 才实例化光晕层，其余按钮保持原有对象数与像素。
- 呼吸只调制阴影色 alpha，几何不变；禁用、加载、倒计时、减少动态效果与窗口隐藏时停止。
- 无填充的扁平样式（style_transparent / style_text / style_hyperlink）没有可衬托光晕的面，因此不绘制。
- 票据皮肤按设计零悬浮，泛光在那里不创建。
- 真实泛光只能在 D3D11 上判定：offscreen 的 Software 场景图不执行着色器效果；验收跑 scripts/manual/glow_button_bloom_probe.py。

### 泛光是通用效果

泛光本体是 ffects/GlowHalo（枚举 Enums.glow），任何矩形控件都能直接用，不必是按钮：

`qml
Rectangle {
    id: card
    width: 180; height: 90
    radius: Enums.radius.large
    color: Enums.accentColor

    GlowHalo {
        target: card
        haloColor: card.color
    }
}
`

GlowHalo 只要求一个矩形 	arget，并接受 haloColor（由使用者提供，因为只有使用者知道自己画了什么表面）。按钮通过 ButtonGlow 适配层把按钮状态（指针态、倒计时、皮肤策略、减少动态效果）绑定上去。

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
