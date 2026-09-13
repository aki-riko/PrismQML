import QtQuick
import QtQuick.Window
import PrismQML as Fluent
import "../../prismqml/PrismQML/_internal" as Internal

Window {
    id: root

    width: 640
    height: 480
    visible: false

    readonly property bool outsideUsesGlobal:
        outsideCard.effectiveSkinContext === Fluent.Enums
    readonly property bool ticketCardUsesScope:
        ticketCard.effectiveSkinContext === ticketScope.context
    readonly property bool ticketButtonUsesScope:
        ticketButton.effectiveSkinContext === ticketScope.context
    readonly property bool ticketPaperUsesScope:
        ticketPaper.effectiveSkinContext === ticketScope.context
    readonly property bool frameUsesScope:
        ticketFrame.effectiveSkinContext === ticketScope.context
    readonly property bool frameChildUsesScope:
        frameChild.effectiveSkinContext === ticketScope.context
    readonly property bool popupUsesScope:
        ticketPopup.effectiveSkinContext === ticketScope.context
    readonly property bool popupMenuUsesScope:
        ticketMenuDelegate.effectiveSkinContext === ticketScope.context
    readonly property bool dialogUsesScope:
        ticketDialog.effectiveSkinContext === ticketScope.context
    readonly property bool dialogBodyButtonUsesScope:
        dialogBodyButton.effectiveSkinContext === ticketScope.context
    readonly property bool dialogWasReparented:
        ticketDialog.parent === root.contentItem
    readonly property string ticketScopeSkin: ticketScope.context.skin
    readonly property bool ticketScopeDark: ticketScope.context.isDark
    readonly property color ticketScopeControlBackground:
        ticketScope.context.stateColor.controlBg
    readonly property color globalControlBackground:
        Fluent.Enums.stateColor.controlBg

    readonly property real globalCardRadius: outsideCard.borderRadius
    readonly property real ticketCardRadius: ticketCard.borderRadius
    readonly property real ticketButtonRadius: ticketButton.radius
    readonly property real ticketFrameRadius: ticketFrame._effectiveRadius
    readonly property real ticketPopupRadius: ticketPopup.popupRadius
    readonly property real ticketDialogRadius: ticketDialog._dialogRadius

    readonly property color globalCardColor: outsideCard.color
    readonly property color ticketCardColor: ticketCard.color
    readonly property color expectedTicketCardColor:
        ticketScope.context.stateColor.controlBg
    readonly property color ticketPopupColor: ticketPopup._popupBackground
    readonly property color expectedTicketPopupColor: ticketScope.context.cardColor
    readonly property color ticketDialogColor: ticketDialog._dialogBackground
    readonly property color expectedTicketDialogColor: ticketScope.context.dialogColor
    readonly property bool ticketPaperVisible: ticketPaper.visible

    Fluent.Card {
        id: outsideCard
        x: 8
        y: 8
        width: 120
        height: 48
    }

    Fluent.SkinScope {
        id: ticketScope
        objectName: "ticketScope"
        x: 160
        y: 32
        width: 320
        height: 260
        skin: "vintage_ticket"

        Fluent.Card {
            id: ticketCard
            x: 0
            y: 0
            width: 180
            height: 68
            title: "Ticket"
            cardType: Fluent.Enums.card.type_header
        }

        Fluent.Button {
            id: ticketButton
            x: 0
            y: 88
            width: 120
            height: 36
            text: "Copy"
            style: Fluent.Enums.button.style_primary
        }

        Fluent.TicketPaper {
            id: ticketPaper
            x: 196
            y: 0
            width: 96
            height: 68
        }

        Internal.ContentFrame {
            id: ticketFrame
            x: 0
            y: 144
            width: 120
            height: 72
            backgroundColor: Fluent.Enums.surfaceColor
            cornerRadius: Fluent.Enums.radius.large

            Fluent.Button {
                id: frameChild
                objectName: "frameChild"
                text: "Frame child"
            }
        }

        Fluent.PopupWindowCore {
            id: ticketPopup
            targetControl: ticketButton
            popupWidth: 120
            popupHeight: 48
            useInWindowPopup: true

            Fluent.MenuDelegate {
                id: ticketMenuDelegate
                objectName: "ticketMenuDelegate"
                width: 120
                text: "Menu item"
            }
        }

        Fluent.DialogBoxCore {
            id: ticketDialog
            contentWidth: 160
            actionsVisible: false

            Fluent.Button {
                id: dialogBodyButton
                objectName: "dialogBodyButton"
                text: "Dialog child"
            }
        }
    }

    Component.onCompleted: {
        ticketDialog.open()
        ticketPopup.openAtControl(ticketButton)
    }
}
