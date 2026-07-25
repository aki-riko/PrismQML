# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Generate, verify, and compile Windows installers. 生成、校验并编译 Windows 安装器。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from ._windows_installer_compile import (
    EXIT_COMPILE,
    InstallerCompileResult,
    compile_installer,
)
from ._windows_installer_core import (
    EXIT_IO,
    EXIT_MANIFEST,
    EXIT_STALE_OUTPUT,
    InstallerResult,
    ManifestError,
    WindowsInstallerManifest,
    check_installer,
    default_output_path,
    doctor_manifest,
    generate_installer,
    load_manifest,
    render_installer,
)


EXIT_OK = 0
EXIT_USAGE = 2
COMMAND_NAMES = frozenset({"doctor", "generate", "check", "compile"})


class InstallerArgumentParser(argparse.ArgumentParser):
    """Argument parser with optional JSON usage errors. 支持 JSON 用法错误的参数解析器。"""

    json_requested = False

    def error(self, message: str) -> None:
        if self.json_requested:
            payload = {
                "ok": False,
                "command": None,
                "error": {"code": "usage_error", "message": message},
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            self.print_usage(sys.stderr)
            sys.stderr.write(f"error: {message}\n")
        raise SystemExit(EXIT_USAGE)


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="emit stable JSON to stdout",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="schema-v1 prismqml-installer.json path",
    )


def _add_generation_arguments(parser: argparse.ArgumentParser) -> None:
    _add_common_arguments(parser)
    parser.add_argument("--version", required=True, help="three or four part release version")
    parser.add_argument(
        "--output",
        type=Path,
        help="generated ISS path; defaults beside the manifest",
    )


def build_parser() -> InstallerArgumentParser:
    """Build the stable public CLI surface. 构建稳定公开 CLI。"""
    parser = InstallerArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit stable JSON to stdout")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="validate manifest and compile readiness")
    _add_common_arguments(doctor)
    generate = subparsers.add_parser("generate", help="atomically generate one ISS file")
    _add_generation_arguments(generate)
    check = subparsers.add_parser("check", help="verify the generated ISS is current")
    _add_generation_arguments(check)
    compile_command = subparsers.add_parser(
        "compile", help="generate and explicitly invoke ISCC"
    )
    _add_generation_arguments(compile_command)
    compile_command.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the compile plan without writing or invoking ISCC",
    )
    return parser


def _output_path(
    manifest: WindowsInstallerManifest, configured: Optional[Path]
) -> Path:
    return Path(configured).resolve() if configured else default_output_path(manifest)


def _result_payload(command: str, result: InstallerResult) -> Dict[str, Any]:
    return {
        "ok": True,
        "command": command,
        "output": str(result.output),
        "sha256": result.sha256,
        "changed": result.changed,
    }


def _doctor_payload(manifest: WindowsInstallerManifest) -> Dict[str, Any]:
    payload = {
        "ok": True,
        "command": "doctor",
        "manifest": str(manifest.source_path),
        "schema": 1,
    }
    payload.update(doctor_manifest(manifest))
    return payload


def _compile_payload(result: InstallerCompileResult) -> Dict[str, Any]:
    return {
        "ok": True,
        "command": "compile",
        "script": str(result.script),
        "installer": str(result.installer),
        "compiler": str(result.compiler),
        "argv": list(result.argv),
        "script_sha256": result.script_sha256,
        "installer_sha256": result.installer_sha256,
        "dry_run": result.dry_run,
        "compiled": result.compiled,
    }


def _emit_json(payload: MappingLike) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _emit_human(payload: MappingLike) -> None:
    command = payload["command"]
    if command == "doctor":
        state = "ready" if payload["ready_to_compile"] else "not ready"
        sys.stdout.write(f"installer manifest is valid; compile status: {state}\n")
        for name, check in payload["checks"].items():
            marker = "ok" if check["available"] else "missing"
            sys.stdout.write(f"- {name}: {marker}\n")
        return
    if command == "compile":
        state = "planned" if payload["dry_run"] else "compiled"
        sys.stdout.write(f"compile: {state} {payload['installer']}\n")
        return
    changed = "updated" if payload["changed"] else "unchanged"
    sys.stdout.write(f"{command}: {changed} {payload['output']}\n")


MappingLike = Dict[str, Any]


def _success_payload(arguments: argparse.Namespace) -> MappingLike:
    manifest = load_manifest(arguments.manifest)
    if arguments.command == "doctor":
        return _doctor_payload(manifest)
    output = _output_path(manifest, arguments.output)
    if arguments.command == "compile":
        result = compile_installer(
            manifest, output, arguments.version, arguments.dry_run
        )
        return _compile_payload(result)
    if arguments.command == "generate":
        result = generate_installer(manifest, output, arguments.version)
    else:
        result = check_installer(manifest, output, arguments.version)
    return _result_payload(arguments.command, result)


def _error_payload(command: Optional[str], error: ManifestError) -> MappingLike:
    return {
        "ok": False,
        "command": command,
        "error": {"code": error.code, "message": str(error)},
    }


def _requested_command(raw_arguments: Sequence[str]) -> Optional[str]:
    return next(
        (argument for argument in raw_arguments if argument in COMMAND_NAMES), None
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the installer CLI and return a stable exit code. 运行 CLI 并返回稳定退出码。"""
    raw_arguments = list(argv) if argv is not None else sys.argv[1:]
    InstallerArgumentParser.json_requested = "--json" in raw_arguments
    parser = build_parser()
    try:
        arguments = parser.parse_args(raw_arguments)
        payload = _success_payload(arguments)
    except ManifestError as error:
        command = _requested_command(raw_arguments)
        payload = _error_payload(command, error)
        if "--json" in raw_arguments:
            _emit_json(payload)
        else:
            sys.stderr.write(f"{error.code}: {error}\n")
        return error.exit_code
    if arguments.json:
        _emit_json(payload)
    else:
        _emit_human(payload)
    return EXIT_OK


__all__ = [
    "EXIT_COMPILE",
    "EXIT_IO",
    "EXIT_MANIFEST",
    "EXIT_OK",
    "EXIT_STALE_OUTPUT",
    "EXIT_USAGE",
    "InstallerResult",
    "ManifestError",
    "WindowsInstallerManifest",
    "build_parser",
    "check_installer",
    "compile_installer",
    "doctor_manifest",
    "generate_installer",
    "load_manifest",
    "main",
    "render_installer",
]


if __name__ == "__main__":
    raise SystemExit(main())
