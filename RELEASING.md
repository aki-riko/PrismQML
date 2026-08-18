# PrismQML 发布指南

本文档保存发布操作细节；开发与架构铁律见 `AGENTS.md`。发布前必须同时遵守两份文档。

## 版本与远程

- `pyproject.toml` 的 `version` 与 `prismqml/__init__.py` 的 `__version__` 必须同步。
- 默认只递增四段版本号 `x.y.z.n` 的最后一段；前三段变更必须由维护者明确决定。
- `prism` 指向 GitHub `git@github.com:aki-riko/PrismQML.git`，CI 与 PyPI 发布在此运行。
- `origin` 指向自建 Gitea `git@git.9li.life:Aquila/PrismQML.git`，不运行发布 CI。
- 发布提交和 tag 必须显式推送到 `prism`；需要同步 Gitea 时再显式推送 `origin`。

## 发布前验证

自动测试必须经 `scripts/test_process.py` 启动，不得直接启动原生失败夹具：

```powershell
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 480 -- .\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py
ctest --test-dir .artifacts\cpp\desktop -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
```

QML probe 的稳定合同是：

- 退出码为 0，错误数为 0。
- singleton 必须经真实 QML 引擎创建并读取，创建期 Qt warning、critical、fatal 为 0。
- required-property 跳过项必须与 probe 中声明的允许集合完全一致；不得在本文写死会随组件注册变化的 OK 数或总数。
- 出现非零结果时必须分析具体错误；需要判定新增回归时，在改动前基线 worktree 运行同一 probe 对比结果。

Windows 原生 Mica 仅在显式配置 `-DPRISM_BUILD_NATIVE_TESTS=ON` 后运行：

```powershell
ctest --test-dir .artifacts\cpp\desktop -L native --interactive-debug-mode 0 --output-on-failure --no-tests=error
```

`tests/test_window_buttons.py`、QML 性能基准和 FPS 探针属于人工可视测试，不得混入自动门禁。Windows 可视性能验收只接受 D3D11，并必须核验实际图形 API；offscreen 仅用于零交互正确性回归。

## 提交、Tag 与 Release

```bash
git add -A
git commit -m "release: vx.y.z.n"
git tag vx.y.z.n
git push prism main
git push prism vx.y.z.n
gh release create vx.y.z.n --repo aki-riko/PrismQML --title "vx.y.z.n" --notes "..."
```

如需同步 Gitea：

```bash
git push origin main
git push origin vx.y.z.n
```

`git push` 使用 SSH 公钥；`gh release` 使用 GitHub token。不得在对话、命令记录或仓库中写入明文 PAT。使用 `gh auth login` 或进程环境中的 `GH_TOKEN`。

## CI 与 abi3

`.github/workflows/release.yml` 是正式构建与发布入口：推送 `v*` tag 后，三平台使用 cibuildwheel 构建 wheel 和 sdist，publish job 通过 PyPI Trusted Publishing 上传。普通提交不发布；`workflow_dispatch` 只构建不发布。

abi3 配置缺一不可：

1. `rust/Cargo.toml`：Pyo3 使用 `abi3-py39`。
2. `pyproject.toml` 的 setuptools-rust 扩展：`py-limited-api = "auto"`。
3. `pyproject.toml` 的 bdist_wheel：`py-limited-api = "cp39"`。

wheel 内 Windows 扩展应为无 Python 小版本后缀的 `prismqml_rs.pyd`；出现 `prismqml_rs.cp3XX-win_amd64.pyd` 表示退化成单版本 wheel。本地构建只用于诊断，正式产物由 CI 生成和发布。

## 下游生效

发布 PrismQML 不会自动更新下游应用。Gitora、quicksketch、Kaleidos 等各自使用独立虚拟环境，必须升级依赖并重新打包：

```bash
pip install -U prismqml==x.y.z.n
```

打包应用会把 PrismQML 嵌入产物，旧产物不会自动获得修复。若曾为热修直接修改下游虚拟环境中的包副本，发布前必须检查并对齐所有副本。

## 包命名

- PyPI 分发名和 Python 导入名：`prismqml`
- QML 模块名：`PrismQML`
- Rust 扩展名：`prismqml_rs`
- 旧名 `fqml`、`fluentqml`、`FluentQML` 不得重新引入；图标集路径、`as Fluent` 别名和 Fluent Design 致谢除外。
