# Charts

## ChartView

```qml
import PrismQML as Fluent

Fluent.ChartView {
    // chart configuration
}
```

Supports bar, line, pie charts, etc., with data zoom (ChartDataZoom). Chart colors adapt to theme and skin.

When `animated: true`, wheel zoom and programmatic changes to `viewportStart` / `viewportEnd` smoothly transition the rendered chart content. Direct chart or handle dragging remains immediate. Set `animated: false` to disable the transition.

## Skin adaptation

Under neo, the chart's axes, grid, and data series switch to the neo high-saturation palette.
