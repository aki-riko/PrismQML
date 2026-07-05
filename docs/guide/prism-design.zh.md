# Prism Design 视觉规范

Prism Design 是 PrismQML 的自有设计语言，也是 `Skin.PRISM_DESIGN` 的唯一视觉标准来源。当前方向定义为 **Prism Glass**：参考 Liquid Glass 的层级、材质和动态原则，但不复刻 Apple 控件、图标、平台布局或系统行为。后续所有 Prism Design 组件、Gallery、示例和截图验收，都应以本文为准。

本文定义设计标准，不替代皮肤系统说明。皮肤切换 API、`Enums.skin`、`Enums.prismDesign` 等用法见 [皮肤系统](skins.zh.md)，组件矩阵、Gallery 验收和评审门禁见 [Prism Design 落地标准](prism-design-implementation.zh.md)。

## 规范状态

| 项 | 标准 |
|----|------|
| 皮肤名 | `Prism Design` |
| Python 枚举 | `Skin.PRISM_DESIGN` |
| QML 字符串 | `prism_design` |
| QML 判断 | `Enums.isPrismDesign` |
| Token 入口 | `Enums.prismDesign.*` |
| 当前方向 | `Prism Glass` |
| 规范等级 | 第三皮肤视觉口径的最高标准 |
| 实现进度 | 以 [Prism Design 落地标准](prism-design-implementation.zh.md)、Gallery 与测试记录为准 |

Prism Design 是规范，不是单个主题色。任何组件只要声明支持 `prism_design`，就必须同时满足本文的颜色、层级、状态、密度、动效和可访问性要求。

## 标准等级

本文使用以下等级描述规范强度：

| 等级 | 含义 |
|------|------|
| 必须 | 新增或调整 Prism Design 时不可违反，违反即不符合第三皮肤标准 |
| 应该 | 默认遵守，只有在组件语义明确冲突时才能例外 |
| 可以 | 可选能力，适合 Gallery、复杂业务界面或后续增强 |
| 禁止 | 不允许进入 Prism Design 组件、示例、Gallery 或截图验收 |

Prism Design 的标准范围覆盖：颜色、字体、图标、圆角、边框、阴影、材质、动效、布局密度、交互状态、语义反馈、图表、弹层、窗口和可访问性。实现细节可随 Qt/QML 能力演进，但视觉结果必须与本文一致。

## 设计人格

Prism Design 的人格是“棱镜玻璃工作台”：清透、有厚度、边缘带光，但仍然服务长期工作流。它应该让开发者工具、桌面应用、AI 工作流、数据看板和设置型界面看起来精致、轻盈、可靠，并且一眼能看出不是 Fluent 的换色版本。

它不是“玻璃拟态”，也不是“青绿色 Fluent”。Prism 的识别度来自三件事：功能层像玻璃一样浮在内容之上，边缘像棱镜一样折出细窄光谱，内容层始终保持清楚、稳定、可读。界面可以有光感，但不能让光感抢走信息。

## 与其它皮肤的边界

| 皮肤 | 视觉范式 | Prism Design 必须避开的相似点 |
|------|----------|--------------------------------|
| Fluent | 平台原生、Mica、柔和圆角、系统主色 | 不复刻 WinUI 控件比例，不依赖平台材质作为身份 |
| Neobrutalism | 粗黑边、硬阴影、高撞色、按压位移 | 不使用硬阴影，不让控件有纸片式压平位移 |
| Prism Design | Prism Glass、浮动功能层、棱镜光谱边、内容层稳定可读 | 不退化成单纯换色，也不把整页做成玻璃拟态 |

Prism Design 的独立性要靠整套规则体现：同一页面切到 Fluent、Neobrutalism、Prism Design 时，用户应能一眼看出第三套皮肤不是前两者的浅改。

## 设计定位

Prism Design 面向桌面生产力应用、开发者工具、AI 工具、数据看板和长期使用的业务界面。它的气质是清晰、冷静、精致、有层次，而不是营销页式的强装饰。

核心目标：

- 让 PrismQML 拥有不依赖外部平台的自有审美，建立 Prism Glass 作为第三皮肤的身份。
- 在 Fluent 的工程稳态和 Neobrutalism 的强辨识度之外，提供一条轻盈、通透、但仍适合桌面工具的路线。
- 让控件库适合真实应用，而不只是适合截图展示。
- 保持 token 驱动，使后续皮肤扩展不会把分支散落到每个控件里。

非目标：

- 不复刻 Apple Liquid Glass、Material、Fluent、Carbon 或其它外部设计语言。
- 不以全局毛玻璃、渐变背景、光晕堆叠作为主要风格；玻璃只属于功能层、弹层和少量激活控件。
- 不牺牲表格、输入、导航、弹层等高频控件的清晰度。
- 不为了“高级感”降低对比度、缩小点击区域或隐藏状态反馈。

## Liquid Glass 参考边界

Prism Glass 参考 Apple Liquid Glass 的方法论，而不是复制视觉结果。参考点只保留以下几类：

| 参考点 | Prism Glass 转译 | 禁止转译 |
|--------|------------------|----------|
| 功能层浮在内容层之上 | 导航、工具栏、菜单、弹层可使用 glass surface | 把正文、表格、卡片全部做成透明玻璃 |
| 材质会表达厚度 | 小控件薄、菜单和对话框更厚，阴影随层级增加 | 每个控件都套 blur 和 glow |
| 边缘光帮助识别形体 | 使用 `spectral edge` 表达 Prism 身份 | 大面积彩虹渐变、背景光球 |
| 内容保持主角 | 数据、文本、表单优先实心 surface | 为了通透降低文字可读性 |
| 适配可访问性 | Reduced Transparency / Increased Contrast 有等价策略 | 只做透明效果，不做降级样式 |

参考资料：

- [Apple Human Interface Guidelines: Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Apple Developer: Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/liquid-glass)
- [WWDC25: Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/)

## 设计原则

### 清晰优先

文字、图标、边界和焦点状态必须永远可见。任何材质、阴影、透明度、渐变和高光都不能压过信息本身。

### 层级可解释

界面必须能被解释为稳定层级：背景、内容面、卡片、浮层、模态层。层级差异来自 token，而不是每个组件临时调色。

### 功能层玻璃

玻璃不是背景装饰，而是交互功能层。导航、工具栏、菜单、Toast、Flyout、Dialog、Slider thumb、Toggle thumb 这类“控制界面行为”的元素可以有 glass surface；正文、表格、列表、输入正文区默认保持实心或近似实心。

### 棱镜边缘

Prism 的自有元素来自边缘，而不是大色块。主色和光谱色优先出现在焦点环、当前项边、弹层高光、进度端点、hover 内发光上。任何光感都必须短、细、贴边。

### 桌面密度

默认密度服务桌面工具：控件尺寸不夸张，信息密度适中，布局可扫读。移动端舒适感不是首要目标。

### 状态完整

所有可交互组件必须覆盖 normal、hover、pressed、focused、disabled、selected。输入类和校验类组件还必须覆盖 error / warning / success。

### Token 先行

所有可复用颜色、几何、阴影、透明度和时长必须进入 `Enums` 或皮肤 token。组件内禁止直接散写 Prism Design 专属值。

### 可扫读

Prism Design 默认服务长期工作流。列表、表格、菜单、命令栏和设置项应该在密集信息下仍然能快速扫读，而不是为了展示效果牺牲密度。

### 可验证

每条视觉规则都必须能在 token、组件状态、Gallery 或截图中找到证据。只存在于口头描述、无法被控件证明的规则，不算落地。

## 视觉关键词

| 关键词 | 含义 | 落地方式 |
|--------|------|----------|
| Clarity 清晰 | 信息优先 | 高可读文字、明确边界、可见焦点 |
| Liquid 液态 | 控制层轻盈、可响应 | hover / pressed 使用内发光和轻微厚度变化 |
| Glass 玻璃 | 功能层漂浮但可读 | overlay、toolbar、menu 使用 glass surface |
| Prism 棱镜 | 自有识别 | 光谱边、斜向高光、少量冷暖色分离 |
| Layered 层次 | 界面有深度 | 内容层稳定、功能层浮起、模态层压住 |
| Calm 冷静 | 不抢业务内容 | 低噪声背景、克制动效、中性色为主 |
| Precise 精确 | 工具感明确 | 稳定尺寸、对齐、状态不跳动 |

## 视觉配方

Prism Design 的页面应由以下元素组合，而不是依赖单一装饰手段：

| 元素 | 建议占比 | 作用 |
|------|----------|------|
| 内容实心 surface | 65% 以上 | 承载信息，保证长期阅读舒适 |
| 玻璃功能层 | 10% - 20% | 承载导航、工具、浮层和激活控件 |
| 状态层 | 10% - 15% | 表达 hover、pressed、selected、focus |
| 光谱强调 | 3% - 8% | 标记主操作、当前项、焦点和关键数据 |
| 语义色 | 按需 | 表达成功、警告、错误、处理中 |
| 阴影与折射 | 少量 | 辅助层级，不成为主要内容 |

如果一个界面看起来主要由渐变、glow 或高饱和色块构成，它就偏离了 Prism Design。Prism Glass 的第一眼应该是“清透的工具界面”，不是“效果图背景”。

## 层级系统

Prism Design 的层级是界面组织的第一规则。颜色、阴影、边框和透明度都必须服务于层级。

| 层级 | 用途 | 视觉要求 | 当前 token |
|------|------|----------|------------|
| Base | 应用外层背景、窗口底色 | 最低对比，承载留白和内容画布 | `background` |
| Content Surface | 主内容区、页面主体、表格、表单 | 低噪声、近实心、可长时间阅读 | `surface` |
| Crystal Surface | 卡片、按钮、输入框、设置项 | 轻微通透感，边界清楚 | `raised` |
| Glass Rail | 导航、工具栏、命令面、激活控件 | 浮在内容之上，可见厚度和边缘光 | `overlay` + spectral edge |
| Floating Glass | Menu、Flyout、Tooltip、Toast | 临时浮层，和内容明显分离 | `overlay` |
| Modal Glass | Dialog、MessageBox、遮罩层 | 最高注意层，必须压住背景 | `overlay` + shadow + scrim |

层级判定规则：

- Base 只承载全局背景和窗口外层，不能放置主要文本段落。
- Content Surface 是工作区，长文本、表格和编辑器应优先落在这里。
- Crystal Surface 是可操作或可聚焦对象，必须有清楚边界。
- Glass Rail 是功能层，主要用于导航、工具栏、命令面和激活控件。
- Floating Glass 是临时内容，关闭后不改变页面结构。
- Modal Glass 会阻断当前流程，必须提供遮罩、焦点闭环和明确操作区。

禁止事项：

- 禁止把整页大 section 都做成浮卡，除非它本身是一个独立工具面板。
- 禁止卡片套卡片制造层级。
- 禁止用大面积渐变、全局玻璃或背景光晕代替 surface 层级。
- 禁止弹层透明到看不清后方与前景边界。

## 颜色系统

### 基础色

当前 `Constants.prismDesign` 的基础色如下，后续调整必须同步更新本文。现有色板是 Prism Glass 的过渡基线：它保证 light / dark 可读，但下一阶段应让 `overlay`、`raised`、`hover`、`selected` 更接近玻璃厚度，而不是继续像普通实心面板。

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `background` | `#EEF3F2` | `#0D1213` | 应用外层背景 |
| `surface` | `#F8FAF9` | `#12191B` | 主内容面 |
| `raised` | `#FCFEFD` | `#192224` | 控件、卡片、面板 |
| `overlay` | `#F4F8F7` | `#1F2A2D` | 弹层、菜单、对话框 |
| `header` | `#E6ECEB` | `#101719` | 顶栏、分组头 |
| `tableBg` | `#F5F8F7` | `#0F1517` | 表格背景 |
| `alternateRow` | `#F1F5F4` | `#151D1F` | 交替行 |

### 前景色

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `foreground` | `#152326` | `#EEF5F3` | 主文本、主图标 |
| `secondaryForeground` | `#566A6D` | `#A4B5B6` | 次级文本、说明 |
| `tertiaryForeground` | `#7A8D90` | `#718687` | 弱说明、辅助信息 |
| `disabledForeground` | `#A4B0B1` | `#53676A` | 禁用文本 |

文字必须优先使用 `Enums.textColor.*`，不要直接读取颜色 token。只有设计 token 调试、视觉测试和文档示例可以直接提及色值。

### 强调色

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `primary` | `#167C80` | `#55D6D2` | 主操作、选中态、焦点 |
| `primaryLight` | `#1C8D90` | `#74E6E1` | hover 派生 |
| `primaryDark` | `#0E5F64` | `#38BDBA` | pressed 派生 |
| `primaryForeground` | `#FFFFFF` | `#061718` | 主色块上的文字 |
| `secondary` | `#516B9A` | `#92A7FF` | 次强调、辅助信息倾向 |
| `warm` | `#C47A25` | `#F0B35D` | 提醒、局部暖色 |
| `glow` | `#88DCD8` | `#3BDCD6` | 局部冷光，不承载文字 |

使用规则：

- 主操作按钮、当前导航项、输入焦点优先使用 `primary`。
- `secondary` 只用于辅助强调，不能和成功色混用。
- `warm` 用于注意和提示，不替代 warning 语义色。
- `glow` 只能做棱镜边、焦点 halo 和视觉辅助，禁止把文本放在 glow 背景上。
- 主色禁止变成大面积 tint；Prism Glass 的身份优先来自边缘光谱，而不是整块青绿色背景。

### 边框与分隔

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `border` | `#C7D4D3` | `#2A393B` | 默认控件边框 |
| `borderLight` | `#DDE6E4` | `#223033` | 弱边界、内部分隔 |
| `borderStrong` | `#8EA4A3` | `#496063` | 焦点、强调边界 |
| `divider` | `#D5DFDD` | `#253437` | 列表、表格、分组分隔 |

边框不是装饰，而是玻璃厚度、层级和可点击区域的提示。浅色模式不能让边框消失，深色模式不能只靠阴影分层。

Prism Glass 的边框分为三类：

| 类型 | 用途 | 视觉要求 |
|------|------|----------|
| Hairline | 内容分隔、表格网格、菜单分隔 | 低对比，不能像控件描边 |
| Glass Rim | 按钮、输入、卡片、导航项 | 1px 边缘，有轻微内外明暗差 |
| Spectral Edge | 当前项、焦点、主操作、弹层高光 | 只出现在一条边或局部角，不包围整块大面积发光 |

### 状态层

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `hover` | `#E6EEED` | `#1D292B` | 悬停 |
| `pressed` | `#DCE7E5` | `#182426` | 按下 |
| `disabled` | `#E3E9E8` | `#1A2224` | 禁用背景 |
| `selected` | `#D4EDEA` | `#163F43` | 选中 |
| `selectedHover` | `#C3E4E0` | `#1B5055` | 选中悬停 |
| `navSelected` | `#F6FAF9` | `#141D1F` | 导航选中中性面 |
| `navSelectedHover` | `#EDF4F2` | `#192629` | 导航选中悬停 |
| `tableHover` | `#E9F0EF` | `#1A2729` | 表格/列表悬停 |

状态层必须有可见差异，但不能让组件尺寸变化。hover、pressed、selected 禁止通过改变文字大小、边距、布局来表达。Prism Glass 的 hover 应像玻璃被点亮，pressed 应像厚度收紧，selected 应有位置或边缘指示。

### 滚动条与透明状态

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `scrollTrack` | `#E1E9E7` | `#101719` | 滚动条轨道 |
| `scrollHandle` | `#8EA4A3` | `#435A5D` | 滚动条手柄 |
| `scrollHandleHover` | `#758D8B` | `#587174` | 手柄悬停 |
| `transparentHover` | `#E7EFEE` | `#1B2729` | 透明按钮、图标按钮 hover |
| `transparentPressed` | `#D9E5E3` | `#172225` | 透明按钮、图标按钮 pressed |

透明状态只用于 TextButton、IconButton、工具栏按钮、菜单触发器等本身不应有实心底的控件。输入框、表格行、卡片和弹层默认不使用透明状态作为正常背景。Glass Rail 可以使用透明状态，但必须有边界和可读前景。

### 语义色

Prism Design 继续使用 `Enums.statusLevel` 和 `Enums.getColorByLevel()` 作为语义色入口。语义色表达业务含义，优先级高于 Prism 主色。

| 语义 | 应用场景 | 规则 |
|------|----------|------|
| Info | 信息提示、说明、普通通知 | 可使用中性或信息色，不等于主操作色 |
| Success | 成功、完成、可用 | 不与 `secondary` 混用 |
| Warning | 警告、风险、需要注意 | 不用 `warm` 替代；`warm` 只是视觉辅助强调 |
| Error | 错误、危险、删除、失败 | 必须配合文本或图标，不只靠颜色 |
| Processing | 处理中、同步中 | 可用于进度、等待、后台任务 |

禁止把所有 InfoBar、Toast、Badge 都染成 `primary`。主色表达“当前/主操作”，语义色表达“业务状态”，二者不能混淆。

### 图表色板

Prism Design 已提供独立图表色板，数据系列颜色必须通过 `Enums.chartColors.palette` 或后续 chart token 获取。

| 序号 | Light | Dark |
|------|-------|------|
| 1 | `#167C80` | `#55D6D2` |
| 2 | `#516B9A` | `#92A7FF` |
| 3 | `#C47A25` | `#F0B35D` |
| 4 | `#C64754` | `#FF8F9A` |
| 5 | `#7B5CB8` | `#BBA4FF` |
| 6 | `#0099A8` | `#5CD7E6` |
| 7 | `#6F8F2E` | `#A6C96B` |
| 8 | `#A65A82` | `#E99BC1` |
| 9 | `#2F7A5C` | `#77C79D` |
| 10 | `#8A6E4E` | `#D2B486` |

图表规则：

- 坐标轴文字使用 `Enums.chartColors.axisLabel`。
- 网格线使用 `Enums.chartColors.gridLine`。
- Tooltip 使用 Overlay 层级，背景、边框、文字必须接入 Prism token。
- 正负值、成功失败等业务语义优先使用语义色，不强行套数据序列色。
- 数据系列不能只靠蓝青相邻色区分，至少保证前 6 个序列有明显色相差异。

### 色彩禁区

禁止以下做法：

- 大面积紫蓝渐变、全屏光晕或背景装饰球。
- 在正文 surface 上使用低透明玻璃导致文字对比不足。
- 用 `glow`、`warm`、`secondary` 直接承载正文文字。
- 在组件内硬编码 Prism 专属 hex。
- 为了暗色“高级感”把边框和分隔线降到不可见。

## 几何系统

下表记录当前运行时 token，必须与 `Constants.prismDesign` 保持同步。它仍保留上一版硬边基线，后续实现 Prism Glass 时应同步调整代码、测试、Gallery 和本文。

| Token | 值 | 用途 |
|-------|----|------|
| `radiusControl` | 2 | Button、Input、ComboBox、菜单项 |
| `radiusCard` | 4 | Card、Panel、SettingCard |
| `radiusPopup` | 6 | Menu、Flyout、Tooltip、Toast |
| `radiusDialog` | 8 | Dialog、MessageBox |
| `borderWidth` | 1 | 默认边框 |
| `focusBorderWidth` | 2 | 键盘焦点、输入焦点 |

几何规则：

- 默认控件不能无条件做大药丸，除非现有 API 明确选择 `shape_pill`。
- Prism Glass 的目标形态应比当前硬边基线更圆润：基础控件约 8px - 12px，卡片约 12px - 16px，弹层约 16px - 20px，对话框约 20px - 28px。真正改实现时必须同步更新 token 表和运行时测试。
- 圆角必须稳定，不因 hover / pressed 改变。
- 点击区域至少保持现有 PrismQML 控件尺寸，不因视觉变薄而缩小。
- 圆角应遵守同心关系：内部控件圆角小于承载它的容器，边距和圆角看起来来自同一几何中心。
- 当前项、弹层、工具栏这类 Glass Rail 可以更圆；表格、列表、代码块、数据面板仍保持更克制的半径。

### 尺寸基线

Prism Design 不单独建立尺寸系统，默认继承 `Enums.controlSize`。视觉调校时应遵守：

| 场景 | 基线 | 规则 |
|------|------|------|
| 普通输入和按钮 | `inputHeight` / 32px 级别 | 桌面工具默认密度，不做移动端大按钮 |
| 大输入和主操作 | `inputHeightLarge` / 40px 级别 | 只用于表单重点项、设置页主操作 |
| 紧凑控件 | `inputHeightCompact` / 28px 级别 | 只用于工具栏、表格内编辑、密集面板 |
| 导航项 | 现有 nav token | 选中指示必须稳定，不改变宽高 |
| 图标按钮 | 32px - 40px | 图标居中，hover 背景不改变布局 |

控件状态变化不得改变外部尺寸、锚点、布局间距、字号或图标大小。视觉反馈只能通过颜色、边框、阴影、透明度或轻微内容内变化表达。

## 阴影与材质

Prism Design 使用“玻璃厚度 + 边缘高光 + 克制阴影”表达层级，不使用 Neobrutalism 的硬阴影，也不依赖 Fluent 式柔软浮起作为主要身份。阴影负责空间，边缘负责材质，透明度负责轻盈；三者不能互相替代。

| 层级 | 用途 | 阴影策略 |
|------|------|----------|
| Level 2 | 普通卡片、按钮 hover | 很轻，只提示可交互，边框仍是主边界 |
| Level 4 | Toast、Dropdown、浮动工具条 | 可见浮起，不能盖过边框 |
| Level 8 | Menu、Flyout、Tooltip | 与内容明显分离，优先靠边界和 surface |
| Level 16 | Dialog、Modal | 强阴影 + 遮罩，仅用于阻断流程 |

边缘阴影 token：

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `edgeShadow` | `#10102326` | `#33000000` | 粘性表头、滚动边缘、浮动分隔的短距离渐隐阴影 |

材质规则：

- Content Surface 必须近似实心，保证正文、表格、代码和输入内容可读。
- 透明和 blur 只能用于 Glass Rail / Floating Glass / Modal Glass / Window 材质层。
- 表格、输入框正文区、代码块、长列表禁止依赖透明背景。
- 阴影不能替代边框，特别是深色主题。
- 玻璃效果必须有降级路径：关闭透明或弱化动态时，组件仍能通过实心 surface、边框和状态层表达层级。

### 材质策略

| 材质 | 使用范围 | 禁止范围 |
|------|----------|----------|
| Solid Surface | 正文、表格、代码、长列表、表单内容 | 无 |
| Crystal Surface | 卡片、按钮、输入框、设置项 | 数据密集行项目 |
| Glass Rail | 导航、工具栏、命令栏、激活控件 | 正文和表格主体 |
| Floating Glass | Menu、Flyout、Tooltip、Toast | 长文本阅读区 |
| Modal Glass | Dialog、MessageBox、遮罩层 | 非阻断普通卡片 |
| Spectral Edge | 当前项、焦点、主操作、进度端点 | 装饰性重复描边 |
| Soft Shadow | 弹层、对话框、少量浮动工具条 | 表格每行、列表每项 |

Prism Design 的“光感”应被控制在边缘、状态和少量高层组件里。默认页面看起来应该清楚、安静、可工作，而不是像一张效果图。

### Glass Token 目标

后续实现时应把下列语义收敛为 token，而不是散落到组件里：

| 语义 | 作用 | 典型用途 |
|------|------|----------|
| `glassOpacity` | 玻璃层不透明度 | Glass Rail、Floating Glass |
| `glassTint` | 玻璃底色 | overlay 派生、toolbar |
| `glassRimLight` | 上/左侧高光边 | Button、Card、Menu |
| `glassRimShadow` | 下/右侧暗边 | Button pressed、Dialog |
| `spectralEdge` | 棱镜光谱边 | Focus、selected、primary action |
| `refractionHighlight` | 折射高光 | Slider thumb、Toggle thumb、Gallery 展示 |

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

### 文本层级

| 层级 | 用途 | 颜色 |
|------|------|------|
| Primary | 标题、正文、控件主文本 | `Enums.textColor.primary` |
| Secondary | 描述、placeholder、metadata | `Enums.textColor.secondary` |
| Tertiary | 弱提示、时间戳、低频辅助 | `Enums.textColor.tertiary` |
| Disabled | 禁用文字 | `Enums.textColor.disabled` |
| On Accent | 主色按钮文字 | `Enums.accentForeground` 或 `Enums.prismDesign.primaryForeground` |

页面标题不能承担产品营销文案角色。PrismQML 是组件框架，示例和 Gallery 的文字应短、准确、可扫读。

## 图标与符号

Prism Design 继续使用 PrismQML 现有图标资产，不引入闭源图标库。图标不是装饰贴纸，而是命令和状态的可识别符号。

| 场景 | 规则 |
|------|------|
| 普通图标 | 跟随 `Enums.textColor.secondary` 或当前文本色 |
| 主操作图标 | 跟随 `Enums.accentColor` 或主按钮前景 |
| 语义图标 | 跟随对应 `StatusLevel` 语义色 |
| 禁用图标 | 跟随 `Enums.textColor.disabled` |
| 图标按钮 | 必须有 hover / pressed 状态层，必要时提供 tooltip |

禁止使用图标替代必要文字，除非控件语义在上下文中高度明确，例如窗口关闭、返回、搜索、设置、刷新。

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

布局规则：

- 页面应优先使用清楚的栏、区段和列表，而不是大量孤立浮卡。
- 真实应用页的第一屏必须呈现可操作内容，不做营销式 hero。
- 工具栏、命令栏、筛选栏应靠近其影响的内容。
- 表格、树、列表的横向对齐必须稳定，状态变化不得造成列宽抖动。
- Gallery 可以更展示化，但仍必须展示真实控件状态。

### 密度等级

| 密度 | 使用场景 | 特征 |
|------|----------|------|
| Compact | 表格、开发工具、命令栏、属性面板 | 较小高度、信息密集、状态仍清晰 |
| Default | 默认控件、设置页、普通表单 | 32px - 40px 控件高度，阅读和效率平衡 |
| Comfortable | Gallery、空态、登录页、确认对话 | 更大留白，但不进入移动端大控件范式 |

同一组件族内部必须保持密度一致。不能让 Button 是 comfortable，Input 是 compact，Menu 又是另一套比例。

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

### 状态优先级

当多个状态同时存在时，按以下优先级决定视觉：

```text
disabled > error > pressed > focused > selected > hover > normal
```

说明：

- Disabled 最高，禁用控件不响应 hover / pressed。
- Error 高于 focus，输入框聚焦时仍必须看得出错误。
- Pressed 高于 focused 和 selected，但释放后应回到 focused / selected。
- Selected 高于 hover；选中项 hover 应使用 `selectedHover`。
- Focused 不能被 hover 完全覆盖，键盘用户必须知道当前位置。

### 状态表现矩阵

| 组件族 | Normal | Hover | Pressed | Focused | Disabled | Selected / Checked | Error |
|--------|--------|-------|---------|---------|----------|--------------------|-------|
| Button | 背景 + 边框 | 状态层 | pressed 层 | focus ring | 低强调 | primary / semantic | 仅危险按钮使用 error |
| Input | raised + 边框 | 边框/背景增强 | 无布局变化 | strong border | 禁用前景 | filled / readonly | error border + 文本/图标 |
| MenuItem | 透明或 overlay | hover 层 | pressed 层 | focus 背景 | 降低文本 | checked 指示 | 不适用 |
| Navigation | 默认文本/图标 | hover 层 | pressed 层 | focus ring | 降低强调 | selected + 位置指示 | 不适用 |
| List / Table | 行背景 | tableHover | pressed | focus row | 禁用行 | selected / selectedHover | 单元格语义 |
| Toggle | 未选边框 | hover 边框 | pressed | focus ring | 禁用 | primary checked | 不适用 |

状态验收不能只看鼠标 hover。至少要在 Gallery 或 probe 样例中展示 keyboard focus、disabled、selected、error。

## 动效

Prism Design 不建立新的动效体系，复用 `Enums.duration.*`。Prism Glass 的动效重点是“材质响应”，不是舞台动画：hover 像玻璃被照亮，pressed 像厚度被压低，弹层像轻玻璃片进入视野。

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

动效偏好：

- 状态变化以颜色、透明度、边框、阴影和局部 rim light 为主。
- 弹层进入可以使用 opacity + 4px 以内位移。
- 对话框进入可以有轻微 scale，但不能超过可感知的“弹窗感”。
- 列表批量出现可用轻微 stagger，但数据密集页面默认不做华丽入场。
- 遵守系统减少动画偏好；无法读取系统偏好时，也不要让循环动画成为默认视觉中心。

## 组件规范

### Window / App Shell

- 窗口外层使用 `background`，主工作区使用 `surface`。
- 标题栏、导航栏、状态栏可以作为 Glass Rail，但必须和内容面有可见边界。
- NavigationWindow 的侧栏应像浮在内容旁的玻璃轨道，内容区必须更接近 Content Surface。
- 透明窗口、Mica、Acrylic 只能作为平台增强；Prism Design 的必要身份来自 Prism Glass token，不来自系统材质。
- StatusBar 使用次级文本和 divider，不抢主内容注意力。

### Button

| 类型 | 背景 | 边框 | 文本 | 状态要求 |
|------|------|------|------|----------|
| Default | `raised` / Crystal Surface | `border` + rim | `textColor.primary` | hover / pressed 可见 |
| Primary | `primary` 或 spectral surface | `primaryDark` / spectral edge | `primaryForeground` | 主操作唯一或少量 |
| Text | 透明 | 透明 | `textColor.primary` | hover / pressed 用透明状态层 |
| Hyperlink | 透明 | 透明 | `accentColor` | hover 可下划线或状态层 |
| Semantic | 语义色 | 语义深色 | on semantic | 危险、成功等业务行为 |

按钮规则：

- Pressed 不能使用 Neobrutalism 的位移压平。
- Loading 状态保持宽高不变。
- 图标和文字间距稳定，不能因状态变化跳动。
- 同一区域只能有一个默认主按钮；多个主要动作必须用层级区分。
- Default 按钮应有轻微玻璃厚度，不能像 Fluent 的灰色圆角按钮。
- Primary 按钮可以更明亮，但不能把一整组按钮都染成青绿色。

### Input / ComboBox / SpinBox / Picker

- 默认背景使用 `raised` 或 Crystal Surface，默认半径使用 `radiusControl`。
- Placeholder 使用 `textColor.tertiary` 或 `textColor.secondary`。
- Focused 使用 `primary` 或 `borderStrong`，边框宽度可升到 `focusBorderWidth`。
- Error 必须显示错误边框，并配合辅助文本或图标。
- ComboBox / DateTimePicker / ColorPicker 的弹层使用 Floating Glass、`overlay` 与 `radiusPopup`。
- SpinBox 的加减按钮、Picker 的导航按钮必须和输入框共享 hover / pressed 逻辑。
- 禁止透明输入框作为默认样式；透明输入只允许在明确的搜索栏或工具栏变体中使用。

### Toggle / CheckBox / Radio / Slider / Rating

- Checked 状态使用 `primary`，unchecked 状态必须有清晰边框。
- ToggleSwitch 的 track、thumb、checked track 在 light/dark 下都要清楚。
- CheckBox 勾号、Radio 内点、Slider thumb 不能只靠低透明度表达。
- Slider track 的已完成段使用 `accentColor` 或语义色，未完成段使用低对比 track。
- Rating 默认使用 `starColor` 或语义提示色，不应被 Prism 主色完全替代。
- Disabled 状态保留控件形状，不得弱化到不可识别。

### Card / SettingCard / Panel

- 默认背景使用 `raised` 或 Crystal Surface，半径使用 `radiusCard`。
- 静态卡片使用弱边框和轻 rim，可交互卡片 hover 使用 `hover`、rim light 或 level2 阴影。
- SettingCard 必须保留标题、说明、控件区的阅读层级。
- HeaderCard / GroupBox / Expander 使用 `divider` 分隔头部和内容。
- 禁止卡片套卡片制造层级；需要嵌套时内层改用 section、列表项或弱分隔。

### Navigation / Tabs / Pagination

- 当前项必须有位置指示，不只靠文字变色。
- 侧边栏/顶栏导航选中使用 `navSelected` + spectral edge，避免大面积主色 tint。
- 列表、表格、分段控件等内容选择仍使用 `selected` / `selectedHover`。
- Tab、Pivot、SegmentedControl 必须有明确当前项边界。
- Paginator / PipsPager 的当前页使用 `primary` 或强边界，disabled 页码可识别。
- 图标和文字必须共享同一状态逻辑。
- 折叠导航不能丢失当前项指示。

### Menu / Flyout / Tooltip / Command Surface

- 背景使用 Floating Glass、`overlay`，半径使用 `radiusPopup`。
- 必须有 glass rim、边框或阴影与页面分离；复杂背景上优先边框 + 阴影同时存在。
- 菜单项 hover / pressed / focused 必须可见，快捷键文字使用次级前景。
- Tooltip 以文字可读性优先，不能使用低透明背景导致不清楚。
- FlyoutSheet、TeachingTip 必须有明确锚点或关闭方式。
- CommandBar 是 Prism Glass 的重点组件：图标按钮使用透明状态层和 rim light，不使用实心卡片堆叠。

### Dialog / MessageBox / Masked Surface

- 对话框背景使用 Modal Glass、`overlay`，半径使用 `radiusDialog`。
- Modal 必须有遮罩，并建立焦点闭环。
- 标题区、内容区、操作区必须层级清楚。
- 主操作按钮使用 Primary，取消按钮使用 Default 或 Text。
- 危险操作使用 error 语义，不使用 Prism 主色冒充危险。
- ProgressDialog 必须同时显示进度语义和可读说明。
- ImageCropperDialog、ColorPickerDialog 这类工具对话框必须清楚区分工具区、预览区和操作区。

### Table / List / Tree / Data Dense

- 表格背景使用 `tableBg`，交替行使用 `alternateRow`。
- Hover 使用 `tableHover`，Selected 使用 `selected`，选中 hover 使用 `selectedHover`。
- 分隔线使用 `divider`，不能重到像卡片边框。
- 列表项必须有稳定高度，图标、标题、说明、右侧操作对齐一致。
- Tree 展开指示、缩进和选中态必须在深色下清楚。
- 数值正负、状态标签、任务状态必须使用语义色，不使用主色。
- 数据密集组件禁止每行复杂阴影、blur 或实时 glow。

### Badge / Tag / Chip / Label

- Badge 表达数量或状态，尺寸紧凑，不能像按钮。
- Tag / Chip 使用 `surface` 或低对比状态层，checked 状态使用 `primary` 或 selected。
- 可关闭 Chip 的关闭按钮必须有独立 hover / pressed。
- Label 默认跟随文本层级，语义 Label 使用 StatusLevel。
- Watermark、Marquee 等弱提示不得压过正文内容。

### Toast / InfoBar / Notification

- Toast 使用 Floating Glass 层级，背景 `overlay`，半径 `radiusPopup`。
- InfoBar 保留语义色主导，不被 Prism 主色覆盖。
- DesktopNotification 必须在深色和浅色下保持边界、标题、正文、操作按钮清楚。
- 关闭按钮 hover 不应破坏语义色区域。
- 通知动画进入和退出必须短促，不阻塞主线程。

### Progress / Skeleton / Loading / State

- Progress 激活色使用 `primary` 或语义色，track 使用低对比状态层。
- Indeterminate 动画不能比正文更抢眼。
- Skeleton 使用低噪声 shimmer，深色下 shimmer 不应刺眼。
- EmptyState、ResultState、OfflineState 使用语义图标 + 标题 + 说明 + 操作按钮的层级。
- Loading 不得阻塞主线程动画，不得造成布局跳动。
- SplashScreen 使用 `background`、`primary` 和 `Enums.splashScreenMetrics`，启动层应安静、居中、短促，可以有细微棱镜边，但不使用大面积 glow 或复杂材质。
- Confetti 默认以 `accentColor` 与 `confettiColors.palette` 组合，作为完成/庆祝反馈使用，不得变成持续高噪声背景特效。

### Chart / Gauge / Indicator

- 数据系列使用 `Enums.chartColors.palette`。
- 轴标签使用 `Enums.chartColors.axisLabel`，网格线使用 `Enums.chartColors.gridLine`。
- Tooltip / MultiTooltip 使用 Floating Glass、`overlay`、`border`、`radiusPopup`。
- Legend、DataZoom、IndicatorBar 必须使用同一套 hover / selected / disabled 逻辑。
- IndicatorBar 非激活渐变端点透明度使用 `Enums.stateColor.indicatorInactiveGradientAlpha`，组件内不得散写 alpha。
- CircularGauge 的 track、value、label 在 light/dark 下必须可读。
- 图表空态、加载态、无数据态必须使用 State 组件语义，不留空白画布。

### Media / Avatar / QRCode / Image

- Avatar 有明确边界，选中或在线状态使用语义色或 `primary` 指示。
- ImageWidget placeholder 使用 Surface / Raised，不使用纯黑或纯白硬块。
- QRCode 默认保持高对比，不应用低透明或复杂渐变背景。
- AudioWaveform 使用主色或语义色表达活跃段，背景轨道使用低对比状态层。

### Icon / Effect / Code / Chat / Auth

- 图标颜色跟随 `textColor`、`accentColor` 或语义色。
- Prism Design 不引入闭源图标资源。
- Effect 组件必须遵守阴影与性能边界。
- CodeBlock 使用清楚边框、surface 和等宽字体，不做低对比暗块。
- ChatBubble 使用左右/角色层级区分，不能只靠颜色。
- LoginWindow 应体现 Prism Design 的窗口、输入、按钮和错误提示标准。

## 可访问性

必须满足：

- 所有交互控件有可见焦点。
- 不只依赖颜色表达状态。
- 禁用态仍能识别控件类型。
- 文本和背景对比足够阅读。
- Toast、Dialog、Menu 等弹层不能被背景干扰。
- 动效不能影响输入响应。

建议在 Gallery 中提供 light / dark 并排检查，至少覆盖按钮、输入、导航、表格、弹层、语义反馈。

### 可访问性细则

| 项 | 标准 |
|----|------|
| 键盘焦点 | 所有可交互控件必须有可见 focus ring 或 strong border |
| 颜色依赖 | 错误、警告、成功、选中不能只靠颜色表达 |
| 文字对比 | 正文、按钮、菜单、Tooltip 在 light/dark 下必须清楚 |
| 图标含义 | 关键图标按钮应有 tooltip、文本标签或上下文 |
| 弹层焦点 | Dialog 和 Menu 应形成可理解的焦点路径 |
| 动效安全 | 不做频闪、无限强闪烁和大幅循环位移 |

Prism Design 可以精致，但不能用“低对比高级灰”牺牲可读性。

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

性能判断：

- 一页中重复出现 20 次以上的元素默认不使用复杂 shader。
- 列表、表格、树形、聊天消息等可滚动重复项优先使用纯色、边框和轻状态层。
- 阴影层级越高，出现数量越少；Dialog 可以 level16，列表项不可以。
- Gallery 可以展示效果上限，但真实控件默认值必须适合生产环境。

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

## 规范治理

本文描述目标标准，不记录阶段性完成度。实现进度、组件矩阵、Gallery 截图、测试结果和剩余缺口统一记录在 [Prism Design 落地标准](prism-design-implementation.zh.md)、提交说明或 PR 描述中。

当文档、token 和控件表现冲突时，按以下方式处理：

| 冲突 | 处理方式 |
|------|----------|
| 文档与 token 不一致 | 先判断是标准变更还是 token 漏改，再同步两边 |
| token 与组件不一致 | 组件应改为读取正确 token，除非标准明确改变 |
| light 与 dark 只有一端达标 | 不算符合 Prism Design |
| Gallery 与真实控件不一致 | 以真实控件修复为先，Gallery 跟进 |
| 视觉效果和性能冲突 | 生产控件优先性能，Gallery 可展示增强效果 |

Prism Design 的标准变更必须留下证据：文档、token、组件、Gallery/测试至少有两类同步更新。只改口径不改证据，或只改组件不改口径，都不算完成。

## 验收标准

一个组件可标记为“符合 Prism Design”，必须同时满足：

- light / dark 都有正确视觉。
- normal / hover / pressed / focused / disabled 状态完整。
- 不硬编码 Prism Design 专属色值。
- 尺寸和布局在状态切换时不抖动。
- 文本、图标、边框在浅色和深色下均清晰。
- 与同类组件使用一致的 radius、border、surface、shadow。
- 能在 Gallery 中与 Fluent / Neobrutalism 并排比较。

### Gallery 验收

Gallery 必须证明 Prism Design 是一套完整皮肤，而不是色板样张。

| 视图 | 必须展示 |
|------|----------|
| Token Board | 色彩、层级、状态层、圆角、阴影 |
| State Wall | normal / hover / pressed / focused / disabled / selected / error |
| Component Matrix | 按钮、输入、导航、卡片、菜单、弹层、表格 |
| Three Skin Compare | Fluent / Neobrutalism / Prism Design 同一界面对照 |
| Real App Surface | 接近真实生产力界面的组合页面 |
| Dark Audit | 深色下的输入、表格、弹层、语义反馈 |

截图必须包含 light 和 dark。只展示浅色单按钮，不足以证明符合 Prism Design。

## 变更流程

修改 Prism Design 视觉标准时必须同步做三件事：

1. 更新本文。
2. 更新 `Constants.prismDesign` 或对应 token。
3. 更新 Gallery / probe / 测试，证明变更生效。

如果只改组件、不改规范，视为未完成；如果只改规范、不验证真实控件，也视为未完成。
