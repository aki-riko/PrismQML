# PrismQML

> **One QML component set, multiple design languages — switchable at runtime.**

PrismQML is a **multi-skin UI engine** built on PySide6 + QML: the same components render as **Fluent** or **Neobrutalism**, switched live, with 120fps+ smooth animations.

<!-- TODO: side-by-side Fluent vs Neobrutalism screenshot of the same UI -->

```python
from prismqml import setSkin, Skin

setSkin(Skin.NEOBRUTALISM)   # switch the whole app's design language in one line
```

## Why PrismQML

- **🎨 Multi-skin engine** — not yet another Fluent clone, but a skinnable engine. `setSkin()` switches between Fluent / Neobrutalism, each with light/dark.
- **🧩 Token-driven architecture** — colors, geometry, shadows all via tokens. New skins drop in with near-zero component changes; skins and components are decoupled.
- **⚡ Pure QML rendering** — no frame-rate cap, 120fps+ smooth animations.
- **🐍 PySide6-native** — seamless integration, business logic stays on the Python side, no C++.
- **📦 Full component set** — buttons / inputs / cards / dialogs / tables / charts / navigation.
- **🌍 Cross-platform** — Windows, macOS, Linux.

## Installation

```bash
pip install prismqml
```

Distribution name matches import name: after `pip install prismqml`, use `from prismqml import ...`.

## Next steps

- [Getting Started](getting-started.md) — run your first window in a few lines
- [Skins](guide/skins.md) — PrismQML's signature capability
- [Components](components/index.md) — all available controls

---

PrismQML evolved from [FluentQML](https://github.com/aki-riko/FluentQML) (now a multi-skin engine). MIT licensed.
