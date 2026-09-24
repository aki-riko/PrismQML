# Navigation

## NavigationBar / NavigationView

The main window's side navigation; compact/expanded form is decided by the [window](../guide/windows.md) `WindowType`. Use `window.addPage()` to add nav items.

### Standalone use inside a page

Both are plain `Item`s, so they can be placed in a page without the window shell (the Gallery's "Vertical navigation" section does exactly that). Two things matter when you do:

**① Selection is a single-direction binding: the host must push it back.** A panel only emits `itemClicked(index)` and never writes `currentIndex` itself — that keeps the "window → navigation" binding one-way:

```qml
NavigationView {
    model: [
        { key: "home", text: "Home", icon: ... },
        { key: "docs", text: "Documents", icon: ... }
    ]
    onItemClicked: (index) => currentIndex = index   // inside a page, this IS the host shell
}
```

`ToggleNavigationBar` does not derive from that base and updates `currentIndex` on its own, so it needs no wiring.

**② `titleBarHeight` defaults to the window title-bar height.** A page has no title bar, so leaving it alone reserves dead space at the top (measured at 48px, which pushes every row down):

```qml
NavigationView {
    titleBarHeight: 0        // no title bar inside a page
    showReturnButton: false  // and no return button either
}
```

## SegmentedControl / Pivot

Both share the `items` model (`{ key, text, icon }` or plain strings) and `currentIndex`, and lay out horizontally by default:

```qml
Fluent.SegmentedControl { items: ["General", "Appearance", "Advanced"] }
Fluent.Pivot { items: [{ key: "docs", text: "Documents" }, { key: "img", text: "Images" }] }
```

`orientation: Qt.Vertical` stacks the cells and turns the bottom underline into a bar pinned to the left edge:

```qml
Fluent.SegmentedControl {
    orientation: Qt.Vertical
    items: ["General", "Appearance", "Advanced"]
}
```

Vertical cells are sized to their content (they do not stretch), and the control is as wide as its widest cell. For a full-width vertical list use `NavigationView` or `ToggleNavigationBar`.

## TabBar / TabWidget

```qml
import PrismQML as Fluent

Fluent.TabWidget {
    // tabs + content
}
```

Horizontal (the default) supports drag reordering, scrolling, closing and an add button. `TabBar` renders the tabs only; page content belongs to the caller or to `TabWidget`.

`orientation: Qt.Vertical` moves the tab column to the leading edge, leaving the rest of the area to the pages:

```qml
Fluent.TabWidget {
    orientation: Qt.Vertical
    width: 360
    height: 220
    tabs: [ { title: "One", content: page1 }, { title: "Two", content: page2 } ]
}
```

Vertical behaviour: rows fill the column width and take the **row height** (`tabWidth`, when set, becomes the row height), long titles elide, the close button sits at the trailing edge, drag reordering runs along the column, the add button lands at the end of the column, and overflow scrolls on Y. The column width comes from `Enums.controlSize.tabBarVerticalWidth`.

## Breadcrumb

Hierarchical path navigation.

## PipsPager

```qml
Fluent.HorizontalPipsPager { count: 5; currentIndex: 0 }
Fluent.VerticalPipsPager { count: 4 }
```

Supports paging buttons and visible-count limits.

## Skin adaptation

Under neo: the selected nav item becomes a **solid orange block + black border + white icon/text** (replacing Fluent's light highlight + sliding indicator); the TabWidget's selected tab is white with a thick black border + hard shadow; pager dots are orange when selected, black otherwise.
