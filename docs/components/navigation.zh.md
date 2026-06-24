# 导航

## NavigationBar / NavigationView

主窗口的侧边导航，由 [窗口](../guide/windows.md) 的 `WindowType` 决定紧凑/展开形态。`window.addPage()` 添加导航项。

## TabWidget 标签页

```qml
import PrismQML as Fluent

Fluent.TabWidget {
    // 标签 + 内容
}
```

支持拖拽排序、滚动、关闭。

## Breadcrumb 面包屑

层级路径导航。

## PipsPager 分页指示器

```qml
Fluent.HorizontalPipsPager { count: 5; currentIndex: 0 }
Fluent.VerticalPipsPager { count: 4 }
```

支持翻页按钮、可见数量限制。

## 皮肤适配

新粗野下：导航选中项为**橙实心块 + 黑边 + 白图标文字**（替代 Fluent 的淡色高亮 + 滑动指示条）；TabWidget 选中标签白底粗黑边 + 硬阴影；分页点选中橙、未选黑。
