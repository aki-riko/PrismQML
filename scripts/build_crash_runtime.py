# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Build the pinned sentry-native crash runtime. 构建固定版本的 sentry-native 崩溃运行时。

Checks out the commit recorded in ``crash_runtime_pin.json``, builds it with the
Crashpad backend and no network transport, and stages the files a crash
reporter needs at runtime. Everything is written under ``.artifacts/cpp/``.
检出 ``crash_runtime_pin.json`` 记录的提交，以 Crashpad 后端、无网络传输构建，
并暂存运行时所需文件。全部产物写入 ``.artifacts/cpp/``。
"""

import argparse
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple


logger = logging.getLogger("prismqml.crash_runtime")
REPO_ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = Path(__file__).with_name("crash_runtime_pin.json")
ARTIFACT_ROOT_ENV = "PRISM_ARTIFACT_ROOT"
CMAKE_COMMAND_ENV = "PRISM_CMAKE_COMMAND"
BUILD_CONFIG = "RelWithDebInfo"
CMAKE_OPTIONS = (
    "-DSENTRY_BACKEND=crashpad",
    "-DSENTRY_TRANSPORT=none",
    "-DSENTRY_BUILD_SHARED_LIBS=ON",
    "-DSENTRY_BUILD_TESTS=OFF",
    "-DSENTRY_BUILD_EXAMPLES=OFF",
    # Compile Crashpad's bundled zlib instead of linking the system one, so the
    # runtime adds no shared-library dependency beyond the platform baseline
    # 编译 Crashpad 自带 zlib 而非链接系统库，不额外引入共享库依赖
    "-DCRASHPAD_ZLIB_SYSTEM=OFF",
)
# crashpad_handler.exe runs as its own process and crashpad_wer.dll is loaded by
# WerFault, so neither can rely on the host's VC++ runtime. Link it statically.
# crashpad_handler.exe 是独立进程、crashpad_wer.dll 由 WerFault 加载，二者都不能依赖宿主的
# VC++ 运行库，因此静态链接。
PLATFORM_CMAKE_OPTIONS: Mapping[str, Tuple[str, ...]] = {
    "win32": ("-DSENTRY_BUILD_RUNTIMESTATIC=ON",),
}
# Files a crash reporter loads or launches, per platform 各平台崩溃上报运行时文件
RUNTIME_FILES: Mapping[str, Tuple[str, ...]] = {
    "win32": ("sentry.dll", "crashpad_handler.exe", "crashpad_wer.dll"),
    "linux": ("libsentry.so", "crashpad_handler"),
    "darwin": ("libsentry.dylib", "crashpad_handler"),
}
HANDLER_NAMES = frozenset(("crashpad_handler", "crashpad_handler.exe"))
Runner = Callable[..., subprocess.CompletedProcess]


@dataclass(frozen=True)
class Pin:
    """Pinned upstream revision. 固定的上游版本。"""

    repository: str
    tag: str
    commit: str


@dataclass(frozen=True)
class Layout:
    """Artifact directories for one build. 一次构建的产物目录。"""

    artifact_root: Path
    source: Path
    build: Path
    install: Path
    runtime: Path


def load_pin(path: Path = PIN_FILE) -> Pin:
    """Read and validate the pin file. 读取并校验版本锁定文件。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    pin = Pin(data["repository"], data["tag"], data["commit"])
    if len(pin.commit) != 40 or any(c not in "0123456789abcdef" for c in pin.commit):
        raise ValueError(f"pin commit must be a full lowercase sha1: {pin.commit!r}")
    return pin


def resolve_layout(environ: Optional[Mapping[str, str]] = None) -> Layout:
    """Resolve directories, honouring PRISM_ARTIFACT_ROOT. 解析目录，遵循 PRISM_ARTIFACT_ROOT。"""
    env = os.environ if environ is None else environ
    configured = env.get(ARTIFACT_ROOT_ENV)
    artifact_root = Path(configured) if configured else REPO_ROOT / ".artifacts"
    base = artifact_root / "cpp" / "sentry-native"
    return Layout(
        artifact_root, base / "src", base / "build", base / "install", base / "runtime"
    )


def _git_head(source: Path, run: Runner) -> str:
    result = run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _uninitialized_submodules(source: Path, run: Runner) -> list:
    result = run(
        ["git", "-C", str(source), "submodule", "status", "--recursive"],
        check=True, capture_output=True, text=True,
    )
    return [line.split()[-1] for line in result.stdout.splitlines() if line.startswith("-")]


def ensure_checkout(pin: Pin, layout: Layout, run: Runner = subprocess.run) -> None:
    """Clone the pinned tag or verify an existing checkout. 克隆固定 tag 或校验已有检出。"""
    if not layout.source.exists():
        layout.source.parent.mkdir(parents=True, exist_ok=True)
        logger.info("cloning %s %s", pin.repository, pin.tag)
        run(
            ["git", "clone", "--depth", "1", "--branch", pin.tag,
             "--recurse-submodules", "--shallow-submodules",
             pin.repository, str(layout.source)],
            check=True,
        )
    head = _git_head(layout.source, run)
    if head != pin.commit:
        raise ValueError(
            f"{layout.source} is at {head}, expected pinned {pin.commit}; "
            "remove the directory to re-clone"
        )
    missing = _uninitialized_submodules(layout.source, run)
    if missing:
        raise ValueError(f"uninitialized submodules in {layout.source}: {missing}")


def cmake_command(environ: Optional[Mapping[str, str]] = None) -> str:
    """Return the CMake executable, honouring PRISM_CMAKE_COMMAND. 返回 CMake 可执行文件。"""
    env = os.environ if environ is None else environ
    return env.get(CMAKE_COMMAND_ENV) or "cmake"


def build_commands(
    layout: Layout, cmake: str, platform: str = sys.platform
) -> Tuple[list, list, list]:
    """Return configure, build and install commands. 返回配置、构建与安装命令。"""
    configure = [
        cmake, "-S", str(layout.source), "-B", str(layout.build),
        f"-DCMAKE_BUILD_TYPE={BUILD_CONFIG}",
        f"-DCMAKE_INSTALL_PREFIX={layout.install}",
        *CMAKE_OPTIONS,
        *PLATFORM_CMAKE_OPTIONS.get(platform, ()),
    ]
    build = [cmake, "--build", str(layout.build), "--config", BUILD_CONFIG, "--parallel"]
    install = [cmake, "--install", str(layout.build), "--config", BUILD_CONFIG]
    return configure, build, install


def _find_unique(root: Path, name: str) -> Path:
    matches = sorted(path for path in root.rglob(name) if path.is_file())
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one {name} under {root}, found {matches}")
    return matches[0]


def _reset_runtime_dir(layout: Layout) -> None:
    runtime = layout.runtime.resolve(strict=False)
    if layout.artifact_root.resolve(strict=False) not in runtime.parents:
        raise ValueError(f"refusing to reset {runtime} outside {layout.artifact_root}")
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir(parents=True)


def stage_runtime(layout: Layout, platform: str = sys.platform) -> Dict[str, Path]:
    """Copy runtime files from the install tree into one directory. 暂存运行时文件。"""
    if platform not in RUNTIME_FILES:
        raise ValueError(f"unsupported platform for crash runtime: {platform}")
    sources = {name: _find_unique(layout.install, name) for name in RUNTIME_FILES[platform]}
    _reset_runtime_dir(layout)
    staged = {}
    for name, source in sources.items():
        destination = layout.runtime / name
        shutil.copy2(source, destination)
        if name in HANDLER_NAMES and platform != "win32":
            mode = destination.stat().st_mode
            destination.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        staged[name] = destination
    return staged


def build_runtime(run: Runner = subprocess.run) -> Dict[str, Path]:
    """Run checkout, build, install and staging. 执行检出、构建、安装与暂存。"""
    pin = load_pin()
    layout = resolve_layout()
    ensure_checkout(pin, layout, run)
    for command in build_commands(layout, cmake_command()):
        logger.info("running %s", " ".join(command))
        run(command, check=True)
    return stage_runtime(layout)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments. 解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Build the crash runtime. 构建崩溃运行时。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parse_args(argv)
    try:
        staged = build_runtime()
    except subprocess.CalledProcessError as exc:
        logger.error("command failed with exit code %s: %s", exc.returncode, exc.cmd)
        return 1
    except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
        logger.error("crash runtime build failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected crash runtime build failure")
        return 1
    for name, path in staged.items():
        logger.info("staged %s -> %s", name, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
