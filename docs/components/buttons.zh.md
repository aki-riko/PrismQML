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

## 样式 style（8 种）

| 值 | 说明 |
|----|------|
| `style_default` | 默认（白底/描边） |
| `style_primary` | 主色填充（自动用主题色；neo 下为橙） |
| `style_transparent` | 透明 |
| `style_filled` | 状态色填充（按 `level` 取成功/危险等） |
| `style_text` | 纯文字 |
| `style_hyperlink` | 超链接 |
| `style_gradient` | 渐变 |
| `style_glow` | 泛光（主色面 + 柔和外圈光晕，带呼吸） |

### 泛光按钮 `style_glow`

泛光沿用 `style_primary` 的主色面、墨色与按压处理，只在外圈额外绘制一层柔和光晕：

```qml
Fluent.Button {
    text: "开始"
    style: Fluent.Enums.button.style_glow
}
```

- 光晕由单个 `RectangularShadow` 绘制。Qt 6.9+ 用有符号距离场渲染且**无离屏图层**，这是 `AGENTS.md` 6.2 规定的矩形表面首选方案，也是真实显示器上唯一真正平滑的衰减；叠加半透明矩形的方案会在真实屏幕上出现可见色带。
- 光晕尺寸按**按钮高度的比例**而不是固定像素：`glowBlurRatio` 0.45、`glowSpreadRatio` 0.10。固定尺寸会在小按钮上显得过大、在大按钮上显得过小；实测该比例下贴边着色约 46/255，读作柔和描边而不是色团。
- 泛光惰性创建：只有 `style_glow` 会实例化光晕层，其余样式保持原有对象数与像素。
- 光晕色跟随已解析的按钮面（而不是原始主色），因此禁用态是灰面配灰光晕，不会出现灰面配蓝光晕。
- 呼吸只调制阴影色的 alpha，几何保持不变，不会触发按钮面重新布局；禁用、加载、倒计时、减少动态效果与窗口隐藏时停止呼吸。
- 票据皮肤按设计零悬浮，泛光在那里收敛为纯主色面。
- 真实泛光只能在 D3D11 上判定：`offscreen` 的 Software 场景图不执行着色器效果。验收请跑 `scripts/manual/glow_button_bloom_probe.py`。

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
