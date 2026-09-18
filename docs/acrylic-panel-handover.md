# 导航面板亚克力显示问题 — 交接文档

> 范围：`WindowsSplit`（设置里"窗口类型 = Window"）左侧导航面板的亚克力背景显示异常。
> 结论状态：4 个缺陷已定位并修复（`de913fdc` → `ccbfe7d5`，已 push `prism/main`），
> 真机 A/B 与离屏像素回归均已通过；第 6 节列出仍未解决/被否决的路线。

---

## 1. 症状（用户视角）

| 症状 | 出现位置 | 状态 |
|------|----------|------|
| 方形色块（浅色偏白、暗色偏蓝，约 8×8 逻辑像素） | 窗口左上角 | 已修 `de913fdc` |
| 面板项后面一层**错位**的模糊重影（"上面一层下面一层"） | 整个面板 | 已修 `8b75ac03` |
| 面板外侧露出**方角的一层**（"没有圆角的那层"） | 面板右上、右下圆角处 | 已修 `c13f52ce` |
| 面板整片没有模糊，只剩右缘一条 | 整个面板 | 我引入的回归，已修 `ccbfe7d5` |

---

## 2. 结构背景（排查前必读）

- `prismqml/PrismQML/_internal/WindowsSplit.qml`
  - 面板容器 `navContainer`：`anchors.topMargin: -window.titleBarHeight` → **比窗口高一个标题栏**。
  - 其内 `NavigationView` 自身尺寸 **320×848**（逻辑），窗口内可见部分是 **320×800**。
- `prismqml/PrismQML/navigation/_internal/NavigationPanelBackground.qml` 三层：
  1. **Layer A `bgCanvas`**：面板底色。路径为"贴窗口一侧直角 + 右侧圆角（右上圆角从 `titleBarHeight` 起，即窗口顶边处）"。
  2. `TicketPaper`：票据皮肤纸纹（fluent 下不可见）。
  3. **Layer B 亚克力**：模糊截图 + 着色（`Enums.stateColor.acrylicTintColor`）。
- 图源：`AcrylicHelper.grabAndBlur(window, 0, 0, navExpandWidth, window.height)`
  → 抓的是**窗口内**的面板区域 **320×800**，由 `image://acrylic/<id>` provider 提供；
  与 Layer B 所在的 320×848 矩形**面积不一致** —— 这是其中两个缺陷的共同根。
- 展开时机：`WindowsSplit.onAboutToExpand` 抓图 → `acrylicEnabled` 变真。

---

## 3. 四个根因与修法

### 3.1 左上角色块 — `de913fdc`
亚克力层里另叠了两块"角填充"矩形（注释写 `Fill top-left/bottom-left corner (no radius)`），
其 `Image` 用 `anchors.right / anchors.bottom` 对齐 → **左上角显示的是模糊图右下角那块区域**
（面板底部选中高亮，因此偏蓝）。它的内边界是直角，所以同时看着像"色块 + 尖角"。

修法：删除这两块冗余填充（亚克力层按外接矩形裁剪，四个角象限本已覆盖，补填充只会用错位区域重绘角落）。

### 3.2 错位重影 — `8b75ac03`
`Image { anchors.fill: parent; fillMode: Image.PreserveAspectCrop }` 把 320×800 的截图铺到 320×848 的层上
→ 纵向放大 **848/800 ≈ 1.06**，并整体上移一个标题栏 → 真实内容后面多一层错位副本。

修法：按截图自身尺寸落位（`y: titleBarHeight`，`height: parent.height - titleBarHeight`）。
真机观测：亚克力 `QQuickImage` 几何 `(0,0,320,848)` → **`(0,48,320,800)`**。

### 3.3 方角外露 — `c13f52ce`
Layer B 是 `Image` + 着色矩形**铺满整层**的矩形面，而面板轮廓右侧是圆角
→ 两块方角画到了圆角面板之外，就是用户看到的"没有圆角的那一层"。

修法：改为 `Canvas` 按面板轮廓裁剪绘制：`clip()` 走与 `bgCanvas` 同一条路径
（左侧直角、右侧自标题栏下方起圆角），再 `drawImage` + 填充着色。

### 3.4 首帧加载竞态（我引入的回归）— `ccbfe7d5`
`Canvas` 按 URL **异步**加载图像，最初的实现只重试一次（16ms）：图还没解码完就放弃，
之后不再重绘。本机快所以画出来了，用户机器上整片没有亚克力（只剩边缘一条）。

修法：有界重试循环（16ms × 180 次 ≈ 3 秒，一旦某次绘制发现 `isImageLoaded` 为真就停止；
超时 `console.warn("Acrylic capture never loaded: ...")` 留痕）。

---

## 4. 验证方法与实测结果

### 4.1 离屏像素回归（自动，进仓库）
`tests/qml/test_navigation_panel_acrylic_corner.py`，复刻 WindowsSplit 容器高度
（容器 y=-48、高 848）+ 上半红/下半绿 320×800 合成图，三条断言：

1. 角落必须取面板**顶部**那块图像区域 —— 改前 `corner=#acf7ac`（取到下半部）失败；
2. 截图中线必须落在窗口中线上 —— 改前 `above=#acf7ac`（被拉伸上移）失败；
3. 亚克力不得越出圆角轮廓（右上/右下角象限）—— 改前两处被填满，失败。

运行：

```bash
python scripts/test_process.py --qt-platform offscreen --timeout 120 -- \
  python -m pytest tests/qml/test_navigation_panel_acrylic_corner.py -q
```

### 4.2 真机 A/B（关键：只看离屏会漏判）
`gallery_probe.py` 在同一实例、同一状态下把亚克力**开/关**各抓一帧逐像素求差，
差集即"亚克力真正画到的像素"：

| 检查点（物理像素） | 结果 | 含义 |
|---|---|---|
| y=600 行 x=40…440 | 全部 `changed` | 面板**整片**有模糊 |
| TR 圆角外 (478,2) | 两帧一致（未绘制） | 方角**不越界** |
| BR 圆角外 (478,1197) | 两帧一致 | 方角不越界 |
| 轮廓内 (466,14)/(466,1186) | `changed` | 面板内侧正常上模糊 |

> 判定几何：面板右缘物理 480、轮廓半径 8 逻辑像素 = 12 物理，两段圆弧圆心
> `(468,12)` / `(468,1188)`；**距离 > 12 的点才算圆角之外**（第一轮我把采样点取在了圆角内侧，
> 那次"越界"结论是错的，已纠正）。

### 4.3 回归面
定向联合 `17 passed`（本文件 3 条 + `test_root_navigation_conventions.py` +
`test_navigation_window_core_conventions.py` + `test_qml_architecture.py::test_navigation_panel_keeps_background_layer_modularized`）；
`scripts/check_qml_conventions.py --changed` = 0 violation。

---

## 5. 诊断工具（下次直接用）

| 工具 | 位置 | 用途 |
|---|---|---|
| `scripts/manual/window_corner_probe.py` | 已入库 | 裸 `Window` 宿主：item 树 + 只渲染 QML 的抓帧 + 角像素，判断"哪里根本没有 QML 绘制"（`alpha=0` 即露出 DWM 背板/桌面） |
| `.artifacts/window-diag/gallery_probe.py` | 临时（未入库） | 跑**真实 Gallery**（App 装配 + main.qml）：展开面板、亚克力开/关 A/B 求差、item 树、`QQuickImage` 几何、`Canvas.isImageLoaded` |
| `.artifacts/window-diag/*.png` / `*.txt` | 临时 | 现场证据图与报告 |

经验：
- 只渲染 QML 用 `qwindow.grabWindow()`；屏幕抓帧要按 DPR 换算偏移（Qt 放大位图但不换算 x/y），且窗口必须在前台，否则抓到别的窗口。
- `probe` 脚本写报告时，若中途异常会**不写报告**，grep 输出时别把上次的旧报告当新结果。

---

## 6. 未解决 / 已否决（重要，别重复踩）

1. **亚克力是展开瞬间的静态快照**：展开后悬停、滚动、切页都不会更新背景，窗口极端缩放时是一次性拉伸。
   属于设计问题；要做成实时的需换机制（周期性重抓，或改用 DWM 原生亚克力）。
2. **导航滚动轨**：`NavigationScrollRail`（`stateColor.scrollTrack` / `scrollHandleDefault`，
   几何约 `x=308..314` 逻辑、宽 6、悬停或滚动后显形）会在面板右缘形成一条很淡的竖带。
   用户曾用箭头指向它，**未确认是否需要改**（如要改：静止不画 track / 收窄 / 裁进列表可视区）。
3. **已试过但不可用的遮罩路线**（不要再原样重试）：
   - `MultiEffect` / `OpacityMask` 作为 `layer.effect`：
     * 在 **offscreen 平台完全不渲染**（探针实测 `maskedBlock = #ffffff`）→ 会让仓库既有的离屏 QML 探针看不到亚克力；
     * 真机上用内联 `Rectangle` 作 `maskSource` 会被**忽略**，亚克力方角照旧越界；
     * 换成 `ShaderEffectSource { sourceItem: ... }`（TeachingTour 的写法）在真机 A/B 下**仍未切掉方角**。
   - 若日后要回到 GPU 遮罩，先写"真机 A/B：圆角外点必须两帧一致"的判据再动手。
4. **Canvas 路线的未知项**：DPR≠1 时 `Canvas` 默认 `tileSize`（1024）是否影响大尺寸绘制完整性未验证；
   若再遇到"只剩一条"，先查 `isImageLoaded` 与重试日志。
5. 首帧加载超过 3 秒会 `console.warn` 并保持无模糊，直到图源变化（有界重试的取舍）。

---

## 7. 本仓纪律（改动前先读根 `AGENTS.md`）

- 所有测试走 `scripts/test_process.py`（强制 offscreen + 私有桌面 + Job Object）；
  **未经发版/生产授权不跑全量测试**，日常只跑与改动直接相关的最小定向测试。
- QML 规范扫描：`python scripts/check_qml_conventions.py --changed --base HEAD`。
- 产物只能落 `.artifacts/`（已 gitignore）；根目录/源码树不得新增散落产物。
- 提交信息用中文；发布提交与 tag 显式推 `prism`。
- 修 BUG 不得改变原有行为与视觉；本轮改动都只是"把错位/越界的绘制收回到正确轮廓内"，
  未改布局、交互、层级或对象创建时序。

---

## 8. 快速验收清单

完全重启 Gallery（不要只热重载）→ 展开导航面板：

- [ ] 面板整片有模糊（不是只剩一条）
- [ ] 面板项后面没有错位的第二层
- [ ] 右侧圆角处没有方角的一层
- [ ] 左上角没有方形色块

若第 1 项不成立，日志中应有 `Acrylic capture never loaded:` —— 把它连同
`.artifacts/window-diag/gallery_probe.py` 的 A/B 输出一起附上继续排查。
