# PrismQML Windows 安装器模板

`prismqml-installer` 根据一个小型 JSON 清单确定性生成 Inno Setup 脚本，并提供显式编译入口。`doctor`、`generate`、`check` 和 `compile --dry-run` 都不会调用 ISCC；只有用户明确运行 `compile` 才会调用已安装的 ISCC。工具不会运行 Nuitka，也不会执行生成的安装程序。

## 行为合同

`install_strategy` 默认是 `in_place`。需要“当前会话不退出、下次启动切新版”时设为 `dual_slot`。

`in_place` 模板固定以下升级行为：

- `AppId` 在所有版本中保持不变，新版覆盖同一安装；
- `CloseApplications=yes`，安装时允许 Inno Setup 关闭占用旧文件的进程；
- `RestartApplications=no`，不依赖 Restart Manager 自动恢复应用，避免重复启动；
- `launch_after_install=false`（默认）时 `[Run]` 使用 `skipifsilent`，静默更新等待用户下次启动；设为 `true` 时，静默安装完成后从新安装目录启动一次新版；
- 用户级安装写入 `{localappdata}\Programs` 且不主动请求管理员权限；
- 机器级安装写入 `{autopf}`，Windows 仍会显示无法绕过的 UAC 安全提示。

`dual_slot` 行为合同：

- 安装根目录下维护 `slot-a` 与 `slot-b`，每次只清理并写入非活动槽；
- 安装器接收 `/PRISMCURRENTSLOT=A|B`，将下次启动槽写入 `prism-update-slot.ini`；
- `CloseApplications=no`，当前进程不退出、不被覆盖；
- `App` 启动时若发现旧槽，会自动分离启动 `LaunchSlot` 指向的新版并结束旧入口；
- 首次安装可按 `launch_after_install` 启动，已有安装的后台更新只在下次启动切换。

运行时静默参数由 PrismQML `AutoUpdater` 负责。模板不包含 `/RESTARTAPPLICATIONS` 或 `/AUTORESTARTAPP`。

完整的 Python/QML 接入、`/SILENT` 与 `/VERYSILENT` 选择、下载进度和真实升级验收见 [自动更新接入](auto-update.md)。

## 清单

复制 [示例清单](examples/prismqml-installer.json) 到应用仓库根目录。七个核心字段必须由应用明确声明：

- `app_id`：永久固定的规范 UUID，不带花括号；
- `name`、`publisher`、`executable`；
- `aumid`：Windows 快捷方式与通知使用的 AppUserModelID；
- `install_scope`：只能是 `user` 或 `machine`，既有应用不得擅自改变；
- `dist_dir`：相对于清单的 Nuitka standalone 目录。

可选字段包括 `homepage`、`icon`、`installer_output_dir`、`output_name`、`chinese_messages_file`、`extension_include`、`launch_after_install` 和 `install_strategy`。`install_strategy` 只能是 `in_place`（默认）或 `dual_slot`。`launch_after_install` 必须是 JSON 布尔值，默认 `false`；双槽已有安装不会立即启动新版。`output_name` 只能使用 `{name}`、`{version}` 占位符且不写 `.exe` 后缀；`extension_include` 用于品牌迁移等应用专属 Inno Setup 逻辑，公共模板不会猜测或删除旧目录。

版本号不写入清单，由发布流程通过 `--version` 唯一注入。

## 命令

```powershell
prismqml-installer doctor --manifest prismqml-installer.json
prismqml-installer generate --manifest prismqml-installer.json --version 1.2.3.4
prismqml-installer check --manifest prismqml-installer.json --version 1.2.3.4
prismqml-installer compile --manifest prismqml-installer.json --version 1.2.3.4 --dry-run
prismqml-installer compile --manifest prismqml-installer.json --version 1.2.3.4
```

从源码仓运行时可使用：

```powershell
.\.venv\Scripts\python.exe -m prismqml.python.tools.windows_installer doctor --manifest prismqml-installer.json
```

默认输出为清单旁的 `installer.generated.iss`。生成器只写相对路径，不把开发机绝对路径写入脚本；内容未变化时不会重写文件。`check` 完全只读，适合 CI 检查生成结果是否漂移。

所有命令都接受全局 `--json`；为兼容直接按子命令阅读帮助的习惯，也支持把它放在子命令后。推荐形式：

```powershell
prismqml-installer --json doctor --manifest prismqml-installer.json
```

JSON 成功结果包含 `ok`、`command` 及命令特有字段。错误结果固定为：

```json
{
  "ok": false,
  "command": "check",
  "error": {
    "code": "stale_output",
    "message": "generated installer is stale: ..."
  }
}
```

`compile --dry-run` 会校验全部输入、解析 ISCC 路径并返回准确的 `argv`、生成脚本路径、预期安装包路径和 `script_sha256`，但不会写文件或启动进程，此时 `installer_sha256` 为 `null`。显式 `compile` 会先原子生成脚本，再以脚本所在目录为工作目录调用 `ISCC <脚本路径>`；它要求预期 `.exe` 必须由本次编译创建或刷新，并返回实际安装包的 `installer_sha256`。

退出码：`0` 成功、`2` 参数错误、`3` 清单错误、`4` 输出缺失或漂移、`5` 文件系统错误、`6` 编译前置条件或 ISCC 编译失败。

`doctor` 即使找不到 dist、图标或 ISCC 也返回 `0`，并通过 `ready_to_compile=false` 和 `checks` 报告缺项。可用 `PRISMQML_ISCC` 指定 ISCC 路径，或将其加入 `PATH`；工具不会自行安装依赖。
