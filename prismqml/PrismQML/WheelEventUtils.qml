// WheelEventUtils - Normalize Qt wheel deltas across system direction settings
// WheelEventUtils - 统一不同系统滚轮方向设置下的 Qt 滚轮增量
pragma Singleton

import QtQml

QtObject {
    // ==================== Public Methods 公开方法 ====================
    function verticalDelta(event) {
        if (!event || !event.angleDelta) return 0
        var delta = event.angleDelta.y
        return event.inverted === true ? -delta : delta
    }

    function horizontalDelta(event) {
        if (!event || !event.angleDelta) return 0
        var delta = event.angleDelta.x
        return event.inverted === true ? -delta : delta
    }
}
