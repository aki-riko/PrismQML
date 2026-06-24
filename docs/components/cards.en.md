# Cards

## Card

```qml
import PrismQML as Fluent

Fluent.Card {
    width: 280; height: 160
    // default slot holds content
}
```

Card type `cardType`:

| Type | Description |
|------|-------------|
| `type_default` | Default card (no hover feedback) |
| `type_hover` | Hover color change |
| `type_elevated` | Elevated (hover enlarges shadow) |
| `type_header` | Card with title header |

```qml
Fluent.Card {
    cardType: Fluent.Enums.card.type_elevated
    width: 280; height: 160
}
```

## Expander

```qml
Fluent.Expander {
    title: "Advanced Settings"
    content: "Click the title to expand"
    // default slot holds expanded content
}
```

## Skin adaptation

- **Fluent**: rounded + blurred shadow; elevated card's shadow grows smoothly on hover
- **Neobrutalism**: thick black border + hard shadow; elevated card doubles the hard-shadow offset on hover; Expander has a thick black divider in the expanded area
