import QtQuick
import QtQuick.Window
import PrismQML
import "../../fluentqml/PrismQML/controls/dialogs"
import "../../fluentqml/PrismQML/controls/buttons/Button"
import "../../fluentqml/PrismQML/controls/data"

// Test: MessageBox inside a component should overlay entire window
// 测试：组件内的MessageBox应该覆盖整个窗口
Window {
    id: mainWindow
    visible: true
    width: 800
    height: 600
    title: "MessageBox Overlay Test"
    color: Enums.backgroundColor
    
    // Left panel - a component containing a MessageBox
    // 左侧面板 - 包含MessageBox的组件
    Rectangle {
        id: leftPanel
        width: 300
        height: 400
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: Enums.spacing.xxl
        color: Enums.cardColor
        radius: Enums.radius.large
        
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.l
            
            Label {
                text: "Left Panel (300x400)"
                type: Enums.label.type_subtitle
            }
            
            ButtonCore {
                text: "Show MessageBox"
                style: Enums.button.style_primary
                onClicked: messageBox.open()
            }
            
            Label {
                text: "MessageBox should overlay\nentire window, not just\nthis panel."
                type: Enums.label.type_body
                color: Enums.secondaryForeground
            }
        }
        
        // MessageBox inside component
        // 组件内的MessageBox
        MessageBox {
            id: messageBox
            title: "Test Dialog"
            content: "This MessageBox is defined inside the left panel,\nbut should overlay the entire window."
        }
    }
    
    // Right panel - for reference
    // 右侧面板 - 作为参照
    Rectangle {
        id: rightPanel
        width: 300
        height: 400
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Enums.spacing.xxl
        color: Enums.cardColor
        radius: Enums.radius.large
        
        Label {
            anchors.centerIn: parent
            text: "Right Panel\n(Should be covered\nby MessageBox mask)"
            type: Enums.label.type_body
            horizontalAlignment: Text.AlignHCenter
        }
    }
    
    // Status text
    Label {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: Enums.spacing.xxl
        text: "Click 'Show MessageBox' - mask should cover BOTH panels"
        type: Enums.label.type_caption
        color: Enums.secondaryForeground
    }
}
