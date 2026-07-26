# PrismQML Automatic Update Integration

PrismQML splits automatic updates into two layers. The Python `Updater` reads the GitHub Latest Release, compares versions, downloads safely, and launches the installer. The QML `AutoUpdater` owns confirmation, download feedback, and installer handoff. Applications should not duplicate the network, progress-toast, or installer-launch logic.

The complete flow is:

```text
Check the Latest Release
→ confirm an available update
→ download the matching platform asset
→ update one feedback object in place
→ verify SHA-256
→ launch the installer
→ quit the current application
→ launch the new version according to the installer manifest
```

## 1. Release asset contract

`Updater` reads the GitHub Latest Release for `OWNER/REPO` by default. The Release must:

- use a tag comparable with the current version, such as `v1.2.3`;
- be published and not be a draft or prerelease;
- contain a launchable asset for the current platform: Windows `.exe`, macOS `.dmg` / `.pkg`, or Linux `.AppImage` / `.run` / `.deb`;
- name the asset with the configured keyword, for example `ExampleApp-Setup-1.2.3.exe` for the default `Setup` keyword;
- expose a `sha256:<64-hex>` asset `digest` through the GitHub API. PrismQML requires the digest by default and verifies it again after download.

If no matching platform asset exists, accepting the update opens the Release page instead of treating an arbitrary file as an installer.

## 2. Inject the Python update backend

When using `App`, call `enable_auto_update()` after constructing `App` and before loading QML that consumes `appUpdater`:

```python
from prismqml import App

CURRENT_VERSION = "v1.2.3"
UPDATE_REPOSITORY = "OWNER/REPO"
UPDATE_ASSET_KEYWORD = "Setup"

app = App()
app.enable_auto_update(
    UPDATE_REPOSITORY,
    CURRENT_VERSION,
    UPDATE_ASSET_KEYWORD,
)

# Continue creating windows, loading pages, and calling app.exec().
```

This creates an `Updater`, enforces Release-asset digest verification, and injects it into the QML root context as `appUpdater`. Applications normally do not need to connect the backend signals directly.

For a manually created `QQmlApplicationEngine`, create and inject `Updater` explicitly. The host remains responsible for QML environment setup and type registration:

```python
from prismqml import Updater

updater = Updater("OWNER/REPO", "v1.2.3", "Setup")
updater.set_require_artifact_digest(True)
engine.rootContext().setContextProperty("appUpdater", updater)
```

Python must retain `updater` until the application exits.

## 3. Add the QML facade

The default presenter is a bottom-right Toast. Create only one `AutoUpdater` per application window:

```qml
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    Fluent.AutoUpdater {
        id: autoUpdater

        updater: appUpdater
        autoDownload: true
        notifyWhenUpToDate: true
        silentArgs: Qt.platform.os === "windows"
            ? "/SILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
            : ""
    }

    Timer {
        interval: Fluent.Enums.duration.toast
        running: true
        repeat: false
        onTriggered: autoUpdater.checkSilently()
    }

    Fluent.Button {
        text: "Check for updates"
        onClicked: autoUpdater.check()
    }
}
```

`check()` is a visible manual check. With `notifyWhenUpToDate=true`, it also reports that the application is current. `checkSilently()` is intended for startup: it suppresses checking, up-to-date, and failure Toasts. If an update actually exists, the update confirmation dialog still opens.

After download starts, the default Toast presenter creates one feedback object. Later progress signals update that object in place instead of reopening a Toast on every change:

```text
43%  (20.0 MB / 46.5 MB)
```

While the server has not supplied a total size, feedback remains indeterminate and shows only received bytes. It switches automatically to determinate progress after the first valid total.

## 4. Choose a progress presenter

To use a modal progress window, replace `feedbackPresenter` with `AutoUpdaterProgressDialogPresenter`:

```qml
Component {
    id: updateProgressPresenter

    Fluent.AutoUpdaterProgressDialogPresenter {}
}

Fluent.AutoUpdater {
    updater: appUpdater
    feedbackPresenter: updateProgressPresenter
}
```

Use `AutoUpdaterToastPresenter` to select Toast feedback explicitly. Do not also listen to download signals and create a second application-level Toast, because that produces duplicate feedback.

## 5. Windows installer template

Copy the [installer manifest example](examples/prismqml-installer.json), then give the application a stable `app_id`, `aumid`, install scope, and Nuitka standalone directory. To launch the new version immediately after an automatic update, set:

```json
"launch_after_install": true
```

Generate and check the Inno Setup script with the same application version:

```powershell
prismqml-installer generate --manifest prismqml-installer.json --version 1.2.4 --output installer.iss
prismqml-installer check --manifest prismqml-installer.json --version 1.2.4 --output installer.iss
prismqml-installer doctor --manifest prismqml-installer.json
```

See [Windows Installer Template](windows-installer.md) for every manifest field and compile command. The generated contract uses:

- `CloseApplications=yes` so the installer may close the process holding old files;
- `RestartApplications=no` so Restart Manager cannot produce a duplicate relaunch;
- `Flags: nowait postinstall` when `launch_after_install=true`, launching the executable once from the new install directory;
- a stable `AppId`, upgrading the same installation instead of creating a second application.

## 6. Choose installer arguments

The application passes Windows runtime arguments through `AutoUpdater.silentArgs`:

| Arguments | User-visible behavior | Recommended use |
|-----------|-----------------------|-----------------|
| Empty string | Full Inno Setup wizard | The user must choose each step |
| `/SILENT /SUPPRESSMSGBOXES /NORESTART /SP-` | Hides the wizard but shows installation progress | Default automatic-update experience |
| `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` | Hides both wizard and installation progress | Installation must be completely hidden |

A machine-wide installation may still display the Windows UAC prompt; that is an operating-system security boundary. Do not combine `/RESTARTAPPLICATIONS` or `/AUTORESTARTAPP` with `launch_after_install=true`, or the application may launch twice.

## 7. End-to-end acceptance

Source tests are not packaged-installation proof. A release should verify at least:

1. application version, Release tag, installer filename, and installed EXE product version agree;
2. installer-script `check` reports no drift;
3. Nuitka and ISCC run on a disposable Windows runner;
4. the installer runs with the application's `/SILENT` arguments into an isolated directory and retains an installation log;
5. installer exit status, uninstall registration, install directory, and product version are correct;
6. with `launch_after_install=true`, the process launched after installation is the EXE from the new directory;
7. that process is stopped before running a packaged SELFTEST from the installation directory;
8. the installer is attached to a public Release only after every gate passes.

User acceptance must exercise two real versions: install the old version, publish the new version, and perform a manual update check. Confirm that startup checking shows no Toast, manual checking provides feedback, download text contains `received MB / total MB`, the same Toast updates in place, the installation progress window appears after the application exits, and the new version launches after installation.

## 8. Troubleshooting

| Symptom | Check |
|---------|-------|
| Startup shows a “checking” Toast | The startup entry must call `checkSilently()`, not `check()` |
| Every progress change opens another Toast | Ensure there is one `AutoUpdater` and no second application-level download Toast |
| Only received bytes appear | The server has not supplied a valid total; progress becomes determinate when it does |
| An update exists but no installer is selected | Check the platform suffix and `asset_keyword` |
| Asset digest is missing or verification fails | Check that the GitHub API exposes a matching asset `digest` |
| No installation progress window appears | Replace `/VERYSILENT` with `/SILENT` |
| The new version does not launch | Set `launch_after_install=true` and confirm generated output does not use `skipifsilent` |
| The application launches twice | Do not enable both Restart Manager relaunch and `[Run] postinstall` |

The real and DRY demonstrations live in `examples/pages/AutoUpdatePage.qml`. DRY mode does not access the network, create files, or launch an installer.
