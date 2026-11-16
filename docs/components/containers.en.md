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

## BottomSheet

An in-window sheet that slides up from the bottom and stacks. Each newly opened sheet
covers the previous one; the sheets below shrink, move up and dim, with their top edge
peeking above the sheet on top. Drag the top handle to expand, collapse or close.

Declare one `BottomSheet` inside another to nest them:

```qml
import PrismQML as Fluent

Fluent.BottomSheet {
    id: settingsSheet
    Fluent.Button { text: "Advanced"; onClicked: advancedSheet.open() }

    Fluent.BottomSheet {
        id: advancedSheet
        detent: Fluent.Enums.sheet.detent_large
        // content
    }
}
```

| Member | Description |
|--------|-------------|
| `open()` / `close()` | Open or close. Closing a sheet also closes the sheets declared inside it |
| `detent: int` | Resting height: `Enums.sheet.detent_medium` (half the window height, default) or `detent_large` (nearly full) |
| `allowLargeDetent: bool` | Whether dragging up or tapping the handle can reach `detent_large`; default `true` |
| `showGrabber: bool` | Whether the top handle is shown; default `true` |
| `expand()` / `collapse()` | Switch to `detent_large` / `detent_medium` |
| `sheetWidthRatio: real` | Sheet width as a fraction of the window width, default `0.9`; centered horizontally |
| `opened: bool` | Read-only; whether the sheet is open |
| `stackIndex: int` | Read-only; position in the window's stack, bottom first, from 0; `-1` once fully closed |

Interaction rules:

- Only the top sheet's handle drags. Dragging down past a quarter of the resting height,
  or flicking down, closes the sheet (from `detent_large` it first collapses to
  `detent_medium`); dragging up expands it.
- `Escape` and a scrim click close only the top sheet. Focus returns to the sheet below,
  so repeated `Escape` presses close the stack one sheet at a time.
- Only the bottom sheet draws the scrim, so the page never gets darker as sheets stack.
  Beyond three levels the lowest sheets fade out.
- Sheets reparent to the window content item, so parent containers do not clip them;
  they never extend past the host window.

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
