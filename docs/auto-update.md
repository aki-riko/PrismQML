# PrismQML 自动更新接入

PrismQML 的自动更新由两层组成：Python `Updater` 负责读取 GitHub Latest Release、版本比较、安全下载和启动安装器；QML `AutoUpdater` 负责更新确认、下载反馈和安装交接。应用不应重复实现网络、进度 Toast 或安装器启动逻辑。

完整流程为：

```text
检查 Latest Release
→ 发现新版并确认
→ 下载同平台安装资产
→ 同一反馈控件原位刷新进度
→ 校验 SHA-256
→ 按安装策略交接
→ `in_place`：启动安装器并退出当前应用
→ `dual_slot`：后台写入非活动槽，当前应用继续运行
→ 下次启动自动切换到新版
```

## 1. 发布资产约定

`Updater` 默认读取 `OWNER/REPO` 的 GitHub Latest Release。Release 必须满足：

- tag 可与当前版本比较，例如 `v1.2.3`；
- Release 已公开，且不是草稿或预发布；
- 包含当前平台可执行的资产：Windows `.exe`、macOS `.dmg` / `.pkg`、Linux `.AppImage` / `.run` / `.deb`；
- 资产名包含应用配置的关键词，例如 `ExampleApp-Setup-1.2.3.exe` 包含默认关键词 `Setup`；
- GitHub API 返回资产的 `sha256:<64位十六进制>` `digest`。PrismQML 默认要求摘要，并在下载完成后再次校验。

如果没有匹配的当前平台资产，更新确认后会打开 Release 页面，而不会把任意文件当成安装器。

## 2. 注入 Python 更新后端

使用 `App` 时，在创建 `App` 后、加载消费 `appUpdater` 的 QML 前调用 `enable_auto_update()`：

```python
from prismqml import App

CURRENT_VERSION = "v1.2.3"
UPDATE_REPOSITORY = "OWNER/REPO"
UPDATE_ASSET_KEYWORD = "Setup"

app = App()
app.enable_auto_update(
    UPDATE_REPOSITORY,
    CURRENT_VERSION,
    UPDATE_ASSET_KEYWORD,
    install_strategy="dual_slot",
)

# 继续创建窗口、加载页面并调用 app.exec()。
```

该调用创建 `Updater`，强制启用 Release 资产摘要校验，并以 `appUpdater` 注入 QML 根上下文。`dual_slot` 会让本次运行继续使用旧槽，安装完成后由启动入口自动切到新槽。应用通常不需要直接连接底层信号。

自行创建 `QQmlApplicationEngine` 时，可以显式创建 `Updater` 并注入同名上下文属性；初始化 QML 环境和注册类型仍由宿主负责：

```python
from prismqml import Updater

updater = Updater("OWNER/REPO", "v1.2.3", "Setup", install_strategy="dual_slot")
updater.set_require_artifact_digest(True)
engine.rootContext().setContextProperty("appUpdater", updater)
```

必须让 Python 持有 `updater`，直至应用退出。

## 3. 接入 QML 门面

默认 Presenter 是右下角 Toast。一个应用窗口只创建一个 `AutoUpdater`：

```qml
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    Fluent.AutoUpdater {
        id: autoUpdater

        updater: appUpdater
        autoDownload: true
        notifyWhenUpToDate: true
        silentArgs: Qt.platform.os === "windows"
            ? "/SILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
            : ""
    }

    Timer {
        interval: Fluent.Enums.duration.toast
        running: true
        repeat: false
        onTriggered: autoUpdater.checkSilently()
    }

    Fluent.Button {
        text: "检查更新"
        onClicked: autoUpdater.check()
    }
}
```

`check()` 是可见的手动检查；当 `notifyWhenUpToDate=true` 时，已是最新版也会显示反馈。`checkSilently()` 用于启动检查，不显示“正在检查”、已是最新版或检查失败 Toast；如果确实发现新版，仍会打开更新确认框。

下载开始后，默认 Toast Presenter 只创建一次反馈对象。后续进度通过属性更新同一对象，不会每次收到进度信号都重新弹 Toast：

```text
43%  (20.0 MB / 46.5 MB)
```

服务端尚未提供总大小时显示不确定进度和已下载字节；首次获得有效总大小后自动切换为确定进度。

## 4. 切换进度展示器

需要模态进度窗口时，将 `feedbackPresenter` 换成 `AutoUpdaterProgressDialogPresenter`：

```qml
Component {
    id: updateProgressPresenter

    Fluent.AutoUpdaterProgressDialogPresenter {}
}

Fluent.AutoUpdater {
    updater: appUpdater
    feedbackPresenter: updateProgressPresenter
}
```

需要恢复 Toast 时使用 `AutoUpdaterToastPresenter`。不要在业务层同时监听下载信号再创建第二套 Toast，否则会产生重复反馈。

## 5. Windows 安装器模板

先复制 [安装器示例清单](examples/prismqml-installer.json)，为应用固定 `app_id`、`aumid`、安装范围和 Nuitka standalone 目录。需要双槽替换安装时，将：

```json
"install_strategy": "dual_slot"
```

若仍使用 `in_place` 并要求安装后立即重启，新安装清单可设 `launch_after_install=true`；双槽已有安装不会在本次会话启动新版。

然后按同一应用版本生成并检查 Inno Setup 脚本：

```powershell
prismqml-installer generate --manifest prismqml-installer.json --version 1.2.4 --output installer.iss
prismqml-installer check --manifest prismqml-installer.json --version 1.2.4 --output installer.iss
prismqml-installer doctor --manifest prismqml-installer.json
```

完整字段和编译命令见 [Windows 安装器模板](windows-installer.md)。生成结果会使用：

- `CloseApplications=no`（双槽）：不关闭当前应用，完整写入非活动槽；
- `RestartApplications=no`：不让 Restart Manager 再启动一次，避免双开；
- `prism-update-slot.ini`：记录下次启动目标槽；
- `App` 启动重定向：旧快捷方式/任务栏入口也会自动进入目标槽；
- 稳定 `AppId`：新版覆盖同一安装，而不是创建第二个应用。

## 6. 安装参数选择

Windows 运行参数由应用传给 `AutoUpdater.silentArgs`：

| 参数 | 用户看到的效果 | 推荐场景 |
|------|----------------|----------|
| 空字符串 | 完整 Inno Setup 向导 | 需要用户逐步选择 |
| `/SILENT /SUPPRESSMSGBOXES /NORESTART /SP-` | 隐藏向导，但显示安装进度窗口 | 默认自动更新体验 |
| `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` | 向导和安装进度窗口都隐藏 | 确实需要完全无界面安装 |

机器级安装仍可能显示 Windows UAC 提示，这是操作系统安全边界。双槽更新不使用 `/RESTARTAPPLICATIONS` 或 `/AUTORESTARTAPP`，也不会在本次运行中重启应用。

## 7. 端到端验收

源码测试不能代替打包安装验收。正式发布至少验证：

1. 版本号、Release tag、安装器文件名与安装后 EXE 产品版本一致；
2. 安装器脚本 `check` 无漂移；
3. 在一次性 Windows runner 上运行 Nuitka 和 ISCC；
4. 使用与应用相同的 `/SILENT` 参数安装到隔离目录，并保留安装日志；
5. 核对安装退出码、卸载注册信息、安装目录和产品版本；
6. `dual_slot` 时确认旧进程仍可操作、非活动槽完整写入，随后从旧快捷方式启动并自动跳转新版；
7. 结束自动启动的进程，再从安装目录执行 packaged SELFTEST；
8. 只有全部通过后，才把安装包附加到公开 Release。

用户侧升级验收应使用两个真实版本：先安装旧版，再发布新版并执行手动检查。确认启动检查不弹 Toast、手动检查有反馈、下载显示 `xx MB / xx MB`、同一 Toast 原位刷新、应用退出后出现安装进度窗口、安装完成后自动启动且版本已更新。

## 8. 常见问题

| 现象 | 检查项 |
|------|--------|
| 启动时弹“正在检查”Toast | 启动入口是否调用 `checkSilently()`，而不是 `check()` |
| 每次进度都重弹 Toast | 是否创建了多个 `AutoUpdater`，或业务层另建了一套下载 Toast |
| 只有已下载大小，没有总大小 | 服务器是否返回有效的下载总长度；获得总长度后会自动切换 |
| 找到新版但没有安装包 | Release 资产后缀或 `asset_keyword` 是否匹配当前平台 |
| 报资产摘要缺失或校验失败 | GitHub API 的资产 `digest` 是否存在且与下载内容一致 |
| 安装时完全没有进度窗口 | 是否误用了 `/VERYSILENT`；需要进度窗口时改为 `/SILENT` |
| 双槽安装后仍进入旧版 | 检查 `prism-update-slot.ini` 的 `LaunchSlot`、目标槽 EXE 和 `App` 是否使用默认槽重定向 |
| 安装后启动两次 | 是否同时启用了 Restart Manager 重启和 `[Run] postinstall` |

Gallery 的真实/DRY 演示见 `examples/pages/AutoUpdatePage.qml`；DRY 模式会模拟双槽准备与下次启动切换，不访问网络、创建文件或启动安装器。
