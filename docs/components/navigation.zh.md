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

## CommandPalette 命令面板

Ctrl+K 风格的命令面板：模态浮层 + 搜索框 + 排名结果列表。过滤、模糊匹配、分组标题、命中高亮与 ↑↓ 导航复用库内搜索栈（`SearchResultList`），本组件只负责开合、遮罩、焦点与命令派发。

```qml
Fluent.CommandPalette {
    id: palette
    shortcut: "Ctrl+K"                        // 可选全局快捷键, 留空则关闭
    placeholderText: "输入命令..."
    hintText: "↑↓ 导航  Enter 执行  Esc 关闭"   // 留空则隐藏底部提示
    items: [
        { key: "open-file", title: "打开文件", subtitle: "Ctrl+O",
          section: "文件", icon: Enums.iconPath + "FolderOpen.svg" },
        { key: "toggle-theme", title: "切换主题", keywords: ["dark", "light"] }
    ]
    onCommandTriggered: (key, item) => runCommand(key)
}
```

- **打开**：`open()` / `toggle()`，或 `shortcut` 指定的快捷键；每次打开都会清空查询并把键盘焦点收进搜索框。
- **关闭**：`Esc`、点击遮罩、`close()`。执行命令时先关闭再发 `onCommandTriggered(key, item)`，宿主拿到的状态已经收敛。
- **数据**：`items` 每项支持 `key / title / subtitle / icon / section / keywords / enabled`；`section` 非空且 `sectionHeaders` 为真时按分组显示。
- **文案**：`placeholderText` / `emptyText` / `hintText` 由调用方注入本地化文本，组件内不硬编码。
- **键路由**：面板打开期间 ↑ / ↓ / Enter / Esc 走窗口级快捷键——焦点在搜索框上，其内部文本输入会先吞掉方向键，事件冒泡不到面板。

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
