# 容器

布局与容器控件。

## 布局

- `Layout` / `RowFit` / `VBoxLayout` — 布局容器
- `SplitPane` — 可拖拽分割面板
- `ScrollArea` — 滚动区域（含平滑滚动 + 自绘滚动条）

## SkinScope 局部皮肤范围

让一棵子树使用不同设计语言，同时保留应用全局 skin 和用户配置：

```qml
import PrismQML as Fluent

Fluent.SkinScope {
    skin: "vintage_ticket"
    Fluent.Card { }
}
```

空 `skin` 跟随最近父范围。大多数情况不需要手工传 token；只有 popup 或对话框
定义在范围外时，才使用 `skinContext: scope.context` 转交上下文。

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

## BottomSheet 底部弹层

从窗口底部滑出的页内弹层，可以一层叠一层。新打开的弹层压在上一层上面，下层会缩小、
上移、压暗，顶边从上层上方露出。拖动顶部手柄可以展开、收起或关闭。

在一个 `BottomSheet` 内部声明另一个，就构成嵌套：

```qml
import PrismQML as Fluent

Fluent.BottomSheet {
    id: settingsSheet
    Fluent.Button { text: "高级选项"; onClicked: advancedSheet.open() }

    Fluent.BottomSheet {
        id: advancedSheet
        detent: Fluent.Enums.sheet.detent_large
        // 内容
    }
}
```

| 成员 | 说明 |
|------|------|
| `open()` / `close()` | 打开或关闭。关闭父层时，声明在它内部的子层会一起关闭 |
| `detent: int` | 停靠高度：`Enums.sheet.detent_medium`（窗口高度的一半，默认）或 `detent_large`（几乎占满） |
| `allowLargeDetent: bool` | 是否允许上拉或点按手柄展开到 `detent_large`，默认 `true` |
| `showGrabber: bool` | 是否显示顶部手柄，默认 `true` |
| `expand()` / `collapse()` | 切换到 `detent_large` / `detent_medium` |
| `sheetMaxWidth: int` | 宽窗口下的最大宽度，弹层水平居中 |
| `opened: bool` | 只读，是否处于打开状态 |
| `stackIndex: int` | 只读，在当前窗口栈中的位置（自底向上，从 0 开始）；完全关闭后为 `-1` |

交互规则：

- 只有栈顶弹层的手柄可以拖动。向下拖过停靠高度的四分之一，或者快速下甩，就会关闭
  （在 `detent_large` 下先收回到 `detent_medium`）；向上拖则展开。
- `Escape` 和点击遮罩都只关闭栈顶一层。焦点会交还给下一层，所以连按 `Escape` 可以逐层关闭。
- 只有最底层画遮罩，叠多少层，背景亮度都不变。超过三层时，最下面的层会淡出。
- 弹层会被重挂到窗口内容项上，不受父容器裁剪；它不会越出宿主窗口。

## Timeline 时间线

虚拟化时间线（大数据量不掉帧）。

## RefreshContainer 下拉刷新

在内容上方包裹一层"下拉即刷新"手势。容器自动探测内容里第一个 `Flickable`
作为滚动面，只在滚动面位于顶部时接管纵向手势，平时把滚动完全交还给它。

```qml
import PrismQML as Fluent

Fluent.RefreshContainer {
    refreshing: model.refreshing          // 宿主状态，由宿主清回 false
    onRefreshRequested: model.reload()
    ListView { model: model.items }       // 内容走默认属性
}
```

| 成员 | 说明 |
|------|------|
| `refreshing: bool` | 宿主所有。触发时容器置 `true`，**宿主完成后必须置回 `false`**（不要绑定它） |
| `pullThreshold: int` | 触发刷新所需下拉距离，默认 `Enums.controlSize.refreshPullThreshold` |
| `interactionEnabled: bool` | 是否允许下拉手势 |
| `target: Flickable` | 显式指定滚动面；为空则自动探测 |
| `progress / armed / indicatorVisible` | 只读：下拉进度、是否已到位、指示器是否可见 |
| `refreshRequested()` | 用户下拉到位或调用 `requestRefresh()` 时发出 |
| `requestRefresh()` | 以编程方式开始一次刷新 |

指示器居中于容器顶部上方，随位移滑入；只读状态可用于自定义绘制。滚动面变化时不
需手工重绑：容器监听内容子项变化后重新探测（也可用 `target` 显式钉死）。

## 皮肤适配

新粗野下：GroupBox / Drawer 等容器粗黑边；Separator 按场景用黑线或中灰（轻量分隔用中灰避免滚动闪烁）。
