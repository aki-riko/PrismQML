// AutoUpdater.qml —— 高层自动更新门面
//
// 把底层 Updater(网络/版本比较/静默安装)与 UI 零件(UpdateDialog / DesktopNotification /
// ProgressRing)串成一条完整链路,应用只需注入 updater 实例并调用 check():
//   检查 → 有新版弹 UpdateDialog 确认 → 右下角 toast 不确定进度环
//        → 拿到总大小转确定环 → 下载完成静默重启安装
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
    property string silentArgs: ""                // 静默安装参数;空则交由 updater 内部默认值
    property bool notifyWhenUpToDate: false        // 已是最新时是否弹提示 toast

    // ---- 展示信息(由宿主 enableAutoUpdate 注入,或应用直接赋值) ----
    // 底层 Updater 未暴露这两项为 QML 可读属性,故在门面层显式持有。
    property string repository: ""
    property string currentVersion: ""

    // ---- 对外信号(供应用可选接管) ----
    signal upToDateNotified(string version)
    signal errorOccurred(string message)
    signal downloadRequested(string version, string downloadUrl, string htmlUrl)

    // ---- 内部状态 ----
    property string _pendingUrl: ""
    property string _pendingHtmlUrl: ""
    property bool _rangeKnown: false
    property bool _checking: false      // 是否处于检查态(不确定环)
    property bool _downloading: false   // 是否处于下载态(不确定环→确定环)
    // 进度环显示条件:检查中或下载中
    readonly property bool _ringVisible: _checking || _downloading

    // 触发一次检查
    function check() {
        if (!updater) {
            console.warn("AutoUpdater: updater 未注入,无法检查更新");
            return;
        }
        // 检查阶段:总量未知,显示不确定进度环(读信息=不确定,下载拿到总大小才转确定)
        root._checking = true;
        root._rangeKnown = false;
        progressRing.indeterminate = true;
        progressRing.start();
        toast.title = qsTr("正在检查更新");
        toast.severity = "info";
        toast.show();
        updater.checkForUpdate();
    }

    // 手动开始下载(autoDownload=false 时供应用调用)
    function startDownload() {
        if (!updater || root._pendingUrl === "")
            return;
        _beginDownload(_pendingVersion, _pendingUrl, _pendingHtmlUrl);
    }

    property string _pendingVersion: ""

    function _beginDownload(version, downloadUrl, htmlUrl) {
        // 无安装包资产 → 跳转 Release 页,不报错
        if (!downloadUrl || downloadUrl === "") {
            if (htmlUrl && htmlUrl !== "")
                updater.openInBrowser(htmlUrl);
            return;
        }
        root._rangeKnown = false;
        root._downloading = true;
        progressRing.indeterminate = true;
        progressRing.start();
        toast.title = qsTr("正在下载更新");
        toast.message = version;
        toast.severity = "info";
        toast.show();
        updater.downloadUpdate(downloadUrl);
    }

    // ---- 接底层 updater 信号 ----
    Connections {
        target: root.updater
        ignoreUnknownSignals: true

        function onUpdateAvailable(version, notes, downloadUrl, htmlUrl) {
            // 检查结束,停不确定环并收起检查 toast,转入确认弹窗
            root._checking = false;
            progressRing.stop();
            toast.hide();
            root._pendingVersion = version;
            root._pendingUrl = downloadUrl;
            root._pendingHtmlUrl = htmlUrl;
            updateDialog.version = version;
            updateDialog.currentVersion = root.currentVersion;
            updateDialog.notes = notes;
            updateDialog.open();
        }

        function onUpToDate(version) {
            root._checking = false;
            progressRing.stop();
            if (!root.notifyWhenUpToDate)
                toast.hide();   // 不提示时收起检查 toast
            if (root.notifyWhenUpToDate) {
                toast.title = qsTr("已是最新版本");
                toast.message = version;
                toast.severity = "success";
                toast.show();
            }
            root.upToDateNotified(version);
        }

        function onCheckFailed(error) {
            root._checking = false;
            progressRing.stop();
            toast.title = qsTr("检查更新失败");
            toast.message = error;
            toast.severity = "error";
            toast.show();
            root.errorOccurred(error);
        }

        function onDownloadProgress(received, total) {
            // 首次拿到有效总大小 → 不确定环转确定环
            if (total > 0 && !root._rangeKnown) {
                root._rangeKnown = true;
                progressRing.stop();
                progressRing.indeterminate = false;
                progressRing.setRange(0, total);
            }
            if (root._rangeKnown)
                progressRing.value = received;
        }

        function onDownloadFinished(filePath) {
            root._downloading = false;
            toast.title = qsTr("下载完成,正在安装");
            toast.message = qsTr("即将自动重启");
            toast.severity = "success";
            // 静默安装并退出;silentArgs 为空则用 updater 内部默认参数
            root.updater.runInstallerAndQuit(filePath, root.silentArgs);
        }

        function onDownloadFailed(error) {
            root._downloading = false;
            progressRing.stop();
            toast.title = qsTr("下载失败");
            toast.message = error;
            toast.severity = "error";
            toast.show();
            root.errorOccurred(error);
        }
    }

    // ---- 更新确认弹窗 ----
    UpdateDialog {
        id: updateDialog
        confirmText: qsTr("下载并安装")
        cancelText: qsTr("稍后")

        onConfirmed: {
            root.downloadRequested(root._pendingVersion, root._pendingUrl, root._pendingHtmlUrl);
            if (root.autoDownload)
                root._beginDownload(root._pendingVersion, root._pendingUrl, root._pendingHtmlUrl);
        }
        onCancelled: {
            // 用户稍后再说,清空待处理状态
            root._pendingUrl = "";
            root._pendingHtmlUrl = "";
        }
    }

    // ---- 右下角下载进度 toast(不确定环 → 确定环) ----
    DesktopNotification {
        id: toast
        position: Enums.notification.posBottomRight
        duration: 0   // 常驻,由下载流程主动 hide

        customContent: Component {
            ProgressRing {
                id: progressRingItem
                visible: root._ringVisible   // 检查/下载态显示;其他提示(失败/最新)不带进度环
                indeterminate: progressRing.indeterminate
                from: progressRing.from
                to: progressRing.to
                value: progressRing.value
            }
        }
    }

    // 进度环状态载体(与 toast 内 customContent 解耦,避免 Loader 重建丢状态)
    QtObject {
        id: progressRing
        property bool indeterminate: true
        property real from: 0
        property real to: 100
        property real value: 0
        function setRange(min, max) { from = min; to = max; value = min; }
        function start() { indeterminate = true; }
        function stop() { indeterminate = false; }
    }
}
