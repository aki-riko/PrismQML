import QtQuick
import PrismQML

// demo 页面: 验证 C++ addPage 能加载页面并应用主题 token
Rectangle {
    color: Enums.backgroundColor
    Text {
        anchors.centerIn: parent
        text: "首页 Home\naccentColor = " + Enums.accentColor
        color: Enums.accentColor
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.title
        horizontalAlignment: Text.AlignHCenter
    }
}
