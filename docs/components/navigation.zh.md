# 导航

## NavigationBar / NavigationView

主窗口的侧边导航，由 [窗口](../guide/windows.md) 的 `WindowType` 决定紧凑/展开形态。`window.addPage()` 添加导航项。

### 页内独立使用

两者都是普通 `Item`，可以脱离窗口外壳直接放进页面（画廊 "Vertical navigation" 区就是这么展示的）。独立使用时有两件事必须知道：

**① 选中项是单向绑定，必须由宿主回灌。** 面板被点击时只发 `itemClicked(index)`，自己不修改 `currentIndex` —— 这是为了避免破坏"窗口 → 导航"的单向绑定：

```qml
NavigationView {
    model: [
        { key: "home", text: "Home", icon: ... },
        { key: "docs", text: "Documents", icon: ... }
    ]
    onItemClicked: (index) => currentIndex = index   // 页面里这段接线就是那个"宿主外壳"
}
```

`ToggleNavigationBar` 不继承该基类，它会自己更新 `currentIndex`，无需接线。

**② `titleBarHeight` 默认等于窗口标题栏高度。** 页内没有标题栏，不归零就会白白留出顶部空白（实测 48px，条目整体被压低）：

```qml
NavigationView {
    titleBarHeight: 0        // 页内无标题栏
    showReturnButton: false  // 页内也不需要返回按钮
}
```

## SegmentedControl / Pivot 分段控件与透视导航

两者共用 `items` 模型（`{ key, text, icon }` 或纯字符串）与 `currentIndex`，默认横向排列：

```qml
Fluent.SegmentedControl { items: ["常规", "外观", "高级"] }
Fluent.Pivot { items: [{ key: "docs", text: "文档" }, { key: "img", text: "图片" }] }
```

`orientation: Qt.Vertical` 改为纵向堆叠，指示器从底部细条变成贴左边缘的竖条：

```qml
Fluent.SegmentedControl {
    orientation: Qt.Vertical
    items: ["General", "Appearance", "Advanced"]
}
```

纵向时单元按内容定宽（不会拉伸铺满），控件宽度取最宽单元。需要"整行铺满"的纵向导航请用 `NavigationView` 或 `ToggleNavigationBar`。

## TabBar / TabWidget 标签页

```qml
import PrismQML as Fluent

Fluent.TabWidget {
    // 标签 + 内容
}
```

横向（默认）支持拖拽排序、滚动、关闭、添加按钮。`TabBar` 只渲染标签，页面内容由调用方或 `TabWidget` 承载。

`orientation: Qt.Vertical` 把标签列放到起始边（左），页面内容占据其余区域：

```qml
Fluent.TabWidget {
    orientation: Qt.Vertical
    width: 360
    height: 220
    tabs: [ { title: "标签1", content: page1 }, { title: "标签2", content: page2 } ]
}
```

纵向形态的行为：标签行占满列宽、**行高取行高**（`tabWidth` 若设置则作为行高）、标题过长省略、关闭按钮贴右、拖拽沿纵轴重排、添加按钮落在列尾、溢出沿 Y 轴滚动。列宽由 `Enums.controlSize.tabBarVerticalWidth` 决定。

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
