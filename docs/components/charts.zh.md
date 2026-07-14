# 图表

## ChartView

```qml
import PrismQML as Fluent

Fluent.ChartView {
    // 图表配置
}
```

支持柱状图、折线图、饼图等，含数据缩放（ChartDataZoom）。图表配色随主题与皮肤适配。

`animated: true` 时，滚轮或程序修改 `viewportStart` / `viewportEnd` 会让实际图表内容平滑过渡；拖动主图或缩放手柄时保持实时跟手。设置 `animated: false` 可关闭过渡。

## 皮肤适配

新粗野下图表的坐标轴、网格、数据系列配色会切换到 neo 高饱和调色板。
