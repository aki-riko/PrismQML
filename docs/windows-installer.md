# PrismQML Windows 安装器模板

`prismqml-installer` 根据一个小型 JSON 清单确定性生成 Inno Setup 脚本。它只读清单并生成或检查 `.iss` 文件，不调用 ISCC、不运行 Nuitka，也不执行安装程序。

## 行为合同

生成模板固定以下升级行为：

- `AppId` 在所有版本中保持不变，新版覆盖同一安装；
- `CloseApplications=yes`，安装时允许 Inno Setup 关闭占用旧文件的进程；
- `RestartApplications=no`，安装完成后不自动重新打开应用；
- `[Run]` 使用 `skipifsilent`，静默更新等待用户下次启动；
- 用户级安装写入 `{localappdata}\Programs` 且不主动请求管理员权限；
- 机器级安装写入 `{autopf}`，Windows 仍会显示无法绕过的 UAC 安全提示。

运行时静默参数由 PrismQML `AutoUpdater` 负责。模板不包含 `/RESTARTAPPLICATIONS` 或 `/AUTORESTARTAPP`。

## 清单

复制 [示例清单](examples/prismqml-installer.json) 到应用仓库根目录。七个核心字段必须由应用明确声明：

- `app_id`：永久固定的 Inno Setup 应用标识，不带花括号；
- `name`、`publisher`、`executable`；
- `aumid`：Windows 快捷方式与通知使用的 AppUserModelID；
- `install_scope`：只能是 `user` 或 `machine`，既有应用不得擅自改变；
- `dist_dir`：相对于清单的 Nuitka standalone 目录。

可选字段包括 `homepage`、`icon`、`installer_output_dir`、`output_name`、`chinese_messages_file` 和 `extension_include`。`extension_include` 用于品牌迁移等应用专属 Inno Setup 逻辑，公共模板不会猜测或删除旧目录。

版本号不写入清单，由发布流程通过 `--version` 唯一注入。

## 命令

```powershell
prismqml-installer doctor --manifest prismqml-installer.json
prismqml-installer generate --manifest prismqml-installer.json --version 1.2.3.4
prismqml-installer check --manifest prismqml-installer.json --version 1.2.3.4
```

从源码仓运行时可使用：

```powershell
.\.venv\Scripts\python.exe -m prismqml.python.tools.windows_installer doctor --manifest prismqml-installer.json
```

默认输出为清单旁的 `installer.generated.iss`。生成器只写相对路径，不把开发机绝对路径写入脚本；内容未变化时不会重写文件。`check` 完全只读，适合 CI 检查生成结果是否漂移。

所有命令都接受 `--json`，例如：

```powershell
prismqml-installer doctor --json --manifest prismqml-installer.json
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

退出码：`0` 成功、`2` 参数错误、`3` 清单错误、`4` 输出缺失或漂移、`5` 文件系统错误。

`doctor` 即使找不到 dist、图标或 ISCC 也返回 `0`，并通过 `ready_to_compile=false` 和 `checks` 报告缺项。可用 `PRISMQML_ISCC` 指定 ISCC 路径，或将其加入 `PATH`；工具不会自行安装依赖。
