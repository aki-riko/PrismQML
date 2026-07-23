// AutoUpdater.qml —— 高层自动更新门面
//
// 把底层 Updater(网络/版本比较/安装启动)与 UI 零件(UpdateDialog / Toast)
// 串成一条完整链路,应用只需注入 updater 实例并调用 check():
//   检查 → 有新版弹 UpdateDialog 确认 → 右下角 Toast 不确定进度环
//        → 拿到总大小转确定环 → 下载完成启动安装程序
//        → 无安装包(downloadUrl 为空)则跳转 Release 页
//
// 用法:
//   AutoUpdater { id: au; updater: appUpdater }   // appUpdater 由宿主 enableAutoUpdate 注入
//   Button { onClicked: au.check() }
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
    //        openInBrowser(url)
    property var updater: null

    // ---- 可配置行为 ----
    property bool autoDownload: true              // 用户确认后是否自动下载(false 则仅发 downloadRequested 信号)
    property string silentArgs: ""                // 安装参数;空则启动可见安装向导
    property bool notifyWhenUpToDate: false        // 已是最新时是否弹提示 toast

    // ---- 展示信息(默认读取底层,应用仍可直接赋值覆盖) ----
    property string repository: updater && updater.repository ? updater.repository : ""
    property string currentVersion: updater && updater.currentVersion ? updater.currentVersion : ""

    // ---- 内部状态 ----
    property string _pendingUrl: ""
    property string _pendingHtmlUrl: ""
    property string _pendingVersion: ""
    property bool _rangeKnown: false
    property bool _checking: false      // 是否处于检查态(不确定环)
    property bool _downloading: false   // 是否处于下载态(不确定环→确定环)
    property bool _awaitingDecision: false
    property var _toast: null

    // ---- 对外信号(供应用可选接管) ----
    signal upToDateNotified(string version)
    signal errorOccurred(string message)
    signal downloadRequested(string version, string downloadUrl, string htmlUrl)

    // 触发一次检查
    function check() {
        if (!updater) {
            console.warn("AutoUpdater: updater 未注入,无法检查更新");
            return;
        }
        if (root._checking || root._downloading || root._awaitingDecision)
            return;
        _clearPending();
        _hideToast();
        // 检查阶段:总量未知,显示不确定进度环(读信息=不确定,下载拿到总大小才转确定)
        root._checking = true;
        root._rangeKnown = false;
        _showToast(
            qsTr("正在检查更新"), "", "info",
            Enums.notification.feature_indeterminate_ring,
            Enums.duration.none, 0
        );
        updater.checkForUpdate();
    }

    // 手动开始下载(autoDownload=false 时供应用调用)
    function startDownload() {
        if (!updater || root._checking || root._downloading || root._awaitingDecision
            || (root._pendingUrl === "" && root._pendingHtmlUrl === ""))
            return;
        _beginDownload(_pendingVersion, _pendingUrl, _pendingHtmlUrl);
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
        _showToast(
            qsTr("正在下载更新"), version, "info",
            Enums.notification.feature_indeterminate_ring,
            Enums.duration.none, 0
        );
        updater.downloadUpdate(downloadUrl);
    }

    function _showError(title, message) {
        _showToast(
            title, message, "error", Enums.notification.feature_normal,
            Enums.duration.notification, 0
        );
        root.errorOccurred(message);
    }

    function _showToast(title, message, severity, feature, duration, progress) {
        var item = root._toast;
        var created = false;
        if (!item) {
            item = NotificationManager.toast.info(
                root, title, message, duration,
                Enums.notification.posBottomRight
            );
            if (!item) {
                console.warn("AutoUpdater: Toast 创建失败");
                return;
            }
            created = true;
            item.objectName = "autoUpdaterToast";
            root._toast = item;
            item.closed.connect(function() {
                if (root._toast === item)
                    root._toast = null;
            });
        }
        item.title = title;
        item.message = message;
        item.severity = severity;
        item.feature = feature;
        item.duration = duration;
        item.progress = progress;
        if (!created)
            item.show();
    }

    function _hideToast() {
        var item = root._toast;
        root._toast = null;
        if (item)
            item.hide();
    }

    function _clearPending() {
        root._pendingVersion = "";
        root._pendingUrl = "";
        root._pendingHtmlUrl = "";
    }

    // ---- 接底层 updater 信号 ----
    Connections {
        function onUpdateAvailable(version, notes, downloadUrl, htmlUrl) {
            if (!root._checking)
                return;
            // 检查结束,停不确定环并收起检查 toast,转入确认弹窗
            root._checking = false;
            root._awaitingDecision = true;
            root._hideToast();
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
            if (!root.notifyWhenUpToDate)
                root._hideToast();   // 不提示时收起检查 Toast
            if (root.notifyWhenUpToDate) {
                root._showToast(
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
            _showError(qsTr("检查更新失败"), error);
        }

        function onDownloadProgress(received, total) {
            if (!root._downloading)
                return;
            // 首次拿到有效总大小 → 不确定环转确定环
            if (total > 0 && !root._rangeKnown) {
                root._rangeKnown = true;
                if (root._toast)
                    root._toast.feature = Enums.notification.feature_progress_ring;
            }
            if (root._rangeKnown && root._toast)
                root._toast.progress = Math.max(0, Math.min(1, received / total));
        }

        function onDownloadFinished(filePath) {
            if (!root._downloading)
                return;
            root._downloading = false;
            if (!root.updater.runInstallerAndQuit(filePath, root.silentArgs)) {
                _showError(qsTr("安装启动失败"), qsTr("无法启动安装程序,请重试"));
                return;
            }
            root._showToast(
                qsTr("安装程序已启动"), qsTr("请按安装程序提示完成更新"),
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
