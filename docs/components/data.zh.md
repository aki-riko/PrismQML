# 数据

列表、表格、树、轮播等数据展示控件。

## TableView / TableWidget 表格

```qml
import PrismQML as Fluent

Fluent.TableWidget {
    // 列定义 + model 数据
    sortingEnabled: true       // 配置 role 的列可点击表头排序
}
```

启用 `sortingEnabled` 后，带有 `role` 的列支持点击表头在升序/降序之间切换；也可以通过
`toggleSort(column)` 或兼容的 `sortItems(column, order)` 程序控制排序。

高性能表格底层有 Rust 加速（`prismqml_rs`，SQLite 分页），见 [SqlListModel](../api/python.md)。

## ListView / ListWidget 列表

```qml
Fluent.ListWidget {
    model: ["列表项 1", "列表项 2", "列表项 3"]
}
```

## TreeView / TreeWidget 树

```qml
Fluent.TreeWidget {
    model: [
        { text: "技术部", expanded: true, children: [
            { text: "前端组" }, { text: "后端组" }
        ]}
    ]
}
```

## Carousel 轮播

```qml
Fluent.Carousel {
    model: [...]   // 图片/内容列表
}
```

支持 peek（露边）/ slide 两种效果，横向/纵向。

## Avatar 头像

```qml
Fluent.Avatar { source: "avatar.png"; size: 48 }
Fluent.Avatar { text: "张"; size: 48 }   // 文字头像
```

## 皮肤适配

新粗野下：列表/表格/树容器粗黑边 + 硬阴影；列表选中项淡橙底；头像圆形黑边。
