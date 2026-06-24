# 标签

小型标签/徽章/筹码。

## Badge 徽章

```qml
import PrismQML as Fluent

Fluent.Badge { count: 8; level: Fluent.Enums.statusLevel.error }    // 计数
Fluent.Badge { text: "NEW"; level: Fluent.Enums.statusLevel.success } // 文字
Fluent.Badge { dot: true }                                          // 红点
```

`level`：info / success / warning / error / attention / processing。

## Tag 标签

```qml
Fluent.Tag { text: "标签" }
```

## Chip 筹码

```qml
Fluent.Chip { text: "可选"; checked: true; closable: true }
```

支持选中态、关闭按钮。

## 皮肤适配

新粗野下：徽章/标签/筹码黑粗边；徽章语义色用高饱和版本；Chip 选中橙底、未选白底，均带黑边 + 硬阴影。
