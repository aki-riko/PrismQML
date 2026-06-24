# Data

List, table, tree, and carousel data-display controls.

## TableView / TableWidget

```qml
import PrismQML as Fluent

Fluent.TableWidget {
    // column definitions + model data
}
```

The high-performance table has a Rust backend (`prismqml_rs`, SQLite paging) for acceleration.

## ListView / ListWidget

```qml
Fluent.ListWidget {
    model: ["Item 1", "Item 2", "Item 3"]
}
```

## TreeView / TreeWidget

```qml
Fluent.TreeWidget {
    model: [
        { text: "Engineering", expanded: true, children: [
            { text: "Frontend" }, { text: "Backend" }
        ]}
    ]
}
```

## Carousel

```qml
Fluent.Carousel {
    model: [...]   // list of images/content
}
```

Supports peek / slide effects, horizontal or vertical.

## Avatar

```qml
Fluent.Avatar { source: "avatar.png"; size: 48 }
Fluent.Avatar { text: "Z"; size: 48 }   // text avatar
```

## Skin adaptation

Under neo: list/table/tree containers have thick black borders + hard shadows; selected list items get a light-orange background; avatars get circular black borders.
