# 窗口

PrismQML 通过 `App.create_window(WindowType)` 创建带导航的主窗口。

## 窗口类型

| 类型 | 枚举值 | 说明 |
|------|--------|------|
| `WindowType.BAR` | 1 | 紧凑侧边导航（默认） |
| `WindowType.SPLIT` | 0 | 展开式侧边导航 |
| `WindowType.FILLED` | 2 | 填充式分割窗口 |

```python
from pathlib import Path

from prismqml import App, WindowType

app = App(application_icon=Path(__file__).with_name("app_icon.png"))

window = app.create_window(WindowType.BAR)     # 紧凑侧边导航
# window = app.create_window(WindowType.SPLIT) # 展开式侧边导航
# window = app.create_window(WindowType.FILLED)# 填充式分割
```

应用图标在 `App` 层配置一次即可；现有窗口、后续窗口、任务栏和默认启动画面会自动
继承。只有需要单独覆盖某个窗口时，才调用该窗口的 `setWindowIcon()`。

## 添加导航页面

```python
window.addPage(HomePage, "Home", "首页")        # QML 组件, 图标名, 标题
window.addPage(SettingsPage, "Settings", "设置")
window.show()
```

## 窗口特性

- **懒加载** — 页面内容延迟到首次切换时加载，加快启动
- **云母效果（Mica）** — Windows 11 半透明背景（非 Fluent 皮肤下自动关闭，以保持各自表面范式）
- **系统托盘** — 见 [系统托盘](tray.md)
- **启动画面** — `SplashScreen` 首屏就绪后自动淡出（默认挂载）

## 启动画面

启动画面由 `NavigationWindowCore` 统一创建、覆盖窗口并等待首页就绪；窗口可见后
默认至少稳定展示 600ms，再播放退场动画。Python、C++ 和纯 QML 使用同一套生命周期。
宿主只传配置，不需要自行创建组件：

```python
window.showSplash(title="PrismQML", subtitle="正在加载组件...")
# window.setSplashEnabled(False)  # 按需关闭
```

```cpp
window.setSplash(true, {}, {}, QStringLiteral("正在加载组件..."));
```

```qml
import PrismQML as Fluent

Fluent.Windows {
    windowTitle: "My App"
    windowIcon: "qrc:/app_icon.svg"
    splashSubtitle: "正在加载..."
    // 可按产品需要覆盖；默认值来自 Enums.duration.splashMinimumVisible。
    splashMinimumVisibleDuration: 600
}
```

主窗口关闭时也复用同一套 `PageTransition`。默认使用
`Enums.lazyAnimation.lazy_circle` 收紧窗口内容；关闭确认完成后先播放收紧，动画完成
才提交真实关闭。关闭请求被宿主否决时，过渡会调用 `stop()` 恢复原页面。

```qml
Fluent.Windows {
    closeAnimationType: Enums.lazyAnimation.lazy_circle
    closeAnimation: null
}
```

`closeAnimationType: Enums.lazyAnimation.none` 会跳过视觉过渡并同步进入真实关闭；设置
`Enums.lazyAnimation.custom` 时，`closeAnimation` 使用前文相同的 `Component` 合同。
因此启动画面、懒加载页面和主窗口退场可以共享同一套内置或自定义生命周期。

收紧节奏由主窗口退场与页面切换共用：时长取
`Enums.lazyLoadingTransitionMetrics.coverDuration`（420ms），缓动取
`Easing.InOutQuad`。收紧的 progress 由 1 走到 0、半径随之线性缩放，所以 ease-in 类
曲线会让半径在大部分时长里几乎不动，最后几帧才跨完剩余全部距离；在低刷新率屏幕上，
观感就是窗口在收到一半时被直接切掉。真机实测两处节奏完全相同，因此共用一套值。

`PageTransition` 公开 `coverDuration` 与 `coverEasing`，自定义过渡可单点覆盖：

```qml
Fluent.PageTransition {
    coverDuration: 360
    coverEasing: Easing.InOutCubic
}
```

调整 `coverDuration` 时注意：懒加载页面切换的 Loader 激活预算由它推导（`coverDuration`
加 `loaderActivationHeadroom`），因此改收紧时长不会挤掉加载指示器的可见时间。

### 启动画面退场动画

默认 `SplashScreen` 使用 `Enums.lazyAnimation.lazy_circle`：它与懒加载页面的收紧/展开过渡共用同一套生命周期。窗口级属性会转发到默认启动画面：

```qml
Fluent.Windows {
    splashExitAnimationType: Enums.lazyAnimation.none
    // 或：Enums.lazyAnimation.lazy_circle（默认）
    // splashExitAnimation: mySplashTransition
}
```

`SplashScreen` 也可以直接配置同名属性：

```qml
SplashScreen {
    exitAnimationType: Enums.lazyAnimation.lazy_circle
    exitAnimation: null
}
```

启动画面退场模式通过 `Enums.lazyAnimation` 访问；普通 `StackedWidget` 切页模式才使用 `Enums.animation`：

| 值 | 行为 |
| --- | --- |
| `Enums.lazyAnimation.none` | 不创建过渡后端，`finish()` 同步完成并隐藏启动画面。 |
| `Enums.lazyAnimation.lazy_circle` | 默认圆形收紧/展开过渡；保留首帧、目标页换帧和失败回退语义。 |
| `Enums.lazyAnimation.custom` | 使用 `exitAnimation` / `splashExitAnimation` 提供的 `Component`。 |

自定义 `Component` 必须实现以下合同。方法的 `sourceItem` 参数是当前要收紧或展开的源项；状态和信号由 `PageTransition` 读取与转发。

```qml
Component {
    Item {
        property bool active: false
        property bool running: false
        property bool collapsing: false
        property bool collapsed: false
        property real progress: 0

        signal collapseStarted()
        signal collapseFinished()
        signal expandStarted()
        signal expandFinished()

        function collapse(sourceItem) { /* ... */ return true }
        function expand(sourceItem) { /* ... */ return true }
        function stop() { /* cancel and restore your state */ }
    }
}
```

`collapse()` / `expand()` 应在开始和完成时分别发出对应信号，并在 `progress`、`collapsing`、`collapsed` 等状态上保持一致；`stop()` 用于取消当前操作。调用 `finish()` 时，默认启动画面会调用 `expand(sourceItem)`，完成信号到达后才隐藏并发出 `finished()`。懒加载页面通常先调用 `collapse(sourceItem)`，切换内容后再调用 `expand(sourceItem)`。

当 `Component` 缺少合同成员、创建失败或内置过渡无法捕获源项时，门面会记录错误并按无动画路径发出开始/完成信号，保证源项处于确定的最终可见性；自定义实现应让 `stop()` 可重复调用。动画完成后门面会释放源项引用，避免下一次 `stop()` 重新显示已经完成收紧的旧页面。

纯 QML 窗口还可以通过 `splashComponent` 替换视觉组件；自定义根对象必须提供
`finish()` 方法，框架会在首页就绪时调用它。

纯 QML 的 `Fluent.Windows` 会在对象创建完成时自动注册到 App 的启动页生命周期，
无需宿主手动调用内部绑定方法。非标准 QML 窗口可通过公开的
`app.attach_startup_window(window)` 接入同一套 FastSplash 生命周期。

### PageTransition

需要在页面或其他覆盖层复用同一套过渡时，可直接使用公开的 `PageTransition`：

```qml
PageTransition {
    id: transition
    animationType: Enums.lazyAnimation.lazy_circle
    revealTarget: true

    function showPage(page) {
        transition.expand(page)
    }
}
```

它公开 `collapse(sourceItem)`、`expand(sourceItem)`、`stop()` 方法，以及 `active`、`running`、`collapsing`、`collapsed`、`progress` 状态和四个生命周期信号。`customAnimation` 属性接受上面的 `Component` 合同；自定义模式推荐同时设置 `animationType: Enums.lazyAnimation.custom`。`animationType: Enums.lazyAnimation.none` 会绕过动态加载并同步发出开始/完成信号。

懒加载页面默认使用 `Enums.lazyAnimation.lazy_circle`，它与普通 `StackedWidget`
切页动画相互独立。

!!! tip "非 Fluent 皮肤下的窗口"
    新粗野、复古票据与新拟态都会自动关闭 Mica，并切换到各自的表面、边框、
    阴影与导航状态。这些都由皮肤系统处理，无需手动配置。
