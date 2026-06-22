# FluentQML 开发规范

> 本文档是 FluentQML 的开发铁律 + 组件索引。贡献代码（含 AI 协作）前必须通读。
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
fluentqml/
├── FluentQML/                # QML 组件（模块名 FluentQML）
│   ├── Enums.qml       # 全局枚举/主题入口（唯一 singleton）
│   ├── Translator.qml  # 多语言翻译
│   ├── qmldir                # 根模块注册（module FluentQML）
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
import FluentQML as Fluent                              // ✅ 模块名引入（推荐）
import "../fluentqml/FluentQML/controls/buttons"        // 目录引入（按需）
```

---

## 二、枚举系统规范

### 2.1 全局枚举入口
- **唯一入口**: `Enums.qml`（`fluentqml/FluentQML/Enums.qml`）
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

`Enums.typography.{level}`：caption(12) / bodySmall(13) / body(14) / bodyLarge(15) / subtitle(16) / title(18) / titleLarge(20) / display(24) / displayLarge(28) / metric(32) / hero(36) / giant(40) / mega(68)

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

---

## 四、代码风格规范

### 4.1 QML import（Qt6 风格，不带版本号）

```qml
import QtQuick                    // ✅ 正确
import QtQuick.Layouts
import QtQuick.Effects            // 阴影效果（MultiEffect / RectangularShadow）
import FluentQML as Fluent        // FluentQML 组件
```

**禁止写法**：

```qml
import QtQuick 2.15               // ❌ Qt5 风格带版本号
import Qt5Compat.GraphicalEffects // ❌ 已弃用
import QtQuick.Controls           // ❌ 见下方说明
```

**禁止 `QtQuick.Controls`**：其控件样式由 Style 子系统决定，Enums 主题色/圆角/阴影无法可靠覆盖，会导致样式割裂。一律使用 FluentQML 自有控件（FluentButton / LineEdit / SpinBox / ComboBoxEntry / FluentScrollBar / Flyout / OverlayDialogBase / ContextMenu 等，qmldir 已注册）。例外：仅 Window/基础设施级 Popup（如 `popupType: Popup.Window`）经评审后可用，且必须封装在 FluentQML 内部。

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

### 4.5 Python 文件头（强制格式）

每个 Python 文件必须以此开头：

```python
# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是 FluentQML 的一部分，采用 MIT 许可证授权。
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
from fluentqml.python.core.logger import info, error, debug, warning
info("加载完成")
error(f"错误: {e}")
```

**唯一例外**：性能基准测试中的计时输出可用 `print`。

---

## 五、文件组织与模块化

### 5.1 单文件行数限制（铁律）

- **500 行**：软警告（新代码尽量遵守）
- **700 行**：硬限制（必须模块化拆分）

**数据资源文件例外**（纯静态数据，无逻辑）：`FluentEnums/Icons.qml`(~5000) / `FluentEnums/Metrics.qml`(~700) / `Translator.qml`(~1200)。`_internal/` 下逻辑内聚的文件可放宽至 600 行。

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
- 根 `qmldir` 注册 `Enums` 为 singleton（`module FluentQML`）
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

| Qt5Compat (废弃) | FluentQML 封装 |
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
// ButtonBase - Button base class 按钮基类
// ==================== Public Props 公开属性 ====================
property string icon: ""   // Icon text (emoji or char) 图标文本
```

- ❌ 纯中文注释 / 纯英文注释 / 中文在前英文在后
- 段落分隔统一用 `// ===== Name 中文 =====`

---

## 八、版本发布规范

> **铁律**：v1.0.0 之前禁止保留向后兼容代码。所有废弃的 API、枚举、属性、组件直接删除或重命名，**不保留 deprecated 别名**。发现旧代码直接重构。

### 发布流程（main → tag → GitHub Release）

远程：`github` = `git@github.com:aki-riko/FluentQML.git`（SSH 公钥用于 push）。

1. **改版本号（两处必须同步）**：
   - `pyproject.toml` 的 `version = "x.y.z"`
   - `fluentqml/__init__.py` 的 `__version__ = "x.y.z"`（回退值）
2. **验证**：发布前 headless 跑一遍确认无新增 QML 警告/错误
   （`QT_QPA_PLATFORM=offscreen` + 加载关键组件，零 `unavailable`/`Duplicate`/属性覆盖警告）。
3. **提交**：`git add -A && git commit`（commit message 写清修复内容 + 版本号）。
4. **打 tag + 推送**：
   ```bash
   git tag vx.y.z
   git push github main
   git push github vx.y.z
   ```
5. **建 GitHub Release**：`gh release create vx.y.z --repo aki-riko/FluentQML --title "vx.y.z" --notes "..."`

### 认证注意（🔴 安全）

- `git push` 走 **SSH 公钥**；`gh release` / GitHub API 走 **token**（两套独立，SSH 密钥不能用于 API）。
- 建 Release 前需 `gh auth login`（浏览器授权，推荐），或设 `GH_TOKEN` 环境变量。
- **绝不把 PAT / token 明文贴进对话或提交进代码**。token 一旦明文出现即视为泄露，必须立即去 `github.com/settings/tokens` 吊销。临时用 token 只通过环境变量传入：`GH_TOKEN=xxx gh release create ...`。

### 包命名（🔴 分发名 ≠ 导入名）

PyPI **分发名** `fqml`（`fluentqml` 已被占用）；Python **导入名** 仍是 `fluentqml`。两者刻意不同，类似 `pip install pillow` 但 `import PIL`。

- **只有"如何安装"语境用 `fqml`**：`pip install fqml`、README 安装命令、PyPI 元数据（`pyproject.toml` 的 `[project] name = "fqml"`）。
- **其余一律保持 `fluentqml`，禁止改动**：
  - import 语句 `from fluentqml import ...` / `import fluentqml`
  - 包目录 `fluentqml/python/...`、QML 模块路径
  - 配置目录 `~/.fluentqml/`
  - Rust crate 名 `fluentqml_rs`（`rust/Cargo.toml`，与 PyPI 无关）
- 改安装命令时只动 `pip install` 那一行，**绝不要批量把 `fluentqml` 替换成 `fqml`**——会改坏所有 import 和路径。

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

公共组件以 `qmldir` 注册为准：根 `fluentqml/FluentQML/qmldir` 及各子目录 `qmldir`。新增/查询组件时直接看 qmldir 注册项，避免维护易过时的独立清单。
