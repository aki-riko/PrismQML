# FastSplash 原生快速启动层改造方案

> 状态：方案草案
>
> 日期：2026-08-28
>
> 当前范围：先实现 Windows，保留 macOS、Linux/X11、Linux/Wayland 的扩展边界。

## 1. 目标

本方案只优化 FastSplash 的可见延迟，指标定义为：

```text
T0 = 启动进程/启动器开始执行
T1 = 用户看到第一张有效启动画面
```

不把主窗口 QML 加载、首页创建、DWM 阴影、Mica、Splash 揭幕动画或主窗口可用时间计入 FastSplash 可见延迟。

目标：

| 场景 | 目标 |
|---|---:|
| Windows 冷启动 | p95 <= 100 ms |
| Windows 热启动 | p95 <= 50 ms |
| 首帧视觉 | 与当前 FastSplash 第一帧保持像素一致，或明确记录差异 |
| 切换过程 | 原生启动层切换到 QML FastSplash 时无黑帧、白帧、空白帧和位置跳变 |
| 失败处理 | Qt 启动失败、主进程崩溃或超时后，原生层可自行退出 |

时间目标是本机性能门禁，不是库的官方保证。必须以真实发布构建、真实 Windows 图形环境和多轮样本验证。

## 2. 当前基线

当前 FastSplash 在 `prismqml/python/window/fast_splash.py` 中通过运行时内联 QML 创建：

```text
QQmlEngine()
  -> QQmlComponent.setData()
  -> component.create()
  -> 设置标题/图标/位置
  -> splash.show()
```

用户在 2026-08-28 提供的四次日志中，`FastSplash 独立启动页已显示` 出现在启动后约 `288–309 ms`。现有日志记录的是 `show()` 调用附近的时间，不是第一张实际提交到屏幕的 FastSplash 帧。

当前代码已经移除了图标 `MultiEffect` 阴影，提交为：

```text
d189ff559 性能: 移除 FastSplash 首帧图标阴影
```

这一步保持了 QML 视觉结构，只去掉了首帧效果模块和图标层阴影。

## 3. 方案选择

### 3.1 方案 A：继续使用 QML FastSplash

把内联 QML 抽成真实文件，使用 `qmlcachegen` 预编译，再通过 `createWithInitialProperties()` 注入标题、图标和副标题。

优点：

- 视觉和现有实现最容易保持一致；
- 不增加原生窗口生命周期；
- 可以继续复用 Qt 的窗口和事件循环。

限制：

- 必须先创建 `QApplication` 才能创建 QML 窗口；
- 不能消除 Qt/Python/D3D11 初始化的基础成本；
- 预计只减少几到几十毫秒，不能直接保证冷启动低于 100 ms。

### 3.2 方案 B：平台原生启动层

在 Qt/QML FastSplash 之前显示一个很小的原生窗口。原生层只负责显示预渲染的第一帧，真正的 QML FastSplash 在后台按原有路径创建；当 QML 首帧完成后，原生层立即隐藏。

优点：

- 可以把用户可见画面提前到 `QApplication` 之前；
- 静态首帧使用同一份像素资源时，可以做到像素级一致；
- 不需要在原生层重建完整的 QML 组件树。

限制：

- 这是“提前显示等价画面”，不会让 QML FastSplash 本体更早完成；
- 透明圆角、动态文本、字体抗锯齿和不同平台合成器会影响跨平台像素一致性；
- 需要增加原生窗口、启动握手、打包和异常退出处理。

### 3.3 推荐

先做 Windows 原生启动层，采用两级交付：

1. 进程内 Win32 前端：验证视觉、位置、DPI、首帧切换和生命周期。
2. 独立 Windows Launcher：把原生画面提前到 Python/Qt 初始化之前，争取冷启动 p95 <= 100 ms。

Windows 原生绘制优先使用系统 Win32/GDI API，不引入重量级 UI 框架。核心 API 包括 [`CreateWindowExW`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw)、[`ShowWindow`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow) 和分层窗口更新接口。

## 4. Windows 架构

### 4.1 组件划分

```text
bootstrap/
├── common/
│   ├── splash_frame_format
│   ├── splash_metadata
│   ├── ready_protocol
│   └── timing_probe
└── windows/
    ├── NativeSplashWindow
    ├── NativeSplashRenderer
    └── PrismQMLLauncher
```

在当前仓库中，Windows 代码优先放在现有 `cpp/` CMake 工程边界内；Python 侧只负责启动、传递元数据和在 QML 首帧后通知原生层，不把 Win32 细节散落到 `fast_splash.py`。

### 4.2 原生窗口

Windows 前端使用：

- `WS_EX_LAYERED` 无边框分层窗口；
- 预解码的 BGRA/RGBA 第一帧；
- `UpdateLayeredWindow` 提交像素；
- `SetProcessDpiAwarenessContext` 统一 DPI 感知；
- 工作区几何计算和屏幕居中；
- `WS_EX_TOOLWINDOW` 避免任务栏图标；
- 明确的 owner/父进程关系和关闭路径。

首帧不在启动阶段解码 PNG。资源构建阶段将当前 FastSplash 第一帧转换为适合直接提交的像素数据，避免把图片解码时间放进 T1。

### 4.3 元数据

要做到首帧像素一致，原生层在显示前必须已经知道：

- 标题；
- 副标题；
- 图标；
- 主题明暗；
- 窗口尺寸；
- DPI 和屏幕位置。

如果这些值只能在 Python/Qt 启动后才能得到，则原生层只能显示通用第一帧，不能承诺完全一致。API 设计需要区分：

- 固定品牌资源：构建期预渲染；
- 启动参数可知资源：Launcher 参数传递；
- 运行时才知道的资源：允许第二帧更新，但不宣称首帧像素一致。

### 4.4 进程内模式

进程内模式用于第一阶段快速验证：

```text
Python 入口
  -> NativeSplashWindow.show()
  -> 创建 QApplication
  -> 创建当前 QML FastSplash
  -> FastSplash 首帧 frameSwapped
  -> NativeSplashWindow.hide()
```

该模式可以验证切换和视觉，但因为 Python 进程已经启动，不能保证完整冷启动低于 100 ms。它的价值是先把窗口行为、DPI、透明度和无闪切换做正确。

### 4.5 独立 Launcher 模式

要争取硬性冷启动目标，使用独立的 `PrismQMLLauncher.exe`：

```text
Launcher.exe 启动
  -> 显示原生第一帧
  -> CreateProcess 启动 Python/Qt 应用
  -> 应用创建 QApplication 和 QML FastSplash
  -> 应用收到 FastSplash 首个 frameSwapped
  -> 应用 SetEvent(READY)
  -> Launcher 隐藏并退出
```

Windows 第一版使用命名事件作为握手：

- Launcher 创建唯一事件名并传给子进程；
- 子进程在 FastSplash 首帧后调用 `SetEvent`；
- Launcher 同时等待 READY、子进程退出和超时；
- 子进程崩溃或超时，Launcher 隐藏原生窗口并返回明确错误码；
- 事件名、进程句柄和临时资源都在退出路径清理。

不使用固定名称，不把路径、密钥或用户数据写入命令行。

## 5. 视觉一致性策略

### 5.1 第一阶段：静态首帧

第一阶段只保证当前 FastSplash 的首帧画面：

- 背景；
- 图标；
- 标题；
- 副标题；
- 圆角和透明边缘；
- 当前窗口尺寸和位置。

原生窗口显示静态帧，QML FastSplash 负责后续 spinner、呼吸动画和揭幕动画。切换只发生一次，不做淡入淡出，避免增加可见时间。

### 5.2 第二阶段：局部动画

如果静态帧切换已经满足速度目标，再考虑原生层播放小范围动画：

- 只缓存 spinner 的局部帧；
- 不保存多张完整 `1200x800` 图片；
- 原生层只更新变化区域；
- QML 首帧准备好后立即交给 QML。

这部分不是冷启动硬门禁，不能为了动画而延后第一张有效画面。

## 6. Windows 分阶段实施

### W0：基线和测量

工作量：`0.5 天`

- 在 FastSplash 控制器记录 `show()` 调用时间；
- 在 `_on_splash_frame()` 记录第一帧时间；
- 将进程启动、原生窗口显示、QML 首帧、原生窗口隐藏分开记录；
- 建立冷启动/热启动各 20 次的样本文件；
- 保留当前去阴影版本作为基线。

验收：能够单独回答 `T0 -> T_native_visible` 和 `T0 -> T_qml_first_frame`，不再使用 `show()` 日志代替真实可见时间。

### W1：第一帧资源管线

工作量：`0.5–1 天`

- 从当前 FastSplash 生成固定尺寸和 DPI 的第一帧；
- 输出 BGRA/RGBA 原始资源；
- 保留源 PNG 仅用于视觉比对和回滚；
- 定义动态标题、副标题和主题不匹配时的降级规则。

验收：同一 Windows/DPI 下原生帧和 QML 首帧像素差异为零，或差异有明确报告。

### W2：进程内 Win32 前端

工作量：`1–1.5 天`

- 实现 `NativeSplashWindow`；
- 完成分层窗口、DPI、屏幕定位、显示和销毁；
- 接入当前 Python App 的启动和 FastSplash 首帧通知；
- 失败时自动回退到当前 QML FastSplash；
- 不改变现有 QML FastSplash 的内容和揭幕逻辑。

验收：无黑帧、无白帧、无位置跳变；重复启动和异常退出不会遗留窗口。

### W3：独立 Launcher

工作量：`1.5–2 天`

- 实现 `PrismQMLLauncher.exe`；
- 加入命名事件 READY 握手；
- 等待子进程 READY、退出和超时；
- 支持开发入口和正式打包入口；
- 记录 Launcher 自身的启动和隐藏时间。

验收：应用崩溃、启动失败、用户提前关闭和超时都能清理原生窗口；正常路径不会重复创建两个可见启动层。

### W4：集成和回退

工作量：`1–1.5 天`

- 将 Launcher 接入 Windows 发布入口；
- 保留无 Launcher 的开发模式；
- 保留当前 QML FastSplash 作为回退；
- 不改变 `App`、`Window` 和 `splash_subtitle` 的现有公开行为；
- 处理已有快捷方式、命令行参数和工作目录。

验收：现有应用入口仍能启动；关闭原生层后 QML FastSplash 生命周期和原有揭幕不变。

### W5：性能和发布验证

工作量：`1.5–3 天`

- Windows D3D11 真实窗口验证；
- 冷启动和热启动各至少 20 个交错样本；
- p50、p95、最大值和失败样本记录；
- 不同 DPI 和多屏位置验证；
- 普通启动、路径含空格、非 ASCII 用户目录和无网络环境验证；
- 检查正式包不依赖开发机路径和临时资源。

验收门禁：

```text
冷启动 p95 <= 100 ms
热启动 p95 <= 50 ms
首帧视觉差异符合既定阈值
无遗留进程、窗口或临时句柄
```

## 7. Windows 工作量结论

| 交付级别 | 工作量 | 结果 |
|---|---:|---|
| 进程内原生前端 MVP | `2–3 天` | 验证视觉、DPI、切换和生命周期 |
| 加独立 Launcher | `再加 1–2 天` | 具备冲击冷启动 `<100 ms` 的结构 |
| Windows 可发布版本 | `7–10 天总计` | 含打包、回退、异常处理和真实性能门禁 |

因此，之前给出的“Windows-only 3–5 天 MVP、7–10 天稳定版本”仍然成立：

- `3–5 天`：原生窗口 + Launcher + 基础真实测量；
- `7–10 天`：发布集成、异常路径、视觉回归、多 DPI 和性能门禁。

如果只做进程内版本，代码会更少，但它不能把“从进程启动到用户看到画面”稳定压进 100 ms；要把 100 ms 作为实际目标，独立 Launcher 不是可选项。

## 8. 跨平台扩展

Windows 版本稳定后再扩展：

### macOS

- `NSWindow` 无边框透明窗口；
- `CGImage`/CoreGraphics 提交预渲染帧；
- `backingScaleFactor` 处理 Retina；
- AppKit 主线程和 `.app` 签名、公证；
- 预计 `2–3 天` 前端，另加打包和验证时间。

### Linux X11

- XCB/Xlib ARGB Visual；
- XRender 或共享内存像素缓冲；
- 屏幕和 compositor 适配；
- 预计 `1.5–2.5 天` 前端。

### Linux Wayland

- `xdg-shell`；
- `wl_shm` 和 `wl_buffer`；
- 透明度、置顶、激活和关闭行为受 compositor 影响；
- 预计 `2.5–5 天` 前端和兼容性验证。

跨平台完整版本预计 `12–20 天`，其中 Wayland、动态文字和平台打包是不确定性最高的部分。

## 9. 不在本阶段做的事情

- 不把 FastSplash 改成另一个完整 UI 框架；
- 不引入 OpenGL，Windows 继续保持 D3D11 唯一路径；
- 不改变 QML FastSplash 的揭幕时长和主窗口 ready 门禁；
- 不在启动层执行网络、磁盘扫描、数据库读取或业务初始化；
- 不为了性能删除现有品牌信息或改变公开 API；
- 不运行 Nuitka 打包验证，除非获得当前任务的明确授权；
- 不把原生启动窗口永久保留为第二套应用窗口。

## 10. 回滚方案

回滚必须保持可逆：

1. 保留当前 QML FastSplash 路径作为默认回退。
2. 原生启动层通过显式开关接入，不覆盖现有 `FastSplashController` 公共行为。
3. Launcher 启动失败时直接执行原有应用入口。
4. 原生窗口异常时立即销毁窗口并继续 QML 路径。
5. 性能或视觉门禁不通过时，只撤销启动层入口和资源，不删除现有 QML 实现。

## 11. 下一步

下一步先执行 W0：补齐 FastSplash 首个 `frameSwapped` 的真实时间戳，建立去阴影版本的 Windows D3D11 基线。基线确认后再实现 W1/W2，先验证进程内原生窗口的视觉和切换，再决定是否接入独立 Launcher。
