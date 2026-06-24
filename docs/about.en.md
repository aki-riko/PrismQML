# About

## What is PrismQML

PrismQML is a multi-skin UI engine built on PySide6 + QML, **evolved from FluentQML** — from a single Fluent Design component library into a skinnable engine supporting multiple design languages (Fluent + Neobrutalism).

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

The API is fully compatible — migration is just a rename.

## Why the rename

The name `FluentQML` locked the library to a single "Fluent" design language. After adding the Neobrutalism skin, it became a multi-skin engine, making the name a misnomer. Since PyPI / GitHub don't support repo renames, PrismQML was created anew (the name evokes a prism — one beam of light refracted into many faces, mirroring one component set rendering multiple design languages). The old FluentQML repo is archived, and the published `fqml` package remains available.

## License

PrismQML is under the [MIT License](https://github.com/aki-riko/PrismQML/blob/main/LICENSE). The bundled Fluent UI System Icons set is also MIT.
