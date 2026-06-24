# 皮肤系统

皮肤系统是 PrismQML 的招牌能力：**同一套控件，多种设计语言**。

## 皮肤与主题正交

PrismQML 把"设计语言"和"明暗"拆成两个独立维度：

| 维度 | 控制 | 取值 |
|------|------|------|
| **skin**（皮肤） | 设计语言 | `fluent` / `neobrutalism` |
| **theme**（主题） | 明暗 | `light` / `dark` / `auto` |

两者自由组合——neo 皮肤也有明暗，Fluent 皮肤也有明暗。

## 切换皮肤

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)          # Fluent Design：圆角、模糊阴影、蓝主色
setSkin(Skin.NEOBRUTALISM)    # 新粗野：粗黑边、硬阴影、橙撞色
```

```python
from prismqml import getSkin
print(getSkin())   # Skin.NEOBRUTALISM
```

## 两种皮肤的视觉范式

=== "Fluent"

    - 圆角（小圆角 / 药丸）
    - 模糊阴影（RectangularShadow，带模糊半径）
    - 蓝色主题色，半透明叠加表达 hover/press
    - Mica 云母效果

=== "Neobrutalism（新粗野）"

    - 粗黑边（2px 纯黑描边）
    - 硬阴影（偏移纯黑矩形，零模糊）
    - 橙色主色 + 高饱和撞色（绿/红/琥珀）
    - 按钮按下"压平"硬阴影、输入聚焦边框转橙
    - 实心扁平（关闭 Mica）

<!-- TODO: Fluent vs Neobrutalism 同界面对比图 -->

## 在 QML 中读取皮肤

```qml
import PrismQML

Rectangle {
    // 大多数情况你无需判断——控件已自动适配皮肤
    radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small
}
```

- `Enums.skin` — 当前皮肤字符串（`"fluent"` / `"neobrutalism"`）
- `Enums.isNeobrutalism` — 布尔便捷判断
- `Enums.neo.*` — neo 皮肤专属 token（borderWidth / radius / shadowOffset 等）

## 架构：token 驱动，皮肤与控件解耦

PrismQML 的皮肤切换不靠在每个控件里写 `if neo`，而是**把差异收敛到 token 层**：

- **颜色**走 `Theme` / `StateColor` / `Constants.neoColors`
- **几何**走 `Metrics`（radius / border / shadow）
- **主色**：`Enums.accentColor` 在 neo 下自动解析成橙——所有引用主色的控件（primary 按钮、选中态、聚焦边框）自动变橙，无需改动

控件本身对皮肤**近乎无感知**。新增第三套皮肤，只需扩展一套 token 调色板 + 少量结构差异分支，几乎不动控件代码。

## 深色 neo

neo 皮肤的深色模式参照 [neobrutalism.dev](https://neobrutalism.dev) 的深色范式：深炭底 + 提亮主色 + 浅色描边/硬阴影 + 浅字。切到深色主题时 neo 皮肤自动应用这套深色调色板。
