# Prism Design 视觉规范

Prism Design 是 PrismQML 的自有设计语言，也是 `Skin.PRISM_DESIGN` 的唯一视觉标准来源。后续所有 Prism Design 组件、Gallery、示例和截图验收，都应以本文为准。

本文只定义设计标准，不替代皮肤系统说明。皮肤切换 API、`Enums.skin`、`Enums.prismDesign` 等用法见 [皮肤系统](skins.md)。

## 规范状态

| 项 | 标准 |
|----|------|
| 皮肤名 | `Prism Design` |
| Python 枚举 | `Skin.PRISM_DESIGN` |
| QML 字符串 | `prism_design` |
| QML 判断 | `Enums.isPrismDesign` |
| Token 入口 | `Enums.prismDesign.*` |
| 当前阶段 | 已有 token 与关键控件 MVP，视觉规范先行补齐 |

Prism Design 是规范，不是单个主题色。任何组件只要声明支持 `prism_design`，就必须同时满足本文的颜色、层级、状态、密度、动效和可访问性要求。

## 设计定位

Prism Design 面向桌面生产力应用、开发者工具、AI 工具、数据看板和长期使用的业务界面。它的气质是清晰、冷静、精致、有层次，而不是营销页式的强装饰。

核心目标：

- 让 PrismQML 拥有不依赖外部平台的自有审美。
- 在 Fluent 的工程稳态和 Neobrutalism 的强辨识度之外，提供第三条长期可用路线。
- 让控件库适合真实应用，而不只是适合截图展示。
- 保持 token 驱动，使后续皮肤扩展不会把分支散落到每个控件里。

非目标：

- 不复刻 Apple Liquid Glass、Material、Fluent、Carbon 或其它外部设计语言。
- 不以全局毛玻璃、渐变背景、光晕堆叠作为主要风格。
- 不牺牲表格、输入、导航、弹层等高频控件的清晰度。
- 不为了“高级感”降低对比度、缩小点击区域或隐藏状态反馈。

## 设计原则

### 清晰优先

文字、图标、边界和焦点状态必须永远可见。任何材质、阴影、透明度、渐变和高光都不能压过信息本身。

### 层级可解释

界面必须能被解释为稳定层级：背景、内容面、卡片、浮层、模态层。层级差异来自 token，而不是每个组件临时调色。

### 克制表达

Prism Design 可以有柔和光感，但不能把光感做成装饰噪声。表达应集中在边缘高光、状态层、轻阴影、局部强调色。

### 桌面密度

默认密度服务桌面工具：控件尺寸不夸张，信息密度适中，布局可扫读。移动端舒适感不是首要目标。

### 状态完整

所有可交互组件必须覆盖 normal、hover、pressed、focused、disabled、selected。输入类和校验类组件还必须覆盖 error / warning / success。

### Token 先行

所有可复用颜色、几何、阴影、透明度和时长必须进入 `Enums` 或皮肤 token。组件内禁止直接散写 Prism Design 专属值。

## 视觉关键词

| 关键词 | 含义 | 落地方式 |
|--------|------|----------|
| Clarity 清晰 | 信息优先 | 高可读文字、明确边界、可见焦点 |
| Layered 层次 | 界面有深度 | surface 分级、阴影层级、边框强弱 |
| Luminous 光感 | 有轻微光泽 | 主色 tint、边缘高光、局部 glow |
| Calm 冷静 | 不抢业务内容 | 低噪声背景、克制动效、中性色为主 |
| Precise 精确 | 工具感明确 | 稳定尺寸、对齐、状态不跳动 |

## 层级系统

Prism Design 的层级是界面组织的第一规则。颜色、阴影、边框和透明度都必须服务于层级。

| 层级 | 用途 | 视觉要求 | 当前 token |
|------|------|----------|------------|
| Base | 应用外层背景、窗口底色 | 最低对比，承载导航和留白 | `background` |
| Surface | 主内容区、页面主体 | 低噪声、可长时间阅读 | `surface` |
| Raised | 卡片、按钮、输入框、面板 | 比 Surface 更近，边界清楚 | `raised` |
| Overlay | Menu、Flyout、Tooltip、Toast | 临时浮层，和内容明显分离 | `overlay` |
| Modal | Dialog、MessageBox、遮罩层 | 最高注意层，必须压住背景 | `overlay` + shadow + scrim |

禁止事项：

- 禁止把整页大 section 都做成浮卡，除非它本身是一个独立工具面板。
- 禁止卡片套卡片制造层级。
- 禁止用大面积渐变代替 surface 层级。
- 禁止弹层透明到看不清后方与前景边界。

## 颜色系统

### 基础色

当前 `Constants.prismDesign` 的基础色如下，后续调整必须同步更新本文。

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `background` | `#F4F7FA` | `#111418` | 应用外层背景 |
| `surface` | `#FBFCFE` | `#171C22` | 主内容面 |
| `raised` | `#FFFFFF` | `#20262E` | 控件、卡片、面板 |
| `overlay` | `#F8FBFF` | `#242B34` | 弹层、菜单、对话框 |
| `header` | `#EEF4F9` | `#151A20` | 顶栏、分组头 |
| `tableBg` | `#F7FAFD` | `#141920` | 表格背景 |
| `alternateRow` | `#F8FBFE` | `#1A2028` | 交替行 |

### 前景色

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `foreground` | `#17202A` | `#EEF3F8` | 主文本、主图标 |
| `secondaryForeground` | `#5F6F80` | `#A6B1BF` | 次级文本、说明 |
| `tertiaryForeground` | `#8392A4` | `#768394` | 弱说明、辅助信息 |
| `disabledForeground` | `#A5B0BC` | `#5D6876` | 禁用文本 |

文字必须优先使用 `Enums.textColor.*`，不要直接读取颜色 token。只有设计 token 调试、视觉测试和文档示例可以直接提及色值。

### 强调色

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `primary` | `#2F6FED` | `#7AA7FF` | 主操作、选中态、焦点 |
| `primaryLight` | `#427EFA` | `#93B8FF` | hover 派生 |
| `primaryDark` | `#245AC7` | `#5D8FE8` | pressed 派生 |
| `primaryForeground` | `#FFFFFF` | `#0F172A` | 主色块上的文字 |
| `secondary` | `#18A999` | `#59D6C7` | 次强调、辅助成功倾向 |
| `warm` | `#D97706` | `#F6B44B` | 提醒、局部暖色 |
| `glow` | `#8EC5FF` | `#4EA0FF` | 局部光感，不承载文字 |

使用规则：

- 主操作按钮、当前导航项、输入焦点优先使用 `primary`。
- `secondary` 只用于辅助强调，不能和成功色混用。
- `warm` 用于注意和提示，不替代 warning 语义色。
- `glow` 只能做边缘光和视觉辅助，禁止把文本放在 glow 背景上。

### 边框与分隔

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `border` | `#D9E3EC` | `#303A46` | 默认控件边框 |
| `borderLight` | `#E7EEF5` | `#26303A` | 弱边界、内部分隔 |
| `borderStrong` | `#AAB8C7` | `#4B5A6B` | 焦点、强调边界 |
| `divider` | `#E2EAF2` | `#2A333D` | 列表、表格、分组分隔 |

边框不是装饰，而是层级和可点击区域的提示。浅色模式不能让边框消失，深色模式不能只靠阴影分层。

### 状态层

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `hover` | `#EEF5FF` | `#26303A` | 悬停 |
| `pressed` | `#E3EDF8` | `#202833` | 按下 |
| `disabled` | `#E9EEF4` | `#20242B` | 禁用背景 |
| `selected` | `#DBEAFF` | `#1D3A63` | 选中 |
| `selectedHover` | `#C9DFFF` | `#254A78` | 选中悬停 |
| `tableHover` | `#EEF5FF` | `#232C36` | 表格/列表悬停 |

状态层必须有可见差异，但不能让组件尺寸变化。hover、pressed、selected 禁止通过改变文字大小、边距、布局来表达。

## 几何系统

| Token | 值 | 用途 |
|-------|----|------|
| `radiusControl` | 6 | Button、Input、ComboBox、菜单项 |
| `radiusCard` | 8 | Card、Panel、SettingCard |
| `radiusPopup` | 10 | Menu、Flyout、Tooltip、Toast |
| `radiusDialog` | 12 | Dialog、MessageBox |
| `borderWidth` | 1 | 默认边框 |
| `focusBorderWidth` | 2 | 键盘焦点、输入焦点 |

几何规则：

- 默认控件不能做大药丸，除非现有 API 明确选择 `shape_pill`。
- 页面主卡片不超过 `radiusCard`，弹层不超过 `radiusPopup`，对话框不超过 `radiusDialog`。
- 圆角必须稳定，不因 hover / pressed 改变。
- 点击区域至少保持现有 PrismQML 控件尺寸，不因视觉变薄而缩小。

## 阴影与材质

Prism Design 使用软阴影和边界高光，不使用 Neobrutalism 的硬阴影。

| 层级 | 用途 | 阴影策略 |
|------|------|----------|
| Level 2 | 普通卡片、按钮 hover | 很轻，只提示可交互 |
| Level 4 | Toast、Dropdown、浮动工具条 | 可见浮起，边框仍清楚 |
| Level 8 | Menu、Flyout、Tooltip | 与内容明显分离 |
| Level 16 | Dialog、Modal | 强阴影 + 遮罩 |

材质规则：

- 默认 surface 必须是实心色。
- 透明和 blur 只能用于 Overlay / Modal / Window 材质层。
- 表格、输入框、正文卡片禁止依赖透明背景。
- 阴影不能替代边框，特别是深色主题。

## 字体与排版

Prism Design 继续使用现有 `Enums.typography` 与 `Enums.fontFamily`。不得为 Prism Design 单独创建字体系统。

| 场景 | 字号 token | 说明 |
|------|------------|------|
| Caption | `caption` | 辅助说明、标签 |
| Body | `body` | 默认控件文本 |
| Body Large | `bodyLarge` | 重要正文 |
| Subtitle | `subtitle` | 分组标题 |
| Title | `title` / `titleLarge` | 页面标题、卡片标题 |
| Display | `display` / `displayLarge` | 示例页大标题 |

排版规则：

- 控件内部不使用 hero 级字号。
- 按钮、输入框、菜单项文字必须垂直居中。
- 文本不能依靠负字距压缩。
- 单行控件内长文本必须截断或换行策略明确，不能溢出容器。

## 间距与密度

Prism Design 默认继承现有 `Enums.spacing`。后续若新增密度系统，应只新增 `comfortable` / `compact` 两档，不允许每个组件自定义密度。

默认建议：

| 场景 | 间距 |
|------|------|
| 控件内部左右 padding | `spacing.l` 起 |
| 紧凑图标与文字 | `spacing.s` / `spacing.m` |
| 卡片内部 | `spacing.xl` 起 |
| 页面 section 间 | `spacing.xxl` 起 |
| 表格行距 | 以可扫读为准，不追求移动端松散感 |

## 交互状态

### 通用状态

| 状态 | 必须表现 |
|------|----------|
| Normal | 明确边界或背景，不误判为禁用 |
| Hover | 使用 `hover` 或对应状态层 |
| Pressed | 使用 `pressed`，可轻微收敛阴影 |
| Focused | 2px focus ring / strong border，键盘可见 |
| Disabled | 前景与背景降低对比，但布局不变 |
| Selected | 使用 `selected`，并配合位置指示 |
| Error | 错误色 + 文本或图标，不只靠颜色 |

### 焦点规则

Prism Design 必须支持键盘可见焦点。输入框、按钮、菜单项、列表项、导航项、Tab 都必须能在键盘焦点下看出当前位置。

焦点不能只靠 hover 表达，也不能只改变鼠标光标。

## 动效

Prism Design 不建立新的动效体系，复用 `Enums.duration.*`。

| 场景 | 时长 | 规则 |
|------|------|------|
| Hover / Pressed | `fast` | 快速反馈 |
| Focus | `fast` / `normal` | 不能滞后输入 |
| Menu / Flyout | `normal` / `medium` | opacity + 小位移 |
| Dialog | `medium` / `dialog` | 进入清楚，退出干净 |
| Page | `page` | 只用于页面切换 |

动效规则：

- 禁止循环光效影响输入和滚动。
- 禁止大幅弹跳。
- 禁止 hover 时移动布局位置。
- 阴影动画必须短而克制。

## 组件规范

### Button

- Default：`raised` 背景 + `border` 边框。
- Primary：`primary` 背景 + `primaryForeground` 文本。
- Text / Hyperlink：默认透明，仅 hover / pressed 显示状态层。
- Filled semantic：保留语义色，不强行套 Prism 主色。
- Pressed：不能使用 neo 位移。
- Focused：必须有可见焦点边界。

### Input / ComboBox / SpinBox

- 默认背景使用 `raised`。
- 默认半径使用 `radiusControl`。
- Focused 使用 `primary` 或 `borderStrong`。
- Placeholder 使用次级前景色。
- Error 必须显示边框 + 辅助文本或图标。
- 禁止透明输入框作为默认样式。

### Toggle / CheckBox / Radio

- 勾选状态使用 `primary`。
- 未选中状态必须有清晰边框。
- Disabled 状态不能只降低 alpha 到不可见。
- Radio 内点、Check 勾号和 Switch thumb 必须在 light/dark 下清楚。

### Card / SettingCard / Panel

- 默认背景使用 `raised`。
- 默认半径使用 `radiusCard`。
- 可交互卡片 hover 使用 `hover`，不能大幅上跳。
- HeaderCard 分隔线使用 `divider`。
- 禁止卡片嵌套卡片。

### Navigation

- 当前项必须有位置指示，不只靠文字变色。
- 侧边栏可使用 `background` / `surface`，内容区使用 `surface`。
- NavigationBarItem 选中态使用 `selected` + `primary` 指示。
- 图标和文字必须共享同一状态逻辑。

### Menu / Flyout / Tooltip

- 背景使用 `overlay`。
- 半径使用 `radiusPopup`。
- 必须有边框或阴影明确分离。
- Tooltip 以文字可读性优先，不能用低透明背景。

### Dialog / MessageBox

- 背景使用 `overlay`。
- 半径使用 `radiusDialog`。
- Modal 必须有遮罩。
- 操作区必须和内容区分开。
- 主操作按钮使用 Primary，危险操作使用 error 语义，不使用 Prism 主色冒充危险。

### Table / List / Tree

- 表格背景使用 `tableBg`。
- 交替行使用 `alternateRow`。
- Hover 使用 `tableHover`。
- Selected 使用 `selected`，选中 hover 使用 `selectedHover`。
- 分隔线使用 `divider`。
- 数值正负、状态标签必须使用语义色，不使用主色。

### Toast / InfoBar / Notification

- Toast 使用 Overlay 层级。
- InfoBar 保留语义色主导，不被 Prism 主色覆盖。
- 通知文本必须在弹层背景上达到清晰可读。
- 关闭按钮 hover 不应破坏语义色区域。

### Progress / Skeleton / Loading

- Progress 激活色使用 `primary` 或语义色。
- Track 使用低对比状态层。
- Skeleton 使用低噪声 shimmer，不能比正文更抢眼。
- Loading 不得阻塞主线程动画。

### Chart

- Prism Design 不在第一阶段重定义完整图表色板。
- 图表色应后续独立进入 chart token。
- 坐标轴、网格线、tooltip 必须使用 Prism 的前景/边框/overlay token。
- 数据系列颜色不能只靠蓝青色一套。

### Icon

- 默认继续使用现有 Fluent icon 资产。
- Prism Design 不引入闭源图标资源。
- 图标颜色跟随 `textColor`、`accentColor` 或语义色。
- 图标按钮必须有 tooltip 或可理解上下文。

## 可访问性

必须满足：

- 所有交互控件有可见焦点。
- 不只依赖颜色表达状态。
- 禁用态仍能识别控件类型。
- 文本和背景对比足够阅读。
- Toast、Dialog、Menu 等弹层不能被背景干扰。
- 动效不能影响输入响应。

建议在 Gallery 中提供 light / dark 并排检查，至少覆盖按钮、输入、导航、表格、弹层、语义反馈。

## 性能边界

Prism Design 的视觉效果必须适合 QML 实时渲染。

禁止：

- 默认控件启用昂贵 blur。
- 列表、表格、树形每行使用复杂 shader。
- 大量实时 glow 或全屏动态渐变。
- hover 时触发重新布局。

允许：

- 使用 `RectangularShadow` 做矩形阴影。
- 使用静态 tint / 边框 / 状态层表达材质。
- 在少量高层弹层中使用轻量透明。

## 实现契约

### Token 流向

Prism Design 的实现应遵循：

```text
ThemeManager.skin
  -> Enums.skin / Enums.isPrismDesign
  -> Constants.prismDesign
  -> Theme / StateColor / textColor
  -> 控件绑定
```

组件优先读取通用 token，例如 `Enums.cardColor`、`Enums.stateColor.controlBg`、`Enums.textColor.primary`。只有几何或结构确实不同，才读取 `Enums.prismDesign.*`。

### 允许的组件分支

允许：

- `Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small`
- Prism Design 专属 focus ring 宽度
- Prism Design 专属 overlay 材质

不允许：

- 在组件里直接写 Prism Design hex 色值。
- 在组件里用多个 `if skin === "prism_design"` 拼出完整样式。
- 复制一份组件只给 Prism Design 使用。
- 为 Prism Design 引入和 `Enums` 平行的新主题入口。

## 当前实现状态

当前已落地：

- Python: `Skin.PRISM_DESIGN`
- QML: `Enums.isPrismDesign`
- QML: `Enums.prismDesign.*`
- Token: `Constants.prismDesign`
- 转发: `Theme` / `StateColor` / `textColor`
- 控件首批接入: Button / InputCore / ComboBoxCore / Card
- 示例页: 设置页皮肤下拉可选 Prism Design
- 测试: `tests/qml/test_prism_design_skin.py`

尚需按本文继续补齐：

- Gallery 三皮肤同屏对照。
- Navigation、Dialog、Flyout、Menu、Table/List 的逐项视觉调校。
- Chart 专属色板。
- Prism Design light/dark 截图验收。
- 全组件 focus / selected / error 状态验收。

## 验收标准

一个组件可标记为“符合 Prism Design”，必须同时满足：

- light / dark 都有正确视觉。
- normal / hover / pressed / focused / disabled 状态完整。
- 不硬编码 Prism Design 专属色值。
- 尺寸和布局在状态切换时不抖动。
- 文本、图标、边框在浅色和深色下均清晰。
- 与同类组件使用一致的 radius、border、surface、shadow。
- 能在 Gallery 中与 Fluent / Neobrutalism 并排比较。

## 变更流程

修改 Prism Design 视觉标准时必须同步做三件事：

1. 更新本文。
2. 更新 `Constants.prismDesign` 或对应 token。
3. 更新 Gallery / probe / 测试，证明变更生效。

如果只改组件、不改规范，视为未完成；如果只改规范、不验证真实控件，也视为未完成。
