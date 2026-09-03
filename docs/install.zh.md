# 安装

## 环境要求

- Python 3.9+
- PySide6 6.9+（Qt 6.9+）——安装 PrismQML 时会自动安装

## 使用 pip 安装

```bash
pip install prismqml
```

分发名与导入名一致：装好后直接 `from prismqml import ...`。

## 平台说明

Windows 宿主在创建首个 `QQuickWindow` 前固定使用 D3D11 图形后端，无需也不应由
应用代码切换；macOS 与 Linux 保留 Qt 的平台默认图形后端。

## 开发模式安装

参与开发或试用最新主干代码时，从仓库源码以可编辑模式安装：

```bash
git clone https://github.com/aki-riko/PrismQML.git
cd PrismQML
pip install -e ".[dev]"
```

## 验证安装

```bash
python -c "import prismqml; print(prismqml.__version__)"
```

能打印出版本号即安装成功。接下来到[快速开始](getting-started.md)，用几行代码跑起第一个窗口。
