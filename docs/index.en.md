<div class="prismqml-hero" markdown>

<span class="hero-eyebrow">PRISMQML</span>

# One QML control set, <em>four design languages</em>

<p class="hero-sub">PrismQML is a multi-skin UI engine built on PySide6 + QML:
the same controls switch between Fluent, Neobrutalism, Vintage Ticket and
Neumorphism at runtime, with independent light/dark theming. One
<code>setSkin()</code> call reskins the whole app at 120fps+.</p>

<div class="hero-actions" markdown>
[Get Started :material-arrow-right:](getting-started.md){ .md-button }
[Skins :material-palette:](guide/skins.md){ .md-button .hero-btn-ghost }
[Components](components/index.md){ .md-button .hero-btn-ghost }
</div>

</div>

<div class="prismqml-grid" markdown>

<div class="prismqml-card" markdown>

<span class="card-icon icon-blue" markdown>:material-palette:</span>

### :material-palette: Multi-skin engine

One `setSkin()` call switches Fluent / Neobrutalism / Vintage Ticket /
Neumorphism — all skins ship light & dark.

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-teal" markdown>:material-puzzle:</span>

### :material-puzzle: Token-driven

Colors, geometry and shadows are all tokens. Adding a skin barely touches
control code — skins and controls stay decoupled.

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-orange" markdown>:material-lightning-bolt:</span>

### :material-lightning-bolt: Pure QML rendering

No frame-rate cap, 120fps+ animations, business logic stays in Python.

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-purple" markdown>:material-package-variant:</span>

### :material-package-variant: 180+ QML types

Buttons, inputs, cards, dialogs, tables, charts, navigation and more.

</div>

</div>

## Four skins

<div class="prismqml-skins" markdown>

<div class="prismqml-skin-card skin-fluent" markdown>

<span class="skin-dot"></span>

### Fluent

Rounded corners, soft shadows, blue accent, optional Mica effect.

</div>

<div class="prismqml-skin-card skin-neobrutalism" markdown>

<span class="skin-dot"></span>

### Neobrutalism

Thick borders, zero-blur hard shadows, orange accent that flattens on press.

</div>

<div class="prismqml-skin-card skin-vintage" markdown>

<span class="skin-dot"></span>

### Vintage Ticket

Warm paper, old-ink foreground and stamp semantic colors with hairline rules.

</div>

<div class="prismqml-skin-card skin-neumorphism" markdown>

<span class="skin-dot"></span>

### Neumorphism

Same-color surfaces, dual soft shadows, embossed interactions.

</div>

</div>

![PrismQML four skins side by side](images/prismqml-skins.png)

## Installation

```bash
pip install prismqml
```

The distribution name matches the import name: `pip install prismqml` then
`from prismqml import ...`. Requires Python 3.9+ and PySide6 6.9+ (Qt 6.9+).
Windows hosts pin D3D11 before the first `QQuickWindow`; other platforms keep
Qt's default backend.

```python
from prismqml import App, WindowType, setSkin, Skin

setSkin(Skin.NEOBRUTALISM)   # one line, whole app reskinned

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("My App")
window.resize(1200, 800)
window.show()
app.exec()
```

## Next steps

- [Getting started](getting-started.md) — first window in a few lines
- [Installation](install.md) — pip install & dev setup
- [Skin system](guide/skins.md) — the signature capability
- [Components](components/index.md) — everything available
- [Component cheat sheet](components/list.md) — quick index of all types by category
- [Auto update](auto-update.md) — check, download progress, install handoff

---

PrismQML evolved from [FluentQML](https://github.com/aki-riko/FluentQML) into a
multi-skin engine. MIT licensed.
