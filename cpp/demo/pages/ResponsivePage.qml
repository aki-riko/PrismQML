import QtQuick
import PrismQML

// 响应式适配示范页: 展示如何用 C++ 注入的 PlatformInfo 做触摸/窄屏适配
// 这是"控件该如何适配移动端"的可运行范本(不改引擎存量, 供适配时参考)
Rectangle {
    id: page
    color: Enums.backgroundColor

    // 防御式读取 PlatformInfo (桌面无强制时 isTouch=false)
    readonly property bool touch: typeof PlatformInfo !== "undefined" && PlatformInfo.isTouch
    readonly property bool compact: typeof PlatformInfo !== "undefined" && PlatformInfo.isCompact
    readonly property int btnH: typeof PlatformInfo !== "undefined" ? PlatformInfo.touchTargetSize : 32
    readonly property string plat: typeof PlatformInfo !== "undefined" ? PlatformInfo.platformName : "?"
    // 软键盘高度: 键盘弹出时输入框上移避让 (随 keyboardChanged 自动更新)
    readonly property int kbH: typeof PlatformInfo !== "undefined" ? PlatformInfo.keyboardHeight : 0

    Column {
        anchors.centerIn: parent
        spacing: 16
        width: Math.min(parent.width - 48, 600)

        Text {
            text: "响应式适配示范"
            color: Enums.accentColor
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.title
        }
        Text {
            text: "平台=" + page.plat + " | 触摸=" + page.touch +
                  " | 窄屏=" + page.compact + " | 触摸目标=" + page.btnH + "px"
            color: Enums.foregroundColor
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.body
            wrapMode: Text.WordWrap
            width: parent.width
        }

        // 按钮高度随触摸态自适应 (桌面32 / 触摸48)
        Rectangle {
            width: parent.width
            height: page.btnH
            radius: 6
            color: Enums.accentColor
            Text {
                anchors.centerIn: parent
                text: "自适应按钮 (高 " + page.btnH + "px)"
                color: "white"
                font.family: Enums.fontFamily
            }
        }

        // 布局随窄屏切换: 宽屏横排 / 窄屏竖排
        Flow {
            width: parent.width
            spacing: 8
            Repeater {
                model: 3
                Rectangle {
                    width: page.compact ? parent.width : (parent.width - 16) / 3
                    height: page.btnH
                    radius: 6
                    color: Enums.isDark ? "#333" : "#e0e0e0"
                    Text {
                        anchors.centerIn: parent
                        text: "项 " + (index + 1)
                        color: Enums.foregroundColor
                        font.family: Enums.fontFamily
                    }
                }
            }
        }
    }

    // 软键盘避让示范: 输入框贴底, 键盘弹出时上移 kbH 不被遮挡
    Rectangle {
        id: inputBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: page.kbH   // 键盘高度避让
        height: 56
        color: Enums.isDark ? "#2a2a2a" : "#f0f0f0"
        Behavior on anchors.bottomMargin { NumberAnimation { duration: 150 } }

        TextInput {
            id: ti
            anchors.fill: parent
            anchors.margins: 16
            verticalAlignment: Text.AlignVCenter
            color: Enums.foregroundColor
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.body
            clip: true
            Text {
                anchors.fill: parent
                anchors.margins: parent.anchors ? 0 : 0
                verticalAlignment: Text.AlignVCenter
                text: "点此输入(测软键盘避让, kbH=" + page.kbH + ")"
                color: Enums.foregroundColor
                opacity: 0.4
                visible: !ti.text && !ti.activeFocus
                font.family: Enums.fontFamily
            }
        }
    }
}
