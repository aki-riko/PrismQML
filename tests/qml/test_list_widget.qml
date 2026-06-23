import QtQuick
import QtQuick.Window
import PrismQML as Fluent
import "../../fluentqml/PrismQML/controls/data/List"

// Test ListWidget - 测试列表控件
Window {
    id: window
    width: 400
    height: 500
    visible: true
    title: "ListWidget Test"
    color: Fluent.Enums.backgroundColor
    
    Column {
        anchors.fill: parent
        anchors.margins: Fluent.Enums.spacing.xl
        spacing: Fluent.Enums.spacing.l
        
        // Title 标题
        Text {
            text: "ListWidget Test 列表控件测试"
            font.family: Fluent.Enums.fontFamily
            font.pixelSize: Fluent.Enums.typography.title
            color: Fluent.Enums.textColor.primary
        }
        
        // Simple string list 简单字符串列表
        Text {
            text: "Simple List 简单列表:"
            font.family: Fluent.Enums.fontFamily
            font.pixelSize: Fluent.Enums.typography.body
            color: Fluent.Enums.textColor.secondary
        }
        
        ListWidget {
            id: simpleList
            width: 300
            height: 180
            model: ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
            
            onItemClicked: (index, item) => {
                console.log("Clicked:", index, item)
            }
            onCurrentItemChanged: (index, item) => {
                console.log("Current changed:", index, item)
            }
        }
        
        // Object list with icons 带图标的对象列表
        Text {
            text: "List with Icons 带图标列表:"
            font.family: Fluent.Enums.fontFamily
            font.pixelSize: Fluent.Enums.typography.body
            color: Fluent.Enums.textColor.secondary
        }
        
        ListWidget {
            id: iconList
            width: 300
            height: 180
            model: [
                { text: "Home", icon: "Home" },
                { text: "Settings", icon: "Settings" },
                { text: "Search", icon: "Search" },
                { text: "Add", icon: "Add" },
                { text: "Delete", icon: "Delete" }
            ]
            
            onItemClicked: (index, item) => {
                console.log("Icon list clicked:", index, item.text)
            }
        }
        
        // Current selection info 当前选中信息
        Text {
            text: "Simple: " + simpleList.currentIndex + " | Icon: " + iconList.currentIndex
            font.family: Fluent.Enums.fontFamily
            font.pixelSize: Fluent.Enums.typography.caption
            color: Fluent.Enums.textColor.secondary
        }
    }
}
