# Containers

Layout and container controls.

## Layout

- `Layout` / `RowFit` / `VBoxLayout` — layout containers
- `SplitPane` — draggable split panel
- `ScrollArea` — scroll area (smooth scrolling + custom scrollbar)

## SkinScope

Apply a different design language to one subtree while preserving the global
skin and user configuration:

```qml
import PrismQML as Fluent

Fluent.SkinScope {
    skin: "vintage_ticket"
    Fluent.Card { }
}
```

An empty `skin` follows the nearest parent scope. Most content needs no manual
token wiring; use `skinContext: scope.context` only when a popup or dialog is
declared outside the scope.

## Separator

```qml
import PrismQML as Fluent

Fluent.Separator { }                    // horizontal, auto-fill
Fluent.Separator { type: 1 }            // vertical
```

## GroupBox

```qml
Fluent.GroupBox {
    title: "Group"
    // content
}
```

## Drawer

Edge-slide panel.

## Timeline

Virtualized timeline (no frame drops on large datasets).

## RefreshContainer

Wraps pull-to-refresh around content. The container auto-detects the first
`Flickable` inside the content as the scroll surface, takes over the vertical
gesture only while that surface sits at its top, and otherwise hands scrolling
back untouched.

```qml
import PrismQML as Fluent

Fluent.RefreshContainer {
    refreshing: model.refreshing          // host-owned state
    onRefreshRequested: model.reload()
    ListView { model: model.items }       // content goes through the default property
}
```

| Member | Meaning |
|--------|---------|
| `refreshing: bool` | Host-owned. The container sets it `true` when a refresh starts; **the host must set it back to `false`** (do not bind it) |
| `pullThreshold: int` | Pull distance that arms a refresh, defaults to `Enums.controlSize.refreshPullThreshold` |
| `interactionEnabled: bool` | Whether the pull gesture is allowed |
| `target: Flickable` | Explicit scroll surface; auto-detected when empty |
| `progress / armed / indicatorVisible` | Read-only: pull progress, whether it is armed, indicator visibility |
| `refreshRequested()` | Emitted when the pull arms or `requestRefresh()` is called |
| `requestRefresh()` | Start a refresh programmatically |

The indicator is centered above the container top and slides in with the
displacement; the read-only state is available for custom drawing. The scroll
surface is re-detected when the content children change, so no manual rebinding
is needed (or pin it explicitly with `target`).

## Skin adaptation

Under neo: GroupBox / Drawer and other containers get thick black borders; Separator uses black or medium-gray depending on context (lightweight dividers use gray to avoid scroll shimmer).
