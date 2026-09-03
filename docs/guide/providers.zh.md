# 系统服务

PrismQML 内置一组系统级服务对象。Python 侧通过 `get_xxx()` 单例获取；使用
`App` 或 `register_types()` 时，同名上下文属性已注入 QML，QML 中可直接引用。

## 剪贴板 ClipboardHelper

| 方法 | 说明 |
|------|------|
| `copy(text)` | 复制文本到剪贴板 |
| `paste()` | 读取剪贴板文本，无内容返回 `""` |

```python
from prismqml import get_clipboard_helper

get_clipboard_helper().copy("已复制的文本")
```

```qml
Fluent.Button {
    text: "复制"
    onClicked: ClipboardHelper.copy("text")
}
```

## 二维码 QRCodeGenerator

依赖可选包 `qrcode`，未安装时 `available` 为 `False`：

```python
from prismqml import get_qrcode_generator

gen = get_qrcode_generator()
if gen.available:
    url = gen.getImageSource("https://example.com", 256, "#000000", "#ffffff", "M")
```

| 成员 | 说明 |
|------|------|
| `available` | `qrcode` 库是否可用 |
| `getImageSource(content, size, fgColor, bgColor, errorLevel)` | 返回 `image://qrcode/...` URL，交给 QML `Image` 显示 |

`size` 取值 32–1024（默认 128），`errorLevel` 为 `L` / `M` / `Q` / `H`。QML
侧直接用现成控件：

```qml
Fluent.QRCode { content: "https://example.com" }
```

详见 [数据](../components/data.md)。

## SVG 渲染 SvgImageProvider

`App` 启动时已注册 `image://svg` 图片提供器，用 `QSvgRenderer` 高质量渲染
SVG 文件，支持 `sourceSize` 指定渲染尺寸：

```qml
Image {
    source: "image://svg/path/to/icon.svg"
    sourceSize: Qt.size(128, 128)   // 可选
}
```

`image://svg/` 之后是一个 QML URL 组件：保留字符只解码一次，再按 Qt URL
语义解析 file / qrc 来源。

## 屏幕取色 ScreenEyedropperManager

| 成员 | 说明 |
|------|------|
| `startPicking(is_dark)` | 显示跟随鼠标的放大镜并开始取色 |
| `stopPicking()` | 停止取色 |
| `colorPicked(QColor)` | 信号：确认选中颜色 |
| `pickingStarted` / `pickingFinished` / `pickingCancelled` | 信号：取色生命周期 |

```python
from prismqml import get_screen_eyedropper_manager

picker = get_screen_eyedropper_manager()
picker.colorPicked.connect(lambda color: print(color.name()))
picker.startPicking(True)   # True = 放大镜使用深色外观
```

左键或回车确认，右键 / `Esc` / 失焦取消。QML 的 `ColorPicker` 控件已内置
调用入口。

## 单实例 SingleInstance

```python
from prismqml import SingleInstance

instance = SingleInstance("com.example.myapp")
instance.activateRequested.connect(raise_main_window)
if not instance.try_lock():
    return  # 已有实例在运行；本进程已向主实例发送激活消息后退出逻辑
app.exec()
instance.unlock()
```

- Windows 用命名互斥体（`Local\\{app_id}`）加锁，其他平台用 `QSharedMemory`
- 第二实例 `try_lock()` 失败时，会向主实例发送一条激活消息并返回 `False`；
  主实例收到后发出 `activateRequested` 信号，可借此把主窗口提到前台
- 主实例无响应（僵尸锁）时，第二实例自动接管启动
- `app_id` 建议使用反向域名格式；也支持 `with SingleInstance("...") as instance:`
  上下文管理器写法
