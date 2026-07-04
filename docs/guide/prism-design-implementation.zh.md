# Prism Design 落地标准

本文是 [Prism Design 视觉规范](prism-design.md) 的执行口径。视觉规范回答“Prism Design 应该长什么样”，本文回答“组件、Gallery、测试和评审如何证明它已经按标准落地”。

Prism Design 的落地不以“看起来像蓝色 Fluent”作为验收标准，而以 token 接入、状态完整、组件族覆盖、light/dark 对照、Gallery 截图和无硬编码为准。

## 完成定义

一个 Prism Design 相关改动只有同时满足以下条件，才可以称为完成：

- 视觉规则已写入 `prism-design.md` 或本文。
- 需要的新值已进入 `Constants.prismDesign`、`Theme`、`StateColor`、`textColor` 或现有 `Enums` token。
- 组件优先绑定通用 token，只有几何、层级或结构确实不同才读取 `Enums.prismDesign.*`。
- light / dark 都通过同一组件样例验证。
- normal / hover / pressed / focused / disabled / selected 等状态按组件类型完整覆盖。
- Gallery 或示例能展示真实控件，而不是只展示色块。
- `git diff --check` 通过。
- QML probe 或对应测试没有新增回归。

如果只完成 token，控件没有接入，不算落地。如果只改控件，没有规范和验收证据，也不算落地。

## 权威来源

当 Prism Design 相关口径发生冲突时，按以下顺序裁决：

| 顺序 | 来源 | 用途 |
|------|------|------|
| 1 | `docs/guide/prism-design.zh.md` | 视觉语言、颜色、几何、状态、组件原则 |
| 2 | 本文 | 落地流程、组件矩阵、Gallery 和评审门禁 |
| 3 | `prismqml/PrismQML/PrismEnums/Constants.qml` | token 的当前真实值 |
| 4 | `prismqml/PrismQML/PrismEnums/Theme.qml` / `StateColor.qml` | 通用 token 转发 |
| 5 | `prismqml/PrismQML/qmldir` | 公共组件注册范围 |
| 6 | Gallery / probe / pytest 输出 | 当前实现是否达标的证据 |

文档和 token 不一致时，不允许“先按代码算”。必须判断是规范变更还是实现遗漏，然后同步两边。

## 落地阶段

| 阶段 | 范围 | 验收结果 |
|------|------|----------|
| P0 Token | `Skin.PRISM_DESIGN`、`Enums.isPrismDesign`、`Enums.prismDesign`、主题转发 | 能切换皮肤，基础颜色和半径可读 |
| P1 核心控件 | Button、Input、ComboBox、Card、基础文本和图标 | 高频界面可以形成 Prism Design 气质 |
| P2 结构控件 | Navigation、Menu、Flyout、Dialog、Toast、InfoBar、SettingsCard | 应用主框架和弹层一致 |
| P3 数据控件 | List、Table、Tree、Badge、Tag、Progress、Chart | 数据密集界面可长期使用 |
| P4 完整体验 | Gallery 对照、截图验收、状态墙、真实页面样例 | 能向用户展示第三套 skin 的完整能力 |

阶段可以并行推进，但不能跳过 P0。任何 P2 之后的组件都必须继承 P0/P1 的 token 口径。

## Token 接入矩阵

### 通用入口优先

组件默认应读取这些通用入口：

| 用途 | 首选入口 | 说明 |
|------|----------|------|
| 应用背景 | `Enums.backgroundColor` | 页面或窗口外层 |
| 内容面 | `Enums.surfaceColor` | 主内容区 |
| 控件面 | `Enums.stateColor.controlBg` / `Enums.cardColor` | Button、Input、Card |
| 弹层面 | `Enums.dialogColor` / `Enums.toastCardColor` | Dialog、Menu、Flyout、Toast |
| 主文本 | `Enums.textColor.primary` | 正文、按钮、标题 |
| 次级文本 | `Enums.textColor.secondary` | placeholder、说明 |
| 弱文本 | `Enums.textColor.tertiary` | metadata、弱提示 |
| 禁用文本 | `Enums.textColor.disabled` | disabled |
| 默认边框 | `Enums.borderColor` / `Enums.stateColor.border` | 控件边界 |
| 强边框 | `Enums.borderStrongColor` / `Enums.stateColor.borderStrong` | focus、selected |
| 分隔线 | `Enums.dividerColor` | list/table/menu 分隔 |
| hover | `Enums.hoverColor` / `Enums.stateColor.hover` | 悬停状态 |
| pressed | `Enums.pressedColor` / `Enums.stateColor.pressed` | 按下状态 |
| selected | `Enums.selectedColor` / `Enums.stateColor.selected` | 选中状态 |
| 主操作 | `Enums.accentColor` | primary 操作、焦点 |

### Prism 专属入口

只有下列场景直接读取 `Enums.prismDesign.*`：

| Token | 允许场景 |
|-------|----------|
| `radiusControl` | Button、Input、ComboBox、MenuItem、Tab 等基础控件半径 |
| `radiusCard` | Card、Panel、SettingsCard、Group 容器 |
| `radiusPopup` | Menu、Flyout、Tooltip、Toast、Drawer |
| `radiusDialog` | Dialog、MessageBox、ProgressDialog |
| `borderWidth` | 需要固定 Prism 默认描边宽度的控件 |
| `focusBorderWidth` | 键盘焦点、输入焦点 |
| `primary` / `primaryLight` / `primaryDark` | 需要明确区分 normal/hover/pressed 的主色组件 |
| `secondary` / `warm` / `glow` | 局部辅助强调，不承载语义状态 |

除 token 定义文件、视觉测试和文档外，组件内禁止写 Prism Design 专属 hex 色值。

## 状态验收矩阵

| 状态 | 必验组件 | 合格标准 |
|------|----------|----------|
| Normal | 所有可见组件 | 层级、边界、文本清楚，不像 disabled |
| Hover | Button、Input、Menu、List、Table、Navigation | 颜色或边界变化可见，布局不移动 |
| Pressed | Button、MenuItem、Navigation、Toggle、Slider | 有按下反馈，不使用 neo 硬位移 |
| Focused | Button、Input、ComboBox、MenuItem、Tab、Navigation | 键盘焦点可见，不能只靠 hover |
| Disabled | 所有交互组件 | 降低强调但仍能识别控件类型 |
| Selected | Navigation、Tab、List、Table、Tree、SegmentedControl | 位置指示和状态层同时存在 |
| Checked | CheckBox、RadioButton、ToggleSwitch、Toggle | 主色清晰，图标和 thumb 对比足够 |
| Error | Input、Picker、Form、InfoBar、Dialog | 不只靠颜色，必须有文本或图标 |
| Warning | Form、InfoBar、Toast、Dialog | 使用语义色，不使用 `warm` 替代 warning |
| Success | Form、InfoBar、Toast、ResultState | 使用语义色，不和 `secondary` 混淆 |
| Loading | Button、Progress、Skeleton、Dialog | 动画不阻塞输入，不抢正文注意力 |
| Empty | EmptyState、EmptyDataState、List、Table | 清楚表达空态，不伪装为错误 |

状态切换不得改变组件外部尺寸、布局锚点、文字字号或图标尺寸。

## 组件族矩阵

### Core / Window

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 窗口底层 | `Windows`、`NavigationWindowCore`、`WindowsCore` | `background`、`surface`、标题栏文字、窗口阴影 |
| 导航窗口 | `NavigationView`、`NavigationBar`、`NavigationBarItem` | 当前项指示、侧栏 surface、内容区 surface |
| 状态区域 | `StatusBar`、`NavigationProfileCard` | 分隔线、次级文本、hover |

验收时必须包含窗口背景、侧边栏、内容面、当前导航项和状态栏。

### Buttons

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 基础按钮 | `Button`、`ButtonCore`、`CustomButtonCore` | 背景、边框、半径、主色、焦点 |
| 内容与附属 | `ButtonContent`、`ButtonDropdown`、`ButtonProgress` | 图标文字间距、进度状态、下拉指示 |
| 窗口按钮 | `CloseButton` | hover / pressed / danger 语义 |

按钮验收必须覆盖 default、primary、text、hyperlink、semantic、disabled、loading。

### Inputs

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 文本输入 | `LineEdit`、`TextEdit`、`InputCore`、`PinInput` | `raised` 背景、placeholder、focus、error |
| 选择输入 | `ComboBox` 系列、`DateTimePicker`、`CalendarPicker`、`ColorPicker` | 输入框与弹层半径、选中项、hover |
| 数值输入 | `SpinBox`、`Slider`、`Rating` | track、thumb、按钮、主色 |
| 开关选择 | `Toggle`、`CheckBox`、`RadioButton`、`ToggleSwitch` | checked、disabled、focus |
| 搜索过滤 | `LocalSearchBar`、`FilterBar`、`ShortcutEditor` | 输入态、chip、键位标签 |

输入验收必须包含 placeholder、focus、filled、error、disabled、readonly 或等价状态。

### Containers

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 卡片面板 | `Card`、`ExampleCard`、`ComponentCard`、`SettingsCard` | `raised`、`radiusCard`、边框、hover |
| 展开与抽屉 | `Expander`、`GroupBox`、`Drawer` | header、分隔线、overlay、展开动画 |
| 布局容器 | `SplitPane`、`ScrollArea`、`ScrollBar`、`Separator` | 分隔线、滚动条、拖拽 handle |
| 特殊容器 | `Timeline`、`DropZone`、`Waterfall`、`Widget` | 状态边界、hover、空态 |

容器禁止卡片套卡片制造层级。需要嵌套时，内层应退为 section 或列表项。

### Navigation

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 顶层导航 | `NavigationBar`、`NavigationView`、`ToggleNavigationBar` | 选中指示、hover、折叠状态 |
| 页内导航 | `TabWidget`、`Pivot`、`SegmentedControl`、`Breadcrumb` | selected、focused、分隔 |
| 翻页导航 | `Paginator`、`PipsPager`、`HorizontalPipsPager`、`VerticalPipsPager` | 当前页、disabled、hover |
| 菜单导航 | `MenuBar` | menu hover、打开态、键盘焦点 |

导航验收必须证明当前项不只靠文字颜色区分。

### Menus / Flyout / Tooltip

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 菜单 | `ContextMenu`、`MenuCore`、`MenuDelegate`、`TreeMenuDelegate` | `overlay`、`radiusPopup`、菜单项状态 |
| 动作 | `Action`、`MenuSeparator`、`SystemTrayMenu` | 图标、文字、快捷键、分隔线 |
| 提示与浮层 | `Flyout`、`TeachingTip`、`ToolTip`、`TipPopup`、`HintIcon` | 可读性、阴影、箭头或锚点 |
| 底部/侧向浮层 | `FlyoutSheet` | overlay 层级、遮罩、关闭状态 |

菜单和浮层必须在复杂背景上仍能读清，不能靠透明度制造层级。

### Dialogs

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 基础对话 | `MessageBox`、`DialogBoxCore`、`MaskedDialog` | `overlay`、`radiusDialog`、遮罩、阴影 |
| 操作对话 | `ConfirmDialog`、`UpdateDialog`、`ProgressDialog` | 主操作、危险操作、进度态 |
| 图片对话 | `ImageCropperDialog`、`ColorPickerDialog` | 工具区、预览区、操作区分层 |

对话验收必须覆盖 modal 遮罩、主按钮、取消按钮、危险按钮和键盘焦点。

### Data

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 文本标签 | `Label`、`Badge`、`Tag`、`Watermark`、`Marquee` | 语义色、弱文本、边框 |
| 列表树表 | `ListView`、`ListWidget`、`TableView`、`TableWidget`、`TreeView`、`TreeWidget` | 行 hover、selected、alternateRow、divider |
| 媒体数据 | `Avatar`、`AvatarSelector`、`ImageWidget`、`AudioWaveform`、`QRCode` | 边界、placeholder、选中态 |
| 指标图表 | `ChartView`、`CircularGauge`、`IndicatorBar`、`ChartDataZoom` | 坐标轴、tooltip、grid、主色与语义色 |
| 翻页展示 | `Carousel`、`HorizontalPipsPager`、`VerticalPipsPager` | 当前项、hover、禁用 |

数据组件验收必须包含密集列表或表格场景，不能只看单个空白控件。

### Feedback

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 语义反馈 | `InfoBar`、`Toast`、`DesktopNotification` | 语义色、overlay、关闭按钮 |
| 进度反馈 | `Progress`、`ProgressBar`、`ProgressRing`、`Skeleton` | track、active、shimmer、低噪声 |
| 状态页面 | `EmptyState`、`EmptyDataState`、`OfflineState`、`ResultState`、`StateWidget` | 图标、标题、说明、操作按钮 |
| 特效反馈 | `Confetti`、`SplashScreen` | 不遮挡主流程，不默认高噪声 |

反馈组件必须优先表达语义，不允许把所有状态都染成 Prism 主色。

### Icons / Effects / Chat / Auth

| 范围 | 组件 | 必须统一的内容 |
|------|------|----------------|
| 图标 | `Icon`、`ChevronIcon`、`CheckIcon`、`CloseIcon` | 跟随文本色、语义色或主色 |
| 效果 | `ShadowedRectangle`、`Shadow`、`ColorOverlay`、`OpacityMask`、`GaussianBlur` | 阴影等级、性能边界 |
| 聊天 | `ChatBubble`、`ChatMessageList`、`MarkdownView`、`CodeBlock` | 气泡层级、代码块、链接、选择态 |
| 认证 | `LoginWindow` | 输入、主按钮、错误提示、窗口背景 |

这些组件不能成为例外区。即使不是第一阶段重点，也必须遵守 token 与状态标准。

## Gallery 验收标准

Gallery 是 Prism Design 的最终视觉证据。新增或调整 Prism Design 时，Gallery 至少应提供以下视图：

| 视图 | 内容 | 目的 |
|------|------|------|
| Token Board | light/dark 色板、surface 层级、状态层、半径 | 验证 token 可见且成体系 |
| State Wall | Button、Input、MenuItem、NavigationItem 的全状态 | 验证 normal 到 disabled 的状态完整 |
| Component Matrix | 按钮、输入、卡片、导航、弹层、表格同页展示 | 验证组件族一致性 |
| Three Skin Compare | 同一界面在 Fluent、Neobrutalism、Prism Design 下并排 | 验证第三套 skin 有独立气质 |
| Real App Surface | 一个接近真实工具界面的组合页面 | 验证信息密度、扫读和长期使用 |
| Dark Audit | 深色模式下的表格、弹层、输入和语义反馈 | 验证深色不是自动反色 |

截图验收必须包含 light 和 dark。只截单个浅色按钮，不足以证明 Prism Design 落地。

## 视觉 QA 清单

每次提交 Prism Design 视觉改动前，至少检查：

- 组件是否仍能在 Fluent 和 Neobrutalism 下正常显示。
- Prism Design 是否只通过 token 分支影响自己，不污染其它 skin。
- hover / pressed / focused 是否可见且不引发布局抖动。
- disabled 是否不会误判为普通状态。
- selected 是否有位置或形状指示，不只靠颜色。
- 深色模式下边框是否足够分层。
- 弹层是否有遮罩、边框或阴影与背景分离。
- 表格和列表是否能在密集数据下保持扫读。
- 文本是否没有溢出按钮、菜单项、卡片标题。
- 动画是否短促克制，不影响输入响应。

## 代码评审门禁

评审 Prism Design 相关 PR 时，必须能回答：

- 是否改了规范或引用了已有规范条款。
- 是否新增或复用了 token，而不是在组件内散写色值。
- 是否列出受影响组件族。
- 是否提供 light / dark 证据。
- 是否覆盖交互状态。
- 是否说明没有破坏 Fluent / Neobrutalism。
- 是否运行了对应 probe 或测试。
- 如果未能运行完整文档构建，是否明确说明环境原因。

缺少上述任一项时，PR 只能标记为未完成。

## 禁止清单

- 禁止把 Prism Design 写成 Fluent 的换色版本。
- 禁止用外部闭源设计语言作为直接标准。
- 禁止为 Prism Design 复制一套组件目录。
- 禁止在组件内部直接写 Prism Design 专属 hex。
- 禁止用全局毛玻璃、全屏渐变或大面积 glow 替代层级。
- 禁止 hover、pressed、selected 改变组件尺寸。
- 禁止只做浅色，不做深色。
- 禁止只做截图，不做真实控件状态。
- 禁止只改文档不更新实现证据，也禁止只改实现不更新文档口径。

## 落地记录格式

后续每完成一个组件族，在提交说明或 PR 描述中按此格式记录：

```text
Prism Design scope:
- Component family:
- Tokens touched:
- States verified:
- Light/Dark evidence:
- Tests/probe:
- Remaining gaps:
```

如果某个组件族暂时不做，必须在 `Remaining gaps` 中说明，不允许静默遗漏。
