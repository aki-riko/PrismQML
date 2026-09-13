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

## Skin adaptation

Under neo: GroupBox / Drawer and other containers get thick black borders; Separator uses black or medium-gray depending on context (lightweight dividers use gray to avoid scroll shimmer).
