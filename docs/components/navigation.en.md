# Navigation

## NavigationBar / NavigationView

The main window's side navigation; compact/expanded form is decided by the [window](../guide/windows.md) `WindowType`. Use `window.addPage()` to add nav items.

## TabWidget

```qml
import PrismQML as Fluent

Fluent.TabWidget {
    // tabs + content
}
```

Supports drag reordering, scrolling, and closing.

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
