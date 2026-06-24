# 卡片

## Card 卡片

```qml
import PrismQML as Fluent

Fluent.Card {
    width: 280; height: 160
    // 默认插槽放内容
}
```

卡片类型 `cardType`：

| 类型 | 说明 |
|------|------|
| `type_default` | 普通卡片（无 hover 反馈） |
| `type_hover` | 悬停变色 |
| `type_elevated` | 悬浮卡（hover 阴影加大） |
| `type_header` | 带标题卡 |

```qml
Fluent.Card {
    cardType: Fluent.Enums.card.type_elevated
    width: 280; height: 160
}
```

## Expander 折叠面板

```qml
Fluent.Expander {
    title: "高级设置"
    content: "点击标题展开"
    // 默认插槽放展开内容
}
```

## 皮肤适配

- **Fluent**：圆角 + 模糊阴影，悬浮卡 hover 阴影渐变加大
- **新粗野**：粗黑边 + 硬阴影；悬浮卡 hover 时硬阴影偏移翻倍；Expander 展开区粗黑分隔线
