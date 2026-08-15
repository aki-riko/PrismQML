// ButtonFeatureLoader - Mutually exclusive button feature shell 互斥按钮功能壳
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import "../../../containers"
import ".."

// ButtonFeatureLoader - Owns progress, toggle, and menu feature branches 承载进度、切换和菜单功能分支
Loader {
    id: featureLoader

    // ==================== Required Props 必需属性 ====================
    required property var button
    required property Item background
    required property bool mainHovered

    anchors.fill: parent
    active: button._hasFeatureVisual || button._hasMenuFeature
    onLoaded: {
        if (button._hasMenuFeature
                && (button.activeFocus
                    || (button.feature === Enums.button.feature_dropdown
                        && mainHovered))) {
            button._prewarmMenu()
        }
    }
    sourceComponent: button._hasProgressBarFeature
                     ? progressFeatureComponent
                     : (button.feature === Enums.button.feature_toggle
                        ? toggleFeatureComponent
                        : (button._hasMenuFeature
                           ? dropdownComponent : null))

    Component {
        id: progressFeatureComponent

        Item {
            id: progressLayerHost

            readonly property bool _progressLayerActive:
                featureLoader.button.feature
                    === Enums.button.feature_indeterminate_bar
                || featureLoader.button.showProgress

            anchors.fill: parent

            Rectangle {
                id: progressMask

                anchors.fill: parent
                radius: featureLoader.button.radius
                layer.enabled: progressLayerHost._progressLayerActive
                visible: false
            }

            Item {
                id: progressContent

                anchors.fill: parent
                layer.enabled: progressLayerHost._progressLayerActive
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskSource: progressMask
                    maskThresholdMin: Enums.mask.thresholdMin
                    maskSpreadAtMin: Enums.mask.spreadAtMin
                }

                ButtonProgress {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: Enums.border.thick
                    feature: featureLoader.button.feature
                    style: featureLoader.button.style
                    progress: featureLoader.button.progress
                    showProgress: featureLoader.button.showProgress
                }
            }
        }
    }

    Component {
        id: toggleFeatureComponent

        ToggleAnimation {
            target: featureLoader.background
            running: featureLoader.button.checked
        }
    }

    Component {
        id: dropdownComponent

        ButtonDropdown {
            isToolButton: featureLoader.button.isToolButton
            feature: featureLoader.button.feature
            menuItems: featureLoader.button._safeMenuItems
            menu: featureLoader.button.menu
            controlEnabled: featureLoader.button.enabled
            loading: featureLoader.button.loading
            showDropdownIndicator: featureLoader.button.showDropdownIndicator
            dropdownOpen: featureLoader.button.dropdownOpen
            parentRadius: featureLoader.button.radius
            fontSize: featureLoader.button.fontSize
            parentStyle: featureLoader.button.style
            textColor: featureLoader.button._styleTextColor
            onMenuItemClicked: (index, text) =>
                featureLoader.button.menuItemClicked(index, text)
            onMainButtonClicked: featureLoader.button.clicked()
            onMenuAboutToOpen: {
                featureLoader.button._dismissToolTipForMenu()
                featureLoader.button.menuAboutToOpen()
            }
        }
    }
}
