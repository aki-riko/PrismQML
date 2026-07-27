# PrismQML Windows Installer Template

`prismqml-installer` deterministically generates an Inno Setup script from a small JSON manifest and provides an explicit compile entry point. `doctor`, `generate`, `check`, and `compile --dry-run` never invoke ISCC. Only an explicit `compile` command invokes an installed ISCC. The tool never runs Nuitka or executes the generated installer.

## Behavior contract

`install_strategy` defaults to `in_place`. Set it to `dual_slot` when the current session must keep running and the new version should take effect on the next launch.

The `in_place` template fixes the following upgrade behavior:

- `AppId` remains stable across releases so a new release upgrades the same installation;
- `CloseApplications=yes` lets Inno Setup close processes that hold old files;
- `RestartApplications=no` avoids Restart Manager relaunches and duplicate starts;
- with the default `launch_after_install=false`, `[Run]` uses `skipifsilent`, so a silent update waits for the user's next launch; set it to `true` to launch the new version once from the installed directory after a silent install;
- per-user installs use `{localappdata}\Programs` without proactively requesting elevation;
- machine installs use `{autopf}`, where Windows can still show the mandatory UAC prompt.

The `dual_slot` contract is:

- maintain `slot-a` and `slot-b` below the install root and replace only the inactive slot;
- accept `/PRISMCURRENTSLOT=A|B` and persist the next launch slot in `prism-update-slot.ini`;
- use `CloseApplications=no`, so the current process is neither closed nor overwritten;
- let `App` redirect stale shortcuts/taskbar entries to the `LaunchSlot` executable at startup;
- allow `launch_after_install` for the first install, while an existing install switches only on the next launch.

PrismQML `AutoUpdater` supplies the runtime silent arguments. The template does not contain `/RESTARTAPPLICATIONS` or `/AUTORESTARTAPP`.

See [Automatic Update Integration](auto-update.md) for the complete Python/QML wiring, `/SILENT` versus `/VERYSILENT`, download feedback, and real upgrade acceptance.

## Manifest

Copy the [example manifest](examples/prismqml-installer.json) to the application repository root. Each application must explicitly declare seven core fields:

- `app_id`: a permanently stable canonical UUID without braces;
- `name`, `publisher`, and `executable`;
- `aumid`: the AppUserModelID used by Windows shortcuts and notifications;
- `install_scope`: either `user` or `machine`; do not change it for an existing application without a migration decision;
- `dist_dir`: the Nuitka standalone directory relative to the manifest.

Optional fields are `homepage`, `icon`, `installer_output_dir`, `output_name`, `chinese_messages_file`, `extension_include`, `launch_after_install`, and `install_strategy`. `install_strategy` accepts only `in_place` (default) or `dual_slot`. `launch_after_install` must be a JSON boolean and defaults to `false`; an existing dual-slot install does not launch the new version immediately. `output_name` may only use the `{name}` and `{version}` placeholders and must omit the `.exe` suffix. Use `extension_include` for application-specific logic such as brand migration; the shared template does not guess or remove legacy directories.

The manifest does not store the release version. The release workflow injects it through `--version`.

## Commands

```powershell
prismqml-installer doctor --manifest prismqml-installer.json
prismqml-installer generate --manifest prismqml-installer.json --version 1.2.3.4
prismqml-installer check --manifest prismqml-installer.json --version 1.2.3.4
prismqml-installer compile --manifest prismqml-installer.json --version 1.2.3.4 --dry-run
prismqml-installer compile --manifest prismqml-installer.json --version 1.2.3.4
```

From a source checkout, use:

```powershell
.\.venv\Scripts\python.exe -m prismqml.python.tools.windows_installer doctor --manifest prismqml-installer.json
```

The default output is `installer.generated.iss` beside the manifest. Generated scripts only contain relative paths and never capture development-machine absolute paths. Identical content is not rewritten. `check` is read-only and is suitable for detecting generated-output drift in CI.

Every command accepts the global `--json` option. It is also accepted after a subcommand for discoverability in subcommand help. The recommended form is:

```powershell
prismqml-installer --json doctor --manifest prismqml-installer.json
```

Successful JSON contains `ok`, `command`, and command-specific fields. Errors use this stable envelope:

```json
{
  "ok": false,
  "command": "check",
  "error": {
    "code": "stale_output",
    "message": "generated installer is stale: ..."
  }
}
```

`compile --dry-run` validates all inputs, resolves ISCC, and returns the exact `argv`, generated-script path, expected installer path, and `script_sha256` without writing files or starting a process; `installer_sha256` is `null`. An explicit `compile` atomically generates the script, invokes `ISCC <script path>` with the script directory as its working directory, requires the expected `.exe` to be created or refreshed by that invocation, and returns its `installer_sha256`.

Exit codes are `0` for success, `2` for invalid arguments, `3` for an invalid manifest, `4` for missing or stale generated output, `5` for file-system errors, and `6` for missing compile prerequisites or ISCC failures.

`doctor` returns `0` even when the dist directory, icon, or ISCC is unavailable, reporting missing items through `ready_to_compile=false` and `checks`. Set `PRISMQML_ISCC` to the compiler path or add it to `PATH`. The tool never installs dependencies automatically.
