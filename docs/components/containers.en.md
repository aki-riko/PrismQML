# Containers

Layout and container controls.

## Layout

- `Layout` / `RowFit` / `VBoxLayout` — layout containers
- `SplitPane` — draggable split panel
- `ScrollArea` — scroll area (smooth scrolling + custom scrollbar)

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
