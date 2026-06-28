import QtQuick
import PrismQML

// demo 页面: 设置页
Rectangle {
    color: Enums.backgroundColor
    Text {
        anchors.centerIn: parent
        text: "设置 Settings\nskin = " + Enums.skin
        color: Enums.foregroundColor
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.subtitle
        horizontalAlignment: Text.AlignHCenter
    }
}
