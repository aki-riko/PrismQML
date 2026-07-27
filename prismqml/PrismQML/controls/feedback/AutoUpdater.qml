// AutoUpdater.qml —— 高层自动更新门面
//
// 把底层 Updater(网络/版本比较/安装启动)与 UI 零件(UpdateDialog / feedback presenter)
// 串成一条完整链路,应用只需注入 updater 实例并调用 check():
//   检查 → 有新版弹 UpdateDialog 确认 → 右下角 Toast 不确定进度环
//        → 拿到总大小转确定环 → 下载完成启动安装程序
//        → 无安装包(downloadUrl 为空)则跳转 Release 页
//
// 用法:
//   AutoUpdater { id: au; updater: appUpdater }   // appUpdater 由宿主 enableAutoUpdate 注入
//   Button { onClicked: au.check() }
//   Component.onCompleted: au.checkSilently()     // Silent startup check 启动静默检查
// Custom presenter 自定义展示器:
//   Component { id: dialogPresenter; AutoUpdaterProgressDialogPresenter {} }
//   AutoUpdater { updater: appUpdater; feedbackPresenter: dialogPresenter }
//
// 说明:本组件不含任何网络逻辑,仅做 UI 编排;网络与安装全部委托注入的 updater。
pragma ComponentBehavior: Bound
import QtQuick
import PrismQML

Item {
    id: root

    // ---- 注入 ----
    // 底层更新器实例(宿主通过 enableAutoUpdate 注入为 appUpdater),须提供以下契约:
    //   信号 updateAvailable(version, notes, downloadUrl, htmlUrl) / upToDate(version)
    //        checkFailed(error) / downloadProgress(received, total)
    //        downloadFinished(filePath) / downloadFailed(error)
    //   方法 checkForUpdate() / downloadUpdate(url) / runInstallerAndQuit(path, args)
    //        / stageInstallerForNextLaunch(path, args) (dual_slot)
    //        openInBrowser(url)
    property var updater: null

    // ---- 可配置行为 ----
    property bool autoDownload: true              // 用户确认后是否自动下载(false 则仅发 downloadRequested 信号)
    property string silentArgs: Qt.platform.os === "windows"
        ? "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
        : "" // Inno Setup silent install arguments Inno Setup 静默安装参数
    property bool notifyWhenUpToDate: false        // 已是最新时是否弹提示 toast
    readonly property bool usesDualSlot:
        updater && updater.installStrategy === "dual_slot"
    // Presenter component contract 展示器组件契约:
    //   property var feedbackModel / property Item presenterHost
    // Defaults to bottom-right Toast; null disables built-in feedback.
    // 默认使用右下角 Toast;设为 null 可完全关闭内置展示。
    property Component feedbackPresenter: defaultFeedbackPresenter

    // ---- 展示信息(默认读取底层,应用仍可直接赋值覆盖) ----
    property string repository: updater && updater.repository ? updater.repository : ""
    property string currentVersion: updater && updater.currentVersion ? updater.currentVersion : ""

    // ---- 展示状态(供自定义 Presenter 只读消费) ----
    readonly property QtObject feedbackModel: QtObject {
        readonly property bool active: root._feedbackActive
        readonly property bool checking: root._checking
        readonly property bool downloading: root._downloading
        readonly property bool preparing: root._installPreparing
        readonly property string title: root._feedbackTitle
        readonly property string message: root._feedbackMessage
        readonly property string severity: root._feedbackSeverity
        readonly property int feature: root._feedbackFeature
        readonly property int duration: root._feedbackDuration
        readonly property real progress: root._feedbackProgress
        readonly property bool indeterminate:
            feature === Enums.notification.feature_indeterminate_bar
            || feature === Enums.notification.feature_indeterminate_ring
        readonly property bool determinate:
            feature === Enums.notification.feature_progress_bar
            || feature === Enums.notification.feature_progress_ring

        function dismiss() {
            root._dismissFeedback();
        }
    }

    // ---- 内部状态 ----
    property string _pendingUrl: ""
    property string _pendingHtmlUrl: ""
    property string _pendingVersion: ""
    property bool _rangeKnown: false
    property bool _checking: false      // 是否处于检查态(不确定环)
    property bool _checkSilent: false   // Suppress startup check feedback 抑制启动检查反馈
    property bool _downloading: false   // 是否处于下载态(不确定环→确定环)
    property bool _installPreparing: false
    property bool _awaitingDecision: false
    property bool _componentReady: false
    property bool _feedbackActive: false
    property string _feedbackTitle: ""
    property string _feedbackMessage: ""
    property string _feedbackSeverity: "info"
    property int _feedbackFeature: Enums.notification.feature_normal
    property int _feedbackDuration: Enums.duration.none
    property real _feedbackProgress: 0
    property var _feedbackPresenterObject: null
    readonly property int _bytesPerKibibyte: 1024
    readonly property int _bytesPerMebibyte: _bytesPerKibibyte * _bytesPerKibibyte

    // ---- 对外信号(供应用可选接管) ----
    signal upToDateNotified(string version)
    signal errorOccurred(string message)
    signal downloadRequested(string version, string downloadUrl, string htmlUrl)
    signal updatePreparedForNextLaunch(string version)

    // Trigger a visible manual check. 触发一次有反馈的手动检查。
    function check() {
        _beginCheck(false);
    }

    // Trigger a startup check without check/result Toast. 触发不显示检查/结果 Toast 的启动检查。
    function checkSilently() {
        _beginCheck(true);
    }

    function _beginCheck(silent) {
        if (!updater) {
            console.warn("AutoUpdater: updater 未注入,无法检查更新");
            return;
        }
        if (root._checking || root._downloading || root._awaitingDecision
            || root._installPreparing)
            return;
        _clearPending();
        _dismissFeedback();
        root._checkSilent = silent === true;
        // 检查阶段:总量未知,显示不确定进度环(读信息=不确定,下载拿到总大小才转确定)
        root._checking = true;
        root._rangeKnown = false;
        if (!root._checkSilent) {
            _presentFeedback(
                qsTr("正在检查更新"), "", "info",
                Enums.notification.feature_indeterminate_ring,
                Enums.duration.none, 0
            );
        }
        updater.checkForUpdate();
    }

    // 手动开始下载(autoDownload=false 时供应用调用)
    function startDownload() {
        if (!updater || root._checking || root._downloading || root._awaitingDecision
            || root._installPreparing
            || (root._pendingUrl === "" && root._pendingHtmlUrl === ""))
            return;
        _beginDownload(_pendingVersion, _pendingUrl, _pendingHtmlUrl);
    }

    function _formatSize(bytes) {
        var value = Math.max(0, Number(bytes) || 0);
        if (value >= root._bytesPerMebibyte)
            return (value / root._bytesPerMebibyte).toFixed(1) + " MB";
        if (value >= root._bytesPerKibibyte)
            return (value / root._bytesPerKibibyte).toFixed(0) + " KB";
        return Math.round(value) + " B";
    }

    function _beginDownload(version, downloadUrl, htmlUrl) {
        if (root._downloading)
            return;
        // 无安装包资产 → 跳转 Release 页
        if (!downloadUrl || downloadUrl === "") {
            if (htmlUrl && htmlUrl !== "" && updater.openInBrowser(htmlUrl)) {
                _clearPending();
                return;
            }
            _showError(qsTr("打开发布页失败"), qsTr("无法打开更新发布页"));
            return;
        }
        root._rangeKnown = false;
        root._downloading = true;
        _presentFeedback(
            qsTr("正在下载更新"), version, "info",
            Enums.notification.feature_indeterminate_ring,
            Enums.duration.none, 0
        );
        updater.downloadUpdate(downloadUrl);
    }

    function _showError(title, message) {
        _presentFeedback(
            title, message, "error", Enums.notification.feature_normal,
            Enums.duration.notification, 0
        );
        root.errorOccurred(message);
    }

    function _presentFeedback(title, message, severity, feature, duration, progress) {
        root._feedbackTitle = title;
        root._feedbackMessage = message;
        root._feedbackSeverity = severity;
        root._feedbackFeature = feature;
        root._feedbackDuration = duration;
        root._feedbackProgress = progress;
        root._feedbackActive = true;
    }

    function _dismissFeedback() {
        root._feedbackActive = false;
    }

    function _createFeedbackPresenter() {
        if (!root._componentReady || root._feedbackPresenterObject
                || !root.feedbackPresenter)
            return;
        var item = root.feedbackPresenter.createObject(root, {
            "feedbackModel": root.feedbackModel,
            "presenterHost": root
        });
        if (!item) {
            console.error(
                "AutoUpdater: feedbackPresenter 创建失败:",
                root.feedbackPresenter.errorString()
            );
            return;
        }
        root._feedbackPresenterObject = item;
    }

    function _destroyFeedbackPresenter() {
        var item = root._feedbackPresenterObject;
        root._feedbackPresenterObject = null;
        if (!item)
            return;
        // Disconnect before deferred destroy to isolate the old presenter.
        // 延迟销毁前先断开模型,避免旧 Presenter 收到新状态。
        item.feedbackModel = null;
        item.presenterHost = null;
        item.destroy();
    }

    function _recreateFeedbackPresenter() {
        if (!root._componentReady)
            return;
        _destroyFeedbackPresenter();
        _createFeedbackPresenter();
    }

    function _clearPending() {
        root._pendingVersion = "";
        root._pendingUrl = "";
        root._pendingHtmlUrl = "";
    }

    onFeedbackPresenterChanged: _recreateFeedbackPresenter()

    Component.onCompleted: {
        root._componentReady = true;
        root._createFeedbackPresenter();
    }
    Component.onDestruction: root._destroyFeedbackPresenter()

    // ---- 默认反馈展示器 ----
    Component {
        id: defaultFeedbackPresenter

        AutoUpdaterToastPresenter {}
    }

    // ---- 短时反馈生命周期 ----
    Timer {
        interval: root._feedbackDuration
        running: root._feedbackActive && root._feedbackDuration > Enums.duration.none
        onTriggered: root._dismissFeedback()
    }

    // ---- 接底层 updater 信号 ----
    Connections {
        function onUpdateAvailable(version, notes, downloadUrl, htmlUrl) {
            if (!root._checking)
                return;
            // 检查结束,停不确定环并收起检查 toast,转入确认弹窗
            root._checking = false;
            root._checkSilent = false;
            root._awaitingDecision = true;
            root._dismissFeedback();
            root._pendingVersion = version;
            root._pendingUrl = downloadUrl;
            root._pendingHtmlUrl = htmlUrl;
            updateDialog.version = version;
            updateDialog.currentVersion = root.currentVersion;
            updateDialog.notes = notes;
            updateDialog.open();
        }

        function onUpToDate(version) {
            if (!root._checking)
                return;
            root._checking = false;
            var silent = root._checkSilent;
            root._checkSilent = false;
            if (silent || !root.notifyWhenUpToDate)
                root._dismissFeedback();   // 不提示时收起检查反馈
            if (!silent && root.notifyWhenUpToDate) {
                root._presentFeedback(
                    qsTr("已是最新版本"), version, "success",
                    Enums.notification.feature_normal,
                    Enums.duration.notification, 0
                );
            }
            root.upToDateNotified(version);
        }

        function onCheckFailed(error) {
            if (!root._checking)
                return;
            root._checking = false;
            if (root._checkSilent) {
                root._checkSilent = false;
                root._dismissFeedback();
                root.errorOccurred(error);
                return;
            }
            _showError(qsTr("检查更新失败"), error);
        }

        function onDownloadProgress(received, total) {
            if (!root._downloading)
                return;
            // 首次拿到有效总大小 → 不确定环转确定环
            if (total > 0 && !root._rangeKnown) {
                root._rangeKnown = true;
                root._feedbackFeature = Enums.notification.feature_progress_ring;
            }
            if (root._rangeKnown) {
                var progress = Math.max(0, Math.min(1, received / total));
                root._feedbackProgress = progress;
                root._feedbackMessage = Math.round(progress * 100) + "%  ("
                    + root._formatSize(received) + " / " + root._formatSize(total) + ")";
            } else {
                root._feedbackMessage = root._formatSize(received) + qsTr(" 已下载");
            }
        }

        function onDownloadFinished(filePath) {
            if (!root._downloading)
                return;
            root._downloading = false;
            if (root.usesDualSlot) {
                if (!root.updater.stageInstallerForNextLaunch(filePath, root.silentArgs)) {
                    _showError(qsTr("后台安装启动失败"), qsTr("无法准备下次启动的新版,请重试"));
                    return;
                }
                root._installPreparing = true;
                root._presentFeedback(
                    qsTr("正在后台准备新版"),
                    qsTr("当前版本可继续使用,完成后下次启动自动切换"),
                    "info", Enums.notification.feature_indeterminate_ring,
                    Enums.duration.none, 0
                );
                return;
            }
            if (!root.updater.runInstallerAndQuit(filePath, root.silentArgs)) {
                _showError(qsTr("安装启动失败"), qsTr("无法启动安装程序,请重试"));
                return;
            }
            root._presentFeedback(
                qsTr("安装程序已启动"), qsTr("安装将在后台静默完成"),
                "success", Enums.notification.feature_normal,
                Enums.duration.notification, 0
            );
        }

        function onDownloadFailed(error) {
            if (!root._downloading)
                return;
            root._downloading = false;
            _showError(qsTr("下载失败"), error);
        }

        function onInstallPreparationFinished() {
            if (!root._installPreparing)
                return;
            root._installPreparing = false;
            root._presentFeedback(
                qsTr("新版已准备完成"),
                qsTr("当前版本继续运行,下次启动将自动切换"),
                "success", Enums.notification.feature_normal,
                Enums.duration.notification, 0
            );
            var version = root._pendingVersion;
            root._clearPending();
            root.updatePreparedForNextLaunch(version);
        }

        function onInstallPreparationFailed(error) {
            if (!root._installPreparing)
                return;
            root._installPreparing = false;
            _showError(qsTr("后台安装失败"), error);
        }

        target: root.updater
        ignoreUnknownSignals: true
    }

    // ---- 更新确认弹窗 ----
    UpdateDialog {
        id: updateDialog
        confirmText: qsTr("下载并安装")
        cancelText: qsTr("稍后")

        onConfirmed: {
            root._awaitingDecision = false;
            root.downloadRequested(root._pendingVersion, root._pendingUrl, root._pendingHtmlUrl);
            if (root.autoDownload)
                root._beginDownload(root._pendingVersion, root._pendingUrl, root._pendingHtmlUrl);
        }
        onCancelled: {
            // 用户稍后再说,清空待处理状态
            root._awaitingDecision = false;
            root._clearPending();
        }
    }

}
