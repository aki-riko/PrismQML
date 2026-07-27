# 皮肤系统

皮肤系统让同一套 PrismQML 控件在 Fluent 与新粗野两种设计语言之间切换。

## 皮肤与主题正交

PrismQML 把设计语言和明暗拆成两个独立维度：

| 维度 | 控制 | 取值 |
|------|------|------|
| **skin**（皮肤） | 设计语言 | `fluent` / `neobrutalism` |
| **theme**（主题） | 明暗 | `light` / `dark` / `auto` |

两种皮肤都支持明暗主题。

## 切换皮肤

```python
from prismqml import Skin, getSkin, setSkin

setSkin(Skin.FLUENT)          # Fluent：圆角、模糊阴影、蓝色主色
setSkin(Skin.NEOBRUTALISM)    # 新粗野：粗边框、硬阴影、橙色主色
print(getSkin())              # Skin.NEOBRUTALISM
```

## 两种视觉范式

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

## 在 QML 中读取皮肤

```qml
import PrismQML

Rectangle {
    radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small
}
```

- `Enums.skin`：当前皮肤字符串（`"fluent"` / `"neobrutalism"`）
- `Enums.isNeobrutalism`：新粗野皮肤便捷判断
- `Enums.neo.*`：新粗野专属几何与阴影 token
- `Enums.splashScreenMetrics.*`：启动画面专用度量

## 架构：token 驱动

皮肤差异优先收敛到 token 层：

- 颜色走 `Theme`、`StateColor` 与 `Constants.neoColors`
- 几何走 `Metrics`（radius / border / shadow）
- 组件专用度量走 `Metrics` 下的专用入口
- `Enums.accentColor` 在新粗野皮肤下自动解析为其固定主色

仅在阴影形态、按压位移等 token 无法表达的结构差异上，组件才读取 `Enums.isNeobrutalism`。

## 深色新粗野

深色新粗野使用深色背景、提亮主色、浅色描边与硬阴影。切换深色主题后，调色板随 `Enums.isDark` 自动更新。
