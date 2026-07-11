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
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe tests\qml\probe_all_components.py
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
3. 需要 offscreen 的测试通过 `set_tests_properties(... ENVIRONMENT ...)` 或 workflow 环境统一设置。
4. 平台不支持的行为在测试内部做明确平台断言或由 CMake 条件注册；任何桌面矩阵都不允许注册数为 0。
5. 删除 `.github/workflows/build-all.yml` 中的 stderr 丢弃、手工 fallback 和 `|| true`。
6. 把 QR 解码依赖加入经过验证的测试依赖集合，优先使用 `opencv-python-headless`，不得依赖开发机全局 Python。

验收：

```powershell
cmake --build cpp\build
ctest --test-dir cpp\build -N
ctest --test-dir cpp\build --output-on-failure --no-tests=error
```

验收判据：

- `ctest -N` 显示预期测试集合且绝不为 0。
- 本地 6 个 C++ 测试程序与 1 个 QR 独立解码测试共 7 项全部通过。
- GitHub 的 Windows、Linux、macOS 日志均能看到实际测试名称和结果。
- 人为让一个临时断言失败时，workflow 必须非零退出；验证后撤销临时改动。

建议提交：`test: register and enforce C++ test execution`

P1 后续回归已完成：pytest 与全组件 probe 在导入 PySide6 前自行以 `setdefault` 启用 `offscreen`，裸命令不再依赖调用者环境，显式平台覆盖仍会保留；新增 2 项隔离子进程回归。Windows 11 Mica 测试继续使用真实 `windows` 平台插件，但改为通过 `winId()` 创建隐藏 HWND、全程不调用 `show()`，并在 DWM 调用前后同时断言 Qt `isVisible()` 与 Win32 `IsWindowVisible()` 均为 false。无 Qt/QML 环境的裸 pytest `167/167`、QML `169/0/12`、无 Qt PATH 的 CTest `7/7` 通过，Mica 结果文件确认隐藏 HWND、Mica 与原生阴影全部成功。提交：`a75540f`。

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

P6C2a 已完成：`Enums.fontMonospace` 统一转发 Python/C++ `ThemeManager.fontMonospace`，CodeBlock、孤立登录组件和 ColorPicker 的 5 个真实消费者已迁移；删除 Windows-only `colorPickerMetrics.monospaceFontFamily` 与零消费者 `iconFontFamily`。运行时测试复现并修正了 `CodeBlock.qml` 从 `controls/chat` 错误导入 `../../..` 导致四处 `Enums is not defined` 的存量缺陷，同一输入修后 4 个等宽字体对象均使用全局 token。canonical 首选字体在本机从 Consolas 变为 Cascadia Code，明确作为视觉决策接受：仓内真实 `CodeBlock.qml` 文本在 376px 宽下高度 `1815→1722` 且组件随内容自适应，6 位 Hex `46≤68`、ARGB `74≤192`、默认 Login 标题 `126≤400` 均无裁切。Label 仅把注释同步到当前真实 `20/28/40/68` 映射，display 字重仍留待独立视觉决策。全量 Python 168、QML `169/0/12`、孤立登录组件正式注册引擎显式加载、无 Qt PATH CTest `7/7`、changed 0 与 `git diff --check` 通过；一次未带 traceback 的瞬态 `.F` 由同一完整套件 168 项和相关用例 5 个独立新进程复验均未再现。全库基线降至 3,231 项，QML012 `7→5`，剩余为 Timeline 2、CycleWheelPicker 2、Rating 1。提交：`b0d23808`。

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
.\.venv\Scripts\python.exe tests\qml\probe_all_components.py
.\.venv\Scripts\python.exe -m pytest
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
- 前置依赖：P4、P6、P7

执行项：

- 通过修复后的生成器补齐 13 个未暴露 SVG：`BulletedList`、`FitPage`、`Hide`、`Message`、`NavigateForward`、`OpenFile`、`OpenFolderHorizontal`、`PowerButton`、`StickyNotes`、`Update`、`View`、`Volume`、`Zoom`。
- 确保 Python/QML 两套枚举数量和值完全一致。
- 对以下文件做下游引用审计：
  - `controls/auth/LoginWindowLightShadow.qml`
  - `controls/containers/Layout/Layout.qml`
  - `controls/inputs/LineEdit/TextInputCore.qml`
  - `controls/inputs/TextEdit/PlainTextEdit.qml`
- 有公共价值的文件补 qmldir 与测试；确认废弃的文件在用户批准后删除。

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
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe tests\qml\probe_all_components.py
cmake --build cpp\build
ctest --test-dir cpp\build --output-on-failure --no-tests=error
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
| P1 CTest 与 C++ CI | 已完成 | 本地 CTest 7/7；Windows 裸 `ctest` 不依赖调用者 Qt PATH；pytest/probe 默认 offscreen，Mica 使用真实 windows 插件与全程隐藏 HWND，Qt/Win32 可见性断言及真实 DWM 调用通过；裸 Python 167、QML 169/0/12、CTest 7/7；Build All [29123637721](https://github.com/aki-riko/PrismQML/actions/runs/29123637721) 五平台通过 | `1dd7e9a2`、`2db05888`、`6d96a2a`、`a75540f` |
| P2 sdist 与发布门禁 | 已完成 | sdist 独立构建、内容校验、全新 venv 安装、QML 169/0/12 与 provider 30 次操作通过；Release [29114520829](https://github.com/aki-riko/PrismQML/actions/runs/29114520829) 全绿 | `a36ba3f5` |
| P3 Provider 生命周期 | 已完成 | 旧 wheel/源码真实输入 3/3 复现已删除对象；修后本地 wheel 与 sdist 各 30/30，CI Linux wheel 与 sdist 各 30 次操作通过 | `4d067411`、`ca256f5b`、`1c344dd1`、`3c831aed`、`13a258fe` |
| P4 Qt 与危险脚本 | 已完成 | P4.1 统一 Qt/PySide6 6.9+；P4.2 三种破坏性失败与事务中断均保持原产物不变，Python 140、QML 169/0/12、CTest 7/7；Build All 29119519828 五平台全绿 | `818deec1`、`6d3395f` |
| P5 Rust 与维护工具 | 已完成 | P5A：Rust 6/6、Python 140、QML 169/0/12、CTest 7/7、Build All 五平台全绿；P5B：两种控制台模式均真实 probe 181 类型且错误非零退出；P5C：普通 import 无环境副作用，真实 App/Translator 输入返回 `OK`，Updater 两端配置语义一致，全量 Python 148、QML 169/0/12、Rust 6/6、无 Qt PATH 裸 CTest 7/7 | `b44c2dc5`、`6d96a2a`、`9bb5271`、`9f497d8a` |
| P6 QML 规范债务 | 进行中 | 扫描器与 CI 新增违规门禁已建立；P6A 六组 v1.0 前兼容 API 已归零；P6B 的 ThemeManager 直接访问、局部主题代理及 Label 重复常量已归零，neo Mica 开关真实输入通过；P6C1 完成 27 处透明表达式与 28 处样式数值等值迁移；P6C2a 统一全局等宽字体入口、删除两个旧字体 token 并修复 CodeBlock 错误相对 import，QML012 降至 5；Python 168、QML 169/0/12、孤立登录组件显式加载、无 Qt PATH CTest 7/7、changed 0 通过；全库基线 3,231（成员顺序 1,936、分节术语 1,203、颜色 39、数值 48、字体 5） | `d5b5852`、`8e3ba4b0`、`e98adebb`、`557930af`、`b0d23808` |
| P7 Python 规范债务 | 待执行 |  |  |
| P8 资源注册 | 待执行 |  |  |
| P9 最终验收 | 待执行 |  |  |

状态只能填写“待执行 / 进行中 / 已完成 / 阻塞”。“已完成”必须同时记录真实测试结果和提交哈希。
