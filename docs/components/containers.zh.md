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
