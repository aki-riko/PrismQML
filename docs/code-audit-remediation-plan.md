# PrismQML 全库审计整改落盘计划

> 审计交付状态：已完成（2026-07-13）
> 整改执行状态：进行中；P6、P7、P9 剩余项不得视为已完成
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

2026-07-16 P1 CI 句柄对象身份判据后续已完成：Build All [29443774449](https://github.com/aki-riko/PrismQML/actions/runs/29443774449) 的 `Desktop windows-latest` 在 `test_only_standard_handles_are_inherited_by_test_process` 返回 91，专项汇总 `26 passed / 1 failed / 1 skipped`，其余六个作业成功。修前判据把“子进程中同一句柄数值可调用 `SetEvent()`”直接视为父 event 被继承；本机真实 Windows 诊断构造出子进程 `SetEvent()` 成功而父 event 仍为 `WAIT_TIMEOUT=258` 的输入，证明进程内句柄编号可被无关 event 复用。反向故意使用 `close_fds=False` 真继承时，父 event 变为 `WAIT_OBJECT_0=0`。测试现改为以父 event 状态验证对象身份，仍拒绝非 `ERROR_INVALID_HANDLE` 的异常失败；生产 launcher 未改。定向入口 `27 passed / 1 skipped`、全量 Python `1828 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML 0、Python 3.9 AST、compileall 与 `git diff --check` 全绿，全部 runner 零可见窗口/零残留；独立 Review P0–P3 全零。修复提交：`72c24eda`；同一 `windows-2025-vs2026` 镜像系列的 Build All [29445180749](https://github.com/aki-riko/PrismQML/actions/runs/29445180749) 七个作业全绿。

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

P6D inputs ColorPickerTrigger 小批已完成：`ColorPicker/_internal/ColorPickerTrigger.qml` 仅把 `Properties 属性` 改为标准 `Public Props 公开属性`，并把首个根子元素前的 `Button with dropdown feature` 改为标准 `Content 内容`；selectedColor、isOpen、signal、implicit size、ButtonCore、feature、enabled、dropdownOpen 与色块内容均未修改。文件总行数保持 46，非注释代码保持 `28→28`，按 PowerShell `Sort-Object` 口径归一 SHA-256 前后同为 `37A0ACAD12F669937773551E5E30C200D48ACE2B9FDA50770A41B1D58CC2AE37`。新增关闭态公开父链回归通过默认 `ColorPicker(type_picker)` 唯一定位真实触发器和直接 ButtonCore，核验 selectedColor、implicit size、`feature_dropdown`、enabled 与 dropdownOpen 绑定；随后只动态修改父级颜色、enabled 和 `_isOpen` 状态，确认触发器与箭头状态同步，不调用 `open()`、不点击、不打开 Popup。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `2→0`，changed scanner `current=0 / baseline=2`；定向 `2/2`、全量 Python `325 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，新测试文件 175 行且最长函数 30 行。全库基线降至 2,940 项：QML008 1,797、QML009 1,104、QML010 17、QML011 22。提交：`28664920`。

P6D inputs ComboBoxDefault 小批已完成：`ComboBox/ComboBoxDefault.qml` 仅把 `Style/Feature Props` 与 `Editable` 两个非标准分节改为普通英文在前双语说明；为规避 Enums 初始化时序而保留的 style/feature 数值默认值、editable 绑定及全部运行代码均未修改。文件总行数保持 20，非注释代码保持 `9→9`，按 PowerShell `Sort-Object` 口径归一 SHA-256 前后同为 `2A4CBA52E810275377B476673162A977A5DA317B6E97ADB24777E59B1FF9F336`。新增关闭态公开父链回归通过默认公开 `ComboBox`（实际 `ComboBoxEntry`）唯一定位同步加载的 `ComboBoxDefault`，核验 style、feature、editable、currentIndex/currentText、enabled 与 `isOpen`；随后只动态修改公开父级 style、feature、currentIndex 和 enabled，确认 `Qt.binding` 与 editable 绑定同步，不点击、不预热、不打开 Popup。改前、改后同一真实输入均通过，QML warning 与新增可见窗口为空。目标文件 QML008 保持 0、QML009 `2→0`，changed scanner `current=0 / baseline=2`；定向 `2/2`、全量 Python `327 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`；新测试文件 167 行，初版 32 行测试函数已在 Review 阶段拆分，最终所有函数不超过 21 行。全库基线降至 2,938 项：QML008 1,797、QML009 1,102、QML010 17、QML011 22。提交：`a17f46a8`；Build All [29196559312](https://github.com/aki-riko/PrismQML/actions/runs/29196559312) 七项全绿，Deploy Docs [29196559295](https://github.com/aki-riko/PrismQML/actions/runs/29196559295) 成功，Windows CI 为 Python `327 passed / 1 skipped`、QML `169/0/12`，runner 均为 `visible_windows=0 / job_active_processes=0`。

P6C15a 条件颜色绑定扫描补强已完成：真实 `MultiSelectToken.qml` 输入在改前只报告第 20、36 行两项 QML009，第 26 行三元表达式内的 `#000000/#ffffff` 未触发 QML010；新增回归先以同类 `property color`、`color`、`border.color` 条件表达式稳定复现 `0→3` 的漏报，同时确认普通字符串、`transparent` 比较、日志内容和 `Enums/PrismEnums` 数据资源均不误报。扫描器现先识别高置信颜色绑定，再在完整单行 RHS 中查找十六进制或 `transparent/white/black` 字面量，同一行多个颜色仍只报一项。扫描器专项 `21/21`、全量 Python `330 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0` 与全库 report-only 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`。全库基线由旧扫描口径 2,938 校正为 2,949 项：QML008 1,797、QML009 1,102、QML010 `17→28`、QML011 22；新增 11 项均为既有条件表达式，不是本批制造的产品违规。本批不宣称 QML010 完整覆盖：多行续写、函数返回、内联对象、Canvas 与自定义颜色属性仍需 P6C15b 分类补强，`MultiSelectToken` 及其余新暴露颜色随后按独立产品批迁移，避免与 P6D 机械分节混合。提交：`263851c1`。

P6C15b 颜色上下文扫描补强已完成：新增纯标准库 `qml_color_contexts.py`，以本机 Qt 6.9 `QColor.colorNames()` 的 148 个稳定命名色快照识别 Qt/QML 命名色，不让只安装 pytest 的 Linux lint 作业依赖 PySide6。扫描范围扩展到真实多行颜色绑定、颜色代码块与命名为 `*Color` 的函数 return、内联对象成员、Canvas `fillStyle/strokeStyle/shadowColor`、`addColorStop()` 以及名称含 `Color` 的自定义属性；结构入口只在字符串已遮罩的代码上定位，再回到等长原文检查字面量，避免日志或 HTML/文本内容伪造 `color:`。比较运算、索引键、普通字符串、普通函数返回、颜色 block 内日志/比较、内联对象非颜色字段、`MultiSelectToken` 的 `transparent` 哨兵和 `ColorPickerDialog` 的 `Red/Green/Blue` 标签均有反向验证。红测先稳定复现多行/自定义颜色与 block/inline/Canvas 两组 `0` 命中，修后扫描器专项 `23/23`、全量 Python `332 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、全库 report-only 与逐行库存一致，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`。全库基线进一步校正为 2,975 项：QML008 1,797、QML009 1,102、QML010 `28→54`、QML011 22；新增 26 行全部是既有实际颜色。新模块 197 行、主扫描器 583 行、测试 442 行，所有函数最长 30 行。本批仍不覆盖 `Qt.rgba/Qt.hsla/Qt.hsva` 数值构色、颜色数组与跨变量数据流，这些另列 P6C15c，不得据此宣称所有颜色硬编码已完整覆盖。提交：`165dbd4`。

P6C16 MultiSelectToken 颜色 token 小批已完成：`PrismEnums/Constants.qml` 的 `chipColors` 新增 `textOnLight: grayColors.textPrimaryLight` 与 `textOnDark: themeColors.accentForeground`，明确表达浅色/深色背景上的固定黑白文字；`MultiSelectToken.qml` 仅把 `_tintFg` 中的 `#000000/#ffffff` 等值替换为上述 `Enums.chipColors` token，HSL 明度阈值 `0.6`、未着色时的 `Enums.accentColor`、标签与关闭按钮绑定及全部交互逻辑均保持不变，同文件第 20、36 行两项 QML009 留给独立 P6D 批次。改前用公开 `ComboBoxMulti`、`ComboBoxMultiTree` 与 `LineEdit(inputType_tag)` 三条真实父链确认默认 token 仍走强调色、浅色 tint 走黑字、深色 tint 走白字，文字、`CloseButton` 属性与实际 `Icon.color` 一致且两个下拉框保持关闭；同一目标文件源码红测稳定失败于第 26 行唯一 QML010。修后新增回归 `3/3`，并在 Fluent/Neo × Light/Dark 四种组合下验证黑白 token 固定；目标 QML010 `1→0`、QML009 保持 2，changed scanner `current=2 / baseline=3` 且零新增。扫描器专项 `23/23`、全量 Python `335 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，用户再次确认本轮未出现弹窗。新测试文件 256 行，Review 后所有函数最长 26 行。全库基线降至 2,974 项：QML008 1,797、QML009 1,102、QML010 53、QML011 22。提交：`8e29044c`；Build All [29200551582](https://github.com/aki-riko/PrismQML/actions/runs/29200551582) 七项全绿，Deploy Docs [29200551590](https://github.com/aki-riko/PrismQML/actions/runs/29200551590) 成功。

P6C15c1 Qt 数值构色扫描补强已完成：新增纯标准库 `qml_color_constructors.py`，在注释/正则遮罩且字符串位置等长对齐的双词法视图上，以一次线性括号配对解析 `Qt.rgba/Qt.hsla/Qt.hsva`；覆盖直接、optional-chain、任意纯括号接收者与静态 bracket 方法（如 `Qt?.rgba`、`((Qt)).hsla`、`Qt['hsva']`），允许合法空白/注释，并排除 `helper.Qt`、`helper . Qt`、`helper(Qt).rgba` 等外部接收者。接收者回溯按 JavaScript ASI 区分行首全局 `Qt` 与跨行点号/调用链，调用按顶层逗号拆参、按起始行去重；共享 `qml_lexer.py` 同步保留 Python `splitlines()` 的来源行边界，`//` 与正则按 ECMAScript CR/LF/LS/PS 终止，使 QML/JavaScript 在 LF、CRLF、CR、U+2028、U+2029 下报告相同且准确的 line/source。未闭合候选改为线性括号索引并设置调用体预算，30,000 个未闭合候选约 240KB 可在线性时间内完成；常量算术使用受限 AST，并同时限制原始长度、节点数、求值深度与三元深度，`RecursionError/MemoryError` 安全降级为不报告。高置信口径报告前三个颜色通道均为固定常量表达式（alpha 可动态）、同一基色 `r/g/b` 加固定 alpha/括号或嵌套三元/`base.a * 固定系数`，以及三个通道统一乘固定暗化系数且 alpha 固定或按同一基色缩放的 RGBA；前导点小数三元、optional chain 与 nullish `??` 已分别解析。`Enums.qml` 与 `PrismEnums` 继续整文件豁免；普通字符串/注释/模板字符串/正则内伪调用、参数化基色与 alpha、运行时像素计算、通用 chart painter、ColorPicker 动态通道编辑、MatrixRain 彩虹 hue 和单参数颜色空间转换均有反向验证。真实 `TabWidget`、`AudioWaveform`、`DataWidgetCore`、`Label` 在改前对应数值构色均为零命中；Review 先后真实复现括号三元、缩放 RGB + alpha、接收者空白/注释/跨行、深表达式、合法调用变体、未闭合候选平方退化、ASI 与多行注释行号错位，最终专项 `14/14`、扫描器两文件 `37/37` 全绿且两路独立 Review 无剩余阻断。新口径在 library 中新增 17 个文件、35 次调用、29 个源行，全部为既有产品债务，QML010 `53→82`、全库 `2,974→3,003`；另有 44 行功能性动态构色保持不报。CI 已把两个扫描测试文件纳入同一 headless runner；维护/命令契约 `37/37`、全量 Python `349 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0`、`py_compile` 与 `git diff --check` 均通过，所有 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`。新模块 367 行、共享 lexer 122 行、测试 266 行，最长函数分别为 23、21、24 行。本批不宣称 P6C15c 完成：library 的颜色数组与高置信简单跨变量传播仍待 c2/c3；此外 `examples` 另有 5 行数值构色和 32 行数组裸色，但当前 repository/changed scanner 只覆盖 `prismqml/PrismQML`，需先设计按规则扩展扫描范围，不能把 examples 的全部 QML008–QML012 债务无差别混入现有门禁。

P6C15c2 颜色数组扫描补强已完成：新增纯标准库 `qml_color_arrays.py`、`qml_color_array_owners.py` 与 `qml_expression_roles.py`，把数组结构/颜色字面量聚合、collection owner/函数帧与参数区间、直接结果表达式角色拆成独立模块；`qml_lexer.py` 新增等长 value marker 结构视图，并在已遮罩前缀上判断正则起点，覆盖 control condition、`else`、`do`、同行块、字符串/注释/前序正则内括号，同时移除 regex 密集输入逐次拼接前缀导致的 O(n²)。扫描口径覆盖 QML/JavaScript 的 `color/colors/palette/swatch/colorStops` 命名绑定、`property color`、`list<color>`、Canvas `fillStyle/strokeStyle`、`addColorStop()`，以及命名函数、函数表达式、方法/getter、block/concise arrow 的直接、分组、`await`、条件和 `&&/||/??` 结果分支；binding 根调用 `colors = make(["red"])` 保持报告，函数/箭头 `return make(["red"])`、语义外层数组中的 call 子树、计算索引、参数默认值/数组解构、对象文本字段、算术/比较/等值操作数均 fail-closed 排除。数组只做一次全文件颜色 literal 扫描并按阻塞深度建位置索引，函数/箭头/参数区间对全部数组起点一次 heap sweep 预注解；同时把 `qml_color_contexts.py` 的字面量前后文判断改为索引式局部查找，真实复现并消除 1000/2000/4000 个颜色函数约 `0.567/2.053/10.376s` 的平方退化，修后约 `0.061/0.118/0.252s`，6000 个颜色函数 + 6000 个参数数组完整扫描约 `1.19–1.25s`。同一 callable 内 1000/2000/4000 个直接 return 数组还曾复现约 `0.410/1.416/6.488s` 的重复 return 扫描，改为全局 return 起止索引与二分定位后，4000 项降至约 `0.42s`。3000 层嵌套、3000 个未闭合候选、超过 16KiB 的闭合数组、600 字符长 owner、五类换行符与真实 examples 均有回归；CI 的轻量 Linux job 已纳入数组、callable-return 与 lexer 专项。最终五扫描专项 `160/160`、维护/命令契约 `37/37`、全量 Python `472 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0`、全库仍为 3,003（QML008 1,797、QML009 1,102、QML010 82、QML011 22），`py_compile` 与 `git diff --check` 均通过；所有 runner 均为 `visible_windows=0 / job_active_processes=0`，用户确认未出现弹窗。三个新扫描模块分别 246/492/207 行，lexer 174 行、颜色上下文 336 行，最长函数不超过 30 行；`qml_conventions.py` 614 行的既有软警告继续保留拆分建议，不在本批扩大。examples 的 32 行数组裸色目前只由测试读取，正式 repository/changed 扫描根尚未扩展；条件/短路表达式选择 callable 本身仍是保守边界，但仓内真实源码为 0 命中，留待后续解析增强。本批不宣称 P6C15c 全部完成：P6C15c3 的高置信简单跨变量传播与 examples 仅 QML010 扩根仍需独立批次。

P6C15c2 examples QML010 扫描根子批已完成：`scan_repository()` 与 `scan_changed()` 现在同时观察 `prismqml/PrismQML`、`examples` 两个根，但 examples 经过 source-path scope 过滤后只保留 QML010，QML001/QML008/QML009/QML011/QML013 等规则不会泄漏；library 根仍是必需入口，examples 根缺失时安全跳过。changed 模式的 tracked、untracked、同根 rename 与跨根 rename 均复用相同过滤：examples→library 会按新 library scope 报告新增非颜色规则，library→examples 会移除非 QML010 规则，旧路径 QML010 指纹仍能映射到新路径并只报告真正新增项。真实全扫纠正了此前“5 行数值 + 32 行数组 = 37”的不完整库存：examples 实际为 43 行 QML010，除 32 行数组、5 行数值构色外，另有 Effects/Icon 的 3 行 `transparent`、Input 的 1 行命名颜色映射、Menu/Settings 的 2 行普通十六进制绑定；全库基线因此由 3,003 校正为 3,046，QML010 `82→125`，QML008 1,797、QML009 1,102、QML011 22 保持不变。新增 `test_qml_example_scope.py` 锁定 repository、tracked/untracked changed、rename baseline 与 7 文件 43 行真实库存；Build All 的 paths 已加入 `examples/**`，轻量 Linux job 纳入该专项，债务步骤名同步改为 library + examples QML010。最终 examples 专项 `5/5`、六扫描专项 `165/165`、维护/命令契约 `37/37`、全量 Python `477 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0`、全库 `3,046` 与 `git diff --check` 均通过，所有 runner 均为 `visible_windows=0 / job_active_processes=0`，用户确认未出现弹窗。`qml_conventions.py` 642 行，继续处于既有 500 行软警告但低于 700 行硬限制，最长函数 29 行；后续不得继续向该文件堆 scope/git 逻辑，应在下一相关重构拆出扫描范围模块。前置颜色数组提交：`86d7e0ee`。P6C15c3 的高置信简单跨变量传播仍待独立批次。

P6C15c3 高置信简单跨变量传播已完成：新增纯标准库 `qml_scope_index.py`、`qml_color_values.py`、`qml_color_binders.py`、`qml_color_symbols.py` 与 `qml_color_dataflow.py`，按作用域树、不可变 primitive 值、词法 binder、BindingId 解析和 use 聚合分层；同时把局部 MatrixRain 数据契约抽到 `qml_local_style_contract.py`，使 `qml_conventions.py` 从本批开始前的 494 行保持在 461 行。传播仅接受 JavaScript `const` 与 QML `readonly property` 的固定命名色/十六进制字符串、固定数值和有界精确 alias 链；QML 未限定 readonly 读取不得跨 child object，跨对象必须经唯一、未遮蔽的显式 id。整个 array/object 引用即使由 const/readonly 持有也因可做元素写、`push` 与逃逸而继续 fail-closed，只允许 primitive 颜色字符串作为既有语义数组的元素。已被现有 context/array 扫描精确覆盖的显式 `property color` 或 JavaScript 十六进制 origin 按 literal span 排除，避免同一硬编码被直接扫描与数据流重复计数；中性 origin 的每个真实 use 仍保留独立事件，changed baseline 的 `1 use→2 use` 可稳定报告 1 个新增。词法索引覆盖 TDZ、function-scoped `var`、block shadow、参数/catch/arrow、对象/数组解构、default/rest、后续 declarator、default/named/namespace import、QML property/id 与唯一 id owner；裸写、复合写、`++/--`、`for..in/of`、解构赋值、dot/static bracket/dynamic bracket id 写均解析到具体 BindingId，普通 `holder.member` 不再按同名误杀。`NumericColorFinding` 新增真实 `qt_start`，直接及传播构色都在 receiver 位置确认 `Qt` 未被局部 const/let/var、参数、catch、解构、import、class、property 或 id 遮蔽。五类换行、条件/短路 origin、多 origin×多 use、malformed/未闭合、alias cycle/深度预算、call/index/比较/对象字段排除及静态/动态 bracket 写均有精确回归；6000 color、6000 numeric 与 4000 cycle 本机约 `1.55s / 2.23s / 0.22s`。Build All 的轻量扫描作业已纳入拆分后的 dataflow、scope 与 performance 三个测试文件。最终 CI 等价扫描套件 `278 passed`、全量 Python `590 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0`、Python 3.9 AST、`py_compile` 与 `git diff --check` 均通过；全仓新增 propagated finding 为 0，全库仍为 3,046（QML008 1,797、QML009 1,102、QML010 125、QML011 22）。全部相关脚本和测试均低于 500 行、函数最长 30 行，两路独立 Review 无剩余阻断；所有 runner 均为 `visible_windows=0 / job_active_processes=0`。

P6C15c3 CI 性能回归补修已完成：首次推送后的 Build All [29213898443](https://github.com/aki-riko/PrismQML/actions/runs/29213898443) 真实暴露 `test_callable_and_parameter_indexes_scale_to_thousands_of_spans` 在 Ubuntu runner 上耗时 `3.571s`、超过保留的 `<3.0s` 门槛，功能断言与其余 277 项均通过。剖析确认 `analyze_color_dataflow()` 对完全不含传播候选的 6000 callable + 6000 parameter 输入仍无条件构建 scope/symbol/numeric 索引，本机约占总耗时的一半；未通过放宽阈值掩盖。修复在进入完整分析前以与现有语法入口一致的 `const / readonly / Qt` 词法触发器保守快退，注释或字符串只会造成额外慢路径，不会漏报；新增 monkeypatch 回归保证无候选源码不得进入 symbol index，并把传播 finding 聚合抽成独立函数以继续满足单函数 30 行门禁。原失败输入修后连续六次约 `0.98–1.05s`；仓库 362 个受跟踪 QML/JS 中 102 个进入快路径，与强制完整分析逐文件结果零差异。最终 CI 等价扫描套件 `279 passed`、全量 Python `591 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、changed scanner `0`、全库仍为 3,046，Python 3.9 AST、`py_compile`、`git diff --check` 与两路独立 Review 均通过，所有 runner 均为 `visible_windows=0 / job_active_processes=0`。提交：`89474354`；重跑 Build All [29214382469](https://github.com/aki-riko/PrismQML/actions/runs/29214382469) 七项全绿。

P6C17 数据组件透明色 token 小批已完成：before 提交 `78ff168` 用真实 QML 同时创建公开 `Carousel`、内部 `PieChartArea/RadarChartArea` 与公开 `Label`，唯一定位 Carousel 根直接阴影和两个 `ChartTooltip`，锁定关闭态颜色 alpha 为 0、Label 默认/红色/透明哨兵切换，以及四个真实源码目标。首次运行因 Carousel 子树另有 6 个按钮阴影而命中 7 个目标，已按源码证据改为“类型 + 直接父对象”定位，生产代码当时未改。实现提交 `4e2e4401` 仅把四处等值透明表达式迁到现有 `Enums.transparent`，同步从数值构色真实库存表删除已清偿的 `Label.qml:24`；`DataWidgetCore` 的销毁期静态 fallback 明确不能依赖 singleton，本批保持不动。定向 `17 passed`，扫描专项在修正陈旧库存后 `40 passed`；一次已 collection 的旧全量进程仍按缓存表得到 `1 failed / 2231 passed / 1 skipped`，全新进程同一输入最终为 `2232 passed / 1 skipped`。QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed 0、Python 3.9 AST、compileall 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库颜色 `69→65`、总库存 `2,604→2,600`。

P6C18 ColorPicker 固定色板小批已完成：before 提交 `369724f` 扩展真实 QML 场景，同时实例化 `GradientSlider` 与内部 `ColorPickerPanel`，按 7 个 `GradientStop` 的真实 QObject 属性锁定位置和红/黄/绿/青/蓝/品红/红颜色，切换 lightness 模式核验黑/灰/白，并在高亮度低饱和与低亮度高饱和输入下验证 selector 黑白边框。首次 selector 定位因测试要求类名精确等于 `QQuickRectangle` 而零命中；源码与 `Enums.spacing.xl=16` 证明尺寸正确，改为“radius 属性 + 16×16 几何”后同一输入通过，生产当时未改。实现提交 `8d1860f8` 复用已有 `Enums.colorPickerGradient.huePos0..6/hueColor0..6`，新增同域 `lightnessDark/Mid/Light` 三项固定色，并让 GradientSlider 七个位置、十处颜色与 ColorPickerPanel 对比边框统一从该事实源读取。精确色板行号测试只同步插入五行后的真实新位置，未放宽豁免。定向首次仅失败于该陈旧行号集合，修正后 `48 passed`；全量 Python `2233 passed / 1 skipped`、扫描专项 `71 passed`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed 0、Python 3.9 AST 285、compileall 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库颜色 `65→54`、总库存 `2,600→2,589`。

P6C19 TabWidget 状态色小批已完成：before 提交 `2f3c7d3` 用真实 `TabWidget` delegate 直接切换 hovered/pressed，并设置 `_dragSourceIndex` 进入真实 drag-source 状态；首次在 `Behavior on color` 启动同一事件拍读取到透明起点，按源码 `Enums.duration.fast` 等待 120ms 后，明暗主题的 hover `0.04/0.06`、pressed `0.03/0.04`、drag `0.05/0.08` alpha 均稳定通过。实现提交 `dbe71d46` 在 `StateColor` 新增 `tabDragSource/tabPressed` 精确语义 token，复用既有 `hover`，把 TabWidget 六处数值构色与 Prism Design 分支收敛为三个状态入口，并从真实数值构色库存表删除已清偿目标。定向 `25 passed`、扫描专项 `40 passed`；首次全量仅 `test_interrupted_switch_continues_from_current_engine_frame` 的固定 20ms 采样出现一帧继续沿旧方向约 1.44px，颜色改动未触及动画/几何，同一失败用例随后 10 个独立新进程 `10/10`，完整全量新进程为 `2235 passed / 1 skipped`。QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed 0、Python 3.9 AST 286、compileall 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库颜色 `54→48`、总库存 `2,589→2,583`。

P6C20 剩余普通组件颜色小批已完成：before 提交 `f51f302` 用真实 Neo `Toggle` 与禁用 `ComboBox` 锁定浅色 `textColorLight=#000000`、Neo 深色仍跟随真实 `accentForeground=#1a1a1a`，以及 ComboBox 禁用边框固定黑色 alpha `0.4`；两处 Canvas 白色同时以源码目标锁定。首次 ComboBox 背景定位命中 wrapper `_background`、`NeoShadow` 与生产 `background` 三项，按真实元对象将目标收窄到唯一 `QQuickRectangle_QML_*`；随后真实运行又纠正“Neo 深色 accentForeground 应为白色”的错误假设，测试改为比较实际 token，生产当时未改。实现提交 `eb044ed8` 公开现有 `grayColors` 事实源，新增 `comboBoxDisabledBorder` 状态 token，并把 PieChart 内标签、ImageCropper destination-out、Toggle 浅色文字与 Neo ComboBox 禁用边框四处迁移为等值 token。定向 `15 passed`、扫描专项 `40 passed`、全量 Python `2237 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed 0、Python 3.9 AST 287、compileall 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库颜色 `48→44`、总库存 `2,583→2,579`；44 条中 43 条为 examples，生产只剩 DataWidgetCore 销毁期 fallback 一条。

P6C21 DataWidget 销毁期透明兜底小批已完成：before 提交 `c5bf1f0` 用真实 `QQmlApplicationEngine` 创建 `DataWidgetCore`，把 `shadowLevel` 置空以进入 fallback 路径，按已验证的 `duration/spacing/shadow` 元属性形状唯一定位 `Enums._metrics`，再真实延迟删除并投递 `DeferredDelete`；修前确认 `_metrics` 已失效、`Enums.shadow=None`、存活 `RectangularShadow` 颜色 alpha 降为 0，且销毁期无未知 Qt/QML warning。实现提交 `54879042` 不新增生命周期例外，而是在组件完成构造时把公开 `Enums.transparent` 值缓存进独立 JS 对象，销毁期继续使用该缓存；同步把三个内部 property 前移到合法成员区，并把真实扫描库存合同由“该行必须被报告”改为“该文件必须保持 QML010 为零”。首次全量因前序 QML 引擎已缓存禁止本地 XHR，测试消息窗口混入 4 条异步 Translator 启动警告而得到 `1 failed / 2237 passed / 1 skipped`；根因修正为从引擎创建前捕获、等待 `Qt.callLater` 启动事件落定后清空，再严格检查销毁阶段，完整 `tests/qml` 为 `208 passed`，最终全量 Python `2238 passed / 1 skipped`。定向 `43 passed`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed 0、Python 3.9 AST 288、compileall、MkDocs strict 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库颜色 `44→43`，43 条全部位于 examples；成员顺序债务同时减少 3 条，总库存 `2,579→2,575`（QML008 1,518、QML009 1,014、QML010 43），生产颜色债务归零。

P6D `feedback/dialogs` 首轮三个机械小批已完成：提交 `4597651a` 把 `HintIcon` 与 `TipPositionHelper` 的 6 个分节统一到 `Size/Content/Internal Props/Readonly State/Public Methods`；提交 `5694624d` 把 `MessageBox` 与 `ProgressDialog` 的 8 个分节统一到 `Readonly State/Content`，并删除文件末尾空的“兼容方法”分节；提交 `e6819b23` 把 `ProgressCore`、统一 `Progress`、`ProgressBarImpl` 与 `IndeterminateBarImpl` 的 14 个分节统一到 `Public Props/Public Methods/Readonly State/Internal Props/Internal Methods/Content`。三批仅改注释，不移动成员、不改属性/函数/动画/API；分批相关真实 QML 分别 `7 passed`、`1 passed`、`2 passed`，changed 扫描分别 `6→0`、`8→0`、`14→0`。累计全量 Python `2238 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、`git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,575→2,547`，QML009 `1,014→986`，QML008 1,518 与 QML010 43 保持不变；`feedback/dialogs` 其余成员顺序与分节债务继续按独立小批处理。

P6D `feedback/dialogs` 第二轮五个机械小批已完成：`14f4eea3` 将 `ResultState` 信号恢复到 property 之后，清理 2 条 QML008；`c7b07546` 调整 `ProgressRing` 重绘 handler 与分节，清理 3 条 QML008、1 条 QML009；`eb455b80` 对齐 `MaskedDialog` 成员区与分节，清理 1 条 QML008、3 条 QML009；`ed580d34` 调整 `ProgressRingImpl` 生命周期成员顺序，清理 5 条 QML008、1 条 QML009；`1e9d6aa8` 调整 `IndeterminateArcImpl` property/function/尺寸/子元素顺序及分节，清理 10 条 QML008、6 条 QML009。五批均不改属性值、动画参数、绑定、Shape 结构或公开 API；各批 changed 扫描均为 0，相关真实 QML 回归通过。累计完整门禁为 Python `2238 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、三提交 changed `26→0` 与 `git diff --check` 全绿，runner 为零可见窗口、零残留。全库总库存 `2,547→2,515`，QML008 `1,518→1,497`、QML009 `986→975`，QML010 43 保持全部位于 examples，QML011/QML013 为 0。

P6D `dialogs` 第三轮首组两个机械小批已完成：`f339dd29` 将 `ConfirmDialog` 的倒计时 property、根 handler、footer 赋值与 Timer 恢复到规范成员区，清理 3 条 QML008、4 条 QML009；`074c7070` 将 `FlyoutSheet` 的 `open/close` 移到信号后、根赋值前，并统一内容分节，清理 2 条 QML008、5 条 QML009。两批均不改函数体、属性值、窗口 flags、定位、销毁或确认/取消行为；相关真实 QML 分别 `1 passed`，ConfirmDialog 另以 `countdown=2 → open → 1.1s → close` 真实生命周期确认 Timer 运行、计数 `2→1→0` 且关闭后停止。累计完整门禁为 Python `2238 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `14→0` 与 `git diff --check` 全绿，runner 为零可见窗口、零残留。全库总库存 `2,515→2,501`，QML008 `1,497→1,492`、QML009 `975→966`，QML010 43 保持全部位于 examples。

DialogBoxCore 快速重复提交正确性批已完成：真实 `QQuickWindow` 中对 `DialogBoxCore` 与派生 `ConfirmDialog` footer 做两次快速鼠标点击，修前两场景均稳定得到 `acceptedCount=2`；`691a2c8c` 在 `DialogBoxCore.accept/reject` 恢复 `_isOpen` 守卫，并让 `ConfirmDialog` 的 `confirmed/cancelled` 复用其现有公开 `isOpen` 状态，保留首击的既有 `accepted/rejected → close/closed` 顺序。新增回归还在关闭动画未结束时立即连续 `open()`，确认每次打开只提交一次；聚焦对话框回归 `5 passed`，changed 扫描无新增，runner 零可见窗口、零残留。

P6D `DialogBoxCore` 机械小批随后独立完成：`9cf8fe69` 只统一 `Public Methods/Content` 分节并把拖拽 `dragStart` property 前移，未改上一提交的幂等守卫、函数体、动画、布局或 API；6 条存量违规（QML008 1、QML009 5）降为 0，幂等及对话框相关回归继续 `5 passed`。累计完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `6→0` 与 `git diff --check` 全绿。全库总库存 `2,501→2,495`，QML008 `1,492→1,491`、QML009 `966→961`，QML010 43 保持全部位于 examples。

P6D `feedback` 下一组三提交已完成：`d77d9a50` 将 `DesktopOverlay` 的公开方法、根 handler 与两个 alias 恢复到规范成员区，清理 5 条 QML008、3 条 QML009；`133af05c` 将 `StateWidget` 的只读派生状态前移到信号前，并统一 `Public Props/Readonly State/Content` 分节，清理 6 条 QML008、3 条 QML009。两批均不改属性值、状态映射、动画器参数、窗口 flags 或视觉绑定；相关反馈测试 `3 passed`、Prism Design skin `1 passed`、QML probe `169 OK / 0 错误 / 12 跳过`。累计完整门禁为 Python `2240 passed / 1 skipped`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `17→0` 与 `git diff --check` 全绿，runner 零可见窗口、零残留。全库总库存 `2,495→2,478`，QML008 `1,491→1,480`、QML009 `961→955`，QML010 43 保持全部位于 examples。

P6D `feedback` Skeleton/Confetti 组三提交已完成：`5a576ef9` 将 `Skeleton` 的 viewport 属性/函数、公开方法、根 handler、layer 赋值与内容分节恢复到规范顺序，清理 8 条 QML008、7 条 QML009；`0811cc78` 将 `Confetti` 的内部计数、函数、根 handler、粒子随机属性与动画停止 handler 前移，清理 15 条 QML008、1 条 QML009。Skeleton 的真实 Flickable 内外、滚动、visible/y/height、64 项批量销毁及零 `Invalid write to global property` 回归 `5 passed`；Confetti 真实运行确认 `start()` 生成 5 个粒子、`_spawnIndex=5`、动画运行且 `stop()` 停止，现有反馈测试 `1 passed`。完整门禁首次因系统中交互程序资源竞争使整套整体降速，在 SQL 子查询段触发 300 秒 runner 超时；同一 SQL 文件独立 `12 passed / 0.76s`，不并发重任务后重启同一标准门禁，Python `2240 passed / 1 skipped` 于 234.55 秒全绿。QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `31→0` 与 `git diff --check` 亦全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,478→2,447`，QML008 `1,480→1,457`、QML009 `955→947`，QML010 43 保持全部位于 examples。

P6D `feedback/dialogs` 下一组三提交已完成：`cc8a51c1` 将 `NotificationManager` 的三个懒加载 helper 下移到现有内部方法区，并统一公开 namespace/内部属性/只读状态分节，清理 3 条 QML008、6 条 QML009；`511e14ba` 将 `OverlayDialogCore` 的公开/内部函数前移到根赋值前、`Connections` handler 前移到 target 前，并统一内容分节，清理 8 条 QML008、4 条 QML009。两批均不改函数体、组件 URL、namespace API、对话框状态机或定时器。NotificationManager 真实命令式调用确认 InfoBar/Toast/Desktop 三组件均 Ready 且缓存对象身份稳定，singleton 消费测试 `1 passed`；OverlayDialogCore 直接文件加载确认 reparent、尺寸同步、目标改宽、accept 定时收尾及再次 open/reject，派生对话框回归 `5 passed`。两批 changed 分别 `9→0`、`12→0`，所有 runner 零可见窗口、零残留。全库总库存 `2,447→2,426`，QML008 `1,457→1,446`、QML009 `947→937`，QML010 43 保持全部位于 examples。

P6D `feedback/Notification` 下一组三提交已完成：`afd11daf` 将 `Toast` 的生命周期属性、公开方法、根 handler 与内容分节恢复到规范成员区，清理 8 条 QML008、11 条 QML009；`f6b1891f` 将 `NotificationStackManager` 的只读状态、内部属性、全部函数与 `Component.onCompleted` 恢复到规范顺序，并统一分节术语，清理 15 条 QML008、6 条 QML009。两批均不改属性值、函数体、堆叠数组、offset 算法、动画参数、销毁行为或公开 API。Toast 真实运行覆盖 desktopMode 与普通动画模式，确认 `show/hide` 消息、severity、closed 与可见性；StackManager 直接运行覆盖窗口/桌面 offset、移除后补位及 `closeAllDesktopNotifications()` 双对象销毁，QML warning 和新增可见窗口均为 0。两批 changed 分别 `19→0`、`21→0`，聚焦反馈回归 `4 passed`。最终完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、三提交 changed `40→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,426→2,386`，QML008 `1,446→1,423`、QML009 `937→920`，QML010 43 保持全部位于 examples。

P6D `feedback/Notification` 动画与桌面通知组三提交已完成：`d16dab7d` 将 `NotificationAnimator` 的派生状态、内部动画对象、信号和方法恢复到规范顺序，并把两个 `ParallelAnimation.onFinished` 前移到子动画之前，清理 18 条 QML008、6 条 QML009；`440773a5` 将 `DesktopNotification` 的语义/动画属性、公开/内部方法、窗口赋值和全部子元素恢复到规范成员区，并统一分节术语，清理 18 条 QML008、8 条 QML009。两批均不改属性值、动画 duration/easing/overshoot、位置公式、Timer 条件、函数体、信号或公开 API。NotificationAnimator 真实时间验证覆盖左上 show、stack reposition、hide 与右下 show，终点几何和信号次数正确；DesktopNotification 真实顶层窗口验证 show 几何、hide/closed 与自动关闭，最终均为零 QML warning、零可见窗口泄漏。两批 changed 分别 `24→0`、`26→0`，相关聚焦回归分别 `5 passed`、`4 passed`。最终完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、三提交 changed `50→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,386→2,336`，QML008 `1,423→1,387`、QML009 `920→906`，QML010 43 保持全部位于 examples。

P6D `feedback` 收尾与 `data` 首批已完成：`a9ddba12` 将 `InfoBarCore` 的派生属性、信号、公开方法、尺寸赋值、完成 handler 与全部子元素恢复到规范成员区，清理 16 条 QML008、15 条 QML009；至此 `controls/feedback` 的当前 QML008/QML009 存量归零。`f3308d32` 将 `AudioWaveform` 的完成 handler 前移到子元素之前，并统一公开方法/内容分节，清理 1 条 QML008、4 条 QML009。两批均不改函数体、布局公式、进度模式、动画参数、Timer 条件、随机波形算法、信号或公开 API。InfoBarCore 真实窗口验证横/竖布局、普通动画、desktopMode 与进度完成自动关闭；AudioWaveform 验证默认生成 50 条数据、点击与拖拽进度，均为零 QML warning、零窗口泄漏。完整门禁首轮在未改动的 TabWidget 状态色测试真实捕获 100ms `ColorAnimation` 于固定 120ms 等待后仍停留在约 94% 的合法中间色；同一旧测试 fresh process `10/10` 通过，证明是负载时序竞争。独立提交 `daa37c2e` 保持最终颜色期望不变，改为使用 `Enums.duration.fast/normal/ultraFast` 有界轮询最终色；修后该文件 fresh process `20/20`、共 40 个测试通过，完整门禁同一失败点与全套均通过。最终门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `36→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,336→2,300`，QML008 `1,387→1,370`、QML009 `906→887`，QML010 43 保持全部位于 examples。

P6D `data/Avatar` 与 `data/Badge` 两组已完成：`112f1afa` 将 `Avatar` 的 Canvas `img` property 前移到自身赋值之前，并统一公开方法术语，清理 1 条 QML008、1 条 QML009；`ad5e8a3e` 将 `AvatarSelector` 的 hovered 派生状态前移到信号之前，并统一公开属性/只读状态/内容分节，清理 1 条 QML008、6 条 QML009。`fd6062f3` 与 `702835a3` 分别统一 `Badge` 的公开属性/只读状态/颜色分组和 `Tag` 的公开方法术语，合计清理 4 条 QML009。四批均不改 Canvas 绘制、hover 动画、文件/裁剪对话框、Badge 模式选择、processing 动画、属性值或公开 API。Avatar/AvatarSelector 相关真实 QML `4 passed`，另验证 hover 进入/离开、`setAvatar` 信号与对话框保持隐藏；Badge 验证 `99+` 上限、零值显隐、dot/text 模式，Tag 相关皮肤回归通过，全部零 QML warning、零窗口泄漏。两组三提交完整门禁均为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict 与 `git diff --check` 全绿，changed 分别 `9→0`、`4→0`，全部 runner 零可见窗口、零残留。全库总库存 `2,300→2,287`，QML008 `1,370→1,368`、QML009 `887→876`，QML010 43 保持全部位于 examples。

P6D `data/Carousel` 内部组件组三提交已完成：`e2231281` 将 `CarouselContent` 的根派生状态、公开方法、mask 赋值和内容组件恢复到规范成员区，同时整理 ListView/PathView delegate Loader 的 `itemData`、peek 几何属性与内置内容 `isImage`，清理 11 条 QML008、6 条 QML009；`dbd71743` 统一 `CarouselNavButton` 的公开属性与按钮配置分组，清理 2 条 QML009。两批均不改 ListView/PathView 模型、index 双向桥接、peek 几何公式、delegate 数据、图片解码配置、按钮图标/尺寸或公开 API。相关真实回归 `11 passed`，覆盖 default ListView、peek PathView 横/竖方向、中心项 `itemData`、自定义 delegate、圆角/阴影与 index 切换；导航按钮联合轮播回归 `7 passed`。最终完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `19→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,287→2,268`，QML008 `1,368→1,357`、QML009 `876→868`，QML010 43 保持全部位于 examples。

P6D `data/Carousel` 公开入口与 Chart 首批已完成：`57d94b48` 将 `Carousel` 的四个派生状态前移到信号之前，并统一 hover/wheel、阴影、内容、指示器、导航按钮与自动播放分组，清理 4 条 QML008、6 条 QML009；`ff650be9` 统一 `BoxplotChartArea` 的公开属性、内容、图表区与 tooltip 分节，清理 4 条 QML009。两批均不改 next/previous/goTo、hover 检测、滚轮、自动播放 Timer、阴影、指标器、箱线图数据、坐标轴、Canvas、tooltip 或公开 API。Carousel 真实窗口验证 next/previous、横竖方向、自动播放与 hover 暂停/恢复，相关回归 `9 passed`；BoxplotChartArea 直接运行验证图表创建、A/B 轴标签、Max/Q3/Median/Q1/Min tooltip 行与 hoveredIndex，相关 Chart 联合回归 `11 passed`，均为零 QML warning、零窗口泄漏。`BarChartContent.qml` 当前 657 行，属于计划 P6E 明确要求降到 600 行以内的文件，避免在 P6D 机械批中混入模块化拆分，成员顺序债务随 P6E 一并处理。最终完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `14→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,268→2,254`，QML008 `1,357→1,353`、QML009 `868→858`，QML010 43 保持全部位于 examples。

P6D Chart 箱线图内容与底部图例组三提交已完成：`37972d3a` 将 `BoxplotChartContent` 的派生状态、信号、内部方法、根重绘 handler、Canvas 属性/绘制函数及 Timer 状态恢复到规范成员区，并统一公开属性、只读状态、内部方法与内容分节，清理 9 条 QML008、5 条 QML009；`6fc7eb2a` 统一 `ChartBottomLegend` 的内部方法与内容分节，并将 delegate 派生属性前移到尺寸赋值之前，清理 2 条 QML008、2 条 QML009。两批非注释代码多重集合与父提交完全一致，不改 valueRange、坐标映射、Canvas 绘制公式、动画参数、图例颜色/标签、隐藏状态、hover/click 信号或公开 API。BoxplotChartContent 使用同一真实 QML 输入在修前、修后验证两组含异常点数据、动画 Canvas、横竖 hover/click 与范围 `-0.5..65.5`，均零 warning；Chart 联合回归 `10 passed`。ChartBottomLegend 修前、修后验证两项图例、隐藏项、hover/click，Prism Design 皮肤回归 `1 passed`，均零窗口泄漏。最终完整门禁为 Python `2240 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、MkDocs strict、changed `18→0` 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留。全库总库存 `2,254→2,236`，QML008 `1,353→1,342`、QML009 `858→851`，QML010 43 保持全部位于 examples。

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
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 120 -- .\.venv\Scripts\python.exe -m pytest tests\test_qml_conventions.py tests\test_qml_color_constructors.py -q
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 120 -- .\.venv\Scripts\python.exe scripts\check_qml_conventions.py --changed --base HEAD
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 120 -- .\.venv\Scripts\python.exe scripts\check_qml_conventions.py --all --report-only --max-details 100
ctest --test-dir cpp\build -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
git diff --check
```

验收判据：QML probe 始终为 `169/0/12` 或在 worktree 对比下证明新增组件导致合理增长；不得新增 warning、skip 或公开兼容别名。

建议提交：每个子批一个 `refactor:` 或 `style:` 提交，不得合成单个超大提交。

### P7：Python 异常、复杂度与规范例外

预期效果：异常信息可追踪，长函数逐步拆分，规范不会误伤 Qt/QML 对外契约。

状态：进行中。P7 规范前置与异常边界首批已完成：`AGENTS.md` 已把 Python snake_case 例外收紧为有 Qt 文档/实际基类依据的 override，或同时具备注册/注入路径与真实 QML、`QMetaObject`、公开 QML 测试/文档消费者的公开契约；普通装饰器、普通 Python 调用方与普通公开 Python API 均不能自动获得 camelCase 例外，pre-1 breaking rename 仍须独立评审、同批迁移且不留兼容别名。生成型 Python 枚举只有在仓内生成器 `--check` 能确定性复现相同文本、文件仅含数据与无副作用查询时才可超过 700 行；当前 `icons.py` 的 Python/QML 双注册表检查真实失败且混有路径、文件 I/O、主题与渲染逻辑，因此明确留给 P8B，P7 禁止盲拆或直接重生成覆盖。异常首批用同一真实输入复现 `importlib.metadata.version()` 的后端 `RuntimeError` 被错误静默回退，以及 `DwmSyncFilter` 吞掉 `KeyboardInterrupt/SystemExit`；修后 `__version__` 仅对 `PackageNotFoundError` 使用源码回退，DWM 已知结构错误保持具体捕获，普通运行时异常用真实 traceback 日志后安全返回 `(False, 0)`，process-control 异常继续传播。Review 进一步真实复现两个自定义 logger formatter 虽收到 `exc_info` 却不输出 traceback，现已共享追加 `formatException()` 结果，并用真实 `sys.exc_info()` 锁定彩色/纯文本、同一 `LogRecord` 跨多 handler 的缓存复用与单次堆栈输出。聚焦 `14 passed`、全量 Python `598 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Python 3.9 AST、`py_compile`、`git diff --check` 与两路独立 Review 均通过；仓内 `except BaseException` 与裸 `except:` 已归零，所有 runner 均为 `visible_windows=0 / job_active_processes=0`。规范提交：`8272d2c0`；异常提交：`354777fe`；缓存回归提交：`a8e80e86`；Build All [29215327021](https://github.com/aki-riko/PrismQML/actions/runs/29215327021) 与补充回归后的 [29215605764](https://github.com/aki-riko/PrismQML/actions/runs/29215605764) 均七项全绿。P7B 用真实失败 watcher 复现 key/global 回调异常虽不阻断后续回调与 Qt `changed` signal、却只留下无 traceback 的 WARNING；修后 watcher 边界继续只捕 `Exception`，失败回调通过 `exception()` 保留堆栈且不吞 `KeyboardInterrupt/SystemExit`。修前新增回归 `2 failed`，修后聚焦 `11 passed`；全量 Python `601 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Python 3.9 AST、`py_compile`、`git diff --check` 与两路独立 Review 均通过，runner 保持 `visible_windows=0 / job_active_processes=0`。提交：`c962014e`；Build All [29216112390](https://github.com/aki-riko/PrismQML/actions/runs/29216112390) 七项全绿。P7C 用 Qt 安装失败的真实调用形状复现 `installDwmSyncFilter()` 在 `RuntimeError` 后残留假全局过滤器、第二次调用误报成功，以及安装阶段 `KeyboardInterrupt/SystemExit` 虽传播却污染状态；修前 `3 failed / 3 passed`，修后改为“局部构造并安装成功后才提交全局”，普通异常通过 `exception()` 保留 traceback，进程控制异常继续传播且状态保持可重试。补充锁定无 `QApplication`、成功幂等、构造阶段普通异常与进程控制异常后，聚焦 `11 passed`；全量 Python `609 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Python 3.9 AST、`py_compile`、`git diff --check` 与两路独立 Review 均通过，runner 保持 `visible_windows=0 / job_active_processes=0`。Review 同时依据 PyObjC v9.0 官方文档与上游 `test_voidp_roundtrip` 纠正旧库存误报：`objc.objc_object(c_void_p=window_id)` 的整数指针关键字是受支持合同，不作伪修复。提交：`bb81d37b`；Build All [29216851715](https://github.com/aki-riko/PrismQML/actions/runs/29216851715) 七项全绿。P7D 依据 PySide6 `QProcess.startDetached()` 的 `(bool, pid)` 合同，用真实失败形状 `(False, 0)` 复现原实现仍返回 True、调用 `QCoreApplication.quit()` 并让未启动安装包的非 Windows 应用退出；Windows 路径同时复现 `ShellExecuteW` 未声明 `argtypes/restype`、默认 4 字节 `c_long` 可能截断 64 位 `HINSTANCE`，以及异常只留无 traceback 的 WARNING。修前聚焦 `3 failed / 24 passed`；修后按元组解包结果，显式使用六项 Windows API 参数类型与 pointer-size 返回类型，按 `<=32` 判断失败，将可枚举异常收窄后交给 `logger.exception()`，并抽出 6–19 行内部 helper，公开 `runInstallerAndQuit(str, str) -> bool` 缩至 20 行且签名不变。最终聚焦 `32 passed`，锁定 detached/Windows 成败、`None/32` 失败边界、完整六参数及 `KeyboardInterrupt/SystemExit` 传播且不退出；全量 Python `618 passed / 1 skipped`、QML `169/0/12`、headless CTest `6/6`、Python 3.9 AST、`py_compile`、`git diff --check` 与两路独立 Review 均通过，runner 保持 `visible_windows=0 / job_active_processes=0`。提交：`e344c8a0`；Build All [29217783690](https://github.com/aki-riko/PrismQML/actions/runs/29217783690) 七项全绿。剩余宽捕获、59 个超长函数、未使用导入与文件头分类继续按 P7 顺序处理。

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

#### P7E-P7K：2026-07-13 追加只读复核批次

以下问题均已用真实隐藏运行链复现；P7E-P7G 已于 2026-07-13 完成，P7H 已于 2026-07-14 完成，P7I 正在按调用链拆批整改，其中 P7I-A/P7I-B/P7I-C、P7I-D1-D5、P7I-F 的 F1-F4、F5a-F5f、F6 与 F7a-F7h 已完成，F5 剩余耦合调用链仍待后续正确性批，下一批继续对 F7 剩余长函数做只读候选 Review 后按单一调用链推进；P7J-P7K 仍按顺序待整改。所有 Python/QML 诊断均经统一 runner 执行并保持 `visible_windows=0 / job_active_processes=0`；D5 及更早批次已有用户桌面确认，用户随后也确认 F1a 门禁未出现错误弹窗，F1b 起后续批次均记录 runner 的零窗口/零残留证据。

1. **P7E 配置事务、schema 与 Python/C++ 对齐（已完成）**

   修复前问题：

   - `SettingsCore.set()` 当前候选实现会在持久化前发出 `valueUpdated`，失败时再发回滚值；`ConfigManager` 直接把该信号转发给 QML，未提交值会真实外泄。`os.replace()` 成功后的日志异常还可能造成磁盘新值、内存旧值。
   - `_read_mapping()` 必须把真实畸形输入产生的 `ValueError`（超长 JSON 整数）与 `RecursionError`（极深嵌套）纳入已知文件输入边界；`_apply_mapping()` 中途失败不得留下部分加载状态。
   - `SettingEntry` 目前作为类属性被同一子类所有实例共享；不同配置文件实例会互相污染值与信号。`__init_subclass__()` 的近祖到远祖合并顺序会让远祖覆盖直接父类 override；重复 `entry.key` 以及同 group 的扁平/嵌套冲突会静默丢字段。必须改成实例隔离或明确收窄公开合同，并在类定义阶段拒绝无损往返不成立的 schema。
   - C++ `ConfigManager::save()` 仍返回 `void`，五个 setter 在保存失败后照样提交内存与成功信号；`load()` 也绕过 DPI/窗口类型合法值约束。Python 修复必须同步审计 C++ 镜像，不能让两端合同分叉。
   - `cpp/tests/test_store.cpp` 当前直接备份、改写并恢复真实 `~/.prismqml/app.json`；进程崩溃或强制终止会污染用户配置。实测在 Windows 修改 `HOME/USERPROFILE/HOMEDRIVE/HOMEPATH` 后 `QDir::homePath()` 仍返回真实用户目录，因此不能把环境重定向当成隔离方案；必须给配置路径提供显式测试 seam，并让失败无需依赖收尾恢复。`test_store.cpp` 与 `test_sqlmodel.cpp` 还使用固定的系统临时文件名，后者不清理三份 shard 数据库；应统一迁移到进程唯一的 `QTemporaryDir`，消除并行冲突与残留。
   - 预期效果：保存失败零未提交通知、内存/磁盘一致、加载全有或全无、配置实例与继承 schema 可预测、自动测试不触碰用户数据。
   - 难度：12-24 小时；风险：高。
   - 验收：同一真实失败输入验证修前失败、修后通过；Python/C++ 成败、信号、回滚、畸形 JSON、三层继承、重复 key、多实例隔离与中断后用户配置零变化均有回归。

   完成记录（2026-07-13）：

   - Python 子批提交 `e48bb127`：类级 `SettingEntry` 收敛为 schema prototype，每个 `SettingsCore` 实例通过真实 QObject 构造/显式 `clone(parent)` 获得独立条目；schema 冲突、三层继承 tombstone、重复 key、扁平/嵌套冲突与带点键均在定义阶段或往返测试中确定性处理。
   - `SettingsCore.set()/load()` 均先完成 prepare、encode/decode、校验与双副本，再提交磁盘/内存和信号；`os.replace()`、目录目标、父路径为文件、不可序列化值、孤立代理字符、超长整数、极深嵌套、复制失败与第二字段校验失败均用真实输入做红绿回归。
   - C++ 子批提交 `dafa2a34`：`ConfigManager` 使用局部 `State` 严格加载，`QSaveFile` 检查目录创建、完整 write 与 commit，只有落盘成功后才替换内存并发送属性信号/`configChanged`；`App` 启动前读取与单例复用 `PRISMQML_CONFIG_FILE → ~/.prismqml/app.json` 路径解析。
   - `test_store`、`test_provider_lifecycle`、`test_sqlmodel` 全部迁移到进程唯一 `QTemporaryDir`；`SqlListModel` 在失败、连接替换、router 重建与析构时关闭并注销 QSqlDatabase，Windows 临时目录删除作为真实锁回归。
   - 最终本地门禁：Python `662 passed / 1 skipped`；QML probe `169 OK / 0 错误 / 12 跳过`；C++ headless `7/7`、Windows native `2/2`；全部 runner 为 `visible_windows=0 / job_active_processes=0`。真实 `~/.prismqml/app.json` 的长度、mtime、SHA-256 在红测、绿测及全量门禁前后完全一致。
   - 两路独立最终 Review 均为“无阻断，可提交”；`prism/main` 与 `origin/main` 已同步到 `dafa2a34`。GitHub Build All Platforms 七路全绿（run `29248729920`），Deploy Docs 构建/部署全绿（run `29248729960`）。

2. **P7F DPI 输入与系统 API 合同（已完成）**
   - `applyDpiScale()` 直接信任 JSON：字符串和列表在 `> 0` 处抛 `TypeError`；`true` 会设置 `QT_SCALE_FACTOR=0.01`，`999` 会设置 `9.99`，负数会以非法返回值走系统模式。float、NaN 与 Infinity 同样未被权威候选集拒绝。
   - `Validator.choice()` 目前因 Python `bool == int` 接受 DPI 的 `False` 与窗口类型的 `True`；`Validator.between()` 对 NaN 出现 `accepts=False` 但 `coerce()` 仍返回 NaN 的不变量破坏。
   - Python `AppConfig.dpi_scale.options` 的 `{0,100,125,150,175,200}` 必须成为 Python 启动前读取、SettingsCore、QML setter、C++ 启动前读取与 C++ ConfigManager 的共同事实源或严格镜像。
   - 微软 `GetDpiForSystem()` 合同明确：调用线程为 DPI-unaware 时固定返回 96；当前“不受 DPI 感知影响”的注释错误，QApplication 创建前调用不能证明拿到真实系统缩放。注册表句柄同时应改为确定性关闭。
   - 预期效果：任意配置文件输入只产生合法离散 DPI，Python/C++ 行为一致，非法值安全回退且不污染 Qt 环境。
   - 难度：4-8 小时；风险：中。
   - 验收：字符串、容器、bool、float、超范围、负数、NaN/Infinity、缺失键、损坏 JSON 与 Windows API/注册表失败矩阵全部零窗口通过。

   完成记录（2026-07-13）：

   - Python 子批提交 `8e24b825`：`Validator.choice()` 改为类型严格匹配并保留 `IntEnum` 往返，`Validator.between().coerce()` 对 NaN、字符串与空值始终收敛到可接受值；DPI/WindowType 候选统一来自 `AppConfig`，启动前读取按整份已知 Window schema 严格校验，并确定性清理四个 Qt DPI 环境变量。
   - Windows DPI 探测改为优先读取注册表且通过上下文管理器确定性关闭句柄；`GetDpiForSystem()` 明确降级为注册表失败后的 awareness-dependent 兜底，不再宣称其能在 DPI-unaware 启动阶段证明真实系统缩放。
   - C++/QML 子批提交 `5fb9e7d8`：新增共享 `ConfigContracts`，DPI 固定为 `{0,100,125,150,175,200}`、WindowType 固定为 `{0,1,2}`；JSON 词法严格拒绝 `150.0`、指数形式与 UTF-8 BOM，整份 Window schema 全有或全无；QML setter 在转换前验证原始 `QVariant` 类型，并公开两组候选列表。安装导出 target 同时显式传播 C++17。
   - `SettingsPage.qml` 改为“候选值 ↔ 索引”映射，不再把索引冒充配置值。真实内部 `ComboBoxDefault.currentIndex + activated` 红测坐实用户选择会打断 wrapper binding：修前后端第二次更新时 card 已到新索引而 wrapper/inner 仍停在旧索引；`SettingsCardContent` 在消费者提交后恢复受控 binding，成功、后续合法/非法后端更新及后端拒绝提交回退均有正式回归。
   - C++ QML 合同测试补上 `QVariantList 元素 → QML 索引 → QVariant setter` 往返；同时用 build 工作目录稳定复现旧 `100 次 processEvents()` 轮询仍处于 `Loading` 的假红，修为 `statusChanged + 5 秒有界事件循环` 后同一 CTest 输入通过。
   - 最终本地门禁：P7F 聚焦 `122 passed`；Python 全量 `736 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；C++ headless `7/7`、Windows native `2/2`。仓库标准 MSVC + Qt 6.11.1 构建输出 `PRISM_BUILD_DONE`；另在系统临时目录用全新 `PRISM_VERIFY_MOBILE=ON` 构建树实编译 `ConfigContracts.cpp`、`App.cpp` 与 `prism_mobile_verify.lib`。
   - 所有 runner 均为 `visible_windows=0 / job_active_processes=0` 且清理成功，用户确认本轮没有出现错误弹窗。真实 `~/.prismqml/app.json` 始终保持 `141` 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`；三路独立最终 Review 均为“无阻断，可提交”。
   - 证据边界：新代码所用 Qt API 已静态确认兼容 6.9，本机实际运行验证为 Qt 6.11.1，现有 CI 固定 Qt 6.10.3；最低 Qt 6.9 运行时仍待独立 lane 实跑，未冒充已验证。

3. **P7G QRCode QML URL 传输协议（已完成）**

   修复前问题：

   - `getImageSource()` 用 `|` 拼接字段，provider 用 `id.split("|")` 解析；真实 `QQmlEngine + Image` 会把分隔符编码为 `%7C`。输入 `HELLO/120/#112233/#445566/H` 后，provider 实际缓存键为 `HELLO%7C120%7C#112233%7C#445566%7CH|150|#000000|#ffffff|M`，即二维码内容变成整段协议，尺寸、颜色与纠错级别全部退回默认且 QML 无报错。
   - Python provider 与生命周期测试直接调用 provider，未经过 QML URL 层，因此无法发现该缺陷；`int(parts[1])` 还位于异常边界外，畸形 id 可直接抛出。C++ 使用完全相同的 `|` 协议，`test_qrcode_gen.cpp` 直接截取 URL 文本后调用 provider，却错误标注为“与 QML 一致”，同样绕过真实 URL 编码。
   - C++ `qrcodegen::QrCode::encodeText()` 对超长内容会抛 `data_too_long`，`QRCodeImageProvider` 没有异常边界；Python/C++ 两端也都缺少尺寸上限，任意正整数可触发超大图像分配。
   - 应改用无歧义的单段编码（例如版本化 JSON + URL-safe Base64），验证尺寸上限、颜色与纠错级别后再生成；不得保留脆弱的分隔符兼容协议。
   - 预期效果：真实 QML 控件生成的内容、尺寸、颜色和纠错级别与公开属性完全一致，畸形/超大输入安全失败。
   - 难度：4-8 小时；风险：中。
   - 验收：必须由隐藏 `QQmlEngine + QRCode.qml + QQuickImageProvider` 真实链抓取并解码二维码内容，不能只直接调用 provider。

   完成记录（2026-07-13）：

   - Python/QML 子批提交 `620da260`：协议统一为 `image://qrcode/v1.<无填充 Base64URL>`，载荷为规范紧凑 JSON 数组 `[1,content,size,foreground,background,errorLevel]`；解码后必须规范重编码完全一致，不保留旧 `|` 分隔协议。
   - 输入合同统一为尺寸 `32..1024`、内容不超过 `1024` UTF-8 字节、颜色有效且不透明并规范化为小写 `#rrggbb`、前后景不同、纠错级别限定并规范化为 `L/M/Q/H`；畸形 Base64URL、非法 UTF-8、深层 JSON、错误字段类型及超限输入均安全返回透明占位图。
   - Python 渲染固定 4 模块 quiet zone、整数模块像素并居中，不做最终缩放；`qrcode` 使用 `optimize=0` 保持整串单模式。缓存改为受 `RLock` 保护的真实 LRU，限制为 64 项、32 MiB。
   - C++ 子批提交 `77d045c5`：实现同构协议、验证、透明失败边界及受 `QMutex` 保护的同额度 LRU；编码改用 `encodeSegments(..., boostEcl=false)`，避免纠错级别自动提升，并补齐 `data_too_long`、分配失败和未知异常边界。
   - 同一真实失败输入 `HELLO / 120 / #112233 / #445566 / H` 已通过隐藏 `QQmlEngine + QRCode.qml + QQuickImageProvider` 完整链验证：provider id、六个字段、请求尺寸、成图尺寸及前后景颜色均保持一致；保留字符与 Unicode 内容由 OpenCV 严格按 `decoded == expected` 验证，不再接受 Latin-1 容错假绿。
   - 最终聚焦 Python `71 passed`；Python 全量 `802 passed / 1 skipped`；QRCode CTest `2/2`、headless CTest `7/7`、Windows native CTest `2/2`；QML probe `169 OK / 0 错误 / 12 跳过`，changed QML 扫描 `0 violation(s)`；Rust `fmt --check`、`clippy --all-targets -D warnings` 与 `cargo test 6/6`、`git diff --check` 全部通过。
   - 仓库标准 MSVC + Qt 6.11.1 构建输出 `PRISM_BUILD_DONE`。全部 runner 为 `visible_windows=0 / job_active_processes=0`，最终 native 夹具退出后无残留测试进程，用户确认未出现错误弹窗；真实用户配置仍为 `141` 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`。Qt 6.9 仅完成源码/API 静态兼容审查，未冒充最低版本已实跑。

4. **P7H NativeWindowHook WinAPI 结果与状态提交（已完成）**
   - `_attach()`、`_apply_framechanged()` 与 `detach()` 忽略 `Get/SetWindowLongPtrW`、`SetWindowPos` 的失败结果，却提交 `_hwnds/_framechanged_hwnds/_original_styles` 状态，可能形成不可重试的假 attached/finalized 或“内部已 detach、原生样式未恢复”。
   - 按微软合同，`SetWindowLongPtrW` 返回 0 既可能失败也可能旧值为 0 的成功，必须 `SetLastError(0)` 后结合 `GetLastError()` 判断；`SetWindowPos` 成功非零、失败为 0。普通异常必须保留 traceback，进程控制异常继续传播。
   - 预期效果：只有全部必要原生调用成功才提交状态，部分失败可安全回滚或重试，detach 不谎报恢复。
   - 难度：4-8 小时；风险：高。
   - 验收：无窗口 mock 合同测试覆盖零返回成功/失败、SetWindowPos 失败、部分提交回滚、重试幂等与 `KeyboardInterrupt/SystemExit`；Windows native 集合仍只能经 CTest 间接运行。

   完成记录（2026-07-14）：

   - 代码提交 `cb19eb88`：Python 与 C++ 的 `attach/finalizeAttach/detach` 统一返回严格 `bool`；WinAPI 按 `clear LastError → call → read LastError` 检查，正确区分 LongPtr 合法零返回与失败，保存 `SetWindowLongPtrW` 实际返回的旧 style，并把 attached、framechanged、restore-pending 三阶段状态及失败重试合同显式化。
   - Python 以 `shiboken6.getCppPointer()` 的 QObject 身份维护 owner generation；C++ 使用 generation、retired owner 与双向 HWND 绑定。两端均拒绝 retired owner 的迟到 attach/finalize，迟到或重复 detach 幂等；public detach 只使用已跟踪 HWND，不再因调用 `winId()` 反向创建平台窗口。
   - `WindowsCore.qml` 的原生启动事务拆入 `NativeWindowStartupHelper.qml`：仅字面 `true` 发布 `nativeHookReady`，失败最多重试一次且不重复 `startShow()`；missing/false/throw/null 四类析构路径由 `engine.warnings + qInstallMessageHandler` 双通道回归锁定，未捕获 QML TypeError/Error 会直接红测。
   - 结构门禁：生产 `native_window.py` 为 490 行，相关 Python/QML 测试函数均不超过 30 行；`WindowsCore.qml` 670 行与 `cpp/tests/test_native_window.cpp` 688 行仍是 500 行软警告，但均低于对应 700 行硬限制，且 C++ 长测试函数已拆分。
   - 最终本地门禁：P7H 聚焦 `41 passed`；Python 全量 `843 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；仓库标准 MSVC + Qt 6.11.1 构建输出 `PRISM_BUILD_DONE`；NativeWindow CTest `1/1`、headless CTest `8/8`、Windows native CTest `2/2`；Rust `fmt --check`、`clippy --all-targets -D warnings` 与 `cargo test 6/6`、`git diff --check` 全部通过。
   - 全部 runner 均为 `visible_windows=0 / job_active_processes=0` 且无测试残留，用户确认未出现错误弹窗。真实 `~/.prismqml/app.json` 始终为 `141` 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`；受保护 audit 日志时间戳与哈希未变。多路最终 Review 清零 P0-P2 后确认可提交。

5. **P7I 剩余规范库存（进行中）**
   - 当前纯 `HEAD` AST 口径已纠正为：`prismqml/python` 仍有 27 个含 `Exception` 的 handler、50 个超过 30 行的函数；`scripts` 有 10/5，其中 2 个 handler 是事务回滚后重新抛出，普通口径仍为 8/5。普通错误路径仍有只记无 traceback 的 `error/warning/debug`，必须继续按真实调用链分类，不能机械收窄。
   - 178 个受跟踪 Python 文件中仍有 9 个不符合强制四行 MIT 头；仓库内没有 Python shebang，额外 Copyright 行应保留并移动到强制四行之后。
   - `tests/qml/bench_skin_frames.py` 把结果硬编码到 `C:/Users/Kotori/frame_bench.txt`，违反路径零硬编码；应改为显式参数、环境变量或测试临时目录。
   - `cpp/tests/qr/verify_qr.py` 的非性能测试诊断仍通过 `print_safe()` 直接调用 `print`；这是旧提交 `2db05888a` 引入的当前 HEAD 合规库存，P7G 仅改动相邻 docstring，后续应迁移到统一 logger 或经评审定义机器可读测试输出例外。
   - 未使用导入需按 AST 候选逐个核对公开 re-export、`TYPE_CHECKING` 与导入副作用后再删除，禁止机械清理。
   - 预期效果：宽捕获具备可解释边界与 traceback，长函数和文件头库存量化归零或仅剩评审例外。
   - 难度：1-3 天；风险：中。
   - 验收：重复 AST 库存、Python 3.9 语法、全量 Python、QML probe、headless CTest、changed scanner 与 `git diff --check` 全部通过。

   已完成子批（2026-07-14）：

   - P7I-A 代码提交 `fe7a4f4e`：`ShadowManager.enableShadowForWindow()` / `disableShadowForWindow()` 保留 QML 用户边界并改用带 `exc_info` 的 traceback 日志。真实输入是经 `deleteLater + DeferredDelete` 销毁的 `QWindow`；两条边界继续返回 `False`，`KeyboardInterrupt/SystemExit` 原样传播。
   - P7I-B 代码提交 `21211777`：`WindowCore._on_close_requested()` 的用户 `closeEvent` 边界保留 `Exception`，异常时记录完整 traceback 并 fail-closed 为拒绝关闭；`closeRequestAccepted` 写回只捕获真实已销毁 `QQuickWindow` wrapper 产生的 `RuntimeError`，同样保留 traceback。真实隐藏 QML 链验证窗口仍可见、拒绝状态写回正确，进程控制异常继续传播。
   - 两批测试均捕获项目 logger 的真实 `LogRecord`，断言唯一目标记录的 `exc_info`、异常类型和 `PlainFormatter` 输出中的真实源码调用点。P7I-B 关闭握手脚本 `PASS`，traceback 聚焦 `20 passed`，Python 全量 `849 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 扫描 0，Python 3.9 AST、compileall 与 `git diff --check` 均通过。
   - 全部 runner 继续为 `visible_windows=0 / job_active_processes=0`，用户明确确认测试期间没有出现弹窗。真实 `~/.prismqml/app.json` 与受保护 audit `LastTest.log` 的字节数和 SHA-256 均保持既有基线；独立 Review 为 P0/P1/P2 全零。下一批为 P7I-C `SqlListModel` 回调边界，暂不混入长函数、文件头、benchmark 路径或 QR stdout 政策。
   - P7I-C 结构过渡评审例外（2026-07-14）：本批只把 formatter 用户回调和 `data/getRow` 公共页读取失败边界抽入 11/14/18 行的小 helper；既有 `_fetch_page` 从 145 行、嵌套深度 5 降为 129 行、深度 4，但仍不满足 30 行/3 层目标。Review 明确批准它仅作为 P7I-C 的过渡例外，剩余查询规划、后端读取、列初始化与分页编排必须在 P7I-F 单独拆分；本例外不得用于向该函数继续加入新逻辑，也不得据此宣称长函数债务完成。
   - P7I-C 代码提交 `3b717770`：`data()` 与公开 QML Slot `getRow()` 共用页读取失败边界，真实删除 SQLite 文件后分别降级为 `None` / `{}` 并保留 traceback，已缓存页仍可读取；真实 Rust 返回 `RuntimeError`，强制 Python fallback 返回 `sqlite3.OperationalError`，两条后端均进入正式回归。formatter 失败保留原值并继续处理后续行，同页同列只记录首个 traceback，避免日志风暴；`data/getRow × KeyboardInterrupt/SystemExit` 与 formatter 进程控制异常均原样传播。
   - P7I-C 聚焦测试正常 logger 与预先初始化非默认 logger 均为 `11 passed`，C++ SqlModel CTest `1/1`；Python 全量 `858 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 扫描 0，全仓 178 个受跟踪 Python 文件的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 runner 为零可见窗口、零残留进程，真实用户配置和受保护 audit 指纹未变化；两路最终 Review 均为 P0/P1/P2 全零。
   - 非阻断既有债务：Python fallback 在数据库路径被删除后会由普通 `sqlite3.connect(path)` 重建空文件；该行为涉及只读 URI 与路径编解码，转入 P7K 合并处理。下一批 P7I-D 按 `logger.install_qt_message_handler`、`_window_compat`、`_window_builder`、`_splash_builder`、`_page_manager` 的真实启动降级调用链逐个整改，不与 P7I-F 长函数拆分混批。
   - P7I-D1 代码提交 `f2b4af11`：`install_qt_message_handler()` 的普通安装失败继续按既有语义降级启动，但改为记录活动 traceback；真实 `qWarning` 锁定 WARNING 级别与 `QML` tag，`KeyboardInterrupt/SystemExit` 原样传播。原 51 行函数拆为 5/20/8/18 行 helper，因此生产超长函数库存 `51→50`。
   - P7I-D2 代码提交 `cc4567b2`：真实 `QQuickWindow` 经 `deleteLater + DeferredDelete` 销毁后，`_restore_visible_state()` 的 `QMetaObject.invokeMethod` 与属性 fallback 两条边界均记录唯一 RuntimeError traceback；继续执行 fallback 的顺序不变，invoke/fallback 两阶段的 `KeyboardInterrupt/SystemExit` 均传播。
   - P7I-D1/D2 最终门禁：logger 聚焦 `7 passed`、logger + App 启动 smoke `15 passed`、可见状态真实脚本 `PASS`、process-control `4 passed`、headless 入口联合 `22 passed`；Python 全量 `866 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 0，全仓 178 个 Python 3.9 AST、compileall 与 `git diff --check` 通过。全部 runner 零可见窗口、零残留进程，用户配置和受保护 audit 指纹未变化。下一批为 P7I-D3 `_window_builder` 文件化窗口 QML 失败回退边界。
   - P7I-D3 结构过渡评审例外（2026-07-14）：本批只把生成窗口 QML 的剖析、文件 component 加载与普通异常边界抽入 17/6/18/27 行 helper；`_create_window()` 从 270 行、控制嵌套深度 3 降为 242 行、深度 2，但仍远超 30 行目标，生产超长函数库存仍为 50。Review 仅批准它作为 D3 文件化加载边界的过渡例外；引擎获取、ContextProperty/ImageProvider 注入、导航与页面 QML 生成、rootObject 装配、信号/pending state 与 Splash 编排必须留给 P7I-F 单独拆分。本例外不得用于继续向 `_create_window()` 堆逻辑，也不得据此宣称长函数债务完成。
   - P7I-D3 代码提交 `ef07928d`：真实缓存路径被普通文件占用时，`cache_dir.mkdir()` 稳定产生 `FileExistsError / WinError 183`；同一真实输入现在记录活动 traceback，并继续通过 inline `engine.loadData()` 创建可见窗口。Review 另发现首次 helper 抽取会在真实 `QQmlComponent.create()` 成功后、剖析回调抛 `RuntimeError` 时丢失已创建对象并误触发第二次加载；新增红测先以真实 QML 对象复现返回 `None`，修后边界保留原对象，日志明确区分“保留已创建窗口”与“实际 fallback”。两阶段的 `KeyboardInterrupt/SystemExit` 均原样传播，standalone 清理使用 `try/finally + DeferredDelete`，且未新增测试 stdout。
   - P7I-D3 最终门禁：process-control `2 passed`，真实 standalone 两条失败链退出码 0，headless 入口矩阵 `19 passed`；Python 全量 `869 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 0，当前工作树 181 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 Python/QML runner 为零可见窗口、零残留进程；真实 `~/.prismqml/app.json` 与两份受保护 audit `LastTest.log` 的字节数和 SHA-256 均保持基线，两路最终 Review 为 P0/P1/P2 全零。下一批为 P7I-D4 `_splash_builder` 文件化 Splash QML 降级边界。
   - P7I-D4 结构过渡评审例外（2026-07-14）：本批只把生成 Splash QML 的剖析、文件阶段异常日志与 component 加载边界抽入 17/7/26 行 helper；`create_splash()` 从 220 行、控制嵌套深度 4 降为 207 行、深度 2，但仍远超 30 行目标，生产超长函数库存仍为 50。Review 仅批准它作为 D4 文件化 component 与非致命创建边界的过渡例外；剖析状态、Splash QML 模板构建、inline `setData`、component 校验/实例化、窗口挂载与引用发布必须留给 P7I-F 单独拆分。本例外不得用于继续向 `create_splash()` 堆逻辑，也不得据此宣称长函数债务完成。
   - P7I-D4 文件化 Splash 边界已完成：真实缓存目录被普通文件占用时，`FileExistsError / WinError 183` 记录活动 traceback 后仍通过 inline `setData` 创建并挂载 Splash；真实文件 component 创建后剖析 `RuntimeError` 会保留该 component 且不误走 inline；真实 `QQuickWindow` 经 `DeferredDelete` 销毁后，挂载阶段 `RuntimeError` 记录 traceback 并按既有非致命语义放弃 Splash、不阻断窗口启动。内外两阶段的 `KeyboardInterrupt/SystemExit` 均原样传播，文件 component 与 inline 来源日志已明确区分。
   - P7I-D4 最终门禁：process-control `4 passed`，真实 standalone 三条失败链退出码 0，headless 入口矩阵 `20 passed`；Python 全量 `874 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 0，当前工作树 183 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。新增测试的 window/splash 两套生成缓存均指向 `TemporaryDirectory`；隔离复验及全量后真实用户 QML 缓存 246 个文件的路径/大小/mtime/SHA-256 快照完全不变。真实 `~/.prismqml/app.json` 与两份受保护 audit `LastTest.log` 指纹同样保持基线，两路最终 Review 为 P0/P1/P2/P3 全零。下一批为 P7I-D5 `_page_manager` 页面创建边界。
   - P7I-D5 结构过渡评审例外（2026-07-14）：本批只把页面尺寸信号、异步页面实例解析与创建异常边界抽入 6/8/6 行 helper；`_start_async_page_load()` 从 125 行、控制嵌套深度 4 降为 112 行、深度 3，但仍远超 30 行目标，生产超长函数库存仍为 50。Review 仅批准它作为 D5 页面失败边界的过渡例外；loading 触发、导航项与容器校验、页面就绪回调、尺寸绑定、deferred 批创建及切换编排必须留给 P7I-F 单独拆分。本例外不得用于继续向 `_start_async_page_load()` 堆逻辑，也不得据此宣称长函数债务完成。
   - P7I-D5 页面失败边界已完成：真实页面工厂 `RuntimeError`、真实 `QQuickItem` 删除后的尺寸信号 `RuntimeError`，以及真实已销毁 `QQuickWindow` 的 navigate/loading start/loading finish 三条 `RuntimeError` 均保留活动 traceback；原有页面来源优先级、失败后 `on_page_ready(None)`、16ms 定时入口、loading 降级与切换语义不变。两处 `Exception` 与三处 `RuntimeError` 边界均不捕获 `BaseException`，10 条 `KeyboardInterrupt/SystemExit` 传播回归通过；新增 standalone 在 PySide6/shiboken6 导入前启用统一 bootstrap，并把 window/splash 生成缓存重定向到 `TemporaryDirectory`。
   - P7I-D5 最终门禁：process-control `10 passed`，真实 standalone 五条失败链退出码 0，headless 入口矩阵 `21 passed`；Python 全量 `885 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 0，当前工作树 185 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 Python/QML runner 为零可见窗口、零残留进程，用户确认未出现错误弹窗；真实 `~/.prismqml/app.json` 与两份受保护 audit `LastTest.log` 的字节数、mtime 和 SHA-256 保持基线。全量门禁期间同机并行 Kaleidos 测试任务向用户缓存新增 `window_d0b55378adedb099867d.qml` 与 `splash_8259d9fec04154f95db7.qml`，两文件内容明确引用 `D:/PrismQML/Kaleidos/src/client/.venv` 及“幻灵匣”标题；未删除该外部缓存。随后以当前 248 文件清单为基线单独复跑 D5 standalone 与 process-control，前后聚合 SHA-256 均为 `EEB0DBFF690C88C938BC470EED4B22FB6D59A253F3CF78D4A8378F6A8D4D0519`，证明 D5 入口本身不写用户缓存。三路独立 Review 为 P0/P1/P2/P3 全零；下一批为 P7I-F 长函数拆分。

   P7I-F 长函数拆分执行计划（2026-07-14）：

   - 当前生产库存按 Python 3.9 AST 复算为 50 个超过 30 行的函数：`window=20 / core=17 / models=8 / providers=4 / state=1`；`config=0`。`icons.py::Icon.to_qicon()` 继续受 P8B 生成器前置约束，P7I-F 不得把它盲拆或粉饰为合规；其余函数仍须归零或形成逐项评审例外。
   - F1 Research 前置真实复现：`Window.setUserCard(...)` 会生成根组件不存在的 `userCard/userCardPosition` 属性，文件 component 与 inline fallback 均报 `Cannot assign to non-existent property "userCardPosition"`，最终 `Window.show()` 抛 `Failed to create window`。本机 `AeroMount/configpilot/Gitora/Kaleidos/quicksketch` 等 6 个下游当前源码零调用；Kaleidos 历史提交曾把头像更新标为“后续通过 setUserCard 实现”，随后因头像不显示改走 `bottomNavigationItems`，证明该入口从未形成可用合同。按 pre-1 规则单独删除 Python `setUserCard`、`_user_card` 与生成字段，不保留兼容别名；公开、可独立实例化的 `NavigationProfileCard` QML 组件继续保留。
   - F1 失效 userCard API 前置清理已完成：删除 `WindowCore.setUserCard`、`_user_card` 及 `_window_builder.py` 中两个不存在的根属性生成分支；公开 `NavigationProfileCard.qml` 与两处 `qmldir` 注册均保留。删除 API 聚焦回归 `5 passed`，BAR/SPLIT/FILLED 三种真实窗口 characterization 均退出 0，headless 入口矩阵 `22 passed`；Python 全量 `887 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML 0，当前工作树 186 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。普通有效窗口改前/改后生成 QML 均为 1761 字节、SHA-256 均为 `456598553B3F9FAE338938D4881EE1252FF2D33D4D300BC201AC15EABEFBEFAA`；`_create_window()` 仍为 223 行，生产超长函数库存仍为 50，未宣称 F1a 或长函数债务完成。
   - F1 前置清理最终隔离与 Review：全部 runner 为 `visible_windows=0 / job_active_processes=0`，未检测到可见窗口且清理归零；本批未复用较早批次的用户桌面确认。真实用户 QML 缓存保持 248 个文件，按“相对路径/长度/UTC ticks/文件 SHA-256”排序聚合后的 SHA-256 仍为 `EEB0DBFF690C88C938BC470EED4B22FB6D59A253F3CF78D4A8378F6A8D4D0519`；真实 `~/.prismqml/app.json` 仍为 141 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`；两份受保护 audit `LastTest.log` 均为 142 字节、各自 mtime 未变、SHA-256 均为 `124952A66B9D1157741E56BB46C83C639680A77FBD5BAB8E3E71AA41BC551195`。代码与测试最终 Review 均为 P0/P1/P2/P3 全零；下一批严格进入 F1a，不顺带移动 engine/context/fallback/root/pending/splash 时序。
   - F1 `_create_window` 按启动时序拆为三个独立提交。F1a 只抽离导航项、底部项、页面容器与根窗口模板的纯 QML 组合，根模板使用模块级 `string.Template`，不移动 engine/context、文件/inline fallback、root/pending/splash 的执行顺序；删除失效 userCard 前置后，目标把 `_create_window()` 从 223 行降至约 145–155 行，所有新增 helper 不超过 30 行。F1b 再拆 engine 获取与 ContextProperty/ImageProvider 注入；F1c 最后拆 root 加载安装、pending 去重/应用与 Splash 收尾，最终主编排目标不超过 30 行。F1a 难度 2–4 小时、风险中；F1b/F1c 各 4–8 小时、风险高。
   - F1a 改前有效 `Window` characterization 已固定：特殊字符标题、非默认尺寸、命名/本地图标、顶部项、`selectable=false` 底部项与预设 Mica 的生成 QML 为 1761 字节，本机 SHA-256 `456598553B3F9FAE338938D4881EE1252FF2D33D4D300BC201AC15EABEFBEFAA`；该绝对路径相关哈希只用于同工作区前后逐字节比较，不作为跨平台硬编码断言。正式回归必须使用 `TemporaryDirectory` 隔离 window/splash 缓存，并真实创建 BAR/SPLIT/FILLED 根窗口，锁定转义、导航 key/selectable、页面容器、尺寸、图标、Mica 与 pending 清空。
   - F1a 纯 QML 组合拆分已完成：根窗口源码迁入模块级 `string.Template` 并使用严格 `substitute()`；顶部导航、底部导航、页面容器、根模板替换、窗口状态解析和组合顺序分别进入 9/10/17/28/14/28 行 helper。`_create_window()` 从 223 行降至 154 行，生产文件为 498 行；组合顺序仍为 top → bottom → pages → profile → component/icon/mica → template → profile，Engine、ContextProperty、ImageProvider、文件/inline fallback、root、pending 与 Splash 的相对时序均未移动。生产超长函数库存仍为 50（`window=20 / core=17 / models=8 / providers=4 / state=1`），因此只宣称 F1a 完成，不宣称 F1 或长函数债务完成。
   - F1a 字节合同与专项验证：既有 1761 字节 / `456598553B3F9FAE338938D4881EE1252FF2D33D4D300BC201AC15EABEFBEFAA` 同工作区 characterization 保持有效；另以固定输入路径、独立 before/after 缓存生成 1826 字节源码，两侧 SHA-256 均为 `AEFD6F0F12391D2A61F97DE086FA02E51FA882B1CA730CD487557566F9F5703C` 且逐字节相等。新增 4 条纯 helper 回归覆盖空集合、两组导航项的完整顺序与字段配对、连续页面容器，以及替换值中的 `$`、引号、花括号、换行和小写布尔；Review 发现的分散 substring 误放行已改为完整字符串等值断言。
   - F1a 最终门禁：纯 helper / window-builder 聚焦 `6 passed`，联合删除 API、转义与 WindowType 聚焦 `17 passed`；真实 BAR/SPLIT/FILLED composition、文件 component 后诊断失败和缓存目录占用 fallback 均退出 0，headless 入口矩阵 `22 passed`。最终 Python 全量 `891 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML `0`，186 个受跟踪 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 Python/QML runner 为 `visible_windows=0 / job_active_processes=0`；真实用户缓存仍为 248 个文件且聚合 SHA-256 为 `EEB0DBFF690C88C938BC470EED4B22FB6D59A253F3CF78D4A8378F6A8D4D0519`，`app.json` 与两份受保护 audit 指纹均未变化。用户随后明确确认该轮未出现错误弹窗；代码与测试最终 Review 均为 P0/P1/P2/P3 全零。Build All `29294081396` 与 Deploy Docs `29294081395` 均成功；下一批严格进入 F1b。
   - F1b Engine/context/provider 拆分已完成：新增 93 行 `_window_engine_setup.py`，把核心 manager 动态加载、Engine 复用/创建、窗口依赖动态加载、七项 ContextProperty 注入、Icon/SVG provider 注册与总编排拆为 7/8/14/22/5/14 行 helper；`_create_window()` 从 154 行降至 120 行，`_window_builder.py` 从 498 行降至 463 行。原顺序仍为 core/config import → profile → get/create/set Engine → profile → Mica/Native/Clipboard/Icon import → profile → Theme/Shadow/Config/Mica/Clipboard/verbose/Native 注入 → profile → Icon → SVG → profile → qml_path；Engine 仍先写入 builder 再交给 `EngineManager`，SVG provider 仍由 Engine 接管。QML 组合模板及 6 个生成 helper 与 `48171374` 对应源码块逐字相等；文件/inline fallback、root 安装、pending 与 Splash 均未触及。生产超长函数库存仍为 50（`window=20 / core=17 / models=8 / providers=4 / state=1`），因此只宣称 F1b 完成，不宣称 F1 或长函数债务完成。
   - F1b 合同与最终门禁：纯 fake 合同锁定已有 Engine 复用、缺失 Engine 创建/注册、两个真实 loader callable 身份、五个 profile 标签、七个 ContextProperty、Icon → SVG provider 顺序，以及普通 `RuntimeError`、`KeyboardInterrupt`、`SystemExit` 的 fail-fast 传播；window-builder + provider 生命周期聚焦 `27 passed`。真实 BAR/SPLIT/FILLED composition 与文件 fallback standalone 均退出 0，headless 入口矩阵 `22 passed`；最终 Python `909 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、187 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 Python/QML runner 为 `visible_windows=0 / job_active_processes=0`；前后真实用户缓存均为 248 个文件且聚合 SHA-256 为 `EEB0DBFF690C88C938BC470EED4B22FB6D59A253F3CF78D4A8378F6A8D4D0519`，`app.json` 与两份受保护 audit 的长度、mtime、SHA-256 均未变化。本批 F1b 未复用用户此前对 F1a 的桌面确认；代码与测试最终 Review 均为 P0/P1/P2/P3 全零。下一批严格进入 F1c。
   - F1c root/pending/Splash 收尾拆分已完成：新增 78 行 `_window_startup.py` 与 115 行 `_window_root_setup.py`，把共享 profile、verbose/cache 环境日志、动态 `qml_path`、file→inline root 选择、root 发布/content/signals、pending 四键去重/日志/应用及同步 Splash 收尾拆为 17/6/13/7/8 与 18/8/6/7/14/14/4/19 行 helper；`_create_window()` 从 120 行降至 20 行，`_window_builder.py` 从 463 行降至 366 行。原 `[WindowBuilder]` 日志 tag 通过显式常量保持，verbose 仍只读取一次并在 Engine 前记录 cache 环境，fallback 仍在成功路径调用两次 `rootObjects()` 并取第二次末项，root → content → signals → pending → Splash 时序及异常/部分状态边界均未改变。F1a 模板加 6 个生成 helper 与 `27e831f0` 对应源码块逐字相等，F2 的 `_splash_builder.py` 零差异。生产超长函数库存 `50→49`（`window=19 / core=17 / models=8 / providers=4 / state=1`），F1 三个子批至此完成，但 P7I-F/P7/P9 与全库仍未完成。
   - F1c 合同与最终门禁：纯 fake 合同锁定 profile 累计计时与 tag、verbose 真值集合、cache 日志、五阶段主编排、file 优先、精确 UTF-8 inline fallback、两次 `rootObjects()`/末 root、无 root 精确异常、root 发布/find/connect、pending 双向 qrc 归一、residual 日志→apply→profile 及 pending→Splash；真实非法 QML 输入稳定命中 `Cannot assign to non-existent property "missingProperty"` 后两路无 root，真实 blocked-cache fallback 与 BAR/SPLIT/FILLED composition 均退出 0。聚焦 `55 passed`、headless 入口 `22 passed`；最终 Python `937 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、191 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 Python/QML runner 为 `visible_windows=0 / job_active_processes=0`；前后真实用户缓存均为 248 个文件且聚合 SHA-256 为 `EEB0DBFF690C88C938BC470EED4B22FB6D59A253F3CF78D4A8378F6A8D4D0519`，`app.json` 与两份受保护 audit 的长度、mtime、SHA-256 均未变化。本批 F1c 未复用用户此前对 F1a 的桌面确认；代码、测试与结构最终 Review 均为 P0/P1/P2/P3 全零。下一批严格进入 F2。
   - F2 `create_splash()` 拆分已完成：Splash QML 迁入同文件模块级 `string.Template` 并使用严格 `substitute()`；共享 profile、值解析、模板渲染、动态 `qml_path` 准备、verbose 环境快照、file→inline component 选择与挂载分别进入 15/7/8/9/7/21/12 行 helper，`create_splash()` 从 207 行降至 30 行，`_splash_builder.py` 从 281 行变为 327 行。file 优先、仅 `None` 才 inline、UTF-8 + `QUrl("inline-splash")`、component error/create None warning、普通异常非致命 traceback、`KeyboardInterrupt/SystemExit` 传播，以及 parent → width → height → QML `_splashInstance` → profile → Python instance/component → debug 的发布顺序均保持；生产超长函数库存 `49→48`（`window=18 / core=17 / models=8 / providers=4 / state=1`）。
   - F2 合同与真实输入：固定 `D:/Fixed/Qml`、qrc 图标及含 `$`、引号、花括号、换行的标题/副标题在改前/改后均为 3455 UTF-8 字节、126 个换行、SHA-256 `2FB0C01D9B0E69109BCAADD7F12F55D03F3D7B3964190D7EF53209E318BE3661` 且逐字节相等；19 条 fake 合同锁定 guard、fallback 值、file fast-path、inline bytes/URL、component error/create None、挂载/发布顺序、旧引用保留、进程控制传播与共享累计计时。真实 standalone 继续覆盖文件 component 后 profile `RuntimeError`、缓存路径 `FileExistsError` inline fallback、已销毁窗口挂载失败，并新增特殊字符、1111×777 尺寸及 QML/Python/component 身份合同；默认挂载测试已改用临时生成缓存并显式销毁 Splash、QQmlComponent 与窗口。
   - F2 最终隔离与门禁：Review 首轮真实发现两份 standalone 虽隔离生成源码、却仍向 `%LOCALAPPDATA%/python/cache/qmlcache` 写入 9 个随机 URL `.qmlc`，且旧清理只释放窗口；现已在任何 Qt import 前固定 `QML_DISABLE_DISK_CACHE=1`、移除 `QML_FORCE_DISK_CACHE`，并逐个 `deleteLater + DeferredDelete` 后断言 Splash/component/window 均失效。修正后专项与最终全量前后 Qt cache 均为 5982 文件、聚合 SHA-256 `4642B41597C4B83BA577E2C7DE38392CB271840BE0CE22ACB405B68CABB0D588`；此前 9 个文件已精确记录路径/mtime/SHA，但因文件删除需显式授权，本批未擅自删除。聚焦 `94 passed`、headless 入口 `22 passed`；最终 Python `952 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、191 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 runner 为 `visible_windows=0 / job_active_processes=0`，残留测试进程 0；真实用户 QML 缓存 248 文件、`app.json` 与两份受保护 audit 指纹前后逐项一致。三路最终 Review 均为 P0/P1/P2/P3 全零；本批未复用此前人工桌面确认，下一批严格进入 F3。
   - F2 runner 缓存隔离补修（2026-07-14）：后续全量验收真实发现统一 runner 虽固定 headless/WER，却没有全局禁用 QML 磁盘缓存，只有两条 Splash standalone 自行设置；标准 pytest/QML probe 因而仍会刷新真实 `%LOCALAPPDATA%/python/cache/qmlcache`。`scripts/test_process.py` 现由 launcher 与 child bootstrap 在任何 Qt import 前统一强制 `QML_DISABLE_DISK_CACHE=1` 并移除 `QML_FORCE_DISK_CACHE`，显式污染环境的父进程与嵌套 runner 回归均锁定覆盖行为；runner/headless 入口 `39 passed / 1 skipped`、零窗口/零残留，提交 `798f92c`。本补修未删除既有 `.qmlc`；同机并行 Kaleidos 任务继续产生的生成 QML/Qt cache 另行按来源归因，不冒充本仓 runner 写入。
   - F3 已拆为两个独立批次：F3a 先修 keyset 正确性与 SQL 合同，F3b 再机械拆 `_fetch_page()`；F3a 不得借正确性改造宣称长函数债务完成，F3b 也不得重新改写已经固定的排序/NULL/参数语义。
   - F3a 真实失败与正确性合同（已完成，代码提交 `42075fa5`）：真实 SQLite、Rust 与 Python fallback 均复现 `ORDER BY rank DESC, id DESC` 期望 `[7,6,5,4,3,2,1]`、旧 row-value `<` 实际 `[7,6,5,4,3,None,None]`，根因是 SQLite tuple 比较遇到 NULL 返回 UNKNOWN。当前合同最多允许一个可空的非末 cursor 列，其余 cursor 输出必须由 schema `NOT NULL` 或等价表达式保证，最终 tie-breaker 必须跨 shard 全局唯一且非空；未传 `nullable_cursor_column` 时为兼容旧调用默认倒数第二列，空字符串显式声明全部非空。简单裸列 ORDER BY 在库内规范化为 `COLLATE BINARY`，函数/限定列/其他 COLLATE/NULLS/LIMIT/OFFSET、CTE、FROM/scalar 嵌套、compound、GROUP/HAVING、WINDOW/OVER、`?NNN` 与残留命名占位符均 fail-closed 拒绝。
   - F3a 受限子查询与性能合同：唯一例外是顶层 WHERE 内一个简单 `IN (SELECT 单列 FROM 单表 WHERE 条件)`；NOT IN、两个子查询、DISTINCT/JOIN/compound/ORDER/LIMIT、EXISTS、scalar SELECT 与继续嵌套均拒绝。真实 Kaleidos 30,000 行 FTS5 形状（命中 8,000、`time=NULL` 1,143）证明双支 UNION 会把 FTS 执行两次并退化到 median `1.746–1.898×` / p95 `1.735–1.933×`；当前对首 cursor 已声明非空的子查询路径使用 `first <=/>= cursor COLLATE BINARY AND expanded` 粗范围守卫，只执行一次 source/FTS，EXPLAIN 恢复 `(book_id,date)` 范围 SEARCH。当前实际文件两轮 ABBA 浅页 median `1.039× / 1.018×`、p95 `1.096× / 0.971×`，深页 median `1.054× / 0.991×`、p95 `1.046× / 0.974×`，全部通过 median `≤1.10×`、p95 `≤1.20×` 门限；DESC/ASC × Rust/Python 连续 59 页及双 shard Rust 均逐行等于 SQLite oracle。
   - F3a 通用性能与状态原子性：RHS 参数侧 `COLLATE BINARY` 保持 tuple 左列裸列，真实 200,000 行 Rust/Python 连续分页均无重无漏，SHA-256 `753aaaf224c91cc2559b38e6e17d5fb1913088a523eb609cb20e2e82bf2f6080`；深游标 NULL 修复后 79,999 行 SHA-256 `27b0fda012c9febf4bfd7dc6a604188250dac6a070144c77c0765bc7192efd75`，旧实现漏 2,061 行。两轮 60 样本 ABBA 为 median `0.98704× / 1.05533×`、p95 `1.00523× / 0.82425×`。`setQuery()` 先 prepare 后 reset，count/main dict 参数各自只归一化一次；prepare、count、列解析、首页读取及 `KeyboardInterrupt/SystemExit` 任一失败均在 `endResetModel()` 前恢复旧 SQL/count/roles/方向/nullable/LRU/formatter，失败不发 query/count 信号且异常继续传播。
   - F3a 持久化回归与结构边界：聚焦三文件为 `67 passed`，新增独立 257 行矩阵把 3 个 nullable 位置 × 8 种方向 × 3 种页大小 × Python/Rust/双 shard 共 216 组合及 4 个失败阶段 × `KeyboardInterrupt/SystemExit` 的 8 项完整实例状态回滚持久化；F3a 四文件联合 `81 passed`，全部 runner 零窗口/零残留。生产超长函数库存已从 F2 后的 48 降到 44（`window=18 / core=17 / models=4 / providers=4 / state=1`），但 `_fetch_page()` 仍为 130 行；`sql_list_model.py` 659 行、`_sql_query_tools.py` 574 行均处于 500 行软警告，前者距 700 行硬限制仅 41 行。本批只批准这些为 F3a→F3b 的临时结构例外，不得继续堆逻辑。
   - F3a 下游边界：Kaleidos 单库及“预先保持全局 id”的双 shard FTS 输入已通过，但其真实 `BookShardRouter` 使用各 shard 独立 AUTOINCREMENT `id`，不满足全局唯一末键。两 shard 相同 `(date,time,id)`、不同内容的真实输入已复现 `count=2` 但第二页为空；在迁移到真正全局唯一且 `NOT NULL` 的 tie-breaker（候选 `sync_uuid`，需补约束、SELECT/ORDER 与复合索引）或实现 per-shard cursor 前，这是独立下游 P1，严禁宣称多 shard 已兼容。金额排序的 `amount` 实际 `NOT NULL`，旧调用未传空字符串会保守生成无意义双 UNION，当前 30k ABBA 未越门限但仍是下游 P2，应按 sort 显式传 `time` 或空字符串。
   - F3a Review 新发现的独立模型 P1（转入 F6 + P7K，不阻断本批）：删除模型当前使用的真实 SQLite 文件后调用公开 `refresh()`，Python fallback 抛 `sqlite3.OperationalError` 并以普通 `sqlite3.connect(path)` 重建空文件，Rust 路径抛 `RuntimeError`；两者都把原本 `count=2 / roles 正常 / getRow(0) 正常` 的模型留成 `count=2 / roles 为空 / getRow(0)={}` 的部分状态。F3a 只承诺 `setQuery()` 原子性，不得把该债务描述为已修；F6 必须让 `refresh()` 在 count、列解析或首页读取失败时按 `_QUERY_STATE_FIELDS` 完整恢复 SQL/count/params/roles/cursor nullable/index/directions/PageCache 对象与内容/formatter/可见行，普通异常与 `KeyboardInterrupt/SystemExit` 均回滚且进程控制异常继续传播。验收须分别注入三个失败阶段并断言 `countChanged=0 / queryChanged=0`，同时明确失败时 `modelAboutToBeReset/modelReset` 是允许且必须平衡的一对，还是改为 prepare-before-reset 后完全不发 reset；P7K 另负责让 Python 读取路径使用正确编码且绝不创建文件的只读 URI，并以 Rust/Python 对同一删除文件及特殊字符路径输入做失败前后快照回归。
   - F3a 最终门禁：Python 全量 `1025 passed / 1 skipped`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；changed QML 扫描 `0 violation(s)`；当前工作树 194 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部统一 runner 均为 `visible_windows=0 / job_active_processes=0`，无残留测试进程，用户明确确认本轮未出现错误弹窗；真实 `~/.prismqml/app.json` 与两份受保护 audit `LastTest.log` 的长度、mtime、SHA-256 均保持既有基线。独立 Review 清零 P0/P1/P2，仅保留矩阵循环失败粒度的非阻断 P3；代码提交为 `42075fa5`。
   - F3b 单独拆 `SqlListModel._fetch_page()` 130 行调用链：以 F3a 提交为新的性能 before，按 route → plan → backend dispatch → column install → format → return 分层，并让 `_resolve_columns()` 复用列安装 helper；目标 `_fetch_page ≤30` 行、深度不超过 2，保持 F3a 的 216 组合、FTS guard、状态回滚、200k/30k ABBA 与全部零交互门禁逐项不变。难度 4–8 小时、风险高。
   - F3b 机械拆分已完成（代码提交 `d2f99369`）：`_fetch_page()` 从 130 行降至 15 行、控制流深度 1，route、plan、fan-out、Rust、SQLite、dispatch、列安装与 `_resolve_columns()` 共 9 个目标方法均不超过 24 行且深度不超过 2；`sql_list_model.py` 为 657 行，仍保留 500 行软警告但低于 700 行硬限制。调用顺序保持 route → plan → dispatch → install → format → return，F3a 的排序、NULL、参数、FTS guard、状态回滚与 Rust/Python 绑定语义未改；延迟 `_fetch_page()` 列安装继续允许历史大小写重复 role，正式 `_resolve_columns()` 路径仍严格拒绝重复列。生产超长函数库存 `44→43`（`window=18 / core=17 / models=3 / providers=4 / state=1`）。
   - F3b 持久化回归与 Review：新增独立 181 行结构合同，运行时 spy 锁定阶段顺序、`validate_unique=False`、rows/end cursor 身份与 formatter 时序；Python 3.9 AST 锁定 9 个方法的行数/深度、三后端 helper 委派、列安装复用、文件硬限制及 models 库存不回升。SQL 六文件聚焦 `104 passed`，代码与测试最终 Review 均为 P0/P1/P2/P3 全零。
   - F3b 性能与最终门禁：固定 F3a `42075fa5` 为 before、最终 blob `0c23d4e4` 为 after，200k Python/Rust 与 30k FTS 浅/深页的 ABBA/BAAB 正式重跑 12/12 轮通过，最差 median `1.06572× ≤1.10×`、p95 `1.10229× ≤1.20×`；200k 全量/深尾及 FTS DESC/ASC 哈希、raw rows/end cursor、SQL/params/EXPLAIN、单 FTS source/无 UNION 均一致。首次正式首轮曾以 p95 `1.21401×` 阻断并停止；镜像位置诊断证明尖峰不绑定 after 后，仅经明确授权完整重跑一次，未删除异常值或放宽门限。在基于 `f9628c71 + F3b` 的 detached 验证 worktree 中运行并排除当前工作树未纳入 F3b 提交的 Dialog/Chart 并行改动后，最终 Python `1081 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、221 个受跟踪 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过；全部 runner 零可见窗口/零残留进程，`app.json`、两份受保护 audit `LastTest.log` 与两份真实性能数据库的长度、mtime、SHA-256 均未变化。临时 worktree 已移除；本批未获得新的人工桌面确认，下一批严格进入 F4。
   - F4 before characterization 已完成（提交 `32056b02`）：新增 21 项页面管线现状合同，锁定同步 `existing → getter → class`、异步 `getter → class → truthy existing` 来源优先级，16/50/200ms 时序与 callback 身份，同步不主动 emit、异步强制双 emit，以及 deferred 两次检查、opacity、登记、batch、finish→switch、普通异常和 `KeyboardInterrupt/SystemExit` 边界。已知 deferred batch 普通异常留下 `_page_instance/_pages/opacity=0` 的部分状态只作现状刻画，F4 不顺手修复。
   - F4 机械拆分已完成（代码提交 `71854655`）：`_create_page()` `93→15` 行，`_start_async_page_load()` `112→29` 行，67 行嵌套 `on_page_ready()` 删除；profile、同步 target/source/attach/finalize、共享动态尺寸 binder、异步 target/ready/attach/finalize/batch/schedule 均拆为不超过 18 行的 helper。`_page_manager.py` 为 336 行，全部函数不超过 29 行、控制流深度不超过 2；生产超长函数库存 `43→40`，window `18→15`。Review 期间真实关闭三类漂移：半成品 stale `_qml_item` binder 与缺页索引 warning 先由同一失败输入复现 `2 failed / 22 passed` 后恢复；抽 loading helper 导致真实 traceback 离开 `_start_async_page_load` 时 standalone 非零，现保留原入口异常定位；测试条件表达式优先级造成 async 假阳性后改为独立 expected 比较并使用 replacement 专属信号名。
   - F4 最终门禁：页面聚焦 `36 passed`，真实 `test_page_manager_boundaries.py` standalone 退出码 0；全量 Python `1113 passed / 1 skipped`，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML `0`，224 个受跟踪 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部 runner 为 `visible_windows=0 / job_active_processes=0` 且清理成功；前后 `app.json` 均为 141 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`，276 个用户生成 QML 缓存与 6498 个 Qt QML 缓存的聚合 SHA-256 分别保持 `C31594774D52BDEE69571BCB7E9CF9A70AD3C9B5F3B493B6ED1AECEF47A2577D`、`9DBAFD850513276FA5B0BBAFF8731A75DC6007F0193138F67C569EE918C5DF52`，两份受保护 audit 日志均为 142 字节且 SHA-256 为 `124952A66B9D1157741E56BB46C83C639680A77FBD5BAB8E3E71AA41BC551195`；本批未取得新的人工桌面确认。代码、测试与结构最终 Review 均为 P0/P1/P2/P3 全零；下一批严格进入 F5。
   - F5a `WindowCore.addPage()` before characterization 已完成（提交 `1b5e072`）：8 项纯状态合同使用 patch 配置后的真实 `WindowCore`，不调用 `show/_create_window`，锁定 class/callable factory/instance/None 四类来源、`page_class/page_getter/_page_instance` 三槽互斥、factory 与 page class 注册阶段不提前执行、text/icon/selectedIcon/selectable metadata、top/bottom 独立追加顺序与当前局部索引 `(0,0,1,1)`，以及 `NavigationItem` 构造的 `RuntimeError/KeyboardInterrupt/SystemExit` 原样传播且零部分登记。Review 首轮发现无关 harness 会阻止未来等价 `self` helper，现已改为真实对象并清零 P0-P3。
   - F5a 机械拆分已完成（代码提交 `093b7dec`）：逐字保留 `isinstance → callable non-class → non-None instance` 判定与三种 source 槽写入，将纯构造抽到 15 行 `_make_navigation_item()`；`addPage()` 从 60 行降至 28 行，只保留 metadata → 选择列表 → append → `len-1`，签名、默认值和公开名称未改，docstring 明确 factory 与局部索引语义。`window_core.py` 为 605 行，仍处于既有 500 行软警告但低于 700 行硬限制；生产超长函数库存 `40→39`、window `15→14`。新增结构门禁精确定位模块直接 helper 与 `WindowCore` 直接方法，并在调用扫描中跳过 nested def/async/lambda；首轮全树按名称扫描的假阳性 P2 已关闭，代码与测试最终 Review 均为 P0/P1/P2/P3 全零。
   - F5a 最终门禁：行为+结构聚焦 `10 passed`，WindowBuilder/root/PageManager 联合 `83 passed`，真实 `window_builder_composition.py` 与 `page_manager_boundaries.py` 均退出 0；全量 Python 两次均为 `1123 passed / 1 skipped`，最终隔离轮为 175.75 秒，QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML `0`，226 个受跟踪 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。首次全量窗口内 Qt QML 缓存同为 6498 文件但指纹变化，最近两份 `.qmlc` 内嵌 URL 精确指向外部 `D:/PrismQML/Kaleidos-android-my-crash-20260715/.../MyPage.qml` 与 `MyCloudAccountSection.qml`；未删除或冒充本仓写入。外部进程结束后以当前状态独占重跑同一全量 pytest，前后 `app.json`、276 个用户生成 QML 缓存、6498 个 Qt QML 缓存及两份 audit 日志逐项一致，生成/Qt 缓存聚合 SHA-256 分别保持 `C31594774D52BDEE69571BCB7E9CF9A70AD3C9B5F3B493B6ED1AECEF47A2577D`、`4BA4B39F6D776EE677848FE6FD4E1ED8F43B754B130AAF8828EDA288A02E12F1`。全部 runner 零可见窗口/零残留进程；本批未取得新的人工桌面确认。
   - F5b `_derive_app_user_model_id()` before characterization 已完成（提交 `a90beb8`）：26 项纯状态合同锁定显式环境变量、packaged executable、Python host script、`__main__`、空入口与稳定默认值；三条无参测试共同锁定默认 `os.environ → sys.executable → sys.argv` 来源及短路顺序，其中环境变量与 executable 短路通过 process-control sentinel 证明，默认 argv 来源通过 Python host 回落到脚本路径证明。executable/script 两阶段的 `OSError/TypeError/ValueError` 继续只回退到下一来源，`KeyboardInterrupt/SystemExit` 继续原样传播。Review 先后补齐默认 argv、环境变量和 executable wiring，最终 P0-P3 全零；已发现的超长 executable 退化没有写入通过合同。
   - F5b 机械拆分已完成（代码提交 `2be95663`）：抽出 11 行 `_derive_executable_app_user_model_id()` 与 6 行 `_derive_current_script_app_user_model_id()`，主入口从 35 行降至 29 行，`window/__init__.py` 为 227 行；显式 env → executable → script → default、两段 ordinary-exception 边界、process-control 传播及模块级 `derive → apply` 时序均保持不变。新增结构门禁只定位三个模块直接函数、跳过 nested def/async/lambda，并锁定 `APP_USER_MODEL_ID = derive()` 后立即 `_apply_app_user_model_id(APP_USER_MODEL_ID)`；生产超长函数库存 `39→38`、window `14→13`。626 组基线动态差分的返回值与异常类型完全一致，代码、测试和结构最终 Review 均为 P0/P1/P2/P3 全零。
   - F5b 最终门禁：before 行为 `26 passed`，行为+结构 `29 passed`，联合 smoke `37 passed`；全量 Python `1148 passed / 1 skipped`（124.15 秒），QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML `0`，227 个受跟踪 Python 输入的 3.9 AST、compileall 与 `git diff --check` 全部通过。全部统一 runner 为 `visible_windows=0 / job_active_processes=0` 且清理成功；门禁前后 `app.json` 均为 141 字节、mtime `2026-07-03T15:38:04.7104529Z`、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`，276 个用户生成 QML 缓存与 6498 个 Qt QML 缓存的当前聚合 SHA-256 分别保持 `AC6275061DDD2869F64BAA175A5319A92DA40D0A3617FE3E7393D2ED81BDB9B3`、`1E9CE49F95719A839DFAEF282DFEC2C01D3C554FDCAB23DCC0A70FD80C01D8D5`，两份受保护 audit 日志仍为 142 字节且 SHA-256 均为 `124952A66B9D1157741E56BB46C83C639680A77FBD5BAB8E3E71AA41BC551195`。两类缓存从 F5a 旧快照到本批门禁前已发生跨 checkpoint 变化，本批只以门禁前当前快照为基线，前后逐项完全一致；未将此前变化归因于 F5b，本批也未取得新的人工桌面确认。
   - F5b Review 新发现的独立 AUMID 正确性债务：200 字符 packaged executable stem 的真实输入当前返回 `PrismQML.App`，根因是 `_make_app_user_model_id()` 在 `identity_path is None` 的超长分支仍对单元素 `clean_parts[:-1]` 取空并回退 `App`，会丢失 executable 身份。F5b 未修改该 helper、未把错误输出固化为合同，也不把该问题冒充已修；后续必须以独立红测/正确性提交处理，不与机械长函数拆分混在同一提交。
   - F5c `WindowCore.show()` before characterization 已完成（提交 `977966f`）：40 项现状合同把 profile 与操作写入同一事件流，并用完整正则锁定 `[启动剖析] WindowCore.show <label>: +Nms / total Nms`；覆盖首次创建、无 root、复用前后双 restore、重复 show、lazy 空导航/bottom-only、eager 有页/零页、current 精确发布时间，以及 `RuntimeError/ValueError/KeyboardInterrupt/SystemExit` 在 create 前后 partial root、native show、两次 restore、lazy 首页和 eager 中途失败八类边界。eager page 1 失败继续保留 page 0 的部分状态；文件 475 行且所有函数不超过 30 行。独立 Review 两轮关闭 profile 时序与 eager-zero 假阴性后为 P0/P1/P2/P3 全零。
   - F5c 机械拆分已完成（代码提交 `2d0881dc`）：新增 65 行 `_window_show.py`，把共享 profiler、root create/reuse/show 与初始页面创建拆为 16/20/11 行 helper；`WindowCore.show()` 从 45 行降至 7 行、控制深度 1，`window_core.py` 从 605 行降至 565 行。原 perf-counter 次数与整数毫秒格式、create/reuse 标签、双 restore、无 root 返回、native show、`WindowCore._current_window_instance = self` 直接发布及 lazy/eager 顺序均保持；普通异常与进程控制异常不捕获，partial state 不回滚。结构门禁精确锁定公开签名、去 docstring 后四条顶层 AST 语句的参数/顺序、三个 helper 唯一性和行数/深度；mutation 证明额外 attribute 调用、第二次 current 赋值及重复同名函数都会失败。生产超长函数库存 `38→37`、window `13→12`，两路最终 Review 为 P0/P1/P2/P3 全零。
   - F5c 最终门禁：行为+结构 `44 passed`，WindowBuilder/root/PageManager 等窗口联合 `165 passed`，真实 standalone `7 passed / 10 deselected`，NativeWindow 启动 `14 passed`；全量 Python `1253 passed / 1 skipped`（217.12 秒），QML probe `169 OK / 0 错误 / 12 跳过`，headless CTest `8/8`，changed QML `0`，Python 3.9 AST `238` 个受跟踪输入、compileall、Rust fmt/clippy/test `6/6` 与 `git diff --check` 全部通过。全部统一 runner 为 `visible_windows=0 / job_active_processes=0` 且清理成功；`app.json` 仍为 141 字节、SHA-256 `FDA2606EDBFC6F79BDEE1E65F316CD25F4002518DBDA6FA3258976EF49D885B9`，两份受保护 audit 日志仍为 142 字节且 SHA-256 均为 `124952A66B9D1157741E56BB46C83C639680A77FBD5BAB8E3E71AA41BC551195`。当前用户生成/Qt QML 缓存分别为 280/6498 文件，聚合 SHA-256 为 `86E33CF0FA1A0BC3050909B709D88660367C3CECE9B9A8872C1DA91EEE9D10C8` / `5F28CE990BBDC857D61B6127457CA4D7F4293A057214983AA4C5D281228BA277`；两类最新 mtime 分别为本地 13:25/15:43，均早于 F5c 首个提交 18:11，证明本批未创建或刷新用户缓存。缓存相对 F5b 的跨任务变化不归因于 F5c；本批未取得新的人工桌面确认。
   - F5 Research 同时发现 `system_tray.addMenu()` 写入的 `submenuActions` 全仓无消费者，QML 路径只创建带箭头父项而未连接真实 submenu；这不是可直接固化的机械合同，后续必须先用隐藏 QQmlEngine 真实复现并单独做正确性决策。`_setAppIcon()` 与 P7K 路径编解码正确性耦合，SystemTray submenu、Mica、AUMID 长标识和 `App.__init__` 生命周期均继续后置，不混入机械拆分。F6 处理其余 models/query tools，F7 处理 core/providers/state。每批仍须先补真实合同、再机械拆分，并重复库存、Python 3.9 AST、全量 Python、QML probe、headless CTest、changed scanner、用户配置/缓存隔离与 `git diff --check`；未使用导入与文件头继续后置。
   - F5d before characterization 已完成：初版提交 `5b483469` 以 98 项行为合同锁定 `super(parent)` 必须先于任何字段赋值、裸 `object()` 类型的 `window_type` 原样保存、21 个字段乘四类 ordinary/process-control 异常的 identity/partial state、配置 factory/property 动态解析、current 不污染、五个可变容器的精确类型与逐实例隔离，以及公开 `WindowCore/Window` 签名。Review 发现 QApplication 与 DeferredDelete 清理不足后，以提交 `65b2524` 增加文件级测试边界、把全部 QObject 构造移入 `try/finally`、断言 wrapper 最终失效，并明确不固化 parent 析构后独立 `QQuickWindow` 仍存活的孤儿根窗口债务；最终测试文件最大函数 26 行，两路 Review 为 P0/P1/P2/P3 全零。
   - F5d 生产拆分仍在工作树、尚未提交时，全量门禁首次真实暴露独立 TabWidget 正确性竞态：模型替换会让新 current delegate 每次短暂出现 `x=0`，旧同步 `_followLayout()` 每次都把 `_near.to=0` 下发给仍在运行的动画；固定 20ms 测试因帧相位仅间歇失败，真实 fresh process 为 12 次 1 失败、30 次 3 失败。先以独立提交 `0b273ad2` 将布局信号合并到既有 0ms sync timer，并在读取几何前调用经运行时 metaobject 验证的 `QQuickRow.forceLayout()`；回归新增 invoke 返回时 `_near.to` 不得指向 provisional 0、最终 target 必须等于 delegate x 的确定性守卫。修后旧输入 30/30、逐 5ms 全轨迹 20/20、初始化/滚动/动态增删/真实拖拽压力 32/32、TabWidget 整套 9/9 通过。
   - 上述独立阻断清零后，F5d 机械拆分以代码提交 `a248dd77` 收口：新增 `_window_init.py`，把配置读取前状态与配置成功后的 Splash 默认值拆为 23/7 行 helper；`WindowCore.__init__()` 从 51 行降至 19 行，严格保持 `super → pre-config state → 构造期动态 import/getConfigManager().lazyLoading → splash state`，不转换 `window_type`、不对 lazy 值做 `bool()`、不捕获/回滚任何异常。结构合同精确锁定五条顶层语句、两个 helper 的完整赋值 AST、签名、唯一性、行数与零控制流；生产超长函数库存 `37→36`、window `12→11`，最终专项/结构/库存 `103 passed`、窗口联合 `207 passed`，独立 Review 全零。最终全量 Python `1353 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0` 与 `git diff --check` 全绿，全部 runner 零可见窗口/零残留进程；受保护 `cpp/.audit-p1-20260711003617/` 未编辑、未暂存、未提交。下一批继续 F5 剩余 window 单一调用链，仍不得把 `_setAppIcon()`/P7K、SystemTray submenu、Mica、AUMID 长标识或 parent 孤儿根窗口债务夹入纯机械批次。

6. **P7J Updater 下载 I/O、并发与响应 schema**
   - 状态：已完成。Python 提交 `a8920870`，C++ 提交 `a6cd258`；下一批进入 P7K，不改版本、不打 tag、不发布。
   - Python 下载回调捕获文件写入/关闭 `OSError` 后只记 warning，不保存失败状态。真实只读文件句柄输入已复现：最后一块写入失败后仍发送 `downloadFinished(path)`，`downloadFailed` 为零，磁盘只保留非空的截断文件。
   - C++ `readyRead` 与 `onDownloadFinished()` 完全忽略 `QFile::write()` 返回值，网络无错即发送成功；Python/C++ 都用 URL 文件名覆盖系统临时目录中的固定目标，跨进程同名下载会互相删除或截断。
   - Python 已阻止同一实例重复下载/检查，C++ 没有对应 guard；重复调用会覆盖 `m_checkReply/m_downloadReply/m_downloadFile`，旧 reply 的 finished 回调可能读取或删除新请求状态。
   - Python release JSON 只验证语法：根数组会在 `.get()` 处抛 `AttributeError`，`assets` 含非对象元素也会穿透；UTF-8 使用 `errors="ignore"`，尾部非法字节可被静默丢弃并继续接受为新版本。C++ 解析行为与 Python 不一致。
   - 应使用进程唯一的原子临时文件，任何 write/flush/close/commit 错误都必须中止、清理并只发失败信号；同一实例的并发请求需明确拒绝或取消旧请求，响应根对象、字段类型和 UTF-8 必须严格校验。
   - 预期效果：截断文件绝不报成功、重复调用不串线、失败不残留安装包、Python/C++ 响应与信号合同一致。
   - 难度：8-16 小时；风险：高。
   - 验收：真实只读/写满文件、尾块失败、close/commit 失败、网络失败、空文件、同名跨进程、重复调用、根数组、畸形 assets、非法 UTF-8 与 process-control 矩阵全部零窗口通过。
   - 完成记录：Python release 响应改为严格 UTF-8、根对象和字段类型校验；下载使用进程唯一 `.part` 文件，完整 write/flush/fsync/close 后才以 `os.replace()` 原子发布。C++ 使用进程唯一目标与 `QSaveFile`，禁用 `directWriteFallback`，检查全部 write 与 `commit()`，reply 回调绑定具体对象并拒绝重复 check/download。两端的网络、短写、flush/close/commit、空文件和 schema 失败均只发一次失败信号并清理；C++ 新增真实 loopback `prism_test_updater`。`updater.py` 为 499 行，生产超长函数库存 `21→19`（core `10→8`）。

7. **P7K URL/本地路径编解码与 Python 注入完整性**
   - 状态：已完成。P7K-A 图标路径提交 `57fd1946`，P7K-B SVG provider 提交 `74c095ef`，P7K-C SqlListModel 只读 URI 提交 `68c9e60a`，P7K-D Python 注册注入提交 `47ebdb30`；下一批进入 P8A 下游资源/孤立组件审计。
   - Python `WindowHelper._resolveIconPath()`、`WindowCore._setAppIcon()` 与 C++ `WindowHelper/SystemTrayIcon` 都通过删除 `file:///` 的前 8 个字符获取本地路径；POSIX `file:///home/user/a.svg` 因而变成错误的相对路径 `home/user/a.svg`，百分号编码与 UNC 也未按 URL 合同解析。三份重复逻辑应统一使用 `QUrl.toLocalFile()`/等价共享 helper。
   - `SvgImageProvider` 直接把 image provider id 当文件路径。真实 QML URL 传输证明空格会解码，但 `%23` 与字面 `|` 会以 `%23/%7C` 留在 id 中；含 `#` 等合法保留字符的真实 SVG 文件因此无法打开。Python/C++ provider 和 `WindowIcon.qml` 必须共享明确的一次编解码合同。
   - `SqlListModel` 的列解析已使用 `file:{path}?mode=ro`，但没有按 SQLite URI 规则编码 `#/%/?`、空格、非 ASCII 与 UNC；count 和 Python fallback 页读取仍直接 `sqlite3.connect(path)`，文件被删除时会创建空数据库。应统一只读连接入口并让 URI 构造在 Windows/POSIX/UNC 上可逆，Rust/Python 两后端都必须保证缺失文件只报错、不创建。
   - Python `register_types(engine)` 没有注入 `ConfigManager` 与 `ClipboardHelper`，而 C++ `registerTypes()` 会注入。真实 wrapper 读取 `DpiManager.userDpiScale` 时 component 创建成功且值回退为 0，但 Qt 日志出现 `ReferenceError: ConfigManager is not defined`；当前全组件 probe 因跳过 singleton 无法发现。
   - 应消除 WindowCore/WindowHelper/SystemTray 的重复图标路径与多尺寸 SVG 渲染实现，并明确 `register_types()` 是完整公开装配还是仅内部子集；公开名称与 Python/C++ 行为必须一致。
   - 预期效果：Windows/POSIX/UNC/百分号路径可逆，SVG 保留字符路径可加载，SqlListModel 只读查询对缺失或特殊字符数据库路径绝不误建文件，公开注册入口加载任意已注册组件时不缺 context 对象。
   - 难度：8-16 小时；风险：中高。
   - 验收：隐藏真实 QML Image/WindowIcon/TableWidget/DpiManager 链覆盖空格、`#`、`%`、`?`、非 ASCII、POSIX、Windows、UNC、qrc，以及 Python/C++ 装配后的 warning 零新增；SqlListModel 的列解析/count/页读取分别在 Rust 与 Python 下覆盖同类路径和删除文件输入，断言查询结果一致、异常后磁盘仍无文件且模型状态按 F6 合同完整恢复。
   - P7K-A 完成记录：新增 Python `_icon_path.resolve_icon_path()` 与 C++ 私有 `detail::resolveIconPath()`，Python `WindowHelper/WindowCore/SystemTrayIcon` 和 C++ `WindowHelper/SystemTrayIcon` 统一以 Qt `QUrl.toLocalFile()` 处理 `file:` URL，并把 `qrc:/`、`qrc:///` 归一为 `:/` 资源路径；直接本地路径与既有 qrc 资源语义保持。真实文件名 `图 标#百分%.png` 修前三条 Python 入口均为空图标，路径仍含 `%E5/%20/%23/%25`，红测 `6 failed / 1 passed`；修后 Python 三入口与 C++ 两入口均能加载同一真实 FullyEncoded URL，Windows 盘符、UNC、POSIX 与 qrc 矩阵跟随 Qt 权威结果。
   - P7K-B 完成记录：`WindowIcon` 对完整 `file:/qrc:` URL 保留已有编码，裸本地与 `:/` 路径整体 `encodeURIComponent` 为一个 provider 组件；Python/C++ `SvgImageProvider` 对裸 provider id 只做一次百分号解码，而 `file:/qrc:` 保持编码交给 `QUrl`，避免 `%23` 提前变成 fragment。真实 QML 传输已坐实：空格会解码，`%23` 保留，字面 `%`/`|` 分别成为 `%25/%7C`；真实文件名 `图 标#百分%23.svg` 的 raw path 与 FullyEncoded file URL 均能渲染，C++ 同一保留字符 file URL 也通过。
   - P7K-C 完成记录：新增私有 `_sqlite_connection.sqlite_read_only_uri()`/`open_read_only()`，按 SQLite URI 规则一次编码 Windows 盘符、POSIX 与 UNC 路径；UNC 使用空 authority 的 `file:////server/share` 形式，避免 SQLite 拒绝非空 authority。列解析、count 与 Python fallback 页读取统一复用 `mode=ro` 连接，Rust 继续使用原生路径与 `SQLITE_OPEN_READ_ONLY`。真实文件名含空格、`#`、字面 `%23` 与中文时 Python/Rust 均能完成 count、列解析和分页；删除文件后两端只报只读打开失败、不重建磁盘文件，F6 查询状态、cache 身份、roles 与已缓存行完整恢复。本机 `\\localhost\C$` 真实 UNC 输入也读取到原行。
   - P7K-D 完成记录：公开 Python `register_types(engine)` 与 C++/窗口装配的共享 context 合同补齐 `ConfigManager`、`ClipboardHelper`。真实 wrapper 预置临时 DPI 125 后，修前创建成功但 singleton/直接值均回退 0，clipboard 为空，并记录两条 `ReferenceError`；修后两个真实引擎均注入同一两个进程单例，wrapper 返回 `125 / 125 / ""`，全部 Qt warning/critical 归零，销毁引擎后单例仍有效。`PlatformInfo` 是 C++ 移动端扩展且 Python QML 当前仅防御式读取，不在本批伪造实现。

### P8：图标枚举与孤立 QML 文件

预期效果：资源、Python 枚举、QML 枚举和 qmldir 注册保持单一事实源。

- 难度：2–4 小时
- 风险：中
- 前置依赖：P4；P8A 孤立文件决策必须在 P6C 收尾前完成，P8B 图标与资源注册在 P6、P7 后完成

执行项：

1. P8A 先对以下文件做下游引用审计：
  - `controls/auth/LoginWindowLightShadow.qml`
  - `controls/containers/Layout/Layout.qml`
  - `controls/inputs/_internal/CropToolButton.qml`
  - `controls/inputs/LineEdit/TextInputCore.qml`
  - `controls/inputs/TextEdit/PlainTextEdit.qml`
  - `DpiManager.qml`：仓内及本机已知下游均无消费者，重复维护 spacing/font/size token，并在 Qt 已使用设备无关坐标时再次乘 `devicePixelRatio`；应评审删除或收敛成只暴露真实且不重复缩放的 DPI 状态。
2. `LoginWindowLightShadow.qml` 当前仓库零消费者、从未注册到根/auth qmldir，但仍被 Python package-data、移动端 qrc glob 与 C++ install 目录分发；历史唯一消费者已删除。其 22 项 QML011 之外仍有大量未扫描的 Canvas/动画/阴影常量与 QML008/QML009/QML010，且 `#000000cc`、`#ffffff26` 按 Qt `#AARRGGBB` 语义并非注释预期的透明黑/白。
3. 推荐路线是审计 Gitora、quicksketch、Kaleidos 等下游直接 URL 引用后，请求用户批准删除该孤儿文件；删除预计 2–4 小时，风险低到中，probe 注册数不变，QML011 可减少 22 项。删除属于敏感操作，未获批准不得执行。
4. 若确认保留公共价值，则先决定正确颜色与固定视觉预设政策，再完整处理 token、成员顺序、API、性能、可访问性、双 qmldir 注册和运行时回归；预计 8–16 小时、风险高，禁止只机械迁移 22 项。
5. P8B 通过修复后的生成器补齐 13 个未暴露 SVG：`BulletedList`、`FitPage`、`Hide`、`Message`、`NavigateForward`、`OpenFile`、`OpenFolderHorizontal`、`PowerButton`、`StickyNotes`、`Update`、`View`、`Volume`、`Zoom`。
6. 确保 Python/QML 两套枚举数量和值完全一致；其他有公共价值的孤立文件补 qmldir 与测试，确认废弃的文件在用户批准后删除。

2026-07-13 追加只读证据：本机 `D:\PrismQML` 下的 AeroMount、ConfigPilot、Gitora、Kaleidos、Kaleidos-k8s-production-rehearsal 与 quicksketch 已排除 `.git/.venv/build/dist/node_modules` 做精确路径、文件名和 QML 类型实例化检索，未发现上述五个候选文件的 PrismQML 直接消费者；唯一 `PlainTextEdit` 命中来自 Kaleidos 归档文档中的 qfluentwidgets/QTextEdit 语境。该证据只证明本机已知下游零消费者，删除仍必须取得用户明确批准。`extract_icons.py --check` 当前真实退出 1；SVG 为 2497、Python Icon 为 2484，差集仍是前述 13 项且无反向多余项。Python `IconProvider` 与 C++ 同名类型目前也不是镜像合同：Python `getPath()` 只返回自定义路径并另有 `get/getAll/getAllNames/count`，C++ `getPath()` 返回内置 SVG 路径且只另有 `isValid`；应在 P8B 决定删除未使用的对称门面或统一公开 API，不能继续以“同名/1:1”描述不同行为。

2026-07-16 P8A 刷新只读审计：再次扫描 AeroMount、configpilot、Gitora、Kaleidos、quicksketch 与 Kaleidos-worktrees，排除 `.git/.venv/venv/site-packages/build/dist/node_modules/site` 后，六个候选均无真实下游源码消费者；Kaleidos 唯一原始命中仍是归档文档里的 qfluentwidgets/QTextEdit 语境。两个独立 `site-packages`/RECORD 命中只证明旧 wheel 确实分发这些文件，不是调用方。仓内 `LoginWindowLightShadow`、`Layout.qml`、`TextInputCore`、`PlainTextEdit` 未注册且零生产实例化，`CropToolButton` 仅 `_internal/qmldir` 注册且零消费者；五者共 884 行，当前扫描分别为 76/30/32/0/1 项、合计 139 项违规。`DpiManager` 是根 singleton，当前生产零消费者、仅两份测试 wrapper 读取，共 68 行/17 项 QML008；推荐保留 `baseDpi/screenDpi/scale/devicePixelRatio/userDpiScale` 等真实状态，删除重复 spacing/font/size 与再次缩放的 `dp/sp/effectiveScale` API。P8A 建议方案为“删除五个孤儿 + 收窄 DpiManager”，可同时清除 156 项存量；文件删除与公开 API 收窄均等待用户明确授权，当前未修改生产 QML/qmldir。

2026-07-16 P8A 删除批次完成：用户明确批准删除五个零消费者孤儿文件；提交 `154cd4e4` 删除 `LoginWindowLightShadow.qml`、`Layout.qml`、`CropToolButton.qml`、`TextInputCore.qml` 与 `PlainTextEdit.qml` 共 884 行，同步移除 `_internal/qmldir` 的 `CropToolButton` 注册，并清理两处仍把 `TextInputCore` 描述为现行继承链的陈旧注释。新增静态回归锁定五文件及五个类型名不得复活、替代链 `ImageCropper`、`LineEditCore`、`TextEditCore` 与四种公开 Layout 文件必须存在；`DpiManager.qml` 及其公开 API 未获同等授权，本批保持不变。当前扫描器复算父提交五文件贡献为 139 项（QML008 75、QML009 21、QML010 21、QML011 22），删除后全库为 2,621 项（QML008 1,538、QML009 1,014、QML010 69、QML011 0），changed 扫描零新增。聚焦输入/裁剪/布局与删除护栏 `23 passed`；全量 Python `2225 passed / 1 skipped`、QML probe/coverage `169 OK / 0 错误 / 12 跳过（181）`、headless CTest `9/9`、Windows native CTest `2/2`、Python 3.9 AST 280、compileall、mkdocs strict 与 `git diff --check` 全绿，全部统一 runner 为零可见窗口、零残留进程，最终 Review P0–P3 全零。P8A 的孤儿删除已完成；后续另批评审 `DpiManager` 收窄，并继续 P8B 图标/资源注册同步。

2026-07-16 P8B-A 生成注册表同步完成：真实 `scripts/extract_icons.py --check` 修前退出 1，同时报告 `icons.py` 与 `Icons.qml` 均陈旧；仓内 2,497 个 SVG 对 Python/QML 两表各 2,484 项，精确缺少 `BulletedList`、`FitPage`、`Hide`、`Message`、`NavigateForward`、`OpenFile`、`OpenFolderHorizontal`、`PowerButton`、`StickyNotes`、`Update`、`View`、`Volume`、`Zoom`，无反向多余项。before 提交 `11882986` 用真实 Python/QML 运行锁定 `str/path/to_qicon/get_all/get_all_enum_names` 与 `Enums.icon.path/iconList` 公开行为；实现提交 `39efe2e8` 把原生成枚举内的路径、文件 I/O、主题判断和 SVG/QIcon 渲染下沉到 69 行 `_icon_enum_runtime.py`，生成文件只保留枚举数据、薄 mixin 继承及无副作用查询方法。生成器现从同一 SVG 集合确定性地产出 Python/QML 双表，补齐 13 项并把 QML singleton 的函数与完成回调移到属性之后；旧 2,484 个值零删除、零改值。最终 SVG/Python/QML 均为 `2,497` 且三组对称差为空，`--check` 退出 0；聚焦图标/生成器 `73 passed`，最终 Review 修正一处测试 helper 36 行后降为 14 行，复测 `21 passed`。全量 Python `2229 passed / 1 skipped`、QML probe/coverage `169 OK / 0 错误 / 12 跳过（181）`、headless CTest `9/9`、Windows native CTest `2/2`、全库扫描 2,621、changed 0、Python 3.9 AST 282、compileall、mkdocs strict 与 `git diff --check` 全绿，全部 runner 为零可见窗口、零残留进程，最终 Review P0–P3 全零。P8B-B 仍需单独统一或删除 Python/C++ `IconProvider` 的不对称公开门面，不夹入本生成器批次。

2026-07-16 P8B-B provider 门面统一完成：六个本机下游源码根精确检索零消费者，GitHub 公开搜索仅命中无关项目；仓内 QML 也不使用 context `Icon`。修前 Python 窗口默认注入 `IconProvider`，而 C++ 明确因可能遮蔽 QML `Icon` 类型而默认不注入；Python `getPath()` 只返回自定义路径并额外暴露 `get/getAll/getAllNames/count/isCustomIcon/register_custom_icon(s)`，C++ 则只提供内置 SVG 的 `getPath/isValid`。before 提交 `4bc9fd0` 用真实 Python/QML 锁定旧自定义路径、枚举查询与显式注册表面；实现提交 `fa4a20d6` 保留 `IconProvider/get_icon_provider/register_icon_provider` 三个显式入口，把 Python/C++ 统一为仅 `getPath(name)`、`isValid(name)` 的最小合同，并从 Python 默认窗口装配删除 `Icon` 注入，不保留 deprecated 别名。真实双引擎显式注册共享同一进程单例，Python `Add` 路径存在、缺失名为 false；MSVC 正确环境重建后 C++ 同一真实输入通过。首次聚焦失败 `12 failed / 55 passed` 已定位为旧测试仍传四元依赖和三参数 provider helper，完整迁移后 Python `64 passed`、C++ `prism_test_store 1/1`，旧表面残留检索为 0。最终全量 Python `2229 passed / 1 skipped`、QML probe/coverage `169 OK / 0 错误 / 12 跳过（181）`、headless CTest `9/9`、Windows native CTest `2/2`、生成器 check 0、全库扫描 2,621、changed 0、Python 3.9 AST 283、compileall、mkdocs strict 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留进程，最终 Review P0–P3 全零。P8B 至此完成；P8 仅剩未获授权的 `DpiManager` 公开 API 收窄决策。

2026-07-16 P8 DpiManager 收窄完成：用户明确批准删除重复公开 API；再次精确扫描 AeroMount、configpilot、Gitora、Kaleidos、quicksketch 与 Kaleidos-worktrees，排除依赖、构建和站点目录后仍为零真实源码消费者。提交 `79932827` 保留 `baseDpi/screenDpi/scale/devicePixelRatio/userDpiScale` 五个只读状态，删除会对 Qt 设备无关坐标再次缩放的 `effectiveScale/dp/sp`，以及 17 个重复 spacing/font/component-size 预设，不保留兼容别名。新增真实 QML 元对象回归锁定公开属性精确集合、删除方法不可调用和状态值有效；旧 Prism Design wrapper 改读保留的 `scale`。修前运行时为 23 个自定义属性加 `dp/sp`，修后仅五个状态；目标文件 QML 违规 `17→0`，全库库存 `2,621→2,604` 且 changed 为 0。最终定向 `3 passed`、全量 Python `2230 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、图标生成器 2,497、Python 3.9 AST 283、compileall、mkdocs strict 与 `git diff --check` 全绿，全部 runner 零可见窗口、零残留进程。P8 至此完成。

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

门禁补强前置：当前 probe 的 `169 OK / 0 错误 / 12 跳过` 中有 5 个 singleton 被无条件跳过，不能作为 singleton 无绑定错误的证据。P9 前必须用 wrapper 强制实例化并读取 `Enums`、`Translator`、`DpiManager`、`NotificationManager` 与 `PopupUtils`，同时捕获 Qt warning；完成后基线应只保留 7 个确需父组件注入的 required-property skip。上述改造必须先在改前 worktree 与当前分支上分别运行，区分存量 singleton 错误与新增回归。

2026-07-14 P7H 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：P7H 聚焦 `41 passed`；Python 全量 `843 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；C++ 经仓库标准 `cpp\build.bat` 输出 `PRISM_BUILD_DONE`，NativeWindow CTest `1/1`、headless CTest `8/8`、Windows native CTest `2/2`；Rust `fmt --check`、`clippy --all-targets -D warnings` 与 `cargo test 6/6`、`git diff --check` 通过。全部 runner 均为 `visible_windows=0 / job_active_processes=0`，最终 native 夹具退出后无残留测试进程，用户确认未出现错误弹窗，真实用户配置快照完全未变。下一阶段为 P7I 剩余规范库存，P7I-P7K 仍待处理；Qt 6.9 仅完成静态兼容审查，本机实际运行版本为 Qt 6.11.1，最低版本运行时仍待独立 lane；P9 前仍须把 5 个 singleton 从无条件跳过改为真实 wrapper 实例化验证。

2026-07-14 P7I-A/P7I-B 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：P7I-A/P7I-B 真实 traceback 聚焦 `20 passed`，P7I-B 关闭握手隐藏脚本 `PASS`；Python 全量 `849 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；Python 3.9 AST、compileall 与 `git diff --check` 通过。全部 runner 均为 `visible_windows=0 / job_active_processes=0`，用户确认测试期间没有出现弹窗，真实用户配置和受保护 audit 指纹均未变化。P7/P7I 仍进行中，下一批为 P7I-C `SqlListModel` 回调边界；P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-C 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：真实 Rust 与强制 Python fallback 的 SqlListModel 回调边界聚焦均为 `11 passed`，C++ SqlModel CTest `1/1`；Python 全量 `858 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；全仓 178 个 Python 文件的 3.9 AST、compileall 与 `git diff --check` 通过。全部 runner 均为 `visible_windows=0 / job_active_processes=0`，真实用户配置与受保护 audit 指纹未变化。P7/P7I 仍进行中，下一批为 P7I-D 窗口启动降级边界；P7I-F 长函数、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-D1/D2 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：logger/真实 App 启动、真实删除窗口恢复边界与进程控制聚焦均通过；Python 全量 `866 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；全仓 178 个 Python 文件的 3.9 AST、compileall 与 `git diff --check` 通过。全部 runner 均为 `visible_windows=0 / job_active_processes=0`，真实用户配置与受保护 audit 指纹未变化。P7/P7I/P7I-D 仍进行中，下一批为 D3 `_window_builder`；D4/D5、P7I-F、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-D3 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：真实文件占用缓存目录的 `FileExistsError / WinError 183` 与真实 component 创建后剖析 `RuntimeError` 两条边界均保留 traceback，并分别执行 inline fallback 或保留已创建对象；进程控制 `2 passed`、standalone 退出码 0、headless 入口 `19 passed`。Python 全量 `869 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；当前工作树 181 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 通过。全部 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，真实用户配置与受保护 audit 指纹未变化。P7/P7I/P7I-D 仍进行中，下一批为 D4 `_splash_builder`；D5、P7I-F、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-D4 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：真实 Splash 文件缓存 `FileExistsError / WinError 183`、文件 component 后剖析 `RuntimeError` 与已销毁窗口挂载 `RuntimeError` 三条边界均保留 traceback，并分别执行 inline fallback、保留文件 component 或非致命放弃 Splash；进程控制 `4 passed`、standalone 退出码 0、headless 入口 `20 passed`。Python 全量 `874 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；当前工作树 183 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 通过。全部 Python/QML runner 均为 `visible_windows=0 / job_active_processes=0`，真实用户配置、用户 QML 缓存 246 文件快照与受保护 audit 指纹均未变化。P7/P7I/P7I-D 仍进行中，下一批为 D5 `_page_manager`；P7I-F、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-D5 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：页面工厂、删除后尺寸信号与已销毁窗口的 navigate/loading start/loading finish 五条真实失败边界均保留 traceback，10 条进程控制传播、standalone 与 headless 入口 `21 passed`。Python 全量 `885 passed / 1 skipped`；changed QML 扫描 `0 violation(s)`；QML probe `169 OK / 0 错误 / 12 跳过`；headless CTest `8/8`；当前工作树 185 个 Python 输入的 3.9 AST、compileall 与 `git diff --check` 通过。全部 runner 均为 `visible_windows=0 / job_active_processes=0`，用户确认未出现错误弹窗，真实用户配置与受保护 audit 指纹未变化；并行 Kaleidos 任务造成的两份外部缓存已单独归因，D5 专项复验前后 248 文件聚合指纹一致。P7/P7I 仍进行中，P7I-D 已完成，下一批为 P7I-F 长函数拆分；P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-F/F1a 完成后的当前验证快照（仍不代表 F1、P7、P9 或全库完成）：模块级 `string.Template` 与 6 个不超过 30 行的 helper 已抽离纯 QML 组合，`_create_window()` 为 154 行、文件 498 行，生产超长函数库存仍为 50。固定路径 before/after 生成源码均为 1826 字节、SHA-256 `AEFD6F0F12391D2A61F97DE086FA02E51FA882B1CA730CD487557566F9F5703C` 且逐字节相等；最终 Python `891 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、headless 入口 `22 passed`、Python 3.9 AST 186、compileall 与 `git diff --check` 全部通过。全部 runner 零可见窗口/零残留进程，用户缓存/配置/audit 指纹未变化；本批未复用较早用户桌面确认。下一批为 F1b Engine/context 注入拆分；F1c、F2-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-F/F1b 完成后的当前验证快照（仍不代表 F1、P7、P9 或全库完成）：Engine、ContextProperty 与 Icon/SVG provider 装配已迁入 93 行内部模块，6 个 helper 为 7/8/14/22/5/14 行；`_create_window()` 为 120 行、`_window_builder.py` 为 463 行，生产超长函数库存仍为 50。聚焦 `27 passed`、真实 composition/fallback 退出 0、headless 入口 `22 passed`、Python `909 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 187、compileall 与 `git diff --check` 全部通过。全部 runner 零可见窗口/零残留进程，用户缓存/配置/audit 指纹未变化；本批 F1b 未复用用户此前对 F1a 的桌面确认。下一批为 F1c root/pending/Splash 收尾拆分；F2-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-F/F1 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：F1a/F1b/F1c 已依次抽离纯 QML 组合、Engine/context/provider 装配，以及 root/pending/Splash 收尾；`_create_window()` 从前置清理后的 223 行降至 20 行，`_window_builder.py` 为 366 行，所有新增/修改 helper 均不超过 30 行，生产超长函数库存为 49。聚焦 `55 passed`、真实 invalid-QML/composition/fallback 退出 0、headless 入口 `22 passed`、Python `937 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 191、compileall 与 `git diff --check` 全部通过。全部 runner 零可见窗口/零残留进程，用户缓存/配置/audit 指纹未变化；F1c 未复用用户此前对 F1a 的桌面确认。下一批为 F2 `create_splash()`；F3-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-14 P7I-F/F2 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：模块级 `string.Template` 与 7 个不超过 21 行的 helper 已抽离 Splash profile、值解析、模板渲染、动态路径准备、verbose 快照、file→inline component 选择及挂载；`create_splash()` 从 207 行降至 30 行，`_splash_builder.py` 为 327 行，生产超长函数库存 `49→48`（`window=18 / core=17 / models=8 / providers=4 / state=1`）。固定特殊输入改前/改后均为 3455 字节、126 个换行、SHA-256 `2FB0C01D9B0E69109BCAADD7F12F55D03F3D7B3964190D7EF53209E318BE3661` 且逐字节相等；聚焦 `94 passed`、真实 fallback/default/timing/composition 均退出 0、headless 入口 `22 passed`、最终 Python `952 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 191、compileall 与 `git diff --check` 全部通过。测试已在 Qt import 前禁用磁盘 QML cache 并显式销毁 Splash/component/window；修正后 Qt cache 5982 文件聚合指纹、用户 QML cache 248 文件、`app.json` 与 audit 指纹均前后不变，runner 零可见窗口/零残留进程。Review 前已产生的 9 个 `.qmlc` 已精确归因但因未获删除授权而保留；三路最终 Review 为 P0/P1/P2/P3 全零，本批未获得新的人工桌面确认。下一批为 F3 `_fetch_page()`；F4-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-15 P7I-F/F3b 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：`_fetch_page()` 已按 route → plan → dispatch → install → format → return 从 130 行机械拆至 15 行，9 个相关方法均不超过 24 行且深度不超过 2；生产超长函数库存 `44→43`、models `4→3`。SQL 聚焦 `104 passed`，固定 F3a before 的 200k/30k Python/Rust ABBA/BAAB 正式 12/12 轮通过，最差 median `1.06572×`、p95 `1.10229×`；首次 p95 `1.21401×` 阻断已保留并完成位置噪声诊断。隔离全量 Python `1081 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 221、compileall 与 `git diff --check` 全部通过；全部 runner 零可见窗口/零残留进程，用户配置、两份受保护 audit 日志及两份真实数据库指纹未变化。代码提交 `d2f99369`，下一批严格为 F4 页面同步/异步加载链；F5-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-15 P7I-F/F4 完成后的当前验证快照（仍不代表 P7、P9 或全库完成）：同步/异步页面加载链已按 profile/target/source/attach/finalize/batch/schedule 机械拆分，`_create_page()` `93→15` 行、`_start_async_page_load()` `112→29` 行，67 行嵌套 ready callback 删除；`_page_manager.py` 336 行且全部函数不超过 29 行、深度不超过 2，生产超长函数库存 `43→40`、window `18→15`。before characterization 提交 `32056b02`，代码提交 `71854655`；最终页面聚焦 `36 passed`、真实 standalone 退出 0，全量 Python `1113 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 224、compileall 与 `git diff --check` 全部通过。全部 runner 零可见窗口/零残留进程，`app.json`、两类用户缓存及两份 audit 日志指纹前后完全一致；本批未取得新的人工桌面确认。下一批严格为 F5 剩余 window 单一调用链；F6-F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁仍待执行。

2026-07-15 P7I-F/F5a 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：`WindowCore.addPage()` 的 class/factory/instance/None 来源、metadata、top/bottom 局部索引与普通/process-control 异常已由 8 项 before characterization 锁定；15 行 `_make_navigation_item()` 抽离纯构造，`addPage()` `60→28` 行，`window_core.py` 605 行，生产超长函数库存 `40→39`、window `15→14`。before 提交 `1b5e072`、代码提交 `093b7dec`；聚焦 `10 passed`、联合 Python `83 passed`、两个真实 standalone 退出 0，最终隔离全量 Python `1123 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 226、compileall 与 `git diff --check` 全部通过。首次全量缓存差异已精确归因于同机外部 Kaleidos-android 的两份 `.qmlc`；独占同一全量入口复验后 `app.json`、两类缓存与两份 audit 指纹完全不变，全部 runner 零可见窗口/零残留。本批未取得新的人工桌面确认；下一批继续 F5b 单一 window 调用链，F5/F6/F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁均未完成。

2026-07-15 P7I-F/F5b 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：AUMID 派生的 env/executable/script/default 优先级、三层无参来源、ordinary fallback 与 process-control 传播已由 26 项 before characterization 锁定；11 行 executable helper 与 6 行 current-script helper 抽离后，`_derive_app_user_model_id()` `35→29` 行，`window/__init__.py` 227 行，生产超长函数库存 `39→38`、window `14→13`。before 提交 `a90beb8`、代码提交 `2be95663`；行为+结构 `29 passed`、联合 smoke `37 passed`、626 组基线动态差分完全一致，最终全量 Python `1148 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 227、compileall 与 `git diff --check` 全部通过。门禁前后 `app.json`、276 个用户生成 QML 缓存、6498 个 Qt QML 缓存及两份 audit 指纹逐项完全一致，全部 runner 零可见窗口/零残留；本批未取得新的人工桌面确认。超长 packaged executable stem 退化为 `PrismQML.App` 与 SystemTray submenu 断链均仅记录为待独立真实修复的正确性债务；下一批 F5c 优先进入 `WindowCore.show()` 单一编排链，F5/F6/F7、P7J/P7K、Qt 6.9 最低版本运行时 lane 与 P9 singleton wrapper 门禁均未完成。

2026-07-15 P7I-F/F5c 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：40 项 before characterization 锁定 `WindowCore.show()` 的完整 profile/操作时序、新建/复用、双 restore、无 root、重复 show、current 发布、lazy/eager 与八类普通/process-control 异常 partial state；`_window_show.py` 三个 helper 为 16/20/11 行，`show()` `45→7` 行、深度 1，`window_core.py` 565 行，生产超长函数库存 `38→37`、window `13→12`。before 提交 `977966f`、代码提交 `2d0881dc`；最终行为+结构 `44 passed`、窗口联合 `165 passed`、真实 standalone `7 passed / 10 deselected`、NativeWindow 启动 `14 passed`，全量 Python `1253 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 238、compileall、Rust fmt/clippy/test `6/6` 与 `git diff --check` 全部通过。全部 runner 零可见窗口/零残留；配置与两份 audit 指纹保持既有基线，两类用户缓存最新 mtime 均早于本批首个提交，确认 F5c 未写用户缓存；本批未取得新的人工桌面确认。下一批严格为 F5d `WindowCore.__init__()` 状态初始化链；`_setAppIcon()`、SystemTray、Mica、AUMID 正确性与 `App.__init__` 继续按既有边界后置。

2026-07-15 P7I-F/F5d 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：`WindowCore.__init__()` 已按 pre-config state / config lookup / Splash state 从 51 行机械拆至 19 行，两个 helper 为 23/7 行；98 项 before 行为合同与后续 QObject 清理补强锁定 super/字段/config/splash 顺序、21 字段异常 partial state、raw window_type/lazy 值、current 不污染和逐实例容器，结构合同锁定五条顶层 AST 语句。真实提交顺序为 before `5b483469` → 隔离 `65b2524` → 全量门禁发现并独立修复 TabWidget delegate 替换瞬态 `x=0` 反向重定向 `0b273ad2` → F5d 代码 `a248dd77`；生产超长函数库存 `37→36`、window `12→11`。TabWidget 修后确定性 target/逐帧/交互压力均通过；最终专项/结构/库存 `103 passed`、窗口联合 `207 passed`、全量 Python `1353 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8` 与 `git diff --check` 全绿；全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。下一批继续 F5 剩余 window 单一调用链，正确性债务继续独立处理。

2026-07-15 P7I-F/F5e 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：`AcrylicHelper.grabAndBlur()` 的参数 guard、屏幕 fallback、跨屏坐标换算、截图/模糊/发布时序、普通异常边界、process-control 传播及异常 partial state 已由 before characterization 锁定；屏幕解析、区域截图与结果发布分别抽为 11/12/9 行 helper，`grabAndBlur()` `68→30` 行，`mica_window.py` 精确 500 行，生产超长函数库存 `36→35`、window `11→10`。before 提交 `2521d690`，代码提交 `ac562a72`；110 组改前/改后动态差分 `0 mismatch`，重复 helper、额外参数与 decorator 三类内存变异均被结构门禁拦截。最终聚焦 `169 passed`、全量 Python `1516 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 与 `git diff --check` 全部通过；两路独立 Review 无 P0–P3，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。下一批继续 F5 剩余 window 单一调用链，Mica/DWM 等正确性债务继续独立处理。

2026-07-15 P7I-F/F5f 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：`_gaussian_blur_image()` 的空图/非正半径同对象返回、ARGB32 转换、11→12 半径缩放边界、奇数与 1px 尺寸、两次缩放参数/顺序，以及普通/process-control 异常 identity 已由 before characterization 锁定；两阶段缩放抽为 21 行 `_scale_acrylic_image()`，主函数 `37→11` 行，`mica_window.py` `500→497` 行，生产超长函数库存 `35→34`、window `10→9`。before 提交 `8f20dec`，代码提交 `a0dc885e`；15 条 fake 流水线、40 组异常边界与 271 组真实 QImage 多格式/尺寸/半径逐字节改前改后全等，调用时局部 `Qt` 导入次数、import hook 失败与模块全局 monkeypatch 语义也保持一致；async/条件同名定义、lambda/`del`/except/global 重绑定六类变异均被结构门禁拦截。首次全量门禁真实采到 Rating hover 在固定 150ms 后仍为 `1.150382`，独立旧测试 5/5 通过，确认是 full-suite 负载下的固定等待抖动；独立提交 `900cad2` 改为目标值连续稳定 30ms、500ms 超时并报告最终值，瞬时 crossing 变异被拒绝，目标测试 10/10。最终聚焦 `222 passed`、全量 Python `1572 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 与 `git diff --check` 全部通过；三路独立 Review 无 P0–P3，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。剩余 9 个 window 超长函数均与 App 生命周期、Mica/DWM、SystemTray submenu、图标路径/P7K 等正确性债务耦合，或仅由超长 docstring 构成；F5 仍为进行中，后续不得用压缩注释或无合同机械拆分冒充完成。

2026-07-15 P7I-F/F6a 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：真实 Rust 路径删除已查询数据库后调用 `SqlListModel.refresh()`，修前同一 `RuntimeError: unable to open database file` 会保留 `count=2`，却把 `getRow(0)` 破坏为 `{}`、清空 roles；修后先捕获查询状态、在独立 `PageCache` 上准备新结果，任意普通/process-control 失败均恢复顶层 list/dict 内容与原 cache，并在 `modelReset` 发出前完成恢复，异常对象身份不变且不发送 `queryChanged/countChanged`。新增 20 项回归覆盖 count/resolve/fetch 三阶段、`ValueError/OSError/RuntimeError/KeyboardInterrupt/SystemExit`、router/formatter 原地污染、reset 配对与信号当刻状态、LRU 内容/顺序/身份，以及成功后的 count、roles 和公开 `data()`；强制 Python fallback 为 `19 passed / 1 skipped`，明确不夹带 P7K 的缺失文件误建债务。代码提交 `6d60680f`；聚焦 `20 passed`、SQL 七文件联合 `124 passed`、全量 Python `1592 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 与 `git diff --check` 全部通过；两路独立 Review P0/P1/P2/P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。生产超长函数库存保持 `34`（`window=9 / core=17 / models=3 / providers=4 / state=1`）；下一批为 F6b `_sql_query_tools.normalize_one()`，目标 models `3→2`。

2026-07-16 P7I-F/F6b 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：30 项 before characterization 锁定 `normalize_one()` 的 None/list/tuple 快路、dict 参数顺序与重复、缺失和 Unicode 参数、单双引号、行/块注释、未闭合输入、普通及 process-control 异常身份、输入不变与浅复制/值身份，并以真实 SQLite 执行验证结果。命名参数扫描机械拆为 8 个顶层 helper，`normalize_one()` `74→12` 行，所有新增 helper 不超过 29 行，`_sql_query_tools.py` 637 行；生产超长函数库存 `34→33`，models `3→2`。before 提交 `173c0f99`、代码提交 `3db0c3b8`；固定 before 上 50,000 组 valid/invalid 随机差分为 0，named 1k/10k/30k/100k 的 median 为 `0.936/0.912/0.945/0.945×`、p95 均不超过 `0.941×`，混合引号/注释输入 median/p95 为 `0.647/0.653×`。最终 SQL 联合 `157 passed`、全量 Python `1625 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 7、compileall 与 `git diff --check` 全部通过；结构门禁已用 async 同名、模块/局部赋值、lambda 与 `strip_strings_and_comments` 多级别名变异复核，三路独立 Review 最终 P0/P1/P2/P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。SQLite 方括号/反引号标识符内冒号误替换以及 dict 下 `@/$` 不归一化均保持为已知正确性债务，未固化为正确合同；下一批独立修复该 SQL 正确性边界，并继续严格排除 P7K 的缺失文件误建债务。

2026-07-16 P7I-F/F6c SQLite 命名参数正确性完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：真实 SQLite 3.49.1 输入先复现方括号/反引号标识符内冒号被误替换、dict 下 `@/$` 不归一化、keyset 把引用标识符误报为残留参数，以及 token-start BOM、`?NNN`、数值与 Tcl suffix 边界漂移；修后新增 215 行私有共享词法模块，统一单双引号、反引号、方括号、行/块注释和 `:/@/$` 参数 span，并按 SQLite tokenizer 的前向 token-state 区分独立 `$x` 与 `a$b`、`1.$x`、BOM 嵌入标识符等上下文。公共调用链整体保持线性扫描；普通 ASCII `:name` 使用同一共享正则快路，`_normalize_dict_params()` 精确 30 行、深度不超过 2，`strip_strings_and_comments()` 的长函数库存同步清零；`_sql_query_tools.py` `637→614` 行，生产超长函数库存 `33→32`、models `2→1`。代码提交 `72ac50f3`；三前缀 531,465 组命名 token 穷举、150,000 组 BOM/token-context、50,000 组合法多参数差分均为 0 mismatch，Rust、Python fallback 与 fan-out 真实模型链通过。相对 F6b 的 1k/10k/30k/100k 正式双向 ABBA 中，colon median 为 `1.0212/1.0228/1.0247/1.0588×`、p95 最大 `1.1672×`，protected median 为 `0.9811/0.9140/0.9203/0.9095×`、p95 最大 `1.0677×`，最坏输入保持线性。最终聚焦 `236 passed`、SQL 联合 `360 passed`、全量 Python `1828 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 10、compileall 与 `git diff --check` 全部通过；三路独立 Review 最终 P0/P1/P2/P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。当前合同只承诺 `:/@/$`；SQLite `#name` 前缀另记为后续债务，P7K 的只读 URI、特殊路径与缺失文件误建仍严格排除。下一批继续 F6 剩余 models/query tools 库存。

2026-07-16 P7I-F/F6d 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：97 项 before characterization 锁定 `SqlListModel.__init__()` 的公开签名、QObject parent、`str/Path/DbRouter` 来源、数据库/Rust 零访问、page/LRU 转换与钳制、18 个字段赋值顺序、逐实例可变状态，以及 `ValueError/OSError/RuntimeError/KeyboardInterrupt/SystemExit` 在容量转换、14 个 query-state 字段与 `PageCache` 构造边界的异常身份和精确 partial state。实现只把连续 14 个 query-state 赋值原序抽到 21 行 `_initialize_empty_query_state()`；source 分支、两次 `str()`、page/LRU 转换仍原位，`__init__()` `44→22` 行，`sql_list_model.py` `670→671` 行，500 行软债继续保留且未粉饰为完成。结构门禁精确锁定两函数签名、完整 AST、helper runtime 绑定与 14 字段顺序，五类重排/改写/重绑定/容量绕过/库存回退变异均被拒绝；models/query tools 超长函数库存 `1→0`，生产总库存 `32→31`（`core=17 / providers=4 / state=1 / window=9 / models=0`），F6 长函数范围完成。before 提交 `bb71edff`、代码提交 `0c7b2722`、库存门禁提交 `0f13bbe7`；最终聚焦 `104 passed`、SQL 联合 `459 passed`、全量 Python `1927 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST、compileall 与 `git diff --check` 全绿，代码/合同/变异 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留。Build All [29449020685](https://github.com/aki-riko/PrismQML/actions/runs/29449020685) 七个作业全绿；P7K 路径/缺失文件误建、SQLite `#name` 与其他正确性债务未混入本批，下一批进入 F7 core/providers/state。

2026-07-16 P7I-F/F7a 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：复用 P7C 已有非 Windows、无 QApplication、成功幂等、构造/安装普通异常、`KeyboardInterrupt/SystemExit`、失败不缓存和可重试合同，并新增“构造 → 原生注册 → 全局发布 → 成功日志”的对象身份与时序 before characterization。实现只把构造及原生注册抽到 15 行 `_try_install_dwm_sync_filter()`，公开 `installDwmSyncFilter()` `32→25` 行；Review 先用同一可注入输入真实复现 `candidate=None` 被 Optional sentinel 误判为失败，随后改用 `(installed, candidate)` 保持旧实现的成功返回、全局状态与日志语义。旧/新入口 14 组状态、普通异常、process-control 和 logger 再抛动态差分为 `0 mismatch`；结构门禁锁定公开零参数签名、唯一 helper、唯一直接委托和两函数均不超过 30 行。生产超长函数库存 `31→30`（`core=16 / providers=4 / state=1 / window=9 / models=0`）。before 提交 `e7d42fe`，代码提交 `901afc76`；最终聚焦 `23 passed`、相关联合 `86 passed`、全量 Python `1930 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 249、compileall 与 `git diff --check` 全绿，两路独立 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。下一批继续 F7 core/providers/state，先补合同再做机械拆分；Updater、图标路径、注册装配及生成器债务继续严格留在 P7J/P7K/P8B。

F7a 补充 CI：Build All [29452118137](https://github.com/aki-riko/PrismQML/actions/runs/29452118137) 的 QML conventions、Windows 零交互门禁、三平台桌面、Android 与 iOS 共七项全绿；Deploy Docs [29452118200](https://github.com/aki-riko/PrismQML/actions/runs/29452118200) 成功。

2026-07-16 P7I-F/F7b 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：先以真实 QML 锁定 `LineEdit → TextEdit → MouseArea` 的精确焦点身份、正常 `editingFinished` 与同一鼠标事件继续投递，再用分支矩阵覆盖非鼠标、无 application、非输入焦点、primary `globalPosition().toPoint()`、旧 `globalPos()` fallback、两阶段 `AttributeError/RuntimeError`、`TypeError/KeyboardInterrupt/SystemExit` 身份、两处坐标 debug 再抛、合法 `None` 与双路径失败。实现只把坐标解析原序抽到 11 行 `_mouse_global_position()`，使用 `(resolved, value)` 区分合法 `None` 与解析失败；`eventFilter()` `34→27` 行，公开 override 参数与始终返回 `False` 的事件不消费语义不变。直接从 before 提交加载旧模块，与工作树新模块执行 38 组同输入动态差分为 `0 mismatch`；结构门禁锁定唯一 helper、唯一直接委托、override 参数及两函数均不超过 30 行。生产超长函数库存 `30→29`（`core=15 / providers=4 / state=1 / window=9 / models=0`）。before 提交 `34067bd`，代码提交 `fbda147a`；最终聚焦 `38 passed`、全量 Python `1964 passed / 1 skipped`、changed QML `0`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Python 3.9 AST 250、compileall 与 `git diff --check` 全绿，三路独立 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。LineEdit padding 点击导致伪 `editingFinished`、`_is_inside()` 右/下边界与 Qt `contains()` 不一致均保留为独立正确性债务；`Store.set()` 缺键 `None`、嵌套 batch，及 Logger 首次命名/失败事务/handler 所有权也已实证，禁止在后续机械拆分中固化。

2026-07-16 F7b 后续 Store 缺键 `None` 对称正确性已完成：真实修前 Python 合同为 `3 failed / 2 passed`，C++ `prism_test_store` 同样失败，证明 `set("missing", None)` 会错误地把缺键当成已有 `None`，既不创建键也不通知。Python/C++ 现统一只在“键已存在且值相等”时跳过；修后 Python Store 联合 `47 passed`、全量 Python `1972 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、Python 3.9 AST 251 与全部 runner 零可见窗口/零残留，三路 Review P0–P3 全零。提交 `08d75a00`；Build All [29455983636](https://github.com/aki-riko/PrismQML/actions/runs/29455983636) 七项全绿。该正确性批未改变长函数库存；嵌套 batch、净零变化仍通知、异常退出 flush、中断残留与 QML PyObject 封送继续留作独立债务。

2026-07-16 P7I-F/F7c 完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：`844c823` 的 before 合同先锁定 `Store.set(self, key, value, force=False)` 的公开调用形状、批处理中状态立即写入而通知延迟、键首次插入顺序、首个 old/最终 new、缺键 `None` 与已有相等 `None` 的 `force=True`。实现只把原有 batch 记录分支抽到 9 行 `_record_batch_change()`，`Store.set()` `33→27` 行；结构门禁要求 batch 真分支唯一直接委托且 `Store.set()` 不再直接操作 `_batch_changes`，生产超长函数库存 `29→28`（`core=15 / providers=4 / state=0 / window=9 / models=0`）。实现 Review 在 `f346787a` 中继续补强已有相等 `7` 的 `force=True`、`None→object` 与重复对象更新身份合同；变异 Review 真实杀死部分内联记录、待通知键排序、相等非 None 错误跳过及 `None→object` 静默丢通知四类错误实现。最终聚焦 `56 passed`、全量 Python `1978 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、changed QML `0`、Python 3.9 AST 258、compileall 与 `git diff --check` 全绿；代码、库存与变异三路最终 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。嵌套 batch、净零变化通知、异常退出 flush、中断后 `_batch_changes` 残留、QML PyObject 封送及 Logger 生命周期债务均未固化；下一批继续 F7 core/providers，P7J/P7K/P8B 仍严格独立。

2026-07-16 P7I-F/F7d DWM 正确性与机械拆分完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：修前真实 raw `_CFuncPtr` 宽句柄输入会因 `DwmSetWindowAttribute` 与 `SetWindowPos` 缺少指针宽度签名在进入 WinAPI 前抛出 `OverflowError`，C++ `disableDwmShadow(0)` 也会忽略失败 HRESULT 并错误返回成功。正确性提交 `88e9b895` 为 Python `DwmSetWindowAttribute`/`SetWindowPos` 补齐官方 ctypes 签名，并按 HRESULT 成功语义处理 DWM 调用；C++ enable/disable 同时在 policy/frame 失败时短路。before 提交 `13602227` 继续锁定公开 enable/disable 在 set/extend/position 普通异常时返回 `False`、`KeyboardInterrupt/SystemExit` 同一对象传播、精确调用顺序与 partial-state，且没有固化 `SetWindowPos == FALSE` 的未决语义。机械提交 `2bc4c6ed` 抽出 25 行 `_apply_dwm_shadow_state()`，`_enableDwmShadow()` `61→13` 行、`_disableDwmShadow()` `33→8` 行，生产超长函数库存 `28→26`（`core=13 / providers=4 / state=0 / window=9 / models=0`）。最终聚焦 `50 passed`、全量 Python `2005 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 3、compileall 与 `git diff --check` 全绿；30 项内存变异 `30/30` 被杀死，三路最终 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。三个提交已同步 `prism/main` 与 `origin/main`。

2026-07-16 P7I-F/F7e ScreenEyedropper 位置更新机械拆分完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：before 提交 `772ecc4` 用 fake screen/window 与真实 `QPoint/QRect` 锁定 `screenAt → primaryScreen fallback → geometry → move → capture → center pixel → QColor → update` 的顺序、四种明确非边界位置、宽高调用次数、None/null 图像、普通异常及 `KeyboardInterrupt/SystemExit` 同一对象传播与 partial-state；机械提交 `c3472550` 抽出 9 行 `_move_eyedropper_near_cursor()`，`_update_position_and_color()` `32→22` 行，生产超长函数库存 `26→25`（`core=13 / providers=3 / state=0 / window=9 / models=0`）。新增真实隐藏 QWidget 回归确认位置 `(66, 66)` 且全程不可见，19 组 before/after 同输入动态差分为 `0 mismatch`；初次变异复核发现“重复 move”与“helper 吞普通异常”两个测试缺口，补强后 `2/2` 被杀死且 survivor 为 0。最终聚焦 `20 passed`、全量 Python `2022 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 3、compileall 与 `git diff --check` 全绿，最终 Review 为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。QRect `right()/bottom()` exact-fit 的 1px 提前翻转与 `primaryScreen() is None` 仍是未固化、未修复的独立正确性债务。

2026-07-16 P7I-F/F7f Notification helper 引擎所有权正确性与机械拆分完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：两个真实 `QQmlApplicationEngine` 先后设为当前引擎时，修前 `_get_helper()` 仍返回 engine A 的同一对象，且 `EngineManager.reset()` 后无当前引擎仍会让公开通知调用返回成功，真实合同为 `2 failed / 2 passed`。正确性提交 `c5ec8f98` 改为先读取当前 engine，缓存只有在 C++ 对象有效且 `parent() is current_engine` 时才能复用；切换 engine、reset、旧 engine 销毁重建与同 engine 幂等修后 `4 passed`，8 类正确性变异全部被杀死，20 次独立重启 `20/20` 无崩溃。before 提交 `0fd0d05` 用纯 fake 锁定 engine lookup、缓存探针、`QQmlComponent → QUrl → setData → isError/errorString → rootContext → create → setParent → publish` 顺序、失败可重试、普通/控制异常身份及 logger 自身异常的精确 partial-state。机械提交 `7747a9f5` 抽出 18 行 `_cached_helper_for()` 与 19 行 `_create_helper()`，`_get_helper()` `42→14` 行，生产超长函数库存 `25→24`（`core=12 / providers=3 / state=0 / window=9 / models=0`）。最终聚焦 `84 passed`、全量 Python `2103 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 5、compileall 与 `git diff --check` 全绿；27 项机械变异在补齐 engine 身份与 helper 名重绑定门禁后 survivor 为 0，最终 Review 为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。三个提交已同步 `prism/main` 与 `origin/main`；主动销毁旧 helper、per-engine cache、`_invoke` 普通异常策略及公开通知“实际显示成功”语义均未混入本批。

2026-07-16 P7I-F/F7g SVG 属性流重写正确性与机械拆分完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：修前有效 UTF-8 但未闭合、标签错配、重复属性、未声明实体或额外根节点的 XML 会静默返回半截或只保留首个 SVG；带前缀的 `s:svg/s:path` 会丢失命名空间，外部 `m:path` 与 SVG 根内显式 `xmlns=""` 的 path 会被错误着色并抢占 `only_paths` 序号，且 `IconCore.path()` 已声明支持的 `qrc:/` 资源会因 `QFile` 不识别该 URL 而返回空串。正确性提交 `8b0e3bb4` 改为畸形 XML 原子抛出含路径/行列的 `ValueError`，以 `qualifiedName()` 保留元素与属性前缀，只让标准 SVG namespace 或无 namespace legacy 根下的 path 计序，并把 `qrc:/` 规范化为 `:/`；仓内真实 `gallery.rcc` 已验证可读且 `QSvgRenderer` 有效。before 提交 `24e0cb4` 锁定签名、QFile 打开/读取/关闭、普通与控制异常身份、零基全局 path 序号、属性顺序与对象字符串化、PI/DTD/comment/CDATA/entity 语义、namespace/xlink、真实像素渲染，以及 `make_icon/paint_icon` 对 payload、索引和异常的透传。机械提交 `77f44cef` 抽出读取、准备、stream 建立、namespace/element、token 分派与完成 helper，正确性修复后的 `_rewrite_svg_attrs()` `134→25` 行，全部目标 helper 最大 23 行，`icon_core.py` 456 行；生产超长函数库存 `24→23`（`core=11 / providers=3 / state=0 / window=9 / models=0`）。重构前后对 2,497 个真实图标 SVG 与 1 个 qrc SVG 的逐字节差分为 `2498/2498 mismatch=0`；26 项变异最终为 `25 killed / 1 equivalent / 0 survivor`，唯一等价项是当前真实 `QXmlStreamReader` 路径不可达的 `EntityReference` token。最终聚焦 `80 passed`、全量 Python `2143 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 261、compileall 与 `git diff --check` 全绿；正确性、before、机械与变异 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。三个提交已同步 `prism/main` 与 `origin/main`；P7J/P7K 的路径/API 审计与 P8B 图标生成器债务未混入本批。

2026-07-16 P7I-F/F7h ScreenEyedropper 绘制字体正确性与机械拆分完成后的当前验证快照（仍不代表 F5、P7、P9 或全库完成）：真实 `QApplication`/隐藏 QWidget 字体输入先复现 `paintEvent()` 强制 `Segoe UI`，使应用字体与控件级 override 的 family 被覆盖；修前两组合同为 `2 failed`。正确性提交 `ab458ab4` 改为复制 `self.font()` 后只设置 13px，保留应用/控件 family、weight 与 italic 且不回写 QWidget 字体，并删除未使用的 `pixel_size`；测试提交 `12af8c8` 先锁定 light/dark、None/null/有效截图、背景/preview/十字线/双描边/文字几何、普通及控制异常同对象传播、真实隐藏像素和顶层 QWidget 零泄漏。机械提交 `f78f6176` 抽出背景 11 行、十字线 7 行、预览 18 行和文字 12 行四个 helper，`paintEvent()` `73→20` 行，文件 382 行；生产超长函数库存 `23→22`（`core=11 / providers=2 / state=0 / window=9 / models=0`）。直接从字体修复提交加载 before 模块，与工作树新模块执行 6 组 fake painter 调用轨迹及 4 组真实 QImage 逐字节差分均为 `0 mismatch`；结构门禁继续锁定 helper 所有权、顶层 `background→preview→label` 顺序、三色前置构造、preview border 区间、captured 分支 crosshair、override 签名及无 Try/save/restore/super。最终聚焦 `43 passed`、全量 Python `2166 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 4、compileall 与 `git diff --check` 全绿；两路最终 Review 均为 P0–P3 全零，全部 runner 零可见窗口/零残留，受保护 audit 目录未触达。fallback 双描边、位置 exact-fit 1px 提前翻转、`primaryScreen() is None` 与 `start_picking()` 失败事务仍为独立债务，未混入本批。三个 F7h 提交已同步 `prism/main` 与 `origin/main`。

2026-07-16 P7I-F/F7i Updater 版本优先级正确性与机械拆分完成后的当前验证快照（仍不代表 P7J、P7K、P9 或全库完成）：公开文档已承诺“语义版本比较”，但修前 Python 会把 `+build` 元数据参与正式版与预发布版优先级，并把空白或仅 `v/V` 前缀标签解析成非空正式版，新增真实调用合同为 `6 failed / 33 passed`；C++ 镜像同样把构建元数据参与比较，且以 `qint64` 解析数字段，超长数字预发布段溢出后退化为字符串比较，修前 `prism_test_store` 失败。提交 `d40b1d59` 统一 Python/C++ tag 合同：去除可选前缀、忽略构建元数据、保留项目四段及可变长度主版本、正式版高于同 core 预发布版、空白或仅前缀视为最小版本；C++ 数字段改为去前导零后的长度与字典序比较，避免整数上限。Python 抽出 6 行 `_normalize_version_tag()` 与 12 行 `_parse_version_segments()`，`_parse_version()` `38→22` 行；50 个真实/代表性 tag 的 2,500 对非目标 before/after 比较为 `0 mismatch`，生产超长函数库存 `22→21`（`core=10 / providers=2 / state=0 / window=9 / models=0`）。最终聚焦 `43 passed`、全量 Python `2174 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `8/8`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 56、compileall、mkdocs strict 与 `git diff --check` 全绿；最终 Review 为 P0–P3 全零，全部 runner 零可见窗口/零残留，用户配置、两类 QML 缓存和受保护 audit 日志前后指纹完全一致。P7J 的下载原子 I/O、并发与响应 schema 债务未混入本批。

2026-07-16 P7J Updater 下载事务、并发与响应 schema 完成后的当前验证快照（仍不代表 P7、P7K、P9 或全库完成）：Python 修前真实短写/flush/close 输入会保留截断文件并错误发送成功，非法 UTF-8、根数组和畸形 asset 也未形成稳定失败合同；C++ 同名 URL 会复用固定目标，write 返回值被忽略，重复调用会覆盖活动 reply。提交 `a8920870` 与 `a6cd258` 分别完成 Python/C++ 对称整改：严格 UTF-8 release schema、进程唯一临时路径、完整写入与原子发布、失败单信号和清理、活动请求 guard、具体 reply 身份绑定；C++ 使用禁用 direct-write fallback 的 `QSaveFile` 并新增真实 loopback CTest。严格 UTF-8 另以 Qt 实际解析验证 JSON 字符串内部 `0xff` 返回 `invalid UTF8 string`，并固化到 C++ 回归。最终聚焦 Python `73 passed`、全量 Python `2204 passed / 1 skipped`、QML probe `169 OK / 0 错误 / 12 跳过`、C++ 构建 `PRISM_BUILD_DONE`、`prism_test_store 1/1`、`prism_test_updater 1/1`、headless CTest `9/9`、Windows native CTest `2/2`、mkdocs strict 与 `git diff --check` 全绿；Review 为 P0–P3 全零，runner 零可见窗口/零残留，受保护 audit 目录未编辑、未暂存、未提交。早期红测留在系统临时目录的一个 `App-Setup.exe` 与三个旧 `.part` 属已知既有残留，本批最终快照证明没有新增，不冒充已清除；下一批进入 P7K。

2026-07-16 P7K-A 图标 URL/本地路径编解码完成后的当前验证快照（仍不代表 P7K、P7、P9 或全库完成）：真实 FullyEncoded PNG 输入含空格、`#`、`%` 与中文，修前 Python `WindowHelper/WindowCore/SystemTrayIcon` 三入口全部加载为空，resolver 把百分号编码原样当磁盘文件名；同时 UNC 被 `Path.resolve()` 错当工作树相对路径，POSIX 根斜杠丢失，qrc 空格不解码。提交 `57fd1946` 新增两端私有共享解析，`file:` 统一委托 `QUrl.toLocalFile()`，qrc 统一为 `:/`，并让 C++ 托盘与窗口路径复用同一实现。红测 `6 failed / 1 passed` 修后为 `9 passed`；相关联合 `146 passed`，全量 Python `2213 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、C++ 构建 `PRISM_BUILD_DONE`、`prism_test_system 1/1`、headless CTest `9/9`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 235、compileall 与 `git diff --check` 全绿；全部 runner 零可见窗口/零残留，Review P0–P3 全零，受保护 audit 未编辑、未暂存、未提交。下一批进入 P7K-B SvgImageProvider/WindowIcon 保留字符编解码。

2026-07-16 P7K-B SvgImageProvider/WindowIcon 保留字符编解码完成后的当前验证快照（仍不代表 P7K、P7、P9 或全库完成）：真实 QML capture provider 证明 raw path 的字面 `#` 保留、字面 `%`/`|` 转为 `%25/%7C`，FullyEncoded file URL 的 `%23/%25` 保持；修前生产 provider 直接把 id 当文件名，两种真实 SVG 输入均返回空图，且 `WindowIcon` 删除 `file:///` 后无法统一处理 UNC。提交 `74c095ef` 建立“URL 来源保留编码、裸路径整体编码、provider 只解码一次”的 Python/C++ 对称合同，并用字面 `%23` 文件名防止合法转义歧义。聚焦 provider/WindowIcon `26 passed`，全量 Python `2216 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、C++ 构建 `PRISM_BUILD_DONE`、provider CTest `1/1`、headless CTest `9/9`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 236、compileall、mkdocs strict 与 `git diff --check` 全绿；全部 runner 零可见窗口/零残留，Review P0–P3 全零，受保护 audit 未触达。一次全量门禁中既有 SegmentedControl 固定 20ms 采样在 `running=true` 且目标已更新时仍停在起点，独立 fresh process 同一输入 `10/10` 通过，随后完整全量重跑全绿；未把该帧相位波动夹入本批。下一批进入 P7K-C SqlListModel 只读 URI。

2026-07-16 P7K-C SqlListModel 只读 URI 完成后的当前验证快照（仍不代表 P7K、P7、P9 或全库完成）：真实特殊路径库修前列解析报 `OperationalError: no such table: records`，Python fallback 删除库后 `refresh()` 同样报错并重建 0 字节文件；新增回归为 `7 failed / 20 passed`。提交 `68c9e60a` 下沉 32 行私有只读连接模块，模型文件 `671→665` 行，统一按 URI 一次编码并让列解析/count/页读取只走 `mode=ro`；Python/Rust 对同一含空格、`#`、字面 `%23`、中文输入均返回两行，删除后分别抛 `OperationalError/RuntimeError: unable to open database file`，磁盘仍无文件且完整状态不变，本机真实 `\\localhost\C$` UNC 查询返回 `[(7,)]`。聚焦 `29 passed`、SQL 联合 `233 passed`、全量 Python `2223 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 279、compileall、mkdocs strict 与 `git diff --check` 全绿；全部 runner 零可见窗口/零残留，Review P0–P3 全零，受保护 audit 未编辑、未暂存、未提交。下一批进入 P7K-D Python 注册注入。

2026-07-16 P7K-D Python 公开注册注入完成后的当前验证快照（仍不代表 P7、P8、P9 或全库完成）：真实 QML wrapper 在临时 `ConfigManager.dpiScale=125` 输入下，修前 `DpiManager.userDpiScale/dpiDirect/clipboardName` 为 `0 / 0 / ""`，根 context 两项均为 `None`，Qt 明确记录 `ConfigManager/ClipboardHelper is not defined`；红测 `1 failed`。提交 `47ebdb30` 在公开 `register_types()` 补齐两个既有单例，两个真实引擎身份一致且销毁后所有权不丢，修后 wrapper 为 `125 / 125 / ""`、Qt warning/critical 为 0；聚焦 `1 passed`，相关联合 `58 passed`。首次全量门禁仅既有 TabWidget 中途反向固定 20ms 采样出现一次旧方向多推进一帧，fresh process 同一输入 `10/10` 通过，未夹带动画修改；随后完整重跑为 Python `2224 passed / 1 skipped`。QML `169 OK / 0 错误 / 12 跳过`、headless CTest `9/9`、Windows native CTest `2/2`、changed QML `0`、Python 3.9 AST 280、compileall、mkdocs strict 与 `git diff --check` 全绿；全部 runner 零可见窗口/零残留，Review P0–P3 全零，受保护 audit 未编辑、未暂存、未提交。P7K 至此完成，下一批进入 P8A。

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

截至 2026-07-17，按剩余工作量粗估整体计划约完成 **85%**：P0–P5、P7J、P7K 与 P8 已完成，P6/P7 继续进行，P9 待执行；该百分比不是按阶段数量简单平均，新增插单会改变剩余时间估算。

| 阶段 | 状态 | 验证记录 | 提交 |
|---|---|---|---|
| P0 基线固化 | 已完成 | 固化审计输入与 12 个合法 QML skip；当前回归基线为 Python 122、QML 169/0/12、CTest 7/7 | `1dd7e9a2` |
| P1 CTest 与 C++ CI | 已完成 | 历史 68 条 DLL 弹窗与 3 次错误生命周期原生崩溃已追溯；统一 runner 覆盖 Python/QML/C++/制品入口。最新止血让 Python/C++ 自动测试及普通后代持续继承 `ErrorMode=0x8003`；专项 13/1、Python 228/1、QML 169/0/12、MSVC 构建、headless CTest 6/6、Windows native 1/1、changed 0 全绿，同一 105 秒真实测试入口未观察到新增顶层窗口，匹配 Event 26/1000/1001 与 dump 增量为 0；Build All [29158555858](https://github.com/aki-riko/PrismQML/actions/runs/29158555858) 的 QML conventions、Windows 零交互门禁、三平台桌面、Android 与 iOS 共 7 个作业全绿，Deploy Docs [29158555852](https://github.com/aki-riko/PrismQML/actions/runs/29158555852) 成功 | `1dd7e9a2`、`2db05888`、`6d96a2a`、`a75540f`、`ce9e0a0`、`5c290a93`、`75ef786`、`383dbeb`、`1d76047` |
| P1 CI 句柄对象身份判据 | 已完成 | 句柄数值复用误报已由“子同数值成功/父 event 仍 timeout”与 `close_fds=False` 真继承对照坐实；测试改用父 event 状态验证对象身份。全量 Python 1828/1、QML 169/0/12、CTest 8/8，Build All [29445180749](https://github.com/aki-riko/PrismQML/actions/runs/29445180749) 七项全绿 | `72c24eda` |
| P1+ Windows 机制级零窗口门禁 | 已完成 | 用户已澄清弹窗来自 Codex 测试；原始任务记录恢复出 2026-07-11 04:55 的真实裸 CTest 命令，六个仓内 EXE 与历史 Event 26 均对应 `0xC0000135`/缺 Qt DLL。当前同一命令 Rust 6/6、CTest 8/8；随后连续三轮 Python 297/1、QML 169/0/12、headless 6/6，runner 窗口/Job 归零，交互桌面本仓窗口、Event 26/1000/1001 与 dump 增量均为 0；用户于 17:28 明确确认本轮没有出现错误弹窗。入口另有精确 Desktop/命名 Job 验真及 11-case 原生失败矩阵 | `728b65a4`、`50714b38`、`af65069d`、`daec535`、`1a5b004` |
| P2 sdist 与发布门禁 | 已完成 | sdist 独立构建、内容校验、全新 venv 安装、QML 169/0/12 与 provider 30 次操作通过；Release [29114520829](https://github.com/aki-riko/PrismQML/actions/runs/29114520829) 全绿 | `a36ba3f5` |
| P3 Provider 生命周期 | 已完成 | 旧 wheel/源码真实输入 3/3 复现已删除对象；修后本地 wheel 与 sdist 各 30/30，CI Linux wheel 与 sdist 各 30 次操作通过 | `4d067411`、`ca256f5b`、`1c344dd1`、`3c831aed`、`13a258fe` |
| P4 Qt 与危险脚本 | 已完成 | P4.1 统一 Qt/PySide6 6.9+；P4.2 三种破坏性失败与事务中断均保持原产物不变，Python 140、QML 169/0/12、CTest 7/7；Build All 29119519828 五平台全绿 | `818deec1`、`6d3395f` |
| P5 Rust 与维护工具 | 已完成 | P5A：Rust 6/6、Python 140、QML 169/0/12、CTest 7/7、Build All 五平台全绿；P5B：两种控制台模式均真实 probe 181 类型且错误非零退出；P5C：普通 import 无环境副作用，真实 App/Translator 输入返回 `OK`，Updater 两端配置语义一致，全量 Python 148、QML 169/0/12、Rust 6/6、无 Qt PATH 裸 CTest 7/7 | `b44c2dc5`、`6d96a2a`、`9bb5271`、`9f497d8a` |
| P6 QML 规范债务 | 进行中 | P6A–P6C21 与 P6D 已完成的小批记录保持不变；扫描器已覆盖字符串、固定数值、数组、callable、examples QML010 与高置信 primitive 传播，P6C16–21 已清理全部生产颜色且未新增生命周期例外，P6D 累计清理 339 条成员顺序/分节术语债务，`controls/feedback` 当前 QML008/QML009 已归零并进入 `data/navigation`；DialogBoxCore 快速重复提交正确性另以真实鼠标红测闭环。当前全库为 2,236 项：QML008 1,342、QML009 851、QML010 43、QML011 0、QML013 0；43 条 QML010 全部属于 examples，生产颜色债务归零。最新全量 Python 2240/1、QML 169/0/12、CTest 9/9 + native 2/2、MkDocs strict、changed 0 | `d5b5852`、`8e3ba4b0`、`e98adebb`、`557930af`、`b0d23808`、`49d6d6d0`、`09c696df`、`a877c2c7`、`6fc6e645`、`2a22c115`、`06eb4af9`、`685d063e`、`bcf0c737`、`4c22e7bc`、`bad57911`、`b281b7b`、`85a75ff3`、`0e438e60`、`1f9d1038`、`b1050f84`、`d4e2e11e`、`10b25427`、`8c633f4f`、`6810e12c`、`1758f484`、`49a899d5`、`0946eea5`、`2c1be8dd`、`cbf934d2`、`4e383715`、`bff2b32b`、`95c3db84`、`41565d4b`、`e17b06ca`、`c284433f`、`744eb6ec`、`ca6eb64b`、`af0b0cd4`、`28664920`、`a17f46a8`、`263851c1`、`165dbd4`、`8e29044c`、`86d7e0ee`、`dc5cf90`、`f329a3e`、`668cfda`、`89474354`、`78ff168`、`4e2e4401`、`369724f`、`8d1860f8`、`2f3c7d3`、`dbe71d46`、`f51f302`、`eb044ed8`、`c5bf1f0`、`54879042`、`4597651a`、`5694624d`、`e6819b23`、`14f4eea3`、`c7b07546`、`eb455b80`、`ed580d34`、`1e9d6aa8`、`f339dd29`、`074c7070`、`691a2c8c`、`9cf8fe69`、`d77d9a50`、`133af05c`、`5a576ef9`、`0811cc78`、`cc8a51c1`、`511e14ba`、`afd11daf`、`f6b1891f`、`d16dab7d`、`440773a5`、`a9ddba12`、`f3308d32`、`daa37c2e`、`112f1afa`、`ad5e8a3e`、`fd6062f3`、`702835a3`、`e2231281`、`dbd71743`、`57d94b48`、`ff650be9`、`37972d3a`、`6fc7eb2a` |
| P7 Python 规范债务 | 进行中 | 已完成框架签名/生成枚举例外、异常边界前四批、P7E–P7H、P7I-A–P7I-D5，以及 P7I-F 的 F1–F4、F5a–F5f、F6 与 F7a–F7i，并完成 P7J 与 P7K；F5 剩余耦合调用链仍待后续正确性批。Store 缺键 `None` 的 Python/C++ 对称正确性、DWM 指针宽度/HRESULT、Notification helper 当前引擎所有权、SVG XML/qrc/namespace、ScreenEyedropper 应用/控件字体、SqlListModel 只读路径与公开注册 context 合同已修复；F7a–F7h 已将 `installDwmSyncFilter()` `32→25`、`eventFilter()` `34→27`、`Store.set()` `33→27`、`_enableDwmShadow()` `61→13`、`_disableDwmShadow()` `33→8`、`_update_position_and_color()` `32→22`、`_get_helper()` `42→14`、`_rewrite_svg_attrs()` `134→25`、`paintEvent()` `73→20` 行，生产超长函数库存 `31→19`（`core=8 / providers=2 / state=0 / window=9 / models=0`）。最新 P7K-D 聚焦 `1 passed`、相关联合 `58 passed`、全量 Python `2224 passed / 1 skipped`、QML `169 OK / 0 错误 / 12 跳过`、C++ headless `9/9`、Windows native `2/2`、changed QML `0`、Python 3.9 AST 280、compileall、mkdocs strict 与 `git diff --check` 全绿，最终 Review P0–P3 全零。F5 与 input focus 正确性债务、Store 嵌套/flush/QML 封送、Logger 生命周期债务、ScreenEyedropper exact-fit/无屏幕/start 事务债务、Notification 旧 helper 主动回收/调用异常策略、F7 后续及剩余导入、文件头、benchmark 路径与测试 stdout 政策仍待处理 | `8272d2c0`、`354777fe`、`a8e80e86`、`c962014e`、`bb81d37b`、`e344c8a0`、`e48bb127`、`dafa2a34`、`1512f723`、`8e24b825`、`5fb9e7d8`、`620da260`、`77d045c5`、`cb19eb88`、`fe7a4f4e`、`21211777`、`3b717770`、`f2b4af11`、`cc4567b2`、`ef07928d`、`6db88a88`、`6bf8569f`、`0c482ed0`、`48171374`、`27e831f0`、`d20053c9`、`798f92c`、`42075fa5`、`d2f99369`、`32056b02`、`71854655`、`1b5e072`、`093b7dec`、`a90beb8`、`2be95663`、`977966f`、`2d0881dc`、`5b483469`、`65b2524`、`0b273ad2`、`a248dd77`、`2521d690`、`ac562a72`、`8f20dec`、`900cad2`、`a0dc885e`、`6d60680f`、`173c0f99`、`3db0c3b8`、`72ac50f3`、`bb71edff`、`0c7b2722`、`0f13bbe7`、`e7d42fe`、`901afc76`、`34067bd`、`fbda147a`、`08d75a00`、`844c823`、`f346787a`、`88e9b895`、`13602227`、`2bc4c6ed`、`772ecc4`、`c3472550`、`c5ec8f98`、`0fd0d05`、`7747a9f5`、`8b0e3bb4`、`24e0cb4`、`77f44cef`、`12af8c8`、`ab458ab4`、`f78f6176`、`d40b1d59`、`a8920870`、`a6cd258`、`57fd1946`、`74c095ef`、`68c9e60a`、`47ebdb30` |
| P7I-F F7i Updater 版本优先级 | 已完成 | Python/C++ 忽略构建元数据、空白标签归一、C++ 任意长度数字段比较；`_parse_version()` `38→22`，库存 `22→21`；Python 2174/1、QML 169/0/12、CTest 8/8 + native 2/2、mkdocs strict 全绿 | `d40b1d59` |
| P7J Updater 下载事务与 schema | 已完成 | Python/C++ 严格 UTF-8 schema、唯一临时文件、完整写入后原子发布、失败单信号清理和活动 reply guard；聚焦 Python 73、全量 Python 2204/1、QML 169/0/12、CTest 9/9 + native 2/2、mkdocs strict 全绿 | `a8920870`、`a6cd258` |
| P7K-A 图标 URL/本地路径 | 已完成 | Python/C++ WindowHelper 与 SystemTray、Python WindowCore 共享 Qt URL 合同；真实保留字符图标三条 Python、两条 C++ 入口通过；Python 2213/1、QML 169/0/12、CTest 9/9 + native 2/2 | `57fd1946` |
| P7K-B SVG provider 编解码 | 已完成 | WindowIcon 保留 URL、整体编码裸路径，Python/C++ provider 只解码一次；真实 `#/%23/%/|` 与非 ASCII 路径通过；Python 2216/1、QML 169/0/12、CTest 9/9 + native 2/2 | `74c095ef` |
| P7K-C SqlListModel 只读 URI | 已完成 | Windows/POSIX/UNC URI 一次编码，Python 列解析/count/页读取统一只读；真实特殊路径和删除文件在 Python/Rust 下结果一致且不建库；Python 2223/1、QML 169/0/12、CTest 9/9 + native 2/2 | `68c9e60a` |
| P7K-D Python 注册注入 | 已完成 | `register_types()` 补齐 ConfigManager/ClipboardHelper；双引擎同一单例、DpiManager wrapper 125、warning/critical 归零；Python 2224/1、QML 169/0/12、CTest 9/9 + native 2/2 | `47ebdb30` |
| P8 资源注册 | 已完成 | 五个孤儿已删除；2,497 项双注册表已同步；Python/C++ IconProvider 已统一；DpiManager 已收窄为五个真实状态。全量 Python 2230/1、QML 169/0/12、CTest 9/9 + native 2/2，全库 QML 库存 2,604、changed 0 | `154cd4e4`、`11882986`、`39efe2e8`、`4bc9fd0`、`fa4a20d6`、`79932827` |
| P9 最终验收 | 待执行 |  |  |

状态只能填写“待执行 / 进行中 / 已完成 / 阻塞”。“已完成”必须同时记录真实测试结果和提交哈希。
