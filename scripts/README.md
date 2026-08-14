# 脚本目录

- 根目录保留可直接执行的维护、验证和性能入口。
- `_qml_lint/` 保存 QML 规范扫描器内部实现；公开入口是 `check_qml_conventions.py`。
- `_test_support/` 保存自动测试进程隔离内部实现；公开入口是 `test_process.py`。
- `manual/` 保存会打开窗口或仅在人工维护时使用的脚本与数据，不进入自动门禁。

自动测试和探针必须通过 `test_process.py` 启动，生成内容必须写入 `.artifacts/`。
