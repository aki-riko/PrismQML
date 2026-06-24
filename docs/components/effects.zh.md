# 特效

视觉特效组件（`effects/` 模块）。

## NeoShadow 硬阴影

新粗野皮肤的招牌——偏移纯色矩形，零模糊：

```qml
import PrismQML

NeoShadow {
    target: bgRect          // 跟随目标矩形几何
    accent: control.focused // true 时转橙强调
}
```

## ShadowedRectangle 阴影矩形

带模糊阴影的矩形（Fluent 风格软阴影），`shadowVisible` 可控开关。

## 其他

- `Shadow` — 通用阴影
- `ColorOverlay` — 颜色叠加
- `GaussianBlur` — 高斯模糊
- `OpacityMask` — 透明度遮罩（圆角裁剪）

## 皮肤适配

`NeoShadow` 专用于新粗野硬阴影范式；Fluent 皮肤用 `ShadowedRectangle` / `RectangularShadow` 模糊阴影。控件内部按皮肤自动选择阴影实现——你通常无需直接使用这些底层特效。
