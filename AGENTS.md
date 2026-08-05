# PrismQML 开发规范

> 本文档是 PrismQML 的开发铁律 + 组件索引。贡献代码（含 AI 协作）前必须通读。
> 违反任何"铁律"应立即停止并报告。

## 目录

- [一、技术栈与目录结构](#一技术栈与目录结构)
- [二、枚举系统规范](#二枚举系统规范)
- [三、主题系统规范](#三主题系统规范)
- [四、代码风格规范](#四代码风格规范)
- [五、文件组织与模块化](#五文件组织与模块化)
- [六、效果与阴影](#六效果与阴影)
- [七、注释规范](#七注释规范)
- [八、版本发布规范](#八版本发布规范)
- [九、违规检测清单](#九违规检测清单)

---

## 一、技术栈与目录结构

### 技术栈
- **前端**: 纯 QML（QtQuick，Qt6 风格 import，不带版本号）
- **后端**: PySide6
- **主题**: ThemeManager（Python 注入），统一通过 `Enums` 访问

### 目录结构

```
prismqml/
├── PrismQML/                # QML 组件（模块名 PrismQML）
│   ├── Enums.qml       # 全局枚举/主题入口（唯一 singleton）
│   ├── Translator.qml  # 多语言翻译
│   ├── qmldir                # 根模块注册（module PrismQML）
│   ├── controls/             # UI 控件（按功能分类）
│   │   ├── buttons/  inputs/  feedback/  containers/
│   │   ├── data/  navigation/  effects/  icons/ ...
│   ├── FluentEnums/          # 枚举/常量/图标映射数据
│   └── _internal/            # 内部窗口实现
└── python/                   # Python 模块
    ├── config/  core/  window/  state/  providers/  models/
```

**QML 引入方式**（Python 端通过 `engine.addImportPath(qml_path().parent)` 注册）：

```qml
import PrismQML as Fluent                              // ✅ 模块名引入（推荐）
import "../prismqml/PrismQML/controls/buttons"        // 目录引入（按需）
```

---

## 二、枚举系统规范

### 2.1 全局枚举入口
- **唯一入口**: `Enums.qml`（`prismqml/PrismQML/Enums.qml`）
- **命名风格**: `snake_case`（如 `type_bar`, `style_primary`）
- **访问方式**: `Enums.{Category}.{enum_value}`

### 2.2 枚举分类

| 子类 | 用途 | 示例 |
|------|------|------|
| `StatusLevel` | 状态级别 | `Enums.StatusLevel.SUCCESS` |
| `Button` | 按钮类型/样式/形状/功能 | `Enums.Button.STYLE_PRIMARY` |
| `Chart` | 图表类型 | `Enums.Chart.TYPE_BAR` |
| `Position` | 位置 | `Enums.Position.TOP_RIGHT` |
| `Notification` | 通知模式/指示器 | `Enums.Notification.MODE_IN_APP` |
| `Slider` | 滑块类型 | `Enums.Slider.TYPE_RANGE` |
| `Orientation` | 方向 | `Enums.Orientation.HORIZONTAL` |
| `Animation` | 动画类型 | `Enums.Animation.OPACITY` |

### 2.3 禁止事项
- ❌ 在组件内部定义枚举
- ❌ 创建新的 `*Enums.qml` 文件
- ❌ 使用 camelCase 枚举命名（如 `typePush`）
- ❌ 使用旧枚举引用（如 `ButtonEnums.xxx`）

### 2.4 新增枚举流程
1. 打开 `Enums.qml`
2. 找到对应 Category（如 `button`）
3. 添加新枚举值（`snake_case`）
4. 更新使用该枚举的组件

```qml
readonly property QtObject button: QtObject {
    readonly property int new_type: 99  // 新增
}
```

---

## 三、主题系统规范

### 3.1 全局主题入口
**唯一入口**: `Enums` —— 所有主题属性通过此访问

| 属性 | 类型 | 说明 |
|------|------|------|
| `Enums.isDark` | bool | 是否深色模式 |
| `Enums.fontFamily` | string | 全局字体 |
| `Enums.accentColor` | color | 主题强调色 |

### 3.2 主题颜色（零硬编码，统一入口）

| 类别 | 属性 |
|------|------|
| **主色调** | `accentColor` / `accentColorLight` / `accentColorDark` |
| **背景** | `backgroundColor` / `surfaceColor` / `cardColor` / `dialogColor` |
| **前景** | `foregroundColor` / `secondaryForeground` / `disabledForeground` / `onAccentColor` |
| **边框** | `borderColor` / `borderLightColor` / `borderStrongColor` / `dividerColor` |
| **交互** | `hoverColor` / `pressedColor` / `disabledColor` / `selectedColor` |
| **阴影** | `shadowColor` / `shadowStrongColor` |

### 3.3 状态颜色 (StatusLevel)

| 方法/属性 | 说明 |
|-----------|------|
| `getColor(severity)` | 根据字符串获取颜色 |
| `getColorByLevel(level)` | 根据枚举获取颜色 |
| `getBgColor(severity)` | 获取背景色 |
| `successColor / warningColor / errorColor / ...` | 语义色属性 |

### 3.4 圆角常量（3 档）

| 常量 | 值 | 用途 |
|------|-----|------|
| `Enums.radius.small` | 4 | 按钮、输入框、菜单、标签 |
| `Enums.radius.large` | 8 | 卡片、面板、对话框、弹窗 |
| `Enums.radius.xlarge` | 16 | 抽屉、Toast |

### 3.5 字体等级（Fluent Design Typography）

`Enums.typography.{level}`：captionCompact(11，项目紧凑扩展) / caption(12) / bodySmall(13) / body(14) / bodyLarge(15) / subtitle(16) / title(18) / titleLarge(20) / display(24) / displayLarge(28) / metric(32) / hero(36) / giant(40) / mega(68)

```qml
Text {
    font.family: Enums.fontFamily
    font.pixelSize: Enums.typography.body
}
```

### 3.6 禁止事项（铁律：拒绝硬编码）

> **核心原则**：任何可复用的数值、颜色、样式参数都必须使用 `Enums` 全局常量。

- ❌ 硬编码颜色值（用 `Enums.statusLevel` / `Enums.gray`）
- ❌ 硬编码圆角（用 `Enums.radius.large`）
- ❌ 硬编码间距（用 `Enums.spacing.m`）
- ❌ 硬编码字体大小（用 `Enums.typography.body`）
- ❌ 硬编码动画时长（用 `Enums.duration.medium`）
- ❌ 硬编码阴影参数（用 `Enums.shadow.levelX`）
- ❌ 组件内定义 `isDark` / `fontFamily`（用 `Enums.isDark` / `Enums.fontFamily`）
- ❌ 直接使用 `ThemeManager`（应通过 `Enums` 访问）
- ❌ 任何数值出现 2 次以上，必须提取为常量

### 3.7 固定视觉预设数据例外（严格受限）

- 仅公开命名的固定视觉预设可使用局部静态颜色数据；通用主题色、组件状态色仍必须进入 `Enums`。
- 当前唯一允许路径：`prismqml/PrismQML/effects/_internal/MatrixRainPresets.js`。
- 该文件只允许保存 QML010 颜色预设与有序名称，不得加入尺寸、动画、阴影参数、状态或业务逻辑。
- 消费组件 QML 内不得继续散落预设颜色字面量；例外必须由扫描器按精确路径登记。
- 新增或扩展例外必须先评审，并同步补充扫描器与运行时回归测试。

---

## 四、代码风格规范

### 4.1 QML import（Qt6 风格，不带版本号）

```qml
import QtQuick                    // ✅ 正确
import QtQuick.Layouts
import QtQuick.Effects            // 阴影效果（MultiEffect / RectangularShadow）
import PrismQML as Fluent        // PrismQML 组件
```

**禁止写法**：

```qml
import QtQuick 2.15               // ❌ Qt5 风格带版本号
import Qt5Compat.GraphicalEffects // ❌ 已弃用
import QtQuick.Controls           // ❌ 见下方说明
```

**禁止 `QtQuick.Controls`**：其控件样式由 Style 子系统决定，Enums 主题色/圆角/阴影无法可靠覆盖，会导致样式割裂。一律使用 PrismQML 自有控件（FluentButton / LineEdit / SpinBox / ComboBoxEntry / FluentScrollBar / Flyout / OverlayDialogCore / ContextMenu 等，qmldir 已注册）。例外：仅 Window/基础设施级 Popup（如 `popupType: Popup.Window`）经评审后可用，且必须封装在 PrismQML 内部。

### 4.2 QML 成员声明顺序（强制）

每个 QML 对象内部成员严格按以下顺序声明（遵循 Qt 官方 QML Coding Conventions）：

1. **id**
2. **property 声明**（含 `readonly property` / `property alias`）
3. **signal 声明**
4. **JavaScript function**（所有 `function` 必须在此声明，**不得**出现在子元素之后或文件末尾）
5. **自身属性赋值**（`width` / `height` / `color` / `anchors` / `text` 等对自身属性的赋值）
6. **子元素对象**（`Rectangle {}` / `Icon {}` / `MouseArea {}` / `Loader {}` 等）
7. **states**
8. **transitions**（含 `Behavior on xxx`，但与目标属性紧邻的 `Behavior` 可就近放置）

```qml
Item {
    id: control                                    // 1. id

    property string text: ""                       // 2. property
    readonly property bool hovered: area.containsMouse

    signal clicked()                               // 3. signal

    function reset() { text = "" }                 // 4. function

    width: 100                                     // 5. 自身属性赋值
    height: 40

    Rectangle { ... }                              // 6. 子元素

    MouseArea { id: area; ... }
}
```

**例外 1 — 引用子元素 id 的只读绑定**：`readonly property` 若引用了后续声明的子元素 `id`（如 `readonly property bool hovered: area.containsMouse`，`area` 是后面的 MouseArea），属正常绑定，**保持在 property 区即可**（QML 绑定不要求 id 先声明）。

**例外 2 — 暴露子元素的 alias 就近声明**：`property alias xxx: child` / `property alias xxx: child.prop`（把某个子元素或其属性对外暴露）允许**紧贴它所代理的子元素声明**（即放在该子元素正上方或附近，而非强制提到 property 区顶部）。这样 alias 与目标子元素相邻，可读性更好，是被接受的惯例。例如 `property alias animator: animator` 紧跟在 `NotificationAnimator { id: animator }` 上方。

除上述两种情况外，严禁把 property 拆到子元素之后。

### 4.3 QML 分节注释术语（统一）

使用统一格式 `// ==================== 标签 ====================` 分节，标签术语**严格按下表**，禁止自创变体：

| 区段 | 统一标签 | 禁止的变体 |
|------|---------|-----------|
| 公开属性 | `Public Props 公开属性` | ~~Props~~ / ~~Properties~~ |
| 必需属性 | `Required Props 必需属性` | ~~Required~~ |
| 内部/私有属性 | `Internal Props 内部属性` | ~~Private~~ / ~~State~~ |
| 只读派生状态 | `Readonly State 只读状态` | ~~State~~ |
| 信号 | `Signals 信号` | ~~Signal~~ |
| 公开方法 | `Public Methods 公开方法` | ~~Methods~~ / ~~Functions~~ |
| 内部方法 | `Internal Methods 内部方法` | ~~Private Methods~~ |
| 自身尺寸/几何 | `Size 尺寸` | ~~Layout~~ / ~~Geometry~~ |
| 子元素内容 | `Content 内容` | ~~UI~~ / ~~Body~~ |

### 4.4 命名约定

| 类型 | 风格 | 示例 |
|------|------|------|
| QML 组件 | PascalCase | `FluentButton.qml` |
| QML 属性 | camelCase | `buttonText` |
| QML 枚举 | snake_case | `type_bar` |
| Python 类 | PascalCase | `ThemeManager` |
| Python 函数 | snake_case | `get_color()` |

**框架签名例外（必须有来源依据）**：

- Qt/PySide 虚方法 override 必须保留官方方法名与签名，例如 `rowCount`、`roleNames`、`nativeEventFilter`；例外必须由 Qt 文档或实际基类的同名虚方法证明，模仿 Qt 命名的普通适配器不算。
- 通过 Qt `Signal` / `Property` / `Slot` 暴露给 QML 的公开 API，可遵循 Qt/QML 的 camelCase；必须同时存在注册/注入路径，以及真实 QML、`QMetaObject` 字符串调用、公开 QML 测试或文档消费者。单有装饰器或普通 Python 调用方不足以证明例外。
- 上述 QML 公开名称在本阶段不得仅因 Python 风格规则改名；若经独立 API 设计评审决定在 v1.0.0 前做 breaking rename，必须同批迁移全部消费者，且不得保留 deprecated 别名。
- 普通公开 Python API 不因“已公开”自动获得 camelCase 例外；不属于已证实的 override 或 QML 公开契约时，普通公开 API 与内部实现均须使用 snake_case，并按版本规范另批迁移。

### 4.5 Python 文件头（强制格式）

每个 Python 文件必须以此开头：

```python
# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
```

### 4.6 Python 异常处理

```python
# ❌ 禁止：裸异常 / 过宽 + 静默
try: ...
except: pass
except Exception: pass

# ✅ 正确：具体异常 + 日志
try: ...
except ValueError as e:
    logger.error(f"值错误: {e}")
except Exception as e:
    logger.exception(f"未知错误: {e}")  # 带堆栈
```

### 4.7 Python 日志（铁律）

> 非性能测试场景严禁 `print`，必须使用 `logger`。

```python
from prismqml.python.core.logger import info, error, debug, warning
info("加载完成")
error(f"错误: {e}")
```

**唯一例外**：性能基准测试中的计时输出可用 `print`。

### 4.8 下拉与菜单必须使用独立原生窗口（铁律）

- 标准下拉、菜单、选择器弹层必须通过 `PopupWindowCore` 使用独立的原生顶层窗口；`Button` 的 `feature_dropdown` / `feature_split` 内置菜单必须保持 `useQtPopupWindow: true`，允许弹层越过宿主窗口边界完整显示。
- 宿主窗口边界不得参与弹层位置夹紧。标准锚定弹层必须保持触发控件左边缘对齐；仅允许根据当前屏幕的 `availableGeometry` 避让屏幕边缘、任务栏及系统保留区域。
- 严禁以点击可靠性、动画、焦点、性能、预热、远程桌面或第二个 HWND 为由，把标准弹层降级为 `useInWindowPopup: true`。这些问题必须在原生弹层的输入、生命周期或预热实现中解决，不得牺牲跨窗口显示能力。
- `useInWindowPopup: true` 只允许用于组件契约明确要求页内渲染且已经过专项评审的场景；必须在调用处写明原因，并保留显式页内模式测试，禁止把它设为通用或按钮菜单默认值。
- 相关修改必须覆盖回归：默认模式确为独立 `QWindow`、靠近宿主右边缘时可越界、左侧锚点不漂移、菜单项首击有效、外部点击与 `Escape` 可关闭、同步替换模型不破坏关闭流程。

---

## 五、文件组织与模块化

### 5.1 单文件行数限制（铁律）

- **500 行**：软警告（新代码尽量遵守）
- **700 行**：硬限制（必须模块化拆分）

**数据资源文件例外**（纯静态数据，无逻辑）：`PrismEnums/Icons.qml`(~5000) / `PrismEnums/Metrics.qml`(~700) / `Translator.qml`(~1200)。`_internal/` 下逻辑内聚的文件可放宽至 600 行。

**生成型 Python 枚举数据例外（严格受限）**：只有能由仓内生成器在 `--check` 模式下确定性地复现相同文本内容、文件头明确标注生成来源、且内容仅含枚举/常量数据与必要的无副作用查询方法时，才可超过 700 行。渲染、文件 I/O、主题判断或业务逻辑必须移入普通模块；生成文件不得手改。

当前 `prismqml/python/core/icons.py` **尚不满足该例外**：`scripts/extract_icons.py --check` 不能复现现有 Python/QML 注册表，且文件混有生成器未产出的图标路径与渲染逻辑。它在 P8B 完成生成器、双注册表和运行逻辑同步前属于待整改遗留文件；P7 不得盲拆、粉饰为合规或直接重生成覆盖。

### 5.2 模块化架构模式

```
ComponentName.qml (入口，~100-200 行)
├── 类型/样式属性声明 + 信号声明
├── Loader 动态加载子模块
└── 公开方法

_internal/
├── ComponentNameStyleHelper.qml  (样式/颜色计算)
├── ComponentNameContent.qml      (内容区域)
└── ComponentNameFeatureX.qml     (功能模块)
```

- **入口文件**：声明公开属性/信号，用 Loader 按 type 加载子模块，提供公开方法
- **子模块**：用 `required property` 接收必需属性，通过信号向上传递事件
- ❌ 入口文件实现具体功能 / 子模块直接访问父组件 / 创建上帝类

### 5.3 qmldir 规范
- 根 `qmldir` 注册 `Enums` 为 singleton（`module PrismQML`）
- 子目录 `qmldir` 不再注册枚举文件，组件按功能分类注册

---

## 六、效果与阴影

### 6.1 阴影等级（Fluent Design Elevation）

`Enums.shadow.{level}`：level2(offset1/blur4) / level4(2/8) / level8(4/16) / level16(8/32) / level28(12/48)

深色主题阴影透明度自动增强 1.5 倍。

### 6.2 铁律：优先 ShadowedRectangle

| 组件 | 技术 | 适用场景 |
|------|------|----------|
| **ShadowedRectangle** ✅ | RectangularShadow (Qt 6.9+ SDF) | 矩形组件（首选，无离屏渲染） |
| **FluentShadow** ⚠️ | MultiEffect (layer.effect) | 仅非矩形/复杂形状 |

```qml
import "../effects"

ShadowedRectangle {
    color: Enums.cardColor
    radius: Enums.radius.large
    shadowLevel: Enums.shadow.level4
}
```

`RectangularShadow` 是 Qt 6.9 内置，使用需 `import QtQuick.Effects`。

### 6.3 Qt5Compat 迁移对照

| Qt5Compat (废弃) | PrismQML 封装 |
|------------------------|------------------|
| `DropShadow` | `FluentShadow` |
| `ColorOverlay` | `FluentColorOverlay` |
| `OpacityMask` | `FluentOpacityMask` |
| `GaussianBlur` | `FluentGaussianBlur` |

封装位于 `controls/effects/`。

---

## 七、注释规范

QML 注释使用**双语格式**（英文在前，中文在后）：

```qml
// ButtonCore - Button core component 按钮核心组件
// ==================== Public Props 公开属性 ====================
property string icon: ""   // Icon text (emoji or char) 图标文本
```

- ❌ 纯中文注释 / 纯英文注释 / 中文在前英文在后
- 段落分隔统一用 `// ===== Name 中文 =====`

---

## 八、版本发布规范

> **铁律**：v1.0.0 之前禁止保留向后兼容代码。所有废弃的 API、枚举、属性、组件直接删除或重命名，**不保留 deprecated 别名**。发现旧代码直接重构。

### 发布流程（main → tag → GitHub Release）

远程：`prism` = `git@github.com:aki-riko/PrismQML.git`（SSH 公钥用于 push）。

> 🔴 **双 remote 必须分清**：本仓有两个远程——
> - `prism` → `git@github.com:aki-riko/PrismQML.git`（**真 GitHub，CI/PyPI 发布在这里跑**）
> - `origin` → `git@git.9li.life:Aquila/PrismQML.git`（自建 gitea，**无 CI**）
>
> 默认 `git push`（无 remote 名）走 `origin`（gitea），**不会触发 GitHub Actions**。
> 发版相关的 commit 和 tag **必须显式 `git push prism ...`** 才能触发 CI。
> 两边都要推时：`git push prism main && git push origin main`，tag 同理。

1. **改版本号（两处必须同步）**：
   - 🔴 **AI 自动升级发版铁律**：AI 自动决定版本升级时，仅允许递增第四位构建号（`x.y.z.n` 中的 `n`）；第一、第二、第三位的任何变更必须由用户或维护者明确决定，AI 不得自行升级。
   - **默认升构建号**：每次发版除非用户/维护者明确指定完整版本号或前三位升级策略，否则只递增最后一位构建号（`x.y.z.n` 中的 `n`）。例如 `0.2.24.1` 下一版默认 `0.2.24.2`，而不是 `0.2.25.0`。
   - `pyproject.toml` 的 `version = "x.y.z.n"`
   - `prismqml/__init__.py` 的 `__version__ = "x.y.z.n"`（回退值）
2. **验证**：发布前必须通过统一零交互门禁；自动测试禁止直接启动
   `prism_test_*.exe`、`prism_native_failure_helper.exe` 或
   `prism_native_failure_loader.exe`，也禁止依赖调用者恰好设置了 Qt PATH /
   `QT_QPA_PLATFORM`。原生失败夹具只能由 `ctest -L native` 间接启动。
   ```powershell
   .\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 480 -- .\.venv\Scripts\python.exe -m pytest
   .\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py
   ctest --test-dir cpp\build -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
   ```
   - `scripts/test_process.py` 在 Qt 导入前固定 headless、UTF-8、faulthandler 与原生无 UI 策略；Windows launcher 先用可继承的错误模式保护 bootstrap，实际测试再启用 WER `NO_UI + QUEUE`。新增自动化子进程必须复用 runner，或在导入 Qt 前调用同一 bootstrap，不得无保护地直接启动。
   - QML probe 遍历 qmldir 全组件 `createComponent`，自身也会强制 `offscreen`；调用者显式传入 `windows/minimal` 不再覆盖自动门禁。
   - 🔴 **当前优化基线：probe 应退出码 0，且约 `174 OK / 0 错误 / 7 跳过 = 181`**。5 个 singleton（Enums / Translator / DpiManager / NotificationManager / PopupUtils）必须通过 QtObject wrapper 触发 QML 引擎真实创建并读取，且 singleton 创建期 Qt warning / critical / fatal 为 0；仅允许跳过 7 个 required-property 内部子模块（ButtonContent / ButtonDropdown / ButtonProgress / ListWidgetItem / SettingsCardContent / HorizontalScrollMixin / ViewportMixin，由父组件注入 required property，单独 createComponent 不成立）。
   - 🔴 **判是否新增回归的权威法**：`git worktree add /tmp/baseline <改动前 commit>`，从主 venv 把编译好的 `prismqml_rs*.pyd` cp 进去 + `PYTHONPATH=/tmp/baseline` 跑同一 probe，对比 OK/错误/跳过三个数字是否一致；一致即零新增。看到非 0 退出码必须先分析具体错误，不可把它当成既有 required-property 基线。
   - Windows 原生 Mica 不是默认 headless 集合：仅在显式配置 `-DPRISM_BUILD_NATIVE_TESTS=ON` 后运行 `ctest --test-dir cpp\build -L native --interactive-debug-mode 0 --output-on-failure --no-tests=error`。
   - `tests/test_window_buttons.py`、`tests/qml/bench_skin_frames.py`、`scripts/fps_probe.py`、`scripts/run_with_fps.py` 等可视/性能入口属于人工测试，不得混入自动门禁；需要运行时必须明确说明会打开窗口。
   - 🔴 **Windows 可视性能验收只接受 D3D11**：被测入口与探针都必须固定 `QSGRendererInterface.GraphicsApi.Direct3D11`，并在结果中核验实际 API 确为 `Direct3D11`。严禁使用 OpenGL、software、offscreen 或其他后端的耗时、帧率、截图作为性能收益或视觉验收结论；`offscreen` 仅用于零交互正确性回归。
3. **提交**：`git add -A && git commit`（commit message 写清修复内容 + 版本号）。
4. **打 tag + 推送**：
   ```bash
   git tag vx.y.z.n
   git push prism main
   git push prism vx.y.z.n
   ```
5. **建 GitHub Release**：`gh release create vx.y.z.n --repo aki-riko/PrismQML --title "vx.y.z.n" --notes "..."`
6. **下游消费者生效（🔴 发版 ≠ 下游自动更新）**：下游应用（Gitora / quicksketch / Kaleidos 等）各自带**独立 `.venv`**，且 `.venv` 被 gitignore——它们装的是 PyPI 包 `prismqml`，**不随引擎源码推送而更新**。引擎发版后，每个下游需：
   - `pip install -U prismqml==x.y.z.n`（升级各自 venv 里的包），
   - 然后**重新打包**（Nuitka）。打包态把 prismqml 整包嵌进 exe，**旧 exe 不重打包则修复不生效**（如 AUMID 这类在导入/启动时生效的逻辑，必须重打包才落到二进制）。
   - 修源码时若直接改了某个下游 venv 内的 prismqml 副本（如热修验证），记得全盘 `find -path "*prismqml*<改的文件>"` 扫所有副本（源库 + 各 venv）按 md5 对齐，避免只改一份。

### 认证注意（🔴 安全）

- `git push` 走 **SSH 公钥**；`gh release` / GitHub API 走 **token**（两套独立，SSH 密钥不能用于 API）。
- 建 Release 前需 `gh auth login`（浏览器授权，推荐），或设 `GH_TOKEN` 环境变量。
- **绝不把 PAT / token 明文贴进对话或提交进代码**。token 一旦明文出现即视为泄露，必须立即去 `github.com/settings/tokens` 吊销。临时用 token 只通过环境变量传入：`GH_TOKEN=xxx gh release create ...`。

### CI 自动发布（🔴 发版靠推 tag，不靠本地打包）

`.github/workflows/release.yml` 是发版的真正执行者，**别在本地手动打包上传**：

- **触发**：推送 `v*` 格式的 tag（如 `v0.2.24.1`）→ 自动触发。普通 push commit 不触发，`workflow_dispatch` 手动触发只构建不发布。
- **构建**：三平台（ubuntu / windows / macos-14）用 `cibuildwheel` 构建 abi3 wheel（`CIBW_BUILD=cp39-*` + `CIBW_CONFIG_SETTINGS=--build-option=--py-limited-api=cp39`）+ sdist。
- **发布**：`publish` job 经 **PyPI Trusted Publishing**（`id-token: write` + `environment: pypi`）自动上传 PyPI，条件 `if: startsWith(github.ref, 'refs/tags/v')`（仅 tag 触发时发布）。
- **看状态**：`gh run list` / `gh run watch`（需先 `gh auth login`）；或浏览器开 `github.com/aki-riko/PrismQML/actions`。三平台构建 + publish 全绿才算发布成功，几分钟后 `pip install prismqml==x.y.z.n` 能装到即坐实。
- 本地 `python -m build` 仅用于调试 wheel 标签，**产物不上传**（CI 出的全平台包才是正式产物）。

### abi3 构建配置（🔴 wheel 必须是 cp39-abi3，不能退化）

含 Rust 扩展（`prismqml_rs`），wheel 必须打成 **`cp39-abi3`**（一个 wheel 兼容 py3.9+），不能退化成 `cp3XX-cp3XX`（绑死单个 Python 版本）。

- **三处配置缺一不可**：
  1. `rust/Cargo.toml`：`pyo3 = { features = ["abi3-py39"] }`（必要但不充分）
  2. `pyproject.toml` 的 `[[tool.setuptools-rust.ext-modules]]`：`py-limited-api = "auto"`
  3. `pyproject.toml` 的 `[tool.distutils.bdist_wheel]`：`py-limited-api = "cp39"` ← **本地 `python -m build` 靠这条才不退化**
- **机制**：setuptools-rust 的 `"auto"` 会去读 `bdist_wheel.py_limited_api` 选项，缺失则不加 abi3 feature，退化成 cp3XX。CI 通过 `CIBW_CONFIG_SETTINGS` 在命令行传，本地构建则靠 `[tool.distutils.bdist_wheel]` 配置。
- **判定 wheel 是否真 abi3 的铁证 = 看 wheel 内 `.pyd` 文件名**：
  - `prismqml_rs.pyd`（无版本后缀）= abi3 通用 ✅
  - `prismqml_rs.cp312-win_amd64.pyd`（带版本后缀）= 绑死单版本 ❌
  - 别只信 "Successfully built"，它对错误标签照样报成功。

### 包命名（分发名 = 导入名 = prismqml）

PyPI **分发名**、Python **导入名**、QML 模块名统一为 `prismqml` / `PrismQML`：

- 安装：`pip install prismqml`，PyPI 元数据 `pyproject.toml` 的 `[project] name = "prismqml"`
- import：`from prismqml import ...` / `import prismqml`
- 包目录 `prismqml/python/...`、QML 模块 `import PrismQML`、配置目录 `~/.prismqml/`
- Rust crate 名 `prismqml_rs`（`rust/Cargo.toml`）
- 旧名 `fqml` / `fluentqml` / `FluentQML` 已全部废弃（前身 FluentQML 已存档）；如在代码中发现残留，属改名遗漏，应改为 prismqml/PrismQML（`controls/icons/fluent` 图标集名、`as Fluent` 别名、致谢微软 Fluent Design 的文本除外）。

---

## 九、违规检测清单

生成/修改代码前必须检查：

**枚举** — 是否引用旧枚举文件 / 命名是否 `snake_case` / 新枚举是否加到 `Enums.qml` / 是否在组件内定义枚举

**主题** — 是否硬编码颜色/圆角/阴影/字体大小 / 是否直接用 `ThemeManager` 而非 `Enums`

**Python** — 文件头是否为 `# coding: utf-8` / 是否含 **MIT** License 头 / 是否有裸异常或静默捕获 / 非测试场景是否误用 `print`

**import** — 是否带版本号（`QtQuick 2.15`）/ 是否用了 `Qt5Compat.GraphicalEffects` / 是否误用 `QtQuick.Controls`

**模块化** — 文件是否超 700 行 / 是否可通过 type 参数整合相似组件 / 子模块是否正确用 `required property`

> **发现违规 → 立即停止 → 报告用户**

---

## 组件索引

公共组件以 `qmldir` 注册为准：根 `prismqml/PrismQML/qmldir` 及各子目录 `qmldir`。新增/查询组件时直接看 qmldir 注册项，避免维护易过时的独立清单。
