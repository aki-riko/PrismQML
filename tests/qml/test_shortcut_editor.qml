import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/inputs"
import "../../prismqml/PrismQML/controls/data"

Window {
    width: 500
    height: 400
    visible: true
    title: "ShortcutEditor Test"
    color: Enums.backgroundColor
    
    Column {
        anchors.centerIn: parent
        spacing: 20
        
        Label {
            type: Enums.label.type_title
            text: "快捷键选择器"
        }
        
        // With shortcut 有快捷键
        ShortcutEditor {
            id: picker1
            shortcut: "Ctrl+Shift+A"
            onShortcutRecorded: (s) => console.log("Recorded:", s)
        }
        
        // Empty 空状态
        ShortcutEditor {
            id: picker2
            onShortcutRecorded: (s) => console.log("Recorded:", s)
        }
        
        Label {
            type: Enums.label.type_body
            text: "点击铅笔图标，然后按快捷键组合"
            color: Enums.textColor.secondary
        }
    }
}
