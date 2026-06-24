# 容器

布局与容器控件。

## 布局

- `Layout` / `RowFit` / `VBoxLayout` — 布局容器
- `SplitPane` — 可拖拽分割面板
- `ScrollArea` — 滚动区域（含平滑滚动 + 自绘滚动条）

## Separator 分隔线

```qml
import PrismQML as Fluent

Fluent.Separator { }                    // 横向，自动填充
Fluent.Separator { type: 1 }            // 纵向
```

## GroupBox 分组框

```qml
Fluent.GroupBox {
    title: "分组"
    // 内容
}
```

## Drawer 抽屉

边缘滑入面板。

## Timeline 时间线

虚拟化时间线（大数据量不掉帧）。

## 皮肤适配

新粗野下：GroupBox / Drawer 等容器粗黑边；Separator 按场景用黑线或中灰（轻量分隔用中灰避免滚动闪烁）。
