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

### Pane display mode

`paneDisplayMode` lets the pane decide its own form instead of hand-managing `isExpanded`:

| Mode | Behaviour |
|---|---|
| `Enums.navigation.pane_unspecified` (default) | Never touches `isExpanded`; behaviour is exactly as before |
| `pane_auto` | Expanded while the pane is at least `Enums.controlSize.navPanelExpandWidth` wide, compact otherwise |
| `pane_left` | Always the expanded sidebar |
| `pane_left_compact` | Always the compact icon rail |
| `pane_left_minimal` | Collapsed to the menu button; `openPane()` / `togglePane()` reveal the rail in place, and the menu button toggles it |

```qml
Fluent.NavigationView {
    paneDisplayMode: Enums.navigation.pane_auto
    // with pane_left_minimal use isPaneOpen / openPane() / closePane() / togglePane()
}
```

Once a mode is set, the mode owns `isExpanded` — "expanded or not" is exactly what it decides. Only `pane_unspecified` opts out and leaves the value to the caller.

A top strip is deliberately out of `paneDisplayMode`'s scope: that belongs to the window shell, and `WindowsBar` currently hosts it with `NavigationBar`.

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

## SelectorBar

A chrome-less selector: the strip sits directly on the page and only the selected cell
carries a sliding pill. It fits switching between a small set of views (2–5), reading
lighter than `SegmentedControl` and flatter than `TabBar`.

```qml
Fluent.SelectorBar {
    items: [
        { key: "overview", text: "Overview" },
        { key: "activity", text: "Activity", icon: "History" },
        { key: "about", text: "About" }
    ]
    onItemClicked: (index, byUser) => view.push(pages[index])
}
```

| Member | Meaning |
|--------|---------|
| `items: var` | `{ key, text, icon }` or plain strings |
| `currentIndex: int` | Selected index; an out-of-range value hides the pill instead of throwing |
| `orientation` | `Qt.Horizontal` (default) / `Qt.Vertical`; vertical stacks content-sized cells |
| `itemFontSize / iconSize` | Cell text and icon size |
| `pillAnimationEnabled` | Whether the pill slides; the first snap is never animated |
| `scrollDuration` | Programmatic pan duration, defaults to `Enums.duration.scroll` (same as TabBar / scroll areas) |
| `scrollable / maxScrollOffset / scrollOffset` | Read-only: horizontal overflow and the current scroll position |
| `itemClicked(index, byUser)` | User click (`byUser` is `true`); programmatic selection never emits it |
| `currentItemChanged(key)` | Selected key changed |
| `setCurrentIndex(idx) / setCurrentItem(key)` | Programmatic selection; out-of-range or unknown values are ignored |
| `addItem(key, text, icon) / getCurrentKey()` | Append an item / read the current key |
| `revealCurrent()` | Scroll the selected cell into view (also runs on selection change; minimal scroll, cell-boundary aligned) |

A horizontal strip scrolls when it does not fit: the selected cell is scrolled into view by the
smallest amount that fits it, preferring a cell boundary as the leading edge so the strip never
leaves a half-cut label behind. The wheel or a drag pans the strip. Programmatic movement (wheel,
auto-reveal) runs through the repository's shared smooth-scroll engine, so it glides rather than
teleports; `scrollDuration` tunes it. Wheel ownership matches `TabBar` — an overflowing strip
consumes the wheel itself, while a strip that fits never competes and lets the wheel reach the
page scroll area. A vertical strip does not scroll and is sized to its content.

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

Vertical behaviour: rows fill the column width and take the **row height** (`tabWidth`, when set, becomes the row height), long titles elide, the close button sits at the trailing edge, drag reordering runs along the column, the add button lands at the end of the column, and overflow scrolls on Y. The column width defaults to `Enums.controlSize.tabBarVerticalWidth` and can be overridden with the public `stripWidth` property (the horizontal counterpart is `tabBarHeight`; `TabWidget` proxies `stripWidth` too).

## CommandPalette

A Ctrl+K style command surface: modal overlay + search field + ranked result list. Filtering, fuzzy matching, group headers, match highlighting and ↑↓ navigation are reused from the library's search stack (`SearchResultList`); this component owns only opening, the scrim, focus and command dispatch.

```qml
Fluent.CommandPalette {
    id: palette
    shortcut: "Ctrl+K"                        // optional global shortcut; empty disables it
    placeholderText: "Type a command..."
    hintText: "Up/Down navigate  Enter run  Esc close"   // empty hides the footer
    items: [
        { key: "open-file", title: "Open File", subtitle: "Ctrl+O",
          section: "File", icon: Enums.iconPath + "FolderOpen.svg" },
        { key: "toggle-theme", title: "Toggle Theme", keywords: ["dark", "light"] }
    ]
    onCommandTriggered: (key, item) => runCommand(key)
}
```

- **Open**: `open()` / `toggle()`, or the `shortcut`. Every open clears the query and takes the keyboard into the search field.
- **Close**: `Esc`, a scrim click, or `close()`. Running a command closes first and then emits `onCommandTriggered(key, item)`, so the host sees a settled state.
- **Data**: each `items` entry accepts `key / title / subtitle / icon / section / keywords / enabled`; a non-empty `section` plus `sectionHeaders: true` groups the list.
- **Copy**: `placeholderText` / `emptyText` / `hintText` are injected by the caller; nothing is hard-coded.
- **Key routing**: while open, ↑ / ↓ / Enter / Esc are window-level shortcuts — the search field holds the focus and its inner text input swallows arrow keys before they can bubble to the panel.

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
