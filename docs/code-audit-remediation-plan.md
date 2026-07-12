# PrismQML 全库审计整改落盘计划

> 状态：进行中
> 创建日期：2026-07-11
> 审计基线：`299e984ee85e0020560bd3d5de9bbe72fc13ed25`（`0.2.24.9`）
> 适用范围：Python、QML、C++、Rust、构建脚本、CI、发布物与文档工具

本文把 2026-07-10 的全库代码异味与违规审计结论转成可逐步执行、可验证、可独立提交的整改计划。既有 `docs/refactor-fix-plan.md` 是已经完成的历史重构记录，本计划不覆盖、不改写该文件。

## 一、整改目标

完成本计划后必须同时满足以下结果：

1. C++ 测试由 CTest 真实注册并执行，任何平台都不允许出现 `Total Tests: 0` 后仍判定成功。
2. 发布工作流只有在 Python、QML、C++、Rust 和制品安装验证全部通过后才能发布。
3. sdist 自包含 Rust 构建输入，可在干净环境中从源码包完成安装与导入。
4. Acrylic、SVG、QRCode 三种 ImageProvider 连续创建并销毁两个 QML 引擎时均不复用已删除对象。
5. Python 与 C++ 的 Qt 最低版本声明和实际 QML 类型要求一致。
6. 图标、翻译、Android/APK 等维护脚本不得先破坏目标再验证输入，失败必须返回非零退出码。
7. QML 与 Python 规范债务采用“阻止新增、逐批归零”的方式处理，不制造一次性大范围回归。
8. 最终保持 Python `118 passed`、QML probe `169 OK / 0 错误 / 12 跳过`，并新增本轮缺陷的回归测试。

## 二、非目标

- 本计划本身不修改版本号、不打 tag、不创建 GitHub Release、不发布 PyPI。
- 不在同一提交中混合发布门禁、生命周期修复和大规模样式整理。
- 不为 v1.0.0 之前的旧 API 新增兼容别名。
- 不把 Qt override、QML 暴露接口等 camelCase 方法未经分类就机械重命名。
- 不在未确认下游引用前删除孤立 QML 文件；涉及删除时须按项目规则单独确认。

## 三、执行纪律

每个阶段均执行以下闭环：

1. `Read`：读取目标文件、同类实现、对应测试和官方文档。
2. `Reproduce`：使用审计中的同一真实输入或发布物复现；不能复现时先补观测。
3. `Edit`：只修改当前阶段列出的范围。
4. `Restart`：完全退出并重新创建 Python/QML/C++ 进程，不假设缓存有效。
5. `Test`：定向测试先通过，再运行阶段要求的全量门禁。
6. `Review`：检查异常处理、硬编码、公开 API、文件规模和无关改动。
7. `Commit`：每个阶段单独提交；本地累计不得超过 3 个未推送提交。

任何测试失败都必须停止当前阶段并分析根因。禁止使用 `|| true`、吞异常、降低断言或把真实失败改成跳过来获得绿灯。

建议实施分支：`codex/audit-remediation`。每个阶段完成后同步 `prism` 与 `origin`，发布相关提交必须显式推送到 `prism`。

## 四、当前基线与证据

| 项目 | 当前结果 | 目标结果 |
|---|---:|---:|
| Python pytest | `118 passed` | 不下降，新增回归测试后总数增加 |
| QML 全组件 probe | `169 / 0 / 12` | 保持 `0` 错误，跳过集合不扩大 |
| CTest 注册数 | `0` | 桌面构建注册全部 5 个测试程序 |
| C++ 测试程序 | 手工执行 5/5 通过 | 由 CTest 和 CI 自动执行 5/5 |
| Rust fmt | 失败 | 通过 |
| Rust clippy `-D warnings` | 5 项失败 | 0 项失败 |
| Rust tests | `0 tests` | 核心查询与分片逻辑有真实测试 |
| 正式 sdist | 缺 3 个 Rust 必需文件 | 三文件存在且源码安装通过 |
| ImageProvider 双引擎复现 | 3/3 报对象已删除 | 3/3 连续双引擎通过 |
| Fluent SVG/枚举 | 13 个 SVG 未暴露 | 资产与两套枚举一致 |
| 工作树 | 干净 | 每阶段结束均干净 |

关键证据位置：

- C++ 测试创建：`cpp/CMakeLists.txt:181`
- CI 吞错命令：`.github/workflows/build-all.yml:51`
- 发布工作流：`.github/workflows/release.yml`
- Rust 扩展声明：`pyproject.toml:66`
- Python Provider 注册：`prismqml/python/core/utils.py:71`、`prismqml/python/window/_window_builder.py:147`、`prismqml/python/providers/lazy_context.py:49`
- C++ Acrylic Provider 注册：`cpp/src/Registry.cpp:46`
- 破坏性图标脚本：`scripts/copy_all_icons.py:13`

## 五、阶段依赖

```text
P0 基线固化
├─ P1 CTest 与 C++ CI ─┐
├─ P2 发布制品门禁 ────┤
├─ P3 Provider 生命周期 ┤
└─ P4 依赖与危险脚本 ──┴─ P5 Rust/维护工具
                                ├─ P6 QML 规范债务
                                └─ P7 Python 规范债务
                                      └─ P8 资产与孤立文件
                                            └─ P9 最终发布验收
```

P1、P2、P3 可以在不同提交中并行设计，但 P6/P7 的大规模整理必须等测试和发布门禁可信后再开始。

## 六、分阶段实施计划

### P0：固化基线与复现入口

预期效果：所有后续阶段都能使用同一命令比较改动前后结果，避免把既有问题误判为新增回归。

- 难度：0.5–1 小时
- 风险：低
- 前置依赖：无

执行项：

- 记录当前 HEAD、Python/QML/C++/Rust 基线和正式发布物哈希。
- 为临时复现脚本约定固定输入，不把失败状态的临时脚本提交进主分支。
- 需要比较既有 QML 行为时，按 `AGENTS.md` 使用 worktree 跑同一 probe。
- 明确 12 个合法 QML 跳过项，禁止后续扩大跳过列表。

验收：

```powershell
git status --short
git rev-parse HEAD
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 300 -- .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py
ctest --test-dir cpp\build -N
cargo test --manifest-path rust\Cargo.toml
```

完成定义：基线结果写入当前阶段提交说明，工作树无额外生成文件。

建议提交：无需单独提交；与 P1 的测试基础设施提交合并。

### P1：恢复 CTest 与 C++ CI 的真实测试

预期效果：三平台 CI 真实执行 C++ 测试；任一程序失败即使 workflow 失败，假绿灯归零。

- 难度：2–4 小时
- 风险：低
- 前置依赖：P0

执行项：

1. 在 `cpp/CMakeLists.txt` 中按 CMake/CTest 官方方式启用测试。
2. 为以下程序逐一添加 `add_test`，不得只创建 executable：
   - `prism_test_store`
   - `prism_test_system`
   - `prism_test_mica`
   - `prism_test_qrcode_gen`
   - `prism_test_sqlmodel`
   - `prism_test_provider_lifecycle`
3. 自动化测试统一经 `scripts/test_process.py` 启动，由入口在导入 Qt 前固定 headless 与原生错误处理策略；不得只依赖调用者环境变量。
4. 平台原生测试必须显式启用并单独标记；默认 headless 集合在任何桌面矩阵都不允许注册数为 0。
5. 删除 `.github/workflows/build-all.yml` 中的 stderr 丢弃、手工 fallback 和 `|| true`。
6. 把 QR 解码依赖加入经过验证的测试依赖集合，优先使用 `opencv-python-headless`，不得依赖开发机全局 Python。

验收：

```powershell
cmake --build cpp\build
ctest --test-dir cpp\build -N
ctest --test-dir cpp\build -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
# 仅 Windows：先显式配置 -DPRISM_BUILD_NATIVE_TESTS=ON
ctest --test-dir cpp\build -L native --interactive-debug-mode 0 --output-on-failure --no-tests=error
```

验收判据：

- `ctest -N` 显示预期测试集合且绝不为 0。
- 默认 headless 集合 6 项全部通过；Windows 显式启用的原生 Mica 集合 1 项通过。
- GitHub 的 Windows、Linux、macOS 日志均能看到实际测试名称和结果。
- 人为让一个临时断言失败时，workflow 必须非零退出；验证后撤销临时改动。

建议提交：`test: register and enforce C++ test execution`

P1 早期后续回归已完成：pytest 与全组件 probe 在导入 PySide6 前自行启用 `offscreen`；Windows 11 Mica 测试继续使用真实 `windows` 平台插件，但改为通过 `winId()` 创建隐藏 HWND、全程不调用 `show()`，并在 DWM 调用前后同时断言 Qt `isVisible()` 与 Win32 `IsWindowVisible()` 均为 false。无 Qt/QML 环境的裸 pytest `167/167`、QML `169/0/12`、无 Qt PATH 的 CTest `7/7` 通过，Mica 结果文件确认隐藏 HWND、Mica 与原生阴影全部成功。提交：`a75540f`。

P1 零交互门禁加固已完成：用户反馈测试会连续弹窗后，Windows 事件日志确认共有 68 条 `Application Popup / Event 26`，来自 6 个 `prism_test_*.exe`，缺失项为 `Qt6Quick.dll`、`Qt6Sql.dll`、`Qt6Svg.dll`、`Qt6Widgets.dll`；另确认 3 次本仓 Python 原生崩溃（`Qt6Core.dll / 0xc0000409` 一次、`ntdll.dll / 0xc0000374` 两次）。后者来自诊断临时脚本先创建 `QQmlEngine`、后创建 `QApplication`，并向短命引擎注入完整 `register_types()` 的错误生命周期，不能当作产品代码已修复的证据。

`ce9e0a0` 当时采用 Windows 两阶段策略：launcher 以可继承的 `ErrorMode=0x8003` 覆盖进入测试 bootstrap 前的 DLL/崩溃框，实际自动化进程随后切换到 `ErrorMode=0x8001` 与 WER flags `0x22`；Windows `taskkill /T /F` 清树失败时返回 125 而不谎报普通 timeout 124，POSIX 则持续检查完整 pgid 并在宽限后发送 `SIGKILL`。pytest、QML probe、覆盖率入口、Qt 子进程、CTest、wheel/sdist 首次原生导入均接入保护；Build All 三平台运行 launcher 回归，并新增 Windows 全量源码 Python/QML job。旧的可视窗口/FPS 独立脚本仍属于人工入口，不计入自动门禁。

同一实现的最终验证为：launcher `13 passed / 1 POSIX-only skipped`，全量 Python `184 passed / 1 POSIX-only skipped`，QML `169/0/12`，headless CTest `6/6`，Windows native Mica `1/1`，调用者 PATH 去除 Qt/PySide 后历史失败目标 `1/1`。每轮对比 Windows `Event 26`、`Application Error 1000`、`Windows Error Reporting 1001` 与 `%LOCALAPPDATA%\CrashDumps`，新增均为 0。提交：`ce9e0a0`。

P1 独立入口补强已完成：AST 门禁以 16 个带主入口且实际导入 PySide6 的自动 Qt 脚本为权威集合，要求可信 bootstrap 在最早 PySide6 import 前顶层执行且不得被重绑定；13 个独立 QML 回归入口进入逐进程运行矩阵，`probe_all_components.py`、input focus 与 provider lifecycle 继续由各自专项运行门禁覆盖。运行矩阵向子进程传入无效平台哨兵并让 runner 使用 `--qt-platform inherit`，正常入口必须自行覆盖为 `offscreen`，bootstrap 回退时也不会启动真实可视平台；`probe_neo_skin.py` 的源码树直接运行路径同时补齐。定向入口 `19/19`、全量 Python `210 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner 0 以及 Event 26/1000/1001 与 CrashDump 零新增均通过；Build All [29158555858](https://github.com/aki-riko/PrismQML/actions/runs/29158555858) 的 7 个作业全绿，Deploy Docs [29158555852](https://github.com/aki-riko/PrismQML/actions/runs/29158555852) 成功。提交：`75ef786`、`383dbeb`。

P1 后代错误框止血已完成：用户再次反馈同一全量测试在桌面连续出现错误弹窗后，真实继承探针确认旧策略下 pytest bootstrap 的直接子进程实际得到 `ErrorMode=0x8001`，`WerGetFlags=0x80070490 / ERROR_NOT_FOUND` 且 flags 为 0；即 `WerSetFlags` 只保护当前进程，而自动化进程主动清除了唯一会由后代继承的 `SEM_NOGPFAULTERRORBOX`。Python launcher/bootstrap 与 C++ `TestProcess.h` 现统一在全生命周期保留 `SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX`（`ErrorMode=0x8003`），C++ 入口额外用 `GetErrorMode()` 自检；当前进程仍设置 WER flags `0x22`，但在 NOGP 优先止血后不再承诺 WER 排队报告一定生成。真实 descendant 回归直接读取并确认继承值；Windows timeout 仍保持 fail-closed，`taskkill` 未确认时返回 125，测试同时确认直接子进程与孙进程 PID 均已消失。最终专项 `13 passed / 1 skipped`、全量 Python `228 passed / 1 skipped`、QML `169/0/12`、MSVC 重编译、headless CTest `6/6`、Windows native Mica `1/1`、changed scanner 0 与 `git diff --check` 全部通过；同一 105 秒真实测试窗口内新增顶层窗口计数为 0，匹配本仓进程的 Event 26/1000/1001 与 CrashDump 均无新增。本结论仅表示该真实入口未再观察到弹窗，不等同于机制级零窗口保证。提交：`1d76047`。

#### P1 后续：Windows 机制级零窗口门禁

状态：已完成。用户于 2026-07-12 17:28（Asia/Shanghai）明确确认，17:07–17:12 的同一历史命令复验及随后三轮完整门禁期间均未出现错误弹窗。真实失败输入、同输入复验、连续三轮门禁、Windows 事件/CrashDump 与用户桌面观察已形成完整闭环；实现与证据提交包括 `728b65a`、`50714b38`、`af65069d`、`daec535`、`1a5b004`。

实际落地：

1. `CreateDesktopW` 创建私有 Desktop；隐藏枚举 sentinel 在专用 worker thread 中执行 `SetThreadDesktop → CreateWindowExW → 消息泵 → DestroyWindow → 恢复原 Desktop`。全量测试曾真实复现 pytest 主线程已有 Qt/USER 对象时 `SetThreadDesktop` 返回 `ERROR_BUSY(170)`，专用线程方案与 caller-thread 隐藏 HWND 回归现已固化。
2. 隐藏 sentinel 保证私有 Desktop 不为空：真实对照确认空 Desktop 的 `EnumDesktopWindows` 会返回 `False + GetLastError=0`，而 sentinel 存在时枚举成功。现在任何枚举返回 0 都 fail closed，不再把 API 失败误判成“无窗口”。
3. 根进程通过 `STARTUPINFOEXW + PROC_THREAD_ATTRIBUTE_HANDLE_LIST` 只继承 stdin/stdout/stderr 三个复制句柄；额外 inheritable Event 哨兵确认不会泄入测试树。
4. 子进程按 `CREATE_SUSPENDED → AssignProcessToJobObject → ResumeThread` 启动；Job 启用 `KILL_ON_JOB_CLOSE` 与 `DIE_ON_UNHANDLED_EXCEPTION`。正常 root 退出后仍等待全部后代归零，timeout、可见窗口、启动失败和异常传播路径均执行 finally 清理。
5. 可见 HWND 先按 `IsWindowVisible` 与 DWM cloaked 过滤，再对 HWND owner 实时执行 `OpenProcess + IsProcessInJob`，避免 Job PID 快照/PID 复用竞态；证据记录 HWND、PID、进程创建时间、镜像路径、Desktop、title、class、style。
6. `CloseHandle`、Job、进程、sentinel 与 Desktop 清理均检查返回值并收集全部错误；主操作与清理同时失败时保留主异常类型，清理聚合作为 cause。`KeyboardInterrupt/SystemExit` 会完成清理后继续传播，不会误转成 125。
7. Python 与 C++ bootstrap 均补齐 UCRT `_set_error_mode(_OUT_TO_STDERR)`；Debug CRT warn/error/assert 定向 stderr。未修改注册表、全局 WER、AeDebug 或系统配置。
8. pytest、QML probe、coverage、CTest 与 CI Windows launcher 专项统一接入 runner；安全哨兵覆盖 root、grandchild、hidden、unrelated、busy caller、额外继承句柄、枚举 error0、CloseHandle 双故障及 unexpected exception cleanup。

历史验收记录（2026-07-12，已被后续用户反馈否定）：

- 全量 pytest：`249 passed / 1 skipped`，外层输出 `visible_windows=0 / job_active_processes=0`。
- QML probe：`169 OK / 0 错误 / 12 跳过 = 181`，外层 Job 归零。
- CTest：headless `6/6`，Windows native Mica `1/1`；私有 Desktop 未破坏隐藏 HWND、DWM/Mica 与原生阴影语义。
- `scripts/verify_coverage.py` 与 `python -X utf8 scripts/verify_coverage.py` 均通过，覆盖 181 个注册类型。
- 最终真实时间窗 `2026-07-12T07:45:48.0788352+08:00` 至 `2026-07-12T07:47:01.9751123+08:00`：System Event 26、Application Event 1000、Application Event 1001、`%LOCALAPPDATA%\CrashDumps` 新增均为 0。
- 三轮独立 Review 最终均无发现；生产文件全部低于 500 行，本批新增或增长函数全部不超过 30 行，`git diff --check` 通过。

边界说明：私有 Desktop 是自动测试可靠性隔离，不是对恶意同用户代码的安全沙箱。真实实验确认 Job `UILIMIT_DESKTOP/HANDLES` 无法阻止进程显式 `OpenDesktopW("Default") + SetThreadDesktop`，且 `UILIMIT_DESKTOP` 会破坏嵌套 runner；因此未加入无效限制，也不再宣称 25ms 轮询能捕获所有短命窗口。当前硬保证是正常自动化入口的 UI 位于私有 Desktop、不会出现在当前用户桌面；轮询负责检测并取证持续可见窗口。

重新打开后的真实状态与执行顺序：

1. 用户已于 2026-07-12 明确澄清，成批弹窗发生在 Codex 执行仓库测试期间，并非用户手工运行测试。当前任务原始 JSONL 进一步恢复出第三批弹窗的真实工具调用：2026-07-11 04:55:38（Asia/Shanghai）启动 `cargo fmt → cargo clippy → cargo test → ctest --test-dir cpp\build --output-on-failure`；System Event 26 在 04:55:40–04:57:40 同窗出现 24 次。
2. 同一原始调用的 CTest 输出确认 `cpp/build/prism_test_store.exe`、`prism_test_system.exe`、`prism_test_mica.exe`、`prism_test_qrcode_gen.exe`、`prism_test_sqlmodel.exe` 与 `prism_test_provider_lifecycle.exe` 均在启动前以 `0xC0000135` 失败；CTest 详细注册同时确认目标完整路径位于当前仓库 `cpp/build`。历史 Event 26 标题与这六个 EXE 一一对应，缺失 DLL 为 `Qt6Quick.dll`、`Qt6Sql.dll`、`Qt6Svg.dll` 或 `Qt6Widgets.dll`。因此真实触发命令、执行目录、目标路径、时间、标题和失败码均已恢复；Event 26 不记录故障进程 PID，该字段无法事后恢复，但不再阻塞同输入复验。
3. 2026-07-12 17:07:48–17:08:16 在当前 `18e925f` 上原样重跑上述真实命令链，Rust `6/6`、CTest `8/8`，退出码 0；交互桌面观察器未发现本仓进程窗口，Event 26、Event 1000/1001 与 CrashDump 增量均为 0。
4. 随后于 17:09:24–17:12:23 连续三轮执行标准 pytest、QML probe 与 headless CTest。每轮均为 Python `297 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `6/6`；每轮 runner 报告 `visible_windows=0 / job_active_processes=0` 且清理成功，Event 26、Event 1000/1001 与 CrashDump 增量均为 0。外层交互桌面观察仅记录 Thorium、Explorer 与 QQ 的无关窗口，没有路径属于本仓的窗口。
5. 全库入口复核未发现标准自动化链的新裸跑路径：CI pytest/probe、现有 CTest 注册和原生失败 verifier 均经过 runner。剩余可绕过面仅为主动直接启动原生测试 EXE、四个人工可视入口，或外部调用者主动覆盖 pytest 配置；这些路径均已明确排除在自动化可靠性契约之外。
6. 用户于 17:28 明确回复“没有出现”，确认 17:07–17:12 的同一历史命令复验及随后三轮完整门禁期间桌面均未再出现错误弹窗。P1+ 完成判据已全部满足，状态恢复为“已完成”，P6D 从 `buttons/inputs` 后续批次继续执行。

2026-07-12 入口 fail-closed 完成记录：Windows 自动入口除版本 marker 外，现同时验证当前线程位于 `PrismQMLTest-<suffix>` 私有 Desktop，且当前进程位于同后缀的精确命名 Job `PrismQMLTestJob-<suffix>`；验证通过 `OpenJobObjectW + IsProcessInJob(具体 Job 句柄)` 完成，不再把“处于任意 Job”当作 runner 身份。pytest 通过 `pyproject.toml` 的早期边界插件在第三方插件与显式 Qt canary 之前执行，并关闭未声明的插件自动发现；仓库根目录、`tests` 子目录、marker 缺失与 marker 伪造四类默认桌面输入均在 canary 导入 PySide6 前拒绝。回归不再把外层仍处于 runner 的子进程称为“真实裸桌面证明”，probe 契约也只要求存在汇总且错误数为 0，不再硬编码组件总数。

原生失败矩阵已落地：companion DLL、pre-main loader 与 fatal helper 分目录构建，CTest 唯一链路为“外层 runner → verifier → 每 case 内层 runner → 原生夹具”，静态契约禁止 helper/loader 裸注册、ALIAS/变量间接绕过、`subprocess` 替代入口及 `shell/executable` 覆盖。11 个 case 包含 loader 成功对照，以及缺 DLL、访问违规、fail-fast、`abort`、`qFatal` 的 root/grandchild；本机退出码分别为 `0xC0000135`、`0xC0000005`、`0xC0000602`、`0xC0000409`、`0xC0000409`。每条记录均包含 UTC 起止时间、case、root/failure PID、完整 Desktop/Job、原始 NTSTATUS、私有 Desktop 可见窗口数、最终活动进程数与清理结果；grandchild 先以 `CREATE_SUSPENDED` 创建，在恢复前验证进入同一命名 Job。缺 DLL 用例使用白名单 PATH 与临时空 CWD，并验证 companion 未污染 loader、Qt、Python、系统或工作目录。

本批当前证据：原生边界/命令/验证器专项 `31 passed`，Windows 结果专项 `29 passed / 1 skipped`；全量 Python `297 passed / 1 skipped`；QML `169 OK / 0 错误 / 12 跳过`；headless CTest `6/6`；Windows native CTest `2/2`；覆盖率普通与 UTF-8 两种入口均覆盖 181 个注册类型。默认交互桌面最终监控时间窗 `2026-07-12T16:43:59.5639473+08:00` 至 `2026-07-12T16:44:06.9796707+08:00` 覆盖完整 native 集合并在结束后继续观察 5 秒，新可见顶层窗口、Event 26、Event 1000/1001 与 CrashDump 增量均为 0。三路独立 Review 最终无 P0–P3；相关 Python 文件均低于 500 行，新增/增长函数均不超过 30 行，9 个改动 Python 文件通过 3.9 语法解析（本机仅安装 Python 3.12，未冒充 3.9 运行时验证）。实现提交：`af65069d`、`daec535`。

最终边界：真实弹窗来源、命令、仓库内目标路径、时间、标题和失败码已由用户澄清、原始任务记录与 Windows 事件日志交叉坐实；同一命令复验、连续三轮完整门禁及用户桌面确认均已通过，P1+ 可以关闭。项目文档已明确禁止直接启动 `prism_test_*.exe`、`prism_native_failure_helper.exe` 与 `prism_native_failure_loader.exe`；pre-main 失败无法由 EXE 内部代码拦截，必须由 CTest/runner 外层保护。`-c`/覆盖 addopts 等主动绕过项目 pytest 配置、直接启动原生测试 EXE、外部 broker、刻意逃逸 Desktop/Job，或同用户代码伪造同名 Desktop/Job，均不属于该可靠性入口契约。

### P2：修复 sdist 并建立发布制品门禁

预期效果：sdist 可独立构建 Rust 扩展；不完整制品无法进入 PyPI 发布 job。

- 难度：2–4 小时
- 风险：中
- 前置依赖：P0；发布 job 合并前应完成 P1

执行项：

1. 先查阅当前 setuptools/setuptools-rust 官方文档，验证 Rust 源文件进入 sdist 的支持方式。
2. 在以下方案中选择经过本仓真实构建验证的一种：
   - `MANIFEST.in` 显式包含 `rust/Cargo.toml` 与 `rust/src/**`；
   - 构建后端官方提供的等价源码包含配置。
3. 在 CI 中解包 sdist 并断言至少包含：
   - `rust/Cargo.toml`
   - `rust/src/lib.rs`
   - `rust/src/shard.rs`
4. 创建干净虚拟环境，从生成的 sdist 执行源码安装、`import prismqml` 和 Rust 扩展导入。
5. 对 wheel 验证内部扩展名：Windows 必须为 `prismqml_rs.pyd`，不得带 `cp312` 等版本后缀。
6. 把 Python、QML、Rust、C++ 和制品验证设为 `publish` 的显式依赖。
7. 发布 job 只下载通过验证的 artifact，不重新生成或混入未验证制品。

验收：

```powershell
$outDir = Join-Path $PWD ('.audit-dist-' + (Get-Date -Format 'yyyyMMddHHmmss'))
.\.venv\Scripts\python.exe -m build --sdist --outdir $outDir
$sdist = Get-ChildItem -LiteralPath $outDir -Filter '*.tar.gz' | Select-Object -First 1
tar -tf $sdist.FullName
```

说明：每次使用新的审计输出目录，避免为了构建而预先删除任何目录。后续清理输出目录属于文件删除操作，必须先确认其解析路径位于仓库内并取得用户确认。

验收判据：从 sdist 安装后，Python 导入、Rust 扩展导入和 QML probe 均通过；tag 发布 job 在任一前置门禁失败时不得运行。

建议提交：`fix: make source distribution self-contained`

### P3：修复 ImageProvider 所有权与多引擎生命周期

预期效果：Python 三种 Provider 和 C++ Acrylic Provider 在测试、热重载、多窗口/多引擎场景中不访问已删除对象。

- 难度：4–8 小时
- 风险：中高
- 前置依赖：P0；回归测试并入 P1/P2 门禁

先复现：

- 使用当前审计输入：创建 engine A、注册 provider、显式销毁 engine A、创建 engine B、再次注册。
- 在改动前分别记录 Acrylic、SVG、QRCode 的 `Internal C++ object ... already deleted`。
- 正式 wheel 也使用同一输入复现，不能只测源码树。

设计约束：

- `QQmlEngine::addImageProvider` 接管的对象不得作为进程级可复用单例返回。
- SVG 和 QRCode 优先改为每引擎新建 provider。
- Acrylic 需要把“共享图像状态”和“engine 拥有的 provider 适配器”分离；不得让 helper 永久持有会被 engine 删除的 provider。
- `EngineManager.reset()` 必须清理所有 engine 绑定引用，但不得误删由其他引擎持有的对象。
- C++ `Registry.cpp` 使用与 Python 一致的所有权模型。

回归测试：

- Python：同一进程顺序创建两个引擎，三种 Provider 各执行一次真实请求或最小可用操作。
- C++：至少覆盖 Acrylic 连续双引擎注册；若宿主设计只允许单引擎，必须在 API 层明确阻止第二引擎并给出确定错误，而不是悬空指针。
- 循环执行 10 次，确认无崩溃、无已删除对象异常、无重复注册警告。
- 从构建后的 wheel 再运行相同测试。

验收判据：源码树与正式 wheel 的双引擎测试均为 3/3 通过，QML probe 保持 `169/0/12`。

建议提交：`fix: scope image providers to QML engine lifetime`

### P4：统一 Qt 版本契约并修复危险脚本

预期效果：安装声明不会允许明显不支持的 Qt 版本；维护脚本在输入无效时保持目标目录原样。

- 难度：3–6 小时
- 风险：中
- 前置依赖：P1、P2

#### P4.1 Qt 最低版本决策

状态：已完成。官方 Qt 源码确认 `RectangularShadow` 为 `QML_ADDED_IN_VERSION(6, 9)`；仓库直接使用该类型且不维护双渲染路径，因此采用提升最低版本方案。Python、CMake、用户文档与 CI 已统一为 Qt/PySide6 6.9+。本地最低版本容器验证 QML `169/0/12`，Build All [29116141665](https://github.com/aki-riko/PrismQML/actions/runs/29116141665) 全平台通过，Build and Release [29116151370](https://github.com/aki-riko/PrismQML/actions/runs/29116151370) 的源码、sdist 和三平台 wheel 均通过；Linux wheel 实际安装 PySide6 6.9.3，三平台 wheel 均完成 QML `169/0/12` 与 Provider 30 次生命周期操作。提交：`818deec1`。

先用官方文档确认 `RectangularShadow` 的最低 Qt 版本，再二选一：

- 推荐方案：将 PySide6 与 CMake 最低版本统一提升到 Qt 6.9。
- 兼容方案：保留 6.5 下限，为所有 `RectangularShadow` 使用点提供经过 Qt 6.5/6.8 真机验证的 fallback。

选择标准：若项目继续把 `RectangularShadow` 作为核心首选且不维护两套渲染路径，采用提升下限方案。

验收判据：Python 元数据、CMake、文档和 CI Qt 版本一致；最低受支持版本能完成 QML probe。

#### P4.2 图标与生成脚本

状态：已完成。修前用脚本副本与临时资源树复现了来源缺失、损坏 SVG、复制中断三种失败，三者都会改变既有目标；修后同类输入、`--check` 不一致和事务提交中断均保持 SVG、Python 枚举、QML 枚举原样。仓库当前真实上游目录缺失输入返回 1，正式 2,497 个 SVG 与两套枚举前后 SHA-256 快照一致。维护脚本定向回归 `15 passed`，全量 Python `140 passed`、QML `169/0/12`、CTest `7/7`、`cargo test` 退出 0；真实 MSVC 桌面、Android arm64 库、arm64 APK、x86_64 APK 和既有构建树 APK 路径均成功。Build All [29119519828](https://github.com/aki-riko/PrismQML/actions/runs/29119519828) 五平台全绿，Deploy Docs [29119519426](https://github.com/aki-riko/PrismQML/actions/runs/29119519426) 全绿。提交：`6d3395f`。

重写 `scripts/copy_all_icons.py` 的执行顺序：

1. 增加 `if __name__ == "__main__"`。
2. 在任何写操作前验证来源目录、SVG 数量和关键文件。
3. 先生成到仓库内受控临时目录。
4. 验证 XML、枚举数量、重复名称和大小写冲突。
5. 全部通过后再替换目标；替换失败必须保留原目录。
6. 生成当前 `PrismEnums/Icons.qml`，禁止重新产生 `FluentEnums` 或带版本号 import。
7. 增加 `--check`/dry-run 模式供 CI 使用。

同步修复：

- `scripts/extract_icons.py` 的旧输出路径。
- `scripts/extract_translations.py` 的旧 `FluentTranslator.qml` 输入路径。
- 5 个 `.bat` 的个人绝对路径，改由环境变量或可提交配置读取。
- Android/APK 脚本在构建失败时必须 `exit /b` 非零。

验收判据：来源缺失、来源损坏和生成中断三种真实失败输入均不会改变现有 2,497 个 Fluent SVG。

建议提交：`fix: make maintenance scripts fail safely`

### P5：Rust、覆盖率工具与库级副作用

预期效果：Rust 质量门禁可执行，维护脚本结果可信，通用 UI 库不夹带未使用的业务数据库逻辑。

状态：已完成。P5A：rustfmt 与 `cargo clippy --all-targets -- -D warnings` 零告警通过；移除无仓内引用及无公开承诺的 `verify_agg_monthly`；分页、count、shard 合并、异常边界及 SQLite 大整数/REAL、原始 TEXT 字节排序共 6 个 Rust 单元测试通过。PyO3 宏误报仅在两个薄 `python_api` wrapper 模块内局部豁免，核心实现无豁免；三个 Python 导出签名与旧版一致，docstring 3/3 保留，fetch/count/fan-out 动态契约通过。全量 Python 140、QML `169/0/12`、CTest 7/7 通过。另以真实裸 `ctest` 输入复现 Windows 缺 Qt DLL 导致 6 个 `0xc0000135` 和连续弹窗，修后调用者 PATH 不含 Qt 时同一命令 7/7、3.31 秒完成。Build All [29123637721](https://github.com/aki-riko/PrismQML/actions/runs/29123637721) 五平台全绿且 Windows 单元测试通过，Deploy Docs [29123637759](https://github.com/aki-riko/PrismQML/actions/runs/29123637759) 全绿。提交：`b44c2dc5`、`6d96a2a`。P5B：修前普通 Windows 命令因 Unicode 警告符号崩溃退出 1，UTF-8 命令输出虚假 `0/109` 却退出 0；修后两种模式都以 offscreen + UTF-8 运行权威组件 probe，得到 `169 OK / 0 错误 / 12 跳过 = 181` 并退出 0，空/畸形/重复注册及 probe 非零退出均会失败。维护脚本测试 17/17、全量 Python 142 通过。提交：`9bb5271`。P5C：普通 `import prismqml` 不再修改 `QML_XHR_ALLOW_FILE_READ`，Python `configure_qml_environment()` 与 C++ `configureQmlEnvironment()` 成为公开显式初始化 API，Python/C++ `App` 在创建引擎前默认启用且均可显式关闭；真实 offscreen 输入验证 `App` 前变量不存在、`App()` 后为 `1`、`Translator.tr("ok") == "OK"`。Updater 两端统一为“非空显式地址 → 非空环境变量 `PRISMQML_UPDATER_API_BASE_URL` → GitHub 默认地址”，并统一去空白与尾斜杠。全量 Python 148、两种控制台模式 QML `169/0/12`、Rust 6/6、调用者 PATH 无 Qt 的裸 CTest 7/7（2.93 秒）及 `git diff --check` 全部通过。提交：`9f497d8a`。

- 难度：4–8 小时
- 风险：中
- 前置依赖：P1、P2、P4

执行项：

- 运行并修复 `cargo fmt --check`。
- 修复或经明确理由局部豁免 Clippy 5 项；禁止模块级关闭全部 warning。
- 为分页、count、shard 合并和异常输入增加 Rust 单元测试。
- 删除或迁出 `verify_agg_monthly` 记账业务函数；删除前确认没有外部公开承诺。
- 对 `scripts/verify_coverage.py` 做决策：按当前 QML 架构重写，或经用户确认删除。不得继续以 `0/109` 且退出 0 的形式保留。
- 默认 Windows 控制台运行不得因 Unicode 输出崩溃。
- 评估 `QML_XHR_ALLOW_FILE_READ`：优先改为显式初始化配置；若 Translator 必须依赖它，在公开初始化 API 和文档中说明，不在普通 import 时静默扩大进程权限。
- Updater API 地址改为可配置端点，Python/C++ 共享同一配置语义。

验收：

```powershell
cargo fmt --manifest-path rust\Cargo.toml -- --check
cargo clippy --manifest-path rust\Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path rust\Cargo.toml
.\.venv\Scripts\python.exe scripts\verify_coverage.py
.\.venv\Scripts\python.exe -X utf8 scripts\verify_coverage.py
```

验收判据：所有命令退出 0，且覆盖率工具只在真实满足目标时退出 0。

建议提交：`refactor: restore Rust and maintenance quality gates`

### P6：QML 规范债务分批归零

预期效果：先阻止新增违规，再按组件域消化现有问题；每批都能独立回滚。

状态：进行中。已完成 P6 门禁基础设施：新增只读扫描器 `scripts/check_qml_conventions.py`，`--changed` 对 Git base 与当前完整文件的违规指纹做多重集合差分，只阻断新增违规，因此可识别“新增子元素导致未改动 property 变成乱序”等上下文回归，同时不强迫 P6A 混入 P6C/P6D 的存量清理；rename 会映射到旧路径基线。`--all` 默认对存量违规返回非零，CI 使用 `--report-only` 仅报告剩余数。扫描器已覆盖 import、Qt5Compat、QtQuick.Controls 评审例外、ThemeManager、局部 enum/主题代理、成员顺序、alias 就近、readonly 前向 id、Behavior、分节术语和保守样式字面量。初始全库基线为 3,335 项；扫描器回归 9/9、全量 Python 157、QML `169/0/12`、changed 模式 0 新增违规通过，Build All [29126501598](https://github.com/aki-riko/PrismQML/actions/runs/29126501598) 的 QML conventions 作业真实通过。提交：`d5b5852`。P6A 已完成：`page_builder`、`Action.clicked`、`shortcutModified`、`SystemTrayMenu.exec`、`CheckIcon.checked` 与 `StackedWidget.pageComponents` 的定义、发射、唯一内部消费者及三套窗口转发均归零；StackedWidget 收敛为 `pageSources` 懒加载或直接子项两条路径。`pageSources` 冷跳页第一拍、主页 latch、完整 WindowsBar 真窗口、直接子项误设 lazyLoading 四条真实输入均通过；全量 Python 161、QML `169/0/12`、changed 0 新增违规通过。全库基线降至 3,327 项：ThemeManager 8、局部主题代理 8、成员顺序 1,961、分节术语 1,204、硬编码颜色 63、样式数值 76、字体 7。提交：`8e3ba4b0`。

P6B 已完成：`Enums.qml` 之外 8 处 `ThemeManager` 直接访问和 8 处局部 `fontFamily` 代理归零，`Label.qml` 的 9 个重复类型常量收敛到 `Enums.label`。Canvas 改为监听最终颜色属性，因此主题色和皮肤切换都会重绘；同一真实 QML 输入复现了 neo 下 `_micaActive=false` 但仍向 MicaManager 传 `enabled=true` 的错误，修正后运行时 fluent→neo→fluent 依次传 `true→false→true`。定向 13 项、全量 Python 165、QML `169/0/12`、无 Qt PATH 裸 CTest `7/7`、changed 0 新增违规均通过。全库基线降至 3,291 项：成员顺序 1,942、分节术语 1,203、硬编码颜色 63、样式数值 76、字体 7；QML004/QML007 均为 0。提交：`e98adebb`。

P6C1 已完成：36 个 QML 文件中的 27 处透明色表达式和 28 处样式数值已等值迁移到现有 `Enums` token；`Widget.qml` 与 `Label.qml` 为保持 changed 门禁同步消除 6 项既有成员顺序违规。Review 发现 `DataWidgetCore.qml` 根对象透明色若单独迁移会在完整成员重排前形成新的顺序违规，因此恢复原值并明确留待 P6D；扫描器漏报的透明表达式、字体、动画、阴影和语义色仍归 P6C2，未宣称 P6C 完成。全量 Python 165、QML `169/0/12`、`LoginWindowLightShadow.qml` 显式 URL 加载、无 Qt/QML 环境与无 Qt PATH 的裸 CTest `7/7`、changed 0 新增违规及 `git diff --check` 均通过。全库基线降至 3,233 项：成员顺序 1,936、分节术语 1,203、硬编码颜色 39、样式数值 48、字体 7。提交：`557930af`。

P6C2a 已完成：`Enums.fontMonospace` 统一转发 Python/C++ `ThemeManager.fontMonospace`，CodeBlock、孤立登录组件和 ColorPicker 的 5 个真实消费者已迁移；删除 Windows-only `colorPickerMetrics.monospaceFontFamily` 与零消费者 `iconFontFamily`。运行时测试复现并修正了 `CodeBlock.qml` 从 `controls/chat` 错误导入 `../../..` 导致四处 `Enums is not defined` 的存量缺陷，同一输入修后 4 个等宽字体对象均使用全局 token。canonical 首选字体在本机从 Consolas 变为 Cascadia Code，明确作为视觉决策接受：仓内真实 `CodeBlock.qml` 文本在 376px 宽下高度 `1815→1722` 且组件随内容自适应，6 位 Hex `46≤68`、ARGB `74≤192`、默认 Login 标题 `126≤400` 均无裁切。Label 仅把注释同步到当前真实 `20/28/40/68` 映射，display 字重仍留待独立视觉决策。全量 Python 168、QML `169/0/12`、孤立登录组件正式注册引擎显式加载、无 Qt PATH CTest `7/7`、changed 0 与 `git diff --check` 通过；一次未带 traceback 的瞬态 `.F` 由同一完整套件 168 项和相关用例 5 个独立新进程复验均未再现。全库基线降至 3,231 项，QML012 `7→5`，剩余为 Timeline 2、CycleWheelPicker 2、Rating 1；Build All [29146012609](https://github.com/aki-riko/PrismQML/actions/runs/29146012609) 五平台与 QML conventions 全绿。提交：`b0d23808`。

P6C2b 已完成：Timeline 的两套非虚拟 info 字体 `i` 与既有虚拟路径统一为 `Info.svg`，三处状态图标尺寸等值迁到 `controlSize.timelineIconText/timelineCardIconText`；CycleWheelPicker 的上下 PUA 字形迁到 `ChevronUp/ChevronDown.svg`，保留 normal/pressed `14/12px`；Rating 的 filled/outline PUA 字形迁到 `StarFilled/StarOutline.svg`，默认尺寸保持 24px，并保留颜色、悬停缩放、两条 Behavior 与点击改值语义。新增运行时回归递归遍历 Repeater/ListView 视觉树，核验 SVG 路径、尺寸、QML Image 实际非透明像素、滚轮按压与 Rating 悬停/点击；Qt headless 的 `grabToImage()` 不包含 `layer.effect` 合成，因此不把父 Icon 抓图误当成资源失败，另以真实 10/8px 光栅预览确认 `Info.svg` 双圆仍清晰并接受该视觉变化。定向 `2/2`、全量 Python 170、QML `169/0/12`、CTest `7/7`、changed 0 与 `git diff --check` 均通过；全库降至 3,226 项：成员顺序 1,936、分节术语 1,203、颜色 39、数值 48，QML012 与 `\uE` PUA 转义均归零。提交：`49d6d6d0`。

P6 扫描器回归加固已完成：字符串/注释清洗提取为独立 lexer，并补充 JavaScript 正则字面量后的 QML 继续扫描覆盖，避免 `/.../` 误吞后续属性。扫描器回归 `11/11`、changed 0 新增违规通过；修正后的全库真实基线为 3,236 项，其中 QML008 成员顺序 1,942、QML009 分节术语 1,203、QML010 颜色 39、QML011 样式数值 52。提交：`09c696df`。

P6C3a 已完成：`SearchResultList.qml` 的列表边距与项间距分别等值迁移到现有 `Enums.spacing.xs/xxs`，派生高度公式同步复用同一 token，避免属性与公式形成两个事实源。同一真实 3 条结果输入迁移前后均为 `hitCount=3 / implicitHeight=156 / margins=4 / spacing=2`。提交：`a877c2c7`。

P6C3b 已完成：Button、InfoBar、Toast 三个进度遮罩删除与 Qt `Rectangle` 默认值重复的 `color: "white"`；同一 offscreen 引擎中未显式设色的 Rectangle 与三个真实遮罩迁移前后均为 `#ffffffff`，遮罩仍保持隐藏且启用 layer。两批均通过扫描器回归 `11/11`、changed 0、全量 Python `184 passed / 1 skipped`、QML `169/0/12` 与 `git diff --check`；全库基线降至 3,231 项：QML008 成员顺序 1,942、QML009 分节术语 1,203、QML010 颜色 36、QML011 样式数值 50。提交：`6fc6e645`。

P6C3c 已完成：CodeBlock 与 Markdown 的固定色板、尺寸、间距和动画时长迁移到现有 `Enums` token，三个聊天内容默认宽度统一复用 `chatContentMaxWidth=600`；新增 `captionCompact=11` 覆盖 CodeBlock、MenuPage、Action、NavigationBarItem、DataWidgetCore 与 Badge，并同步更新规范。真实运行时输入先复现 Markdown `spacing=5` 及 MarkdownView、ChatBubble、ChatMessageList 多处 `ReferenceError: Enums is not defined`，修正错误相对导入后同一输入通过；新增 `test_chat_style_tokens.py` 固化颜色、间距、字体与宽度契约。定向 `3/3`、全量 Python `187 passed / 1 skipped`、QML `169/0/12`、MenuPage 显式加载 `Ready`、changed 0 与 `git diff --check` 均通过；全库基线为 3,216 项：QML008 1,942、QML009 1,203、QML010 33、QML011 38。提交：`2a22c115`。

P6C4 已完成：MatrixRain 的 17 套、51 个固定视觉预设色集中到唯一 `_internal/MatrixRainPresets.js`，默认色、`setTheme()` 与 `getAvailableThemes()` 由同一受验证数据契约驱动；17 套完整 palette、顺序、有效主题信号及未知主题不变更行为均有运行时回归。扫描器的 all/changed 范围扩展到 `.qml/.js`，普通 JavaScript 十六进制颜色继续报 QML010；唯一精确路径只豁免颜色本身，并以 QML013 严格拒绝额外函数、getter、计算属性、尺寸/动画/状态字段、重复主题及 `themes/themeNames` 顺序漂移。Review 还发现并修正新增/未跟踪文件被空基线同指纹抵消的问题；根对象成员重排同步消除 54 项 QML008、1 项 QML009 与 3 项 QML010。扫描器与运行时定向 `18/18`、全量 Python `194 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0、`git diff --check` 及 Windows Event 26 零新增均通过；`pyproject.toml` 的 `PrismQML/**/*.js` package-data 已核对，本地 venv 因缺少 setuptools 且未获准安装依赖而未重复构建制品。全库基线降至 3,158 项：QML008 1,888、QML009 1,202、QML010 30、QML011 38，QML013 为 0。提交：`06eb4af9`。

P6C5 已完成：`CarouselContent.qml` 的遮罩及 `BeforeAfterSlider.qml` 的分割线与手柄删除 3 处与 Qt `Rectangle` 默认值重复的 `color: "white"`；新增真实 offscreen 运行时回归，通过当前 Carousel 的 `layer.effect` 创建上下文实例化实际 `MultiEffect`，直接核验 `maskSource.sourceItem`，确认默认 Rectangle 与三处目标仍为 `#ffffffff`。Carousel 保持 `layer.enabled=true`、`borderRadius=16` 及 `300×200` 遮罩几何，分割线保持 `2×200 / x=149`，手柄保持 `20×20 / x=140 / y=90`；源码契约同时禁止三个目标重新出现任何显式 `color` 赋值。同一真实输入改前 `1/1`、改后 `2/2`，Carousel 与新增回归定向 `8/8`；全量 Python `212 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，Windows Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,155 项：QML008 1,888、QML009 1,202、QML010 27、QML011 38。提交：`685d063e`。

P6C6 已完成：Toast 容器顶部额外间距与颜色条上移量成对复用 `Enums.spacing.cardElevate`，保持颜色条绝对顶边仍与普通 `spacing.m=8` 外边距对齐；公共 `SplashScreen.qml` 的进度环边框与弧点负偏移分别迁到 `Enums.border.normal`、`Enums.spacing.micro`。新增真实 offscreen 运行时回归，以尺寸、圆角和父子关系定位实际目标后仅用 `QQmlProperty` 读取四项属性，确认 Toast `360×80`、容器 `y=11`、色条相对 `y=-3`，Splash 进度环 `20×20 / border=2`、弧点 `6×6 / y=-1` 均不变；源码契约同时覆盖扫描器漏报的 `spacing.m + 3`。同一真实输入改前 `1/1`、改后 `2/2`；全量 Python `214 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过。Research 早期曾对整棵内部对象树批量构造 `QQmlExpression`，触发一次 `python/Qt6Core c0000005`；统一 runner 阻止了弹窗，但留下 Event 1000/1001 与 `python.exe.89016.dmp`。根因收敛后该探针已弃用，最终测试不含 `QQmlExpression`；从 `2026-07-12 01:20:43 +08:00` 起的正式验证窗口内 Event 26/1000/1001 与 CrashDump 均零新增。全库基线降至 3,152 项：QML008 1,888、QML009 1,202、QML010 27、QML011 35。提交：`bcf0c737`。

P6C7 已完成：`AvatarSelector.qml` 悬停遮罩中的相机图标与 “Change” 文本从固定白色字面量迁到同样恒为 `#ffffffff` 的 `Enums.themeColors.accentForeground`，避免误用 neo 下会变为深色的动态 `Enums.accentForeground`；`GradientSlider.qml` 的外层手柄删除与 Qt `Rectangle` 默认白色重复的赋值，同时明确保留 lightness 渐变终点的语义 `"white"`。新增真实 offscreen 回归，按图标值、文本、尺寸和圆角定位三个实际目标，在 Fluent 明/暗与 neo 深色下均确认固定白色不变；手柄继续保持 `200×24` 滑轨、`value=0.25` 时 `20×20 / x=45 / y=2 / border=2`。同一真实输入改前 `1/1`、改后 `2/2`；全量 Python `216 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，正式验证窗口 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,149 项：QML008 1,888、QML009 1,202、QML010 24、QML011 35。提交：`4c22e7bc`。

P6C8 已完成：在 `Enums.chartColors` 新增固定 `#ffffffff` 的 `strongText`，统一 BarChartContent 最大/最小气泡 2 处、LineChartMarkers 最大/最小气泡 2 处及 ChartTooltip 强数值 1 处；token 复用固定 `themeColors.accentForeground`，不会在 neo 深色下像动态 `Enums.accentForeground` 一样变成深色。新增真实 offscreen 回归，向三个内部组件注入完整 required property 与唯一数值/文本，分别在其子树中定位五个实际 Label，并在 Fluent 明/暗与 neo 深色下确认颜色逐字节保持 `#ffffffff`；源码契约锁定 token 定义与 `2/2/1` 引用。`BarChartContent.qml` 已有 657 行，本批仅替换两项属性值，没有增加逻辑。同一真实输入改前 `1/1`、改后 `2/2`；全量 Python `218 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，正式验证窗口 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,144 项：QML008 1,888、QML009 1,202、QML010 19、QML011 35。提交：`bad57911`。

P6C9 已完成：Stepper 的已完成勾选图标与当前步骤数字、OfflineState 的重试文字统一从固定白色迁到动态 `Enums.accentForeground`，使主色块前景在 neo 深色皮肤下随 `accentColor=#fffb923c` 正确切换为 `accentForeground=#ff1a1a1a`。新增真实 offscreen 回归，以唯一图标、步骤数字和重试文本定位三个实际消费者；颜色收敛采用最多 1000ms 的轮询，不绑定当前动画时长，源码契约分别锚定 `checkIcon`、`numberText` 与 `retryTextItem`，且不使用曾触发崩溃的 `QQmlExpression`。runner 自测与定向回归 `15 passed / 1 skipped`、全量 Python `220 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过；从正式验证基线起 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,142 项：QML008 1,888、QML009 1,202、QML010 17、QML011 35。提交：`b281b7b`。

P6C10 已完成：`ListWidgetItem.qml` 的 reveal 悬浮光晕从分散的 `120×120 / radius=60 / x=-60 / y=-60` 四组字面量收敛到 `Enums.controlSize.listRevealDiameter=120`；宽度成为唯一事实源，高度、圆角与鼠标中心偏移分别由 `width`、`height` 派生，不使用语义不符的 `Enums.radius.pill`。真实 offscreen required-property 输入在改前定位到 `ListWidgetItem_QMLTYPE_*` 内的实际 `QQuickRectangle_QML_*`，确认列表项高度 36、光晕可见且几何为 `120×120 / 60 / -60 / -60`；新增无 Window、无输入注入、无 `QQmlExpression` 的运行时与源码契约，改前运行时 `1/1`、改后 `2/2`。全量 Python `222 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，正式验证窗口 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,141 项：QML008 1,888、QML009 1,202、QML010 17、QML011 34。提交：`85a75ff3`。

P6C11 已完成：新增 `Enums.duration.none=0`，将 `BreadcrumbDelegate.qml` 的初始 `PauseAnimation.duration=0` 迁到该 token，并把 `index * 50` 的逐项交错延迟绑定到现有 `Enums.duration.instant=50`。真实 offscreen Breadcrumb 连续添加 `root/section/leaf` 三项后保持 `count=3 / currentIndex=2 / currentKey=leaf`，运行时直接确认新 token 仍为 `0/50`；源码契约锁定两个目标绑定且禁止旧字面量。Research 曾同步尝试收敛 TipPopup/Widget 的 `-1/500/0`，但 changed scanner 真实报出 4 个新增 QML008：这些属性位于既有错误成员区，必须与 P6D 对应文件的完整成员重排同批处理；相关未提交替换已用反向补丁完整恢复，没有修改扫描器或放宽门禁。本批改前运行时 `1/1`、改后专项 `2/2`；全量 Python `224 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，正式验证窗口 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,140 项：QML008 1,888、QML009 1,202、QML010 17、QML011 33。提交：`0e438e60`。

P6C12 已完成：为 SplashScreen 新增 `Enums.duration.splashBreathe=1200`、`splashProgressSpin=1000` 与 `Enums.shadow.splashIcon.blurNormalized=0.8 / offset=6`，等值迁移两条呼吸动画、无限进度旋转和图标 MultiEffect 阴影。扫描器 QML011 同步覆盖此前漏报的 `shadowHorizontalOffset/shadowVerticalOffset` 直接数值；全库盘点确认唯一剩余字面量是本批已迁移的 Splash 垂直偏移，其他消费者均已使用 token。改前真实 offscreen 对象树确认两条 `QQuickNumberAnimation` 为 `1200/1200ms`、唯一 `QQuickRotationAnimation` 为 `1000ms / loops=-1`，实际创建的 `QQuickMultiEffect` 为 `shadowBlur=0.8 / shadowVerticalOffset=6`；改后运行时直接读取同一动画和 layer.effect，且不使用 Window、原生句柄或 `QQmlExpression`。扫描器与 Splash 定向 `21/21`、全量 Python `226 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed 0 与 `git diff --check` 均通过，正式验证窗口 Event 26/1000/1001 与 CrashDump 零新增。全库基线降至 3,136 项：QML008 1,888、QML009 1,202、QML010 17、QML011 29。提交：`1f9d1038`。

P6C13 已完成：为 `PopupWindowCore` 的 Anim C 新增五个角色明确的 `Enums.popupMetrics` 时长 token，等值迁移显示透明度 `120ms`、显示缩放 `240ms`、裁剪展开 `1ms`、隐藏透明度 `100ms` 与隐藏缩放 `110ms`；同时删除已被新 token 取代且全库零消费者的 `fadeInDuration=100`、`settleDuration=200`、`hideDuration=150`，避免保留两套事实源。改前真实隐藏实例直接读取五个 `QQuickNumberAnimation`，确认 `opacity 0→1 / 120`、`_scale 0.7→1 / 240`、`_clipHeight 0→180 / 1`、`opacity →0 / 100`、`_scale →0.85 / 110`；改后专项在 `visible=false` 下实例化唯一嵌套 `QWindow`，不调用 `open()`、`show()` 或 `prewarm()`，运行值与源码契约 `2/2` 通过。最终全量 Python `228 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Windows native Mica `1/1`、changed 0 与 `git diff --check` 均通过；同一 105 秒真实测试窗口内新增顶层窗口计数为 0，匹配本仓进程的 Event 26/1000/1001 与 CrashDump 无新增。全库基线降至 3,131 项：QML008 1,888、QML009 1,202、QML010 17、QML011 24。提交：`b1050f84`。

P6C14 已完成：`ShadowedRectangle` 的 `shadowOffsetX/shadowSpread` 与 `Shadow` 的 `horizontalOffset/spread` 删除和 QML `real` 类型默认值重复的显式零初始化，保留公开属性、可写性和底层绑定；`ShadowedRectangle` 同时删除 `Enums.shadow &&` 以及 `blur=16 / color=#1A000000 / offset=4` 三组不可达硬编码 fallback，`shadowLevel=null` 统一回落到 `Enums.shadow.level4`。`Shadow.shadowScale` 的中性基准 `1.0` 收敛为 `Enums.shadow.baseScale`。扫描器补齐 `shadowSpread/horizontalOffset/verticalOffset/spread/shadowScale`，正向覆盖直接赋值、property 声明、正负数与小数，负向确认相似长名称不误报。改前无 Window 实例确认四个公开默认值与底层效果均为 0、level4 垂直偏移为 2；改后真实设置 `shadowLevel=null` 验证 blur/color/offsetY fallback，并以 `3.5/2.25/-4.5/0.75` 非零输入确认 RectangularShadow/MultiEffect 绑定继续生效。专项 `20/20`、全量 Python `230 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Windows native Mica `1/1`、changed 0 与 `git diff --check` 均通过；桌面监测出现 3 个与测试无关的 OBS/Explorer 窗口，按进程归属的测试相关新增窗口为 0，匹配 Event 26/1000/1001 与 CrashDump 无新增。全库基线降至 3,130 项：QML008 1,888、QML009 1,202、QML010 17、QML011 23；剩余 QML011 中 22 项来自未注册、零消费者但仍随包分发的 `LoginWindowLightShadow.qml`，另 1 项为必须与 P6D 成员重排同批处理的 `TipPopup.duration=-1`。提交：`d4e2e11e`。

P6D TipPopup 小批已完成：`TipPopup.qml` 根对象及两个内部 `Window` 按属性、信号、方法、自身赋值、子元素顺序完整重排，分节统一为规范术语，原有函数体、显示/隐藏调用、Timer 条件与子元素相对顺序均未改变；默认 `duration=-1` 等值迁移到新增的 `Enums.duration.persistent`，为后续 tooltip 同语义消费者提供共享的不自动关闭哨兵。真实 offscreen 实例直接确认 token 与 `TipPopup.duration` 均为 `-1`，两个内部 `QWindow` 均保持隐藏，全程不调用 `show()`；源码契约同时锁定 token、禁止旧字面量并要求目标文件 QML008/QML009/QML011 全部归零。专项与扫描器回归 `21/21`、全量 Python `231 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Windows native Mica `1/1`、changed `current=0 / baseline=30` 与 `git diff --check` 均通过；149 秒正式审计窗口内仅观察到 Explorer、Steam/CS2 与任务管理器的非测试窗口，测试相关新增可见顶层窗口为 0，Event 26/1000/1001 与 CrashDump 增量均为 0。全库基线降至 3,100 项：QML008 1,867、QML009 1,194、QML010 17、QML011 22；剩余 QML011 全部来自等待 P8A 删除/公开决策的 `LoginWindowLightShadow.qml`。提交：`10b25427`。

P6D Widget 小批已完成：公开基类 `Widget.qml` 的根 `Item`、内部 `Popup` 与 `MouseArea` 按成员类别完整重排，6 个非规范分节改为标准标签或普通双语说明，函数体与根子元素相对顺序保持不变；`QtQuick.Controls` 继续仅用于库内封装的 `Popup.Window` 例外。默认 `toolTipDuration=-1 / toolTipShowDelay=500 / toolTipHideDelay=0` 分别等值迁移到 `Enums.duration.persistent`、新增的 `tooltipShowDelay` 与 `Enums.duration.none`，`HintIcon` 的显式快速覆盖 `100ms` 保持不变；同时修正了 import、居中实现与独立窗口 tooltip 三组单语或失真注释。独立只读 A/B probe 用同一真实 QML 输入分别加载改前提交与当前源码，`default=320×0`、`content=80×30`、`preferred=120×40`、`preferred+content=120×40`、居中子项 `x=50/y=15`、tooltip `-1/500/0` 全部逐项相等，两侧 QML warning 与新增顶层窗口均为空；落盘专项进一步捕获 `engine.warnings`、验证真实 Button/HintIcon 继承值并按窗口实例差集拒绝新可见窗口，20 轮独立 runner 重启均通过。最终专项 `4/4`、全量 Python `235 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Windows native Mica `1/1`、changed `current=0 / baseline=34` 与 `git diff --check` 均通过；158 秒正式审计窗口内唯一新 HWND 归属于测试前已启动的 Explorer 进程，其标题为“任务切换”，测试相关新增可见顶层窗口为 0，Event 26/1000/1001 与 CrashDump 增量均为 0。全库基线降至 3,066 项：QML008 1,839、QML009 1,188、QML010 17、QML011 22。提交：`8c633f4f`。

P6D buttons 叶子子批已完成：`CloseButton.qml`、`InputActionButton.qml` 与内部 `ButtonProgress.qml` 的 10 个非规范分节改为标准标签或普通双语说明，并同步修正重复、单语或失真的触达注释；三个产品文件的非注释行与改前提交逐行精确一致（分别 `52/52`、`18/18`、`66/66`），没有移动成员、修改绑定或改变子元素顺序。真实隐藏实例直接创建三个组件，确认 CloseButton `28×28 / hovered=false / pressed=false`、InputActionButton 在 `100×40` 父项内为 `30×30 / transparent / default shape`、ButtonProgress 为 `200×3 / feature_progress_bar / progress=0.4 / showProgress=true`，QML warning 与新增可见窗口均为空。专项 `2/2`、全量 Python `237 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Windows native Mica `1/1`、changed `current=0 / baseline=10` 与 `git diff --check` 均通过；约 148 秒正式审计窗口内 5 个新 HWND 全部归属于测试前已启动的 Thorium 应用进程，测试相关新增可见顶层窗口为 0，Event 26/1000/1001 与 CrashDump 增量均为 0。全库基线降至 3,056 项：QML008 1,839、QML009 1,178、QML010 17、QML011 22。提交：`6810e12c`。

P6D ButtonStyleHelper 小批已完成：`ButtonStyleHelper.qml` 的 `effectiveEnabled/bgColor/borderColor/textColor` 四个只读属性统一置于内部方法之前，`_getDefaultBgColor/_neoIsAccentStyle/_neoBorderColor/_neoTextColor` 四个函数保持函数体与相对顺序不变并整体移到属性区之后；5 个非规范分节改为标准标签或普通双语说明，触达的单语注释同步改为英文在前、中文在后。改前与改后均为 148 行非注释代码，排序归一后的 SHA-256 同为 `33D0A1D91BF9BB569F68A1B578EFC427DFDAA648BECD1D076F78FBA42B2AE236`，证明本批只重排成员和修改注释。目标文件 QML008/QML009 `7→0`，changed scanner `current=0 / baseline=7`；Fluent/Neobrutalism Button 真实探针全部通过并保持 neo primary 背景色 `#F97316`，全量 Python `297 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均报告 `visible_windows=0 / job_active_processes=0`。全库基线降至 3,049 项：QML008 1,837、QML009 1,173、QML010 17、QML011 22。提交：`1758f484`；Build All [29187754183](https://github.com/aki-riko/PrismQML/actions/runs/29187754183) 七项全绿，Deploy Docs [29187754138](https://github.com/aki-riko/PrismQML/actions/runs/29187754138) 成功。

P6D ButtonContent 小批已完成：内部 `ButtonContent.qml` 将 12 个 required 属性、7 个公开可写属性与 4 个只读派生状态分别归入规范成员区，`spacing` 移到属性之后；`Canvas.ringColor` 移到自身赋值前，`Connections.onProgressChanged()` 移到 `target` 前，五个根子元素的相对顺序及所有绑定、处理器和绘制算法保持不变。7 个非规范分节改为标准标签或普通双语说明，触达的动画说明同步改为英文在前、中文在后。改前与改后均为 120 行非注释代码，排序归一后的 SHA-256 同为 `851E9A292DDFFBBEF8672432D57DDEF0AE4F4339BCBA4C3C1EA23F98815E2BE9`。新增隐藏真实父链回归只实例化公开 `Button`，经 `Loader` 定位实际 `ButtonContent`，核验 12 个 required 注入、字体/倒计时属性及 `text/progress/loading/pressed/enabled/textColor` 动态同步；改前、改后均为 `3/3`，QML warning 与新增可见窗口为空。目标文件 QML008/QML009 `13→0`，changed scanner `current=0 / baseline=13`；全量 Python `298 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，测试文件 255 行且所有函数不超过 29 行。全库基线降至 3,036 项：QML008 1,831、QML009 1,166、QML010 17、QML011 22。提交：`49a899d5`。

P6D ButtonDropdown 小批已完成：内部 `ButtonDropdown.qml` 将带默认值的 `parentStyle` 与 6 个内部只读样式状态移到根对象信号之前，5 个公开只读交互状态保持原表达式；`PopupWindowCore` 的 `_contentHeight/_needsScroll` 移到自身属性赋值之前，所有函数、信号、绑定、MouseArea、Behavior、菜单结构与颜色语义均保持不变。7 个非规范分节改为规范属性区、唯一 `Content 内容` 分节或普通英文在前双语说明。改前与改后均为 200 行非注释代码，按前两批相同的 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `2FC2B1BC1E79A6DC2A10E2BB4530BB1DB40D327E925AB8E6A10DC876B0E95999`。新增隐藏真实父链回归只实例化公开 `Button`，经真实 `Loader` 定位实际 `ButtonDropdown` 与关闭态 `PopupWindowCore`，核验 8 个 required、`parentStyle`、5 个交互状态、小菜单高度，以及切换 split、工具按钮、disabled/loading/style/radius 和 10 项长菜单后的绑定与滚动上限；测试不调用 `openMenu()` 或 `prewarm()`，改前、改后同一输入均为 `1/1`，QML warning 与新增可见窗口为空。目标文件 QML008/QML009 `16→0`，changed scanner `current=0 / baseline=16`；叶组件定向 `4/4`、全量 Python `299 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，测试文件 376 行且所有函数不超过 29 行。全库基线降至 3,020 项：QML008 1,822、QML009 1,159、QML010 17、QML011 22。提交：`0946eea5`。

P6D CustomButtonCore 小批已完成：公开 `CustomButtonCore.qml` 将 6 个基础属性、只读字体、3 个可覆盖颜色回调、内容偏移及 4 个派生状态统一置于信号之前，`contentWidth/contentHeight/opacity` 移到子元素之前；五个子元素的绘制与交互顺序保持 `RectangularShadow → NeoShadow → Rectangle → Row → MouseArea`。8 个非规范分节改为规范属性/状态/尺寸/内容区或普通英文在前双语说明，并修正文件头错误声称所有按钮继承该组件及单语阴影/信号说明；`radius_`、所有回调函数体、绑定、数值、颜色和公开 API 均未改变。改前与改后均为 103 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `11ED048C3F28B55ADCDF151E1A4D2B96C9C66F753C5B1B0D4ECC253C554F307A`。新增隐藏真实父链回归只实例化公开 `ColorPicker(type_screen)`，经真实 `screenLoader` 唯一定位实际 `CustomButtonCore`，核验 `200×40` 父子尺寸、`80×32` 内容尺寸、默认 `normal/opacity=1.0` 以及禁用父组件后的 `disabled/opacity=0.6`，改前、改后同一输入均为 `1/1`，QML warning 与新增可见窗口为空。目标文件 QML008/QML009 `18→0`，changed scanner `current=0 / baseline=18`；叶组件定向 `5/5`、全量 Python `300 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，测试文件 435 行且所有函数不超过 29 行。全库基线降至 3,002 项：QML008 1,812、QML009 1,151、QML010 17、QML011 22。提交：`2c1be8dd`；Build All [29189012906](https://github.com/aki-riko/PrismQML/actions/runs/29189012906) 七项全绿，Deploy Docs [29189012898](https://github.com/aki-riko/PrismQML/actions/runs/29189012898) 成功。

P6D ButtonCore 分节注释子批已完成：530 行的 `ButtonCore.qml` 先按风险拆批，本步只将 19 个非规范分节改为规范 `Public Props/Signals/Public Methods/Size/Content` 区或普通英文在前双语说明，并在首个子元素前补充标准 `Content 内容` 分节；没有移动或改写任何非注释代码。改前与改后均为 401 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `6CE3B303DFD5026FF84A2952868C540EAE4BCCEA863D532579C4A223D0D350DE`。目标文件 QML009 `19→0`，7 项 QML008 明确保留给下一独立成员顺序子批；changed scanner `current=7 / baseline=26` 且新增违规为 0。Button/叶组件定向 `9/9`、全量 Python `300 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`。全库基线降至 2,983 项：QML008 1,812、QML009 1,132、QML010 17、QML011 22。文件仍超过 500 行软警告，背景/颜色动画协调模块化另列 4–8 小时中高风险架构任务，不混入本次机械整改。提交：`cbf934d2`。

P6D ButtonCore 成员顺序子批已完成：根 `Component.onCompleted/onPressedChanged/onHoveredChanged` 三个处理器整体移到首个子元素之前，`Connections.onBgColorChanged/onBorderColorChanged` 移到 `target` 前，下拉箭头 Loader 的 `_useAccentForeground` 移到 anchors 前，`border` alias 仅移动到 `_bg` Rectangle 正上方并保持目标 `_bg.border`。所有处理器/函数体、绑定、Loader 激活与注入、alias 目标及 16 个根子元素的相对顺序均不变；改前与改后仍为 401 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `6CE3B303DFD5026FF84A2952868C540EAE4BCCEA863D532579C4A223D0D350DE`。新增独立隐藏回归只实例化三个公开 `Button`：QML 侧暴露 `border.width/color` 标量验证 alias，自定义匿名 Rectangle 验证 `contentData/hasCustomContent` 归属与默认 ButtonContent 不加载，普通按钮验证初始化/按压/悬浮颜色处理器，并动态经过 none/dropdown/split/progress/none 验证 ButtonContent/ButtonDropdown/ButtonProgress 创建销毁和 required 注入；dropdown/split 只核验关闭态，禁止 `click/openMenu/prewarm`。同一三个运行时输入改前 `3/3`、改后完整专项 `4/4`，QML warning 与新增可见窗口为空。目标文件 QML008 `7→0`，changed scanner `current=0 / baseline=7`；全量 Python `304 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，新测试文件 307 行、最长函数 22 行。全库基线降至 2,976 项：QML008 1,805、QML009 1,132、QML010 17、QML011 22。提交：`4e383715`。

P6D inputs CalendarNavButton 小批已完成：`DatePicker/_internal/CalendarNavButton.qml` 仅把唯一非规范 `Props 属性` 分节改为 `Public Props 公开属性`，signal、三元颜色绑定、`Icon → MouseArea` 子元素顺序以及全部非注释代码均未改变。改前与改后均为 28 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `F4296CE7059F5572381E12F84A6753BCEBD88D4705D67B20207F03090CF14239`。新增可复用 inputs 叶组件隐藏回归只实例化公开 `CalendarPickerCore`，唯一定位两个真实导航按钮并核验 `chevron_up/chevron_down`、`32×34`、透明背景、标准圆角及 MouseArea 默认未悬浮/未按下；测试不点击导航按钮，不进入月份动画，也不实例化带 PopupWindowCore 的 `CalendarPicker`。同一真实父链改前 `1/1`、改后完整专项 `2/2`，QML warning 与新增可见窗口为空。目标文件 QML009 `1→0`，changed scanner `current=0 / baseline=1`；全量 Python `306 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，新测试文件 157 行、最长函数 24 行。全库基线降至 2,975 项：QML008 1,805、QML009 1,131、QML010 17、QML011 22。提交：`bff2b32b`；Build All [29190568153](https://github.com/aki-riko/PrismQML/actions/runs/29190568153) 七项全绿，Deploy Docs [29190568182](https://github.com/aki-riko/PrismQML/actions/runs/29190568182) 成功。

P6D inputs DateTimeButtons 小批已完成：`Picker/_internal/DateTimeButtons.qml` 仅把唯一非规范 `Props 属性` 分节改为 `Public Props 公开属性`，`control` 注入、尺寸、Row、两个 Button、点击处理器及全部非注释代码均未改变。改前与改后均为 34 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一后 SHA-256 同为 `A5EE2B675A7D480A7C95BD4948FB97793F8461537A6F445F35822CB120AC1A49`。新增关闭态真实父链回归通过公开 `DateTimePicker(type_datetime/time_second)`，经真实 `PopupWindowCore → Loader → DateTimePickerPopup` 唯一定位实际 `DateTimeButtons`，核验父控件注入、52 高度、标准间距、确认/取消文本与 primary/default 样式绑定、等宽公式，以及 picker、PopupWindowCore 均保持关闭且未预热；测试不调用 `open/openPopup/prewarm`，也不点击按钮。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `1→0`，changed scanner `current=0 / baseline=1`；定向 `24/24`、全量 Python `308 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，测试文件 267 行且所有函数不超过 24 行。全库基线降至 2,974 项：QML008 1,805、QML009 1,130、QML010 17、QML011 22。提交：`95c3db84`。

P6D inputs FocusLine 小批已完成：公开 `FocusLine.qml` 将 `Props 属性`、`Layout 布局` 两个非规范分节改为 `Public Props 公开属性`、`Size 尺寸`，并把文件头两行纯中文实现说明与高度行的纯中文说明改为英文在前双语注释；所有属性、anchors、尺寸、裁剪、Rectangle 与 Behavior 均未改动。改前与改后均为 28 行非注释代码；既有 PowerShell `Sort-Object` 口径会保留行尾注释，因此归一 SHA-256 从 `382315EF88E192501D3DB2FD19849EBF25CEA149401167D3B7B2E8C5B21C6D52` 变为 `B5C98FD88B32F2AEDDEDB93CFEBBE6E91B6D5398C07872BC2F2838A65516DE60`，完整产品 diff 已复核仅含上述五行注释修改。新增关闭态真实父链回归通过公开 `DateTimePicker` 唯一定位实际 `FocusLine`，核验默认隐藏、强调色、父圆角、标准边框高度、clip，以及带 Behavior 的真实 QQuickRectangle 派生子项保持零宽、标准 focusLineHeight、圆角与颜色绑定；测试不打开 picker、不触发动画或交互。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `2→0`，changed scanner `current=0 / baseline=2`；定向 `26/26`、全量 Python `310 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，测试文件 335 行且所有函数不超过 24 行。全库基线降至 2,972 项：QML008 1,805、QML009 1,128、QML010 17、QML011 22。提交：`41565d4b`。

P6D inputs Toggle 内容叶组件小批已完成：`ToggleDefaultContent.qml` 与 `ToggleSubtitleContent.qml` 分别将 `Props 属性`、`Layout 布局` 改为标准 `Public Props 公开属性`、`Content 内容`，未修改任何属性、spacing、Loader、Icon、Label 或可见性绑定。改前与改后非注释代码分别保持 29 行、21 行，按相同 PowerShell `Sort-Object` 口径归一 SHA-256 分别同为 `020F75D61D609283F7B809D4B324F47BE93E913ABF5ACE7354168BFDD1E4476A`、`4D34AFE1D21682A242B41D43C956AA11E84A6E2385AB00F60802993ABF13CF48`。新增独立隐藏回归创建 default/subtitle 两个公开 `Toggle`，经真实 `contentLoader` 创建并唯一定位两种叶组件，核验 control type、显示 type、文本、图标、iconSize、textColor、showIcon、标准间距、Loader 激活与 body/caption Label 文本；随后只动态修改公开 text/icon/subtitle，确认叶组件与 Label 绑定同步、空图标停用 Loader、空副标题隐藏 caption，不点击、不改变 checked，也不触发控件侧交互计时器或任何窗口。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。两个目标文件 QML008 均保持 0、QML009 合计 `4→0`，changed scanner `current=0 / baseline=4`；定向 `25/25`、全量 Python `315 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，新测试文件 255 行且所有函数不超过 21 行。全库基线降至 2,968 项：QML008 1,805、QML009 1,124、QML010 17、QML011 22。提交：`e17b06ca`；Build All [29192226634](https://github.com/aki-riko/PrismQML/actions/runs/29192226634) 七项全绿，Deploy Docs [29192226641](https://github.com/aki-riko/PrismQML/actions/runs/29192226641) 成功。

P6D inputs DateTimePicker 分节注释小批已完成：公开 `DateTimePicker.qml` 将根对象 13 个非规范分节收敛，最终仅保留标准 `Public Props/Readonly State/Internal Props/Signals/Internal Methods/Public Methods/Size/Content` 分节；其余值、范围、计算状态、显示、交互初始化与弹窗子组降为普通英文在前双语说明。同步删除空的“可选覆盖”旧 API 说明，并补齐 hour 未设置语义与日期顺序两条单语行尾注释，其中日期顺序按真实 `DateTimeHelpers.buildDisplayModel()` 修正为东亚 YMD、其他区域 MDY。所有属性、信号、函数、绑定、子元素及顺序均未改动。改前与改后均为 216 行非注释代码；既有 PowerShell `Sort-Object` 口径保留行尾注释，因此归一 SHA-256 从 `4A9EA5223863CEE221A3BF23D4740C6AA2BD69D8C7BD92EB8C94A0A38082F9B6` 变为 `E15986E94B9A02F6FBE2C88AA9858B64164B1286AA1A6D0225E6AA56944FAE7D`，完整产品 diff 已复核仅含注释。既有关闭态公开父链继续真实创建 `DateTimePicker → PopupWindowCore → DateTimePickerPopup → DateTimeButtons` 与 `FocusLine`，不调用 `open/openPopup/prewarm` 或点击；改前、改后同一输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `13→0`，changed scanner `current=0 / baseline=13`；定向 `27/27`、全量 Python `316 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，测试文件 355 行且所有函数不超过 24 行。全库基线降至 2,955 项：QML008 1,805、QML009 1,111、QML010 17、QML011 22。提交：`c284433f`。

P6D inputs DateTimePickerPopup 小批已完成：内部 `DateTimePickerPopup.qml` 将 6 个 Loader alias 从文件末尾移到根 `control` 属性之后，保持 alias 名称与目标完全一致；滚轮区域 `_wheelWidth` 移到自身 `width/height` 赋值之前，根分节改为标准 `Public Props/Content`。同步补齐三列滚轮和高亮实现的英文在前双语说明，并把旧的 `controlBgHover` 描述纠正为代码真实使用的半透明 `accentColor`；所有 Loader、CycleWheelPicker、处理器、分隔线、高亮、按钮及相对子元素顺序均未改变。改前与改后均为 173 行非注释代码，按相同 PowerShell `Sort-Object` 口径归一 SHA-256 同为 `382994B47132EA72E559D1B22D97447CA2E5A9253B00738660C11982DD69299C`。关闭态公开父链通过元对象确认 6 个 alias 均为唯一 `QQuickLoader*` alias、可读且不可写，源码契约同时锁定每个 alias 与对应 id 各恰好一次；真实滚轮 Row 恰有 7 个直接 Loader，前 6 个激活等宽、24H 下 AM/PM 未激活且宽 0，动态把 picker 宽度改到 360 后 `_wheelWidth` 与六个激活 Loader 宽度同步变化。测试全程确认 picker/PopupWindowCore 均未打开、未预热、未排队预热，且不使用历史曾触发 `c0000005` 的 `QQmlExpression`。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 `7→0`、QML009 `1→0`，changed scanner `current=0 / baseline=8`；定向 `29/29`、全量 Python `318 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，测试文件 483 行且所有函数不超过 28 行。全库基线降至 2,947 项：QML008 1,798、QML009 1,110、QML010 17、QML011 22。提交：`744eb6ec`。

P6D inputs PasswordStrengthIndicator 小批已完成：公开 `PasswordStrengthIndicator.qml` 仅将 `calculateStrength()` 完整函数块移动到根对象自身 `implicitWidth/implicitHeight` 赋值之前，函数体、属性、绑定、Row、Repeater、Rectangle、Label 与 Behavior 均未修改。改前与改后非注释代码均为 48 行，归一 SHA-256 同为 `FF6B86DC5E352F16391990CACBE9CF2847AD0C964D1E4CF14E3A9A3DCED11AD6`。新增公开实例动态回归在同一组件上依次验证 `"" → 0 / ""`、`"abc" → 0 / "Very Weak"`、`"abcdefgh1" → 1 / "Weak"`、`"Abcdefgh1" → 2 / "Fair"`、`"Abcdefgh1!" → 3 / "Strong"`、`"Abcdefghijk1!" → 4 / "Very Strong"`，并核验真实 Label 使用 `type_caption`；测试不点击、不触发窗口，也不对带 Behavior 的颜色中间态作脆弱断言。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 `1→0`、QML009 保持 0，changed scanner `current=0 / baseline=1`；定向 `22/22`、全量 Python `320 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，新测试文件 145 行且所有函数不超过 21 行。全库基线降至 2,946 项：QML008 1,797、QML009 1,110、QML010 17、QML011 22。提交：`ca6eb64b`；Build All [29193582883](https://github.com/aki-riko/PrismQML/actions/runs/29193582883) 首轮仅既有 `test_lazy_reload` 在固定 500ms 内未满足异步加载前提，同一包装入口本地连续 5/5 通过后仅重跑失败作业，第 2 次得到 Python `320/1`、QML `169/0/12` 并全绿；Deploy Docs [29193582892](https://github.com/aki-riko/PrismQML/actions/runs/29193582892) 成功，未为一次性时序抖动修改产品代码。

P6D inputs CropToolButton 研究后暂缓：`_internal/CropToolButton.qml` 当前仅剩 QML009 1 项，但自初始提交起只有 `_internal/qmldir` 注册且仓内语义消费者为 0；公开 `ImageCropper/ImageCropperDialog/AvatarSelector` 链实际通过 `ImageCropperPanel` 使用 4 个通用 `Button`，不会创建该组件，文件头“从 ImageCropperDialog 提取”的说明也已过时。直接实例化内部叶组件可做到 warning 与新增可见窗口为 0，但不能冒充公开真实父链；本阶段不重新接线、不粉饰说明、不删除文件，去留并入 P8 孤立资源决策。

P6D inputs SpinBox 按钮叶组件小批已完成：`SpinBoxButton.qml` 与 `MiniSpinButton.qml` 分别把 `Transparent Tool Button Style` 普通化为英文在前双语说明、把 `Size Override` 改为标准 `Size 尺寸`，并把尺寸与双击转发的纯中文说明补齐为英文在前双语；style、iconSize、preferredWidth/Height、radius、`onDoubleClicked` 及全部运行代码均未修改。两文件总行数分别为 `29→30`、`25→26`，非注释代码保持 `11→11`、`10→10`，按相同 PowerShell `Sort-Object` 口径归一 SHA-256 分别同为 `F1AE28428ED3CCEB1ECE08FE95C1F7A7ED41FD1FCF8F78A80025814CE37F4397`、`62389D95B53C1668C7A1B02BDEC1AFF33B11A1B907ECA596BA5A197FDE72FE14`。新增公开父链回归同时实例化 normal 与 compact `SpinBox`，唯一定位真实 `subtract/add/chevron_up/chevron_down` 四个叶按钮，核验透明样式、small/tiny 圆角、micro 图标尺寸、normal 75% 等宽公式与 compact 父级分半公式，并动态把高度从 `48→56`、`28→32` 后确认绑定同步；测试不点击、不启动自动重复、不发送滚轮或悬停。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。两目标文件 QML008 均保持 0、QML009 合计 `4→0`，changed scanner `current=0 / baseline=4`；定向 `3/3`、全量 Python `323 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`；本机未安装 Black，按规则未临时安装依赖，新测试文件 212 行且所有函数不超过 21 行。全库基线降至 2,942 项：QML008 1,797、QML009 1,106、QML010 17、QML011 22。提交：`af0b0cd4`。

P6D inputs ColorPickerTrigger 小批已完成：`ColorPicker/_internal/ColorPickerTrigger.qml` 仅把 `Properties 属性` 改为标准 `Public Props 公开属性`，并把首个根子元素前的 `Button with dropdown feature` 改为标准 `Content 内容`；selectedColor、isOpen、signal、implicit size、ButtonCore、feature、enabled、dropdownOpen 与色块内容均未修改。文件总行数保持 46，非注释代码保持 `28→28`，按 PowerShell `Sort-Object` 口径归一 SHA-256 前后同为 `37A0ACAD12F669937773551E5E30C200D48ACE2B9FDA50770A41B1D58CC2AE37`。新增关闭态公开父链回归通过默认 `ColorPicker(type_picker)` 唯一定位真实触发器和直接 ButtonCore，核验 selectedColor、implicit size、`feature_dropdown`、enabled 与 dropdownOpen 绑定；随后只动态修改父级颜色、enabled 和 `_isOpen` 状态，确认触发器与箭头状态同步，不调用 `open()`、不点击、不打开 Popup。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `2→0`，changed scanner `current=0 / baseline=2`；定向 `2/2`、全量 Python `325 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，新测试文件 175 行且最长函数 30 行。全库基线降至 2,940 项：QML008 1,797、QML009 1,104、QML010 17、QML011 22。

- 难度：3–7 天
- 风险：中高
- 前置依赖：P1–P5

先建立检查器：

- 新增只读 QML 规范扫描脚本，支持 `--changed` 与 `--all`。
- 初期 CI 对改动文件相对 Git base 的新增违规强制为零，同时输出全库剩余数。
- 全库归零后再把 `--all` 升为强制门禁。
- 扫描器必须识别 alias 就近声明、引用后续 id 的 readonly property 等规范例外。

分批顺序：

1. P6A：删除 v1.0 前兼容代码。
   - `page_builder`
   - `Action.clicked`
   - `shortcutModified`
   - `SystemTrayMenu.exec`
   - `CheckIcon.checked`
   - `StackedWidget.pageComponents`
2. P6B：主题入口统一。
   - 除 `Enums.qml` 外直接访问 `ThemeManager` 的文件由 7 降到 0。
   - 组件内 `fontFamily`/`isDark` 派生属性按规范收敛。
   - `Label.qml` 的重复类型常量迁移到全局枚举。
3. P6C：硬编码样式。
   - 颜色、字体、字号、间距、圆角、动画、阴影全部转入现有 Enums 分类。
   - 特效预设色等确需局部数据的场景先补充规范例外，再保留数据；不得靠口头解释绕过。
   - 核对 `PrismEnums/Label.qml` 注释中 `subtitle/title/title_large/display` 的 `16/18/20/24px` 与当前组件实际 `20/28/40/68px` 映射差异；未完成视觉语义决策前不固化任一组数值。
4. P6D：成员顺序与分节术语。
   - 按 `buttons/inputs`、`feedback/dialogs`、`data/navigation`、`windows/effects` 四批处理。
   - 每批只做机械整理，不混合行为重构。
5. P6E：文件规模。
   - `_internal/BarChartContent.qml` 降到 600 行以内。
   - 11 个超过 500 行的非例外文件逐个提出拆分建议；行为复杂的文件另立功能提交。

每批验收：

```powershell
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 300 -- .\.venv\Scripts\python.exe -m pytest
git diff --check
```

验收判据：QML probe 始终为 `169/0/12` 或在 worktree 对比下证明新增组件导致合理增长；不得新增 warning、skip 或公开兼容别名。

建议提交：每个子批一个 `refactor:` 或 `style:` 提交，不得合成单个超大提交。

### P7：Python 异常、复杂度与规范例外

预期效果：异常信息可追踪，长函数逐步拆分，规范不会误伤 Qt/QML 对外契约。

- 难度：2–5 天
- 风险：中
- 前置依赖：P1–P5；可与 P6 分支串行执行

执行顺序：

1. 先更新规范定义：
   - Qt override、Qt signal/slot、公开 QML API 允许遵循框架签名。
   - 明确生成型 Python 枚举数据是否属于文件规模例外；未决定前不得盲拆 `icons.py`。
2. 清理 34 个宽捕获：
   - 优先移除 `shadow.py` 的 `BaseException` 捕获。
   - 能确定错误类型的改为具体异常。
   - 兜底 `Exception` 必须使用带堆栈日志并说明继续运行是否安全。
3. 处理 59 个超长函数：
   - 优先 `_create_window`、`create_splash`、`SqlListModel._fetch_page`、页面异步加载流程。
   - 单次拆分只处理一个调用链，保留公开方法签名。
4. 清理确认无副作用的未使用导入。
5. 修正不符合四行 MIT 模板的 Python 文件头；第三方文件和自动生成文件先分类。

验收判据：

- `BaseException` 业务捕获为 0。
- 新增或修改函数满足 30 行/3 层约束，或有经过评审的明确例外。
- Python 全量测试不低于当前基线。
- QML 暴露 API 和 Qt override 未因 snake_case 整理而破坏。

建议提交：按异常、窗口构建、数据模型、文件头/导入分别提交。

### P8：图标枚举与孤立 QML 文件

预期效果：资源、Python 枚举、QML 枚举和 qmldir 注册保持单一事实源。

- 难度：2–4 小时
- 风险：中
- 前置依赖：P4；P8A 孤立文件决策必须在 P6C 收尾前完成，P8B 图标与资源注册在 P6、P7 后完成

执行项：

1. P8A 先对以下文件做下游引用审计：
  - `controls/auth/LoginWindowLightShadow.qml`
  - `controls/containers/Layout/Layout.qml`
  - `controls/inputs/LineEdit/TextInputCore.qml`
  - `controls/inputs/TextEdit/PlainTextEdit.qml`
2. `LoginWindowLightShadow.qml` 当前仓库零消费者、从未注册到根/auth qmldir，但仍被 Python package-data、移动端 qrc glob 与 C++ install 目录分发；历史唯一消费者已删除。其 22 项 QML011 之外仍有大量未扫描的 Canvas/动画/阴影常量与 QML008/QML009/QML010，且 `#000000cc`、`#ffffff26` 按 Qt `#AARRGGBB` 语义并非注释预期的透明黑/白。
3. 推荐路线是审计 Gitora、quicksketch、Kaleidos 等下游直接 URL 引用后，请求用户批准删除该孤儿文件；删除预计 2–4 小时，风险低到中，probe 注册数不变，QML011 可减少 22 项。删除属于敏感操作，未获批准不得执行。
4. 若确认保留公共价值，则先决定正确颜色与固定视觉预设政策，再完整处理 token、成员顺序、API、性能、可访问性、双 qmldir 注册和运行时回归；预计 8–16 小时、风险高，禁止只机械迁移 22 项。
5. P8B 通过修复后的生成器补齐 13 个未暴露 SVG：`BulletedList`、`FitPage`、`Hide`、`Message`、`NavigateForward`、`OpenFile`、`OpenFolderHorizontal`、`PowerButton`、`StickyNotes`、`Update`、`View`、`Volume`、`Zoom`。
6. 确保 Python/QML 两套枚举数量和值完全一致；其他有公共价值的孤立文件补 qmldir 与测试，确认废弃的文件在用户批准后删除。

验收判据：

- Fluent SVG 集合减去枚举值的差集为 0。
- 29 个 qmldir 的所有目标存在，singleton 均带 `pragma Singleton`。
- 不存在“文件仍在包内但无法通过模块导入”的未说明状态。

建议提交：`fix: synchronize icon and QML resource registries`

### P9：最终发布前验收

预期效果：形成可以进入下一版本发布流程的唯一绿灯状态，但本阶段不实际发布。

- 难度：2–4 小时
- 风险：低
- 前置依赖：P1–P8 全部完成

必须执行：

```powershell
.\.venv\Scripts\python.exe -m compileall prismqml tests scripts
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 300 -- .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py
cmake --build cpp\build
ctest --test-dir cpp\build -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
# 仅 Windows：先显式配置 -DPRISM_BUILD_NATIVE_TESTS=ON
ctest --test-dir cpp\build -L native --interactive-debug-mode 0 --output-on-failure --no-tests=error
cargo fmt --manifest-path rust\Cargo.toml -- --check
cargo clippy --manifest-path rust\Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path rust\Cargo.toml
git diff --check
```

制品验收：

- 构建 wheel 与 sdist。
- 检查 wheel 标签及内部 Rust 扩展名。
- 解包 sdist 检查 Rust 源码。
- 在两个干净虚拟环境中分别从 wheel 和 sdist 安装。
- 对两个安装环境执行导入、Provider 双引擎回归和 QML probe。
- CI 三平台全绿且日志中能看到真实测试名称。

完成后另行请求用户确认版本号、tag、推送与 GitHub/PyPI 发布，不把“验收通过”等同于“已经发布”。

建议提交：只提交验收中发现并修正的明确问题；纯验收不创建空提交。

## 七、建议提交序列

| 顺序 | 建议提交信息 | 主要范围 |
|---:|---|---|
| 1 | `test: register and enforce C++ test execution` | CMake、build-all CI、测试依赖 |
| 2 | `fix: make source distribution self-contained` | sdist、release CI、制品验证 |
| 3 | `fix: scope image providers to QML engine lifetime` | Python/C++ Provider、回归测试 |
| 4 | `fix: align Qt requirements and harden maintenance scripts` | Qt 下限、图标/翻译/APK 脚本 |
| 5 | `refactor: restore Rust and maintenance quality gates` | Rust、覆盖率工具、库副作用 |
| 6+ | `refactor: remove pre-v1 compatibility APIs` | 兼容别名与调用方 |
| 7+ | `style: align QML conventions in <domain>` | 按组件域拆分 |
| 8+ | `refactor: narrow Python errors and long functions` | 按调用链拆分 |
| 最后 | `fix: synchronize resource registries` | 图标与孤立 QML |

任意三个本地提交后必须推送；高风险 P3 必须单独推送，便于回滚和评审。

## 八、风险与回滚纪律

| 风险 | 监控信号 | 回滚原则 |
|---|---|---|
| Provider 所有权调整导致崩溃 | 已删除对象、双重释放、退出时崩溃 | 只回滚 P3，不夹带其他重构 |
| QML 机械整理改变绑定顺序 | probe 新 warning、属性覆盖、视觉差异 | 按组件域回滚单批提交 |
| Qt 下限提高影响下游 | 下游 venv 无法解析依赖 | 发布前列出消费者并验证升级路径 |
| sdist 配置遗漏文件 | 解包断言或源码安装失败 | 阻断 publish，不允许手工补传 |
| 删除旧 API 影响下游 | 仓内/下游调用扫描命中 | 先迁移调用方，再在同一阶段删除 |
| 脚本替换资源失败 | 文件数、哈希、XML 验证变化 | 保留原目录，不做半完成覆盖 |

禁止使用 `git reset --hard` 或 `git checkout --` 清理失败改动。需要回退时使用可审查的反向补丁或独立 revert，并保留失败证据。

## 九、状态追踪

| 阶段 | 状态 | 验证记录 | 提交 |
|---|---|---|---|
| P0 基线固化 | 已完成 | 固化审计输入与 12 个合法 QML skip；当前回归基线为 Python 122、QML 169/0/12、CTest 7/7 | `1dd7e9a2` |
| P1 CTest 与 C++ CI | 已完成 | 历史 68 条 DLL 弹窗与 3 次错误生命周期原生崩溃已追溯；统一 runner 覆盖 Python/QML/C++/制品入口。最新止血让 Python/C++ 自动测试及普通后代持续继承 `ErrorMode=0x8003`；专项 13/1、Python 228/1、QML 169/0/12、MSVC 构建、headless CTest 6/6、Windows native 1/1、changed 0 全绿，同一 105 秒真实测试入口未观察到新增顶层窗口，匹配 Event 26/1000/1001 与 dump 增量为 0；Build All [29158555858](https://github.com/aki-riko/PrismQML/actions/runs/29158555858) 的 QML conventions、Windows 零交互门禁、三平台桌面、Android 与 iOS 共 7 个作业全绿，Deploy Docs [29158555852](https://github.com/aki-riko/PrismQML/actions/runs/29158555852) 成功 | `1dd7e9a2`、`2db05888`、`6d96a2a`、`a75540f`、`ce9e0a0`、`5c290a93`、`75ef786`、`383dbeb`、`1d76047` |
| P1+ Windows 机制级零窗口门禁 | 已完成 | 用户已澄清弹窗来自 Codex 测试；原始任务记录恢复出 2026-07-11 04:55 的真实裸 CTest 命令，六个仓内 EXE 与历史 Event 26 均对应 `0xC0000135`/缺 Qt DLL。当前同一命令 Rust 6/6、CTest 8/8；随后连续三轮 Python 297/1、QML 169/0/12、headless 6/6，runner 窗口/Job 归零，交互桌面本仓窗口、Event 26/1000/1001 与 dump 增量均为 0；用户于 17:28 明确确认本轮没有出现错误弹窗。入口另有精确 Desktop/命名 Job 验真及 11-case 原生失败矩阵 | `728b65a4`、`50714b38`、`af65069d`、`daec535`、`1a5b004` |
| P2 sdist 与发布门禁 | 已完成 | sdist 独立构建、内容校验、全新 venv 安装、QML 169/0/12 与 provider 30 次操作通过；Release [29114520829](https://github.com/aki-riko/PrismQML/actions/runs/29114520829) 全绿 | `a36ba3f5` |
| P3 Provider 生命周期 | 已完成 | 旧 wheel/源码真实输入 3/3 复现已删除对象；修后本地 wheel 与 sdist 各 30/30，CI Linux wheel 与 sdist 各 30 次操作通过 | `4d067411`、`ca256f5b`、`1c344dd1`、`3c831aed`、`13a258fe` |
| P4 Qt 与危险脚本 | 已完成 | P4.1 统一 Qt/PySide6 6.9+；P4.2 三种破坏性失败与事务中断均保持原产物不变，Python 140、QML 169/0/12、CTest 7/7；Build All 29119519828 五平台全绿 | `818deec1`、`6d3395f` |
| P5 Rust 与维护工具 | 已完成 | P5A：Rust 6/6、Python 140、QML 169/0/12、CTest 7/7、Build All 五平台全绿；P5B：两种控制台模式均真实 probe 181 类型且错误非零退出；P5C：普通 import 无环境副作用，真实 App/Translator 输入返回 `OK`，Updater 两端配置语义一致，全量 Python 148、QML 169/0/12、Rust 6/6、无 Qt PATH 裸 CTest 7/7 | `b44c2dc5`、`6d96a2a`、`9bb5271`、`9f497d8a` |
| P6 QML 规范债务 | 进行中 | P6A–P6C14 与 P6D 已完成小批记录保持不变；P1+ 已完成，`buttons` 当前批已归零，`inputs` 已开始逐个清理。全库真实基线 2,940（成员顺序 1,797、分节术语 1,104、颜色 17、数值 22，QML013 0），22 项 QML011 全部等待 P8A 的 LoginWindowLightShadow 删除/公开决策；`CropToolButton` 已确认零消费者并转入 P8 去留审计 | `d5b5852`、`8e3ba4b0`、`e98adebb`、`557930af`、`b0d23808`、`49d6d6d0`、`09c696df`、`a877c2c7`、`6fc6e645`、`2a22c115`、`06eb4af9`、`685d063e`、`bcf0c737`、`4c22e7bc`、`bad57911`、`b281b7b`、`85a75ff3`、`0e438e60`、`1f9d1038`、`b1050f84`、`d4e2e11e`、`10b25427`、`8c633f4f`、`6810e12c`、`1758f484`、`49a899d5`、`0946eea5`、`2c1be8dd`、`cbf934d2`、`4e383715`、`bff2b32b`、`95c3db84`、`41565d4b`、`e17b06ca`、`c284433f`、`744eb6ec`、`ca6eb64b`、`af0b0cd4` |
| P7 Python 规范债务 | 待执行 |  |  |
| P8 资源注册 | 待执行 | P8A 提前处理孤立文件决策；LoginWindowLightShadow 已确认仓内零消费者、未注册但仍随包分发；CropToolButton 已确认仅 `_internal/qmldir` 注册、仓内零消费者且头部用途说明过时。两者均需先完成下游审计，再根据结果决定保留、公开或请求用户批准删除，不在 P6 机械整理中重接线或粉饰 |  |
| P9 最终验收 | 待执行 |  |  |

状态只能填写“待执行 / 进行中 / 已完成 / 阻塞”。“已完成”必须同时记录真实测试结果和提交哈希。
