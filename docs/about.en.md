# About

## What is PrismQML

PrismQML is a multi-skin UI engine built on PySide6 + QML, **evolved from
FluentQML** from a single Fluent Design component library into an engine for
Fluent, Neobrutalism, Vintage Ticket, and Neumorphism.

## Key features

- **Multi-skin engine**: one `setSkin()` call switches between Fluent,
  Neobrutalism, Vintage Ticket and Neumorphism — all with light & dark themes
- **Token-driven**: colors, geometry and shadows are all theme tokens; skins
  and controls stay decoupled, so adding a skin barely touches control code
- **Pure QML rendering**: all control rendering happens in QML — no
  frame-rate cap, smooth animations
- **Native PySide6**: create windows, register types and write business logic
  straight from Python — no C++ needed for application UIs
- **180+ QML types**: buttons, inputs, cards, dialogs, tables, charts,
  navigation and more
- **Complete desktop capabilities**: config persistence, reactive state,
  system tray, Mica effect and auto update out of the box
- **Cross-platform**: Windows, macOS and Linux

## Four design languages

PrismQML ships four complete design languages. The same control code reskins
as a whole without modification, and every skin supports light & dark themes:

- **Fluent**: rounded corners, soft shadows, blue accent
- **Neobrutalism**: thick borders, hard shadows, orange accent
- **Vintage Ticket**: warm paper, old-ink foreground, hairline rules and stamp
  semantic colors
- **Neumorphism**: same-color surfaces, dual soft shadows, embossed
  interactions

See the [skin system](guide/skins.md) for the token structure and
customization of each skin.

## Project info

- **Author**: aki-riko
- **License**: MIT
- **Origin**: a multi-skin engine evolved from FluentQML
- **GitHub**: [github.com/aki-riko/PrismQML](https://github.com/aki-riko/PrismQML)
- **Docs**: [aki-riko.github.io/PrismQML](https://aki-riko.github.io/PrismQML/)

## Migrating from FluentQML

If you're using the old FluentQML (PyPI package `fqml`, import name `fluentqml`), to migrate to PrismQML:

| Old (FluentQML) | New (PrismQML) |
|-----------------|----------------|
| `pip install fqml` | `pip install prismqml` |
| `import fluentqml` | `import prismqml` |
| `from fluentqml import App` | `from prismqml import App` |
| QML `import FluentQML` | QML `import PrismQML` |
| `~/.fluentqml/` | `~/.prismqml/` |

Steps:

1. `pip uninstall fqml && pip install prismqml`
2. Global replace `fluentqml` → `prismqml` (Python), `FluentQML` → `PrismQML` (QML)
3. In requirements, `fqml` → `prismqml`

Package, import, and QML module names are the core migration steps. PrismQML
does not retain deprecated compatibility aliases before v1.0.0. Projects that
used FluentQML internal paths or removed APIs should migrate against the current
[Python API](api/python.md) and [component overview](components/index.md).

## Why the rename

The name `FluentQML` locked the library to a single "Fluent" design language. After adding the Neobrutalism skin, it became a multi-skin engine, making the name a misnomer. Since PyPI / GitHub don't support repo renames, PrismQML was created anew (the name evokes a prism — one beam of light refracted into many faces, mirroring one component set rendering multiple design languages). The old FluentQML repo is archived, and the published `fqml` package remains available.

## License

PrismQML is under the [MIT License](https://github.com/aki-riko/PrismQML/blob/main/LICENSE). The bundled Fluent UI System Icons set is also MIT.
