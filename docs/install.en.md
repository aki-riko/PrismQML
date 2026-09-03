# Installation

## Requirements

- Python 3.9+
- PySide6 6.9+ (Qt 6.9+) — installed automatically together with PrismQML

## Install with pip

```bash
pip install prismqml
```

The distribution name matches the import name: after installing, use
`from prismqml import ...` directly.

## Platform notes

On Windows, the host pins the D3D11 graphics backend before the first
`QQuickWindow`; application code does not need to and should not switch
backends. macOS and Linux retain Qt's platform-default graphics backend.

## Development install

To contribute or try the latest code on main, install in editable mode from
the repository:

```bash
git clone https://github.com/aki-riko/PrismQML.git
cd PrismQML
pip install -e ".[dev]"
```

## Verify the installation

```bash
python -c "import prismqml; print(prismqml.__version__)"
```

If the command prints a version number, the installation is working. Head to
[Getting started](getting-started.md) to bring up your first window in a few
lines of code.
