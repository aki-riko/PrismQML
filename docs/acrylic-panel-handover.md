# 导航面板亚克力显示问题 — 交接文档

> 范围：`WindowsSplit`（设置里"窗口类型 = Window"）左侧导航面板的亚克力背景显示异常。
> **当前 main 实际状态**：`de913fdc`（角块）+ `8b75ac03`（错位重影）+ `91023dce`（本文档）。
> 其中"方角外露"的修复提交 `c13f52ce` / `ccbfe7d5` **已从 main 被回退**
> （reflog：`reset: moving to 8b75ac03`），对象仍在库里，可按第 6.4 节决定是否恢复。

---

## 0. 当前状态速览

| 项 | 值 |
|---|---|
| main HEAD | `91023dce 文档: 导航面板亚克力显示问题交接` |
| 生效修复 | `de913fdc` 角填充（左上角色块）、`8b75ac03` 模糊图对齐（错位重影） |
| 未生效（已回退） | `c13f52ce` 亚克力按轮廓裁剪（方角外露）、`ccbfe7d5` 首帧加载有界重试 |
| 亚克力当前实现 | `NavigationPanelBackground.qml`：`Image`（`y: titleBarHeight`、`height: parent.height - titleBarHeight`）+ 着色 `Rectangle`，**无轮廓遮罩** |
| 定向测试 | `16 passed`（`test_navigation_panel_acrylic_corner.py` 2 条 + 根导航规范 + 导航窗核心规范 + 架构合同） |
| 遗留缺陷 | 亚克力是**矩形面**，在面板右侧两个圆角处会露出方角（"没有圆角的那一层"） |

---

## 1. 症状（用户视角）

| 症状 | 出现位置 | 状态 |
|------|----------|------|
| 方形色块（浅色偏白、暗色偏蓝，约 8×8 逻辑像素） | 窗口左上角 | 已修 `de913fdc` |
| 面板项后面一层**错位**的模糊重影（"上面一层下面一层"） | 整个面板 | 已修 `8b75ac03` |
| 面板外侧露出**方角的一层**（"没有圆角的那层"） | 面板右上、右下圆角处 | **未修（修复被回退）** |
| 面板整片没有模糊，只剩右缘一条 | 整个面板 | 曾由 `c13f52ce` 引入，`ccbfe7d5` 修好，两者都已回退；当前 main 无此问题 |

---

## 2. 结构背景（排查前必读）

- `prismqml/PrismQML/_internal/WindowsSplit.qml`
  - 面板容器 `navContainer`：`anchors.topMargin: -window.titleBarHeight` → **比窗口高一个标题栏**。
  - 其内 `NavigationView` 自身尺寸 **320×848**（逻辑），窗口内可见部分是 **320×800**。
- `prismqml/PrismQML/navigation/_internal/NavigationPanelBackground.qml` 三层：
  1. **Layer A `bgCanvas`**：面板底色。路径为"贴窗口一侧直角 + 右侧圆角（右上圆角自 `titleBarHeight` 起，正好落在窗口顶边）"。
  2. `TicketPaper`：票据皮肤纸纹（fluent 下不可见）。
  3. **Layer B 亚克力**：模糊截图 + 着色（`Enums.stateColor.acrylicTintColor`）。
- 图源：`AcrylicHelper.grabAndBlur(window, 0, 0, navExpandWidth, window.height)`
  → 抓的是**窗口内**的面板区域 **320×800**，由 `image://acrylic/<id>` provider 提供；
  与 Layer B 所在的 320×848 矩形**面积不一致** —— 这是其中两个缺陷的共同根。
- 展开时机：`WindowsSplit.onAboutToExpand` 抓图 → `acrylicEnabled` 变真。
- 轮廓几何（判定用）：面板右缘在**物理 480**，圆角半径 8 逻辑像素 = **12 物理**，
  两段圆弧圆心 `(468,12)` 与 `(468,1188)`；**距离 > 12 的点才算圆角之外**。

---

## 3. 根因与修法

### 3.1 左上角色块 — `de913fdc`（在 main 上）
亚克力层里另叠了两块"角填充"矩形（注释 `Fill top-left/bottom-left corner (no radius)`），
其 `Image` 用 `anchors.right / anchors.bottom` 对齐 → **左上角显示的是模糊图右下角那块区域**
（面板底部选中高亮，因此偏蓝）；内边界是直角，所以同时看着像"色块 + 尖角"。

修法：删除冗余填充（亚克力层按外接矩形裁剪，四个角象限本已覆盖，补填充只会用错位区域重绘角落）。

### 3.2 错位重影 — `8b75ac03`（在 main 上）
`Image { anchors.fill: parent; fillMode: Image.PreserveAspectCrop }` 把 320×800 的截图铺到 320×848 的层
→ 纵向放大 **848/800 ≈ 1.06** 并整体上移一个标题栏 → 真实内容后面多一层错位副本。

修法：按截图自身尺寸落位（`y: titleBarHeight`，`height: parent.height - titleBarHeight`）。
真机观测：亚克力 `QQuickImage` 几何 `(0,0,320,848)` → **`(0,48,320,800)`**。

### 3.3 方角外露 — `c13f52ce` + `ccbfe7d5`（已实现，**已从 main 回退**）
Layer B 是 `Image` + 着色矩形**铺满整层**的矩形面，而面板轮廓右侧是圆角
→ 两块方角画到圆角面板之外，就是"没有圆角的那一层"。

曾实现的修法：改为 `Canvas` 按面板轮廓裁剪绘制（`clip()` 走与 `bgCanvas` 同一条路径，
再 `drawImage` + 填充着色）。`c13f52ce` 首版只做了一次 16ms 加载重试，
在较慢的机器上首帧放弃重绘、面板整片失去模糊（"只剩一条"）；
`ccbfe7d5` 改成有界重试循环（16ms × 180 ≈ 3 秒，成功即停，超时 `console.warn`）后修复。

真机 A/B 证据（亚克力开/关两帧逐像素求差，`ccbfe7d5` 状态）：
`y=600` 行 x=40…440 全部 `changed`（整片覆盖）；圆角外 `TR(478,2)`、`BR(478,1197)` 两帧完全一致（不越界）。
即：**带上有界重试的 Canvas 路线在真机上是可用的**；回退是维护者决定。

---

## 4. 验证方法

### 4.1 离屏像素回归（自动，进仓库）
`tests/qml/test_navigation_panel_acrylic_corner.py`，复刻 WindowsSplit 容器高度
（容器 y=-48、高 848）+ 上半红/下半绿 320×800 合成图：

1. `test_acrylic_panel_corner_keeps_the_panel_image_region`：角落必须取面板**顶部**图像区域
   —— 改前 `corner=#acf7ac`（取到下半部）失败；
2. `test_acrylic_panel_image_aligns_with_the_visible_panel`：截图中线必须落在窗口中线上
   —— 改前 `above=#acf7ac`（被拉伸上移）失败。

> 回退掉的 `c13f52ce` 里还有第 3 条 `test_acrylic_stays_inside_the_rounded_panel_silhouette`
> （亚克力不得越出圆角轮廓），恢复该提交时会一并回来。

```bash
python scripts/test_process.py --qt-platform offscreen --timeout 120 -- \
  python -m pytest tests/qml/test_navigation_panel_acrylic_corner.py -q
```

### 4.2 真机 A/B（关键：只看离屏会漏判）
让同一实例在"亚克力开/关"两个状态各抓一帧逐像素求差，差集即亚克力真正画到的像素。
判据：**面板内部整片 `changed`；圆角外点两帧一致**。脚本见第 5 节。

### 4.3 回归面（当前 main）
`16 passed`：本文件 2 条 + `test_root_navigation_conventions.py` +
`test_navigation_window_core_conventions.py` + `test_qml_architecture.py::test_navigation_panel_keeps_background_layer_modularized`；
`python scripts/check_qml_conventions.py --changed --base HEAD` = 0 violation。

---

## 5. 诊断工具（下次直接用）

| 工具 | 位置 | 用途 |
|---|---|---|
| `scripts/manual/window_corner_probe.py` | 已入库 | 裸 `Window` 宿主：item 树 + 只渲染 QML 的抓帧 + 角像素；`alpha=0` 即"这里根本没有 QML 绘制"（露出 DWM 背板/桌面） |
| `.artifacts/window-diag/gallery_probe.py` | 临时（未入库） | 跑**真实 Gallery**（App 装配 + main.qml）：展开面板、亚克力开/关 A/B 求差、item 树、`QQuickImage` 几何、`Canvas.isImageLoaded` |
| `.artifacts/window-diag/*.png` / `*.txt` | 临时 | 现场证据图与报告 |

经验：
- 只渲染 QML 用 `qwindow.grabWindow()`；屏幕抓帧要按 DPR 换算偏移（Qt 放大位图但不换算 x/y），
  且窗口必须在前台，否则抓到别的窗口。
- probe 脚本中途异常会**不写报告**，grep 输出时别把上一次的旧报告当成本次结果。
- 采样点务必按物理像素与圆心距离算，别凭感觉取"角落"（我第一轮就取在圆角内侧，结论是错的）。

---

## 6. 未解决 / 已否决

### 6.1 亚克力是展开瞬间的静态快照
展开后悬停、滚动、切页都不会更新背景；窗口极端缩放时是一次性拉伸。属设计问题，
要做成实时需换机制（周期性重抓，或改用 DWM 原生亚克力）。

### 6.2 导航滚动轨
`NavigationScrollRail`（`stateColor.scrollTrack` / `scrollHandleDefault`，几何约 `x=308..314` 逻辑、
宽 6、悬停或滚动后显形）会在面板右缘形成一条很淡的竖带。用户曾用箭头指向它，
**未确认是否需要改**（可选：静止不画 track / 收窄 / 裁进列表可视区）。

### 6.3 已试过但**不可用**的遮罩路线（别原样重试）
- `MultiEffect` / `OpacityMask` 作为 `layer.effect`：
  - **offscreen 平台完全不渲染**（探针实测 `maskedBlock = #ffffff`）→ 会让仓库既有的离屏 QML 探针
    看不到亚克力；
  - 真机上用内联 `Rectangle` 作 `maskSource` 会被**忽略**，方角照旧越界；
  - 换成 `ShaderEffectSource { sourceItem: ... }`（TeachingTour 的写法）在真机 A/B 下**仍未切掉方角**。
- 结论：若日后要回到 GPU 遮罩，先写"真机 A/B：圆角外点两帧一致"的判据再动手。

### 6.4 方角外露的处置选项（交维护者决定）
1. **恢复已回退的一对提交**（推荐，已有真机 A/B 证据）：
   ```bash
   git cherry-pick c13f52ce ccbfe7d5     # 含第 3 条离屏回归
   ```
   恢复后按 4.2 复测一次（`ccbfe7d5` 已含加载重试，务必确认面板整片有模糊）。
2. 把轮廓 alpha 直接烘进截图（改 `AcrylicHelper` provider）——涉及 Python/C++ 双实现与 API 变更，成本最高。
3. 把面板轮廓改成直角（`bgCanvas` + 描边同步改）——能消除方角，但属于可见设计变更，需先征得同意。

---

## 7. 本仓纪律（改动前先读根 `AGENTS.md`）

- 所有测试走 `scripts/test_process.py`（强制 offscreen + 私有桌面 + Job Object）；
  **未经发版/生产授权不跑全量测试**，日常只跑与改动直接相关的最小定向测试。
- QML 规范扫描：`python scripts/check_qml_conventions.py --changed --base HEAD`。
- 产物只能落 `.artifacts/`（已 gitignore）；根目录/源码树不得新增散落产物。
- 提交信息用中文；发布提交与 tag 显式推 `prism`。
- 修 BUG 不得改变原有行为与视觉；`de913fdc`/`8b75ac03` 都只是"把错位绘制收回到正确区域"，
  未改布局、交互、层级或对象创建时序。

---

## 8. 快速验收清单

完全重启 Gallery（不要只热重载）→ 展开导航面板：

- [ ] 面板整片有模糊（不是只剩一条）
- [ ] 面板项后面没有错位的第二层
- [ ] 左上角没有方形色块
- [ ] （当前 main 仍会失败）右侧圆角处没有方角的一层 —— 需先按 6.4 处置

若"整片有模糊"不成立，日志中应有 `Acrylic capture never loaded:`（仅恢复 6.4.1 后可能出现的提示），
把它连同 `.artifacts/window-diag/gallery_probe.py` 的 A/B 输出一起附上继续排查。
