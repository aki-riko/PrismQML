import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/Layout"
import "../../prismqml/PrismQML/controls/data"
import "../../prismqml/PrismQML/controls/buttons"

// FlowLayout Test - Property-based testing for FlowLayout modes
// FlowLayout测试 - 流式布局模式的属性测试
Window {
    id: root
    width: 800
    height: 600
    visible: true
    title: "FlowLayout Property Tests"
    color: Enums.backgroundColor

    // ==================== Test State 测试状态 ====================
    property int testsPassed: 0
    property int testsFailed: 0
    property int testsRun: 0
    property var testResults: []

    // ==================== Test Runner 测试运行器 ====================
    function runAllTests() {
        testsPassed = 0
        testsFailed = 0
        testsRun = 0
        testResults = []

        console.log("========== FlowLayout Property Tests ==========")

        // Property 1: Default mode preserves original dimensions
        runPropertyTest1()

        // Property 2: Wrapping behavior
        runPropertyTest2()

        // Property 4: Horizontal mode equal height per row
        runPropertyTest4()

        // Property 5: Vertical mode equal width
        runPropertyTest5()

        // Property 7: Mode switch round-trip
        runPropertyTest7()

        console.log("========== Results ==========")
        console.log("Passed: " + testsPassed + "/" + testsRun)
        console.log("Failed: " + testsFailed + "/" + testsRun)
    }

    function assert(condition, message) {
        testsRun++
        if (condition) {
            testsPassed++
            testResults.push({ passed: true, message: message })
            console.log("✓ " + message)
        } else {
            testsFailed++
            testResults.push({ passed: false, message: message })
            console.log("✗ " + message)
        }
    }

    function floatEqual(a, b, tolerance) {
        return Math.abs(a - b) < (tolerance || 0.01)
    }

    // ==================== Property 1 Test 属性1测试 ====================
    // Feature: flow-layout-enhancement, Property 1: Default Mode Preserves Original Dimensions
    // Validates: Requirements 2.3
    function runPropertyTest1() {
        console.log("\n--- Property 1: Default Mode Preserves Original Dimensions ---")

        // Test with various item sizes 测试各种尺寸的子项
        var testCases = [
            [{ w: 100, h: 50 }, { w: 80, h: 60 }, { w: 120, h: 40 }],
            [{ w: 50, h: 100 }, { w: 50, h: 50 }, { w: 50, h: 75 }],
            [{ w: 200, h: 30 }]
        ]

        for (var t = 0; t < testCases.length; t++) {
            var items = testCases[t]
            testFlowDefault.mode = Enums.flow.default_

            // Clear and add items 清空并添加子项
            testModel1.clear()
            for (var i = 0; i < items.length; i++) {
                testModel1.append({ itemWidth: items[i].w, itemHeight: items[i].h })
            }

            // Wait for layout 等待布局
            Qt.callLater(function() {
                // Verify dimensions 验证尺寸
                for (var j = 0; j < testFlowDefault.children.length; j++) {
                    var child = testFlowDefault.children[j]
                    if (child && child.objectName === "testItem") {
                        var expected = items[j]
                        assert(
                            floatEqual(child.width, expected.w) && floatEqual(child.height, expected.h),
                            "Property 1: Item " + j + " preserves size (" + expected.w + "x" + expected.h + ")"
                        )
                    }
                }
            })
        }
    }

    // ==================== Property 2 Test 属性2测试 ====================
    // Feature: flow-layout-enhancement, Property 2: Wrapping Behavior
    // Validates: Requirements 2.1, 2.2
    function runPropertyTest2() {
        console.log("\n--- Property 2: Wrapping Behavior ---")

        testFlowWrap.mode = Enums.flow.default_
        testModel2.clear()

        // Add items that should wrap 添加应该换行的子项
        // Container width is 300, items are 120 each
        testModel2.append({ itemWidth: 120, itemHeight: 50 })
        testModel2.append({ itemWidth: 120, itemHeight: 50 })
        testModel2.append({ itemWidth: 120, itemHeight: 50 }) // Should wrap

        Qt.callLater(function() {
            var items = []
            for (var i = 0; i < testFlowWrap.children.length; i++) {
                var child = testFlowWrap.children[i]
                if (child && child.objectName === "testItem") {
                    items.push({ x: child.x, y: child.y })
                }
            }

            if (items.length >= 3) {
                // First two items should be on same row (y=0)
                assert(items[0].y === 0 && items[1].y === 0, "Property 2: First two items on row 0")
                // Third item should wrap to next row
                assert(items[2].y > 0, "Property 2: Third item wraps to new row")
                assert(items[2].x === 0, "Property 2: Wrapped item starts at x=0")
            }
        })
    }

    // ==================== Property 4 Test 属性4测试 ====================
    // Feature: flow-layout-enhancement, Property 4: Horizontal Mode Equal Height Per Row
    // Validates: Requirements 3.1, 3.2, 3.3
    function runPropertyTest4() {
        console.log("\n--- Property 4: Horizontal Mode Equal Height Per Row ---")

        testFlowHorizontal.mode = Enums.flow.horizontal
        testModel3.clear()

        // Add items with different heights 添加不同高度的子项
        testModel3.append({ itemWidth: 100, itemHeight: 40 })
        testModel3.append({ itemWidth: 100, itemHeight: 80 }) // Tallest in row
        testModel3.append({ itemWidth: 100, itemHeight: 60 })

        Qt.callLater(function() {
            var heights = []
            for (var i = 0; i < testFlowHorizontal.children.length; i++) {
                var child = testFlowHorizontal.children[i]
                if (child && child.objectName === "testItem") {
                    heights.push(child.height)
                }
            }

            if (heights.length >= 3) {
                // All items in same row should have equal height (max = 80)
                assert(
                    floatEqual(heights[0], 80) && floatEqual(heights[1], 80) && floatEqual(heights[2], 80),
                    "Property 4: All items have equal height (80)"
                )
            }
        })
    }

    // ==================== Property 5 Test 属性5测试 ====================
    // Feature: flow-layout-enhancement, Property 5: Vertical Mode Equal Width
    // Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    function runPropertyTest5() {
        console.log("\n--- Property 5: Vertical Mode Equal Width ---")

        testFlowVertical.mode = Enums.flow.vertical
        testFlowVertical.columnCount = 3
        testModel4.clear()

        // Add items with different widths 添加不同宽度的子项
        testModel4.append({ itemWidth: 80, itemHeight: 50 })
        testModel4.append({ itemWidth: 120, itemHeight: 60 })
        testModel4.append({ itemWidth: 100, itemHeight: 40 })

        Qt.callLater(function() {
            var widths = []
            for (var i = 0; i < testFlowVertical.children.length; i++) {
                var child = testFlowVertical.children[i]
                if (child && child.objectName === "testItem") {
                    widths.push(child.width)
                }
            }

            if (widths.length >= 3) {
                // Expected width: (400 - 2*8) / 3 = 128
                var expectedWidth = (testFlowVertical.width - 2 * testFlowVertical.spacing) / 3
                assert(
                    floatEqual(widths[0], expectedWidth, 1) &&
                    floatEqual(widths[1], expectedWidth, 1) &&
                    floatEqual(widths[2], expectedWidth, 1),
                    "Property 5: All items have equal width (~" + Math.round(expectedWidth) + ")"
                )
            }
        })
    }

    // ==================== Property 7 Test 属性7测试 ====================
    // Feature: flow-layout-enhancement, Property 7: Mode Switch Round-Trip
    // Validates: Requirements 3.5, 4.7, 6.3
    function runPropertyTest7() {
        console.log("\n--- Property 7: Mode Switch Round-Trip ---")

        testFlowRoundTrip.mode = Enums.flow.default_
        testModel5.clear()

        // Add items 添加子项
        var originalSizes = [
            { w: 100, h: 50 },
            { w: 80, h: 70 },
            { w: 120, h: 40 }
        ]

        for (var i = 0; i < originalSizes.length; i++) {
            testModel5.append({ itemWidth: originalSizes[i].w, itemHeight: originalSizes[i].h })
        }

        Qt.callLater(function() {
            // Switch to horizontal mode 切换到水平模式
            testFlowRoundTrip.mode = Enums.flow.horizontal

            Qt.callLater(function() {
                // Switch back to default mode 切换回默认模式
                testFlowRoundTrip.mode = Enums.flow.default_

                Qt.callLater(function() {
                    // Verify dimensions restored 验证尺寸恢复
                    var idx = 0
                    for (var j = 0; j < testFlowRoundTrip.children.length; j++) {
                        var child = testFlowRoundTrip.children[j]
                        if (child && child.objectName === "testItem" && idx < originalSizes.length) {
                            var expected = originalSizes[idx]
                            assert(
                                floatEqual(child.width, expected.w) && floatEqual(child.height, expected.h),
                                "Property 7: Item " + idx + " restored to (" + expected.w + "x" + expected.h + ")"
                            )
                            idx++
                        }
                    }
                })
            })
        })
    }

    // ==================== UI Layout UI布局 ====================
    Column {
        anchors.fill: parent
        anchors.margins: Enums.spacing.l
        spacing: Enums.spacing.m

        // Header 标题
        Row {
            spacing: Enums.spacing.m

            Label { type: Enums.label.type_title; text: "FlowLayout Property Tests" }

            Button {
                text: "Run Tests"
                onClicked: root.runAllTests()
            }

            Label {
                type: Enums.label.type_body
                text: "Passed: " + testsPassed + " | Failed: " + testsFailed
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        // Test containers 测试容器
        Row {
            spacing: Enums.spacing.l
            width: parent.width

            // Property 1 Test Container
            Column {
                spacing: Enums.spacing.s
                Label { type: Enums.label.type_caption; text: "Property 1: Default Mode" }
                Rectangle {
                    width: 300
                    height: 150
                    color: Enums.cardColor
                    border.color: Enums.borderColor
                    radius: Enums.radius.small

                    FlowLayout {
                        id: testFlowDefault
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.s
                        mode: Enums.flow.default_

                        Repeater {
                            model: ListModel { id: testModel1 }
                            Rectangle {
                                objectName: "testItem"
                                width: model.itemWidth
                                height: model.itemHeight
                                color: Enums.accentColor
                                radius: Enums.radius.small
                            }
                        }
                    }
                }
            }

            // Property 2 Test Container
            Column {
                spacing: Enums.spacing.s
                Label { type: Enums.label.type_caption; text: "Property 2: Wrapping" }
                Rectangle {
                    width: 300
                    height: 150
                    color: Enums.cardColor
                    border.color: Enums.borderColor
                    radius: Enums.radius.small

                    FlowLayout {
                        id: testFlowWrap
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.s
                        mode: Enums.flow.default_

                        Repeater {
                            model: ListModel { id: testModel2 }
                            Rectangle {
                                objectName: "testItem"
                                width: model.itemWidth
                                height: model.itemHeight
                                color: Enums.statusLevel.infoColor
                                radius: Enums.radius.small
                            }
                        }
                    }
                }
            }
        }

        Row {
            spacing: Enums.spacing.l
            width: parent.width

            // Property 4 Test Container
            Column {
                spacing: Enums.spacing.s
                Label { type: Enums.label.type_caption; text: "Property 4: Horizontal (Equal Height)" }
                Rectangle {
                    width: 400
                    height: 150
                    color: Enums.cardColor
                    border.color: Enums.borderColor
                    radius: Enums.radius.small

                    FlowLayout {
                        id: testFlowHorizontal
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.s
                        mode: Enums.flow.horizontal

                        Repeater {
                            model: ListModel { id: testModel3 }
                            Rectangle {
                                objectName: "testItem"
                                width: model.itemWidth
                                height: model.itemHeight
                                color: Enums.statusLevel.successColor
                                radius: Enums.radius.small
                            }
                        }
                    }
                }
            }

            // Property 5 Test Container
            Column {
                spacing: Enums.spacing.s
                Label { type: Enums.label.type_caption; text: "Property 5: Vertical (Equal Width)" }
                Rectangle {
                    width: 400
                    height: 150
                    color: Enums.cardColor
                    border.color: Enums.borderColor
                    radius: Enums.radius.small

                    FlowLayout {
                        id: testFlowVertical
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.s
                        mode: Enums.flow.vertical
                        columnCount: 3

                        Repeater {
                            model: ListModel { id: testModel4 }
                            Rectangle {
                                objectName: "testItem"
                                width: model.itemWidth
                                height: model.itemHeight
                                color: Enums.statusLevel.warningColor
                                radius: Enums.radius.small
                            }
                        }
                    }
                }
            }
        }

        // Property 7 Test Container
        Column {
            spacing: Enums.spacing.s
            Label { type: Enums.label.type_caption; text: "Property 7: Mode Switch Round-Trip" }
            Rectangle {
                width: 400
                height: 100
                color: Enums.cardColor
                border.color: Enums.borderColor
                radius: Enums.radius.small

                FlowLayout {
                    id: testFlowRoundTrip
                    anchors.fill: parent
                    anchors.margins: Enums.spacing.s
                    mode: Enums.flow.default_

                    Repeater {
                        model: ListModel { id: testModel5 }
                        Rectangle {
                            objectName: "testItem"
                            width: model.itemWidth
                            height: model.itemHeight
                            color: Enums.statusLevel.errorColor
                            radius: Enums.radius.small
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        // Auto-run tests after a short delay 短暂延迟后自动运行测试
        Qt.callLater(runAllTests)
    }
}
