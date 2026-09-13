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

## 局部皮肤范围

`SkinScope` 只替换其子树的设计语言，不调用 `Enums.setSkin()`，也不会写入用户的
全局外观配置。它适合把邀请函、票据、嵌入式工具等局部区域做成与应用主皮肤不同的
视觉语言：

```qml
import PrismQML as Fluent

Fluent.SkinScope {
    id: inviteTicket
    skin: "vintage_ticket"

    Fluent.Card {
        title: "邀请函"
        Fluent.Button { text: "复制" }
    }
}
```

- `skin` 支持与全局设置相同的四个值；空字符串会跟随最近的父范围。
- 局部范围继承全局明暗和基础强调色，因此全局切换 light/dark 时局部票据也会同步更新。
- Card、Button、Label、Separator、TicketPaper、DialogBoxCore、ContentFrame、PopupWindowCore
  及按钮下拉菜单会自动使用最近范围的 token。
- popup 或对话框若定义在范围外、但由范围内控件触发，可显式传递只读 context：

```qml
Fluent.PopupWindowCore {
    skinContext: inviteTicket.context
}
```

`context` 只用于跨父级或跨窗口的上下文转交；普通页面只需要写 `SkinScope`。

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
