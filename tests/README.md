# 测试目录

- 根目录保存 Python 产品行为与公共 API 测试。
- `qml/` 保存 QML 场景、组件探针和 QML 行为测试。
- `tooling/` 保存测试运行器、维护脚本、构建入口和 QML 扫描工具自身的回归测试。

所有自动测试均由 `scripts/test_process.py` 启动；可视和性能入口不属于自动门禁。
