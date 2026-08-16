# 皮肤系统

皮肤系统让同一套 PrismQML 控件在 Fluent、新粗野、复古票据与新拟态四种
设计语言之间切换。

## 皮肤与主题正交

PrismQML 把设计语言和明暗拆成两个独立维度：

| 维度 | 控制 | 取值 |
|------|------|------|
| **skin**（皮肤） | 设计语言 | `fluent` / `neobrutalism` / `vintage_ticket` / `neumorphism` |
| **theme**（主题） | 明暗 | `light` / `dark` / `auto` |

四种皮肤都支持明暗主题，`skin` 与 `theme` 可以自由组合。

## 切换皮肤

```python
from prismqml import Skin, getSkin, setSkin

setSkin(Skin.FLUENT)          # Fluent：圆角、模糊阴影、蓝色主色
setSkin(Skin.NEOBRUTALISM)    # 新粗野：粗边框、硬阴影、橙色主色
setSkin(Skin.VINTAGE_TICKET)  # 复古票据：暖纸、油墨细线、印章语义色
setSkin(Skin.NEUMORPHISM)     # 新拟态：同色表面、双向软阴影、凹凸交互
print(getSkin())              # Skin.NEUMORPHISM
```

## 四种视觉范式

![四套皮肤组件实景对比](../images/prismqml-skins.png)

=== "Fluent"

    - 圆角控件与柔和阴影
    - 蓝色主题色
    - 半透明状态层表达 hover / pressed
    - 可选 Mica 云母效果

=== "Neobrutalism（新粗野）"

    - 粗边框与零模糊硬阴影
    - 橙色主色和高饱和语义色
    - 按下时压平硬阴影
    - 实心表面，不使用 Mica

=== "Vintage Ticket（复古票据）"

    - 暖纸背景、旧油墨前景与印章语义色
    - 直角表面、细线边框与票据式分隔
    - 默认使用等宽字体，不使用悬浮阴影与 Mica

=== "Neumorphism（新拟态）"

    - 画布与表面同色，通过明暗双向软阴影表达层级
    - 凸起表面、内凹输入与按压反馈使用统一 token
    - 无描边表面，不使用 Mica

## 在 QML 中读取皮肤

```qml
import PrismQML

Rectangle {
    // 大多数控件无需手动分支；这里只展示公开状态与 token
    radius: Enums.isVintageTicket ? Enums.ticket.radius : Enums.radius.small
}
```

- `Enums.skin`：当前皮肤字符串（`"fluent"` / `"neobrutalism"` / `"vintage_ticket"` / `"neumorphism"`）
- `Enums.isNeobrutalism`：新粗野皮肤便捷判断
- `Enums.isVintageTicket`：复古票据皮肤便捷判断
- `Enums.isNeumorphism`：新拟态皮肤便捷判断
- `Enums.neo.*`：新粗野专属几何与阴影 token
- `Enums.ticket.*`：复古票据专属几何与配色 token
- `Enums.neumorphism.*`：新拟态专属几何、阴影与配色 token
- `Enums.splashScreenMetrics.*`：启动画面专用度量

## 架构：token 驱动

皮肤差异优先收敛到 token 层：

- 颜色走 `Theme`、`StateColor` 与各皮肤调色板
- 几何走 `Metrics`（radius / border / shadow）
- 组件专用度量走 `Metrics` 下的专用入口
- `Enums.accentColor` 自动解析为当前皮肤主色

仅在阴影形态、按压位移等 token 无法表达的结构差异上，组件才读取对应的
`Enums.is*` 状态。

## 明暗适配

四套调色板都随 `Enums.isDark` 自动更新。新粗野深色模式使用深炭背景、提亮
主色与浅色硬边；复古票据切换为深色纸面和浅色油墨；新拟态则维持同色表面，
同时调整成对阴影与文字对比度。
