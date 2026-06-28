import QtQuick
import PrismQML

// demo 数据页: 用 C++ 注入的 UserModel(SqlListModel) 驱动 ListView
// 验证 C++ QAbstractListModel 的 roleNames(name/role) -> QML 数据流
Rectangle {
    color: Enums.backgroundColor

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 12

        Text {
            text: "用户列表 (来自 C++ SqlListModel, 共 " +
                  (UserModel ? UserModel.count : 0) + " 行)"
            color: Enums.accentColor
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.title
        }

        ListView {
            width: parent.width
            height: parent.height - 60
            clip: true
            model: UserModel
            spacing: 6
            delegate: Rectangle {
                width: ListView.view.width
                height: 48
                radius: 6
                color: Enums.isDark ? "#2a2a2a" : "#f5f5f5"
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    spacing: 20
                    Text {
                        text: (model.name !== undefined ? model.name : "")
                        color: Enums.foregroundColor
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                        width: 120
                    }
                    Text {
                        text: (model.role !== undefined ? model.role : "")
                        color: Enums.accentColor
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.body
                    }
                }
            }
        }
    }
}
