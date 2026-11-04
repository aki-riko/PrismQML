# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Wheel build hook that bundles the crash runtime. 打包崩溃运行时的 wheel 构建钩子。

All package metadata lives in pyproject.toml. This file only extends build_py so
the sentry-native files staged by scripts/build_crash_runtime.py are copied into
the wheel under prismqml/_native/crash/. They never enter the source tree or the
sdist. Build wheels from the source directory (cibuildwheel, ``pip wheel .`` or
``python -m build --wheel``); a wheel built from an extracted sdist cannot see
the repository's .artifacts/ unless PRISM_ARTIFACT_ROOT points at it.
所有元数据在 pyproject.toml；本文件只扩展 build_py，把 scripts/build_crash_runtime.py
暂存的 sentry-native 文件复制进 wheel 的 prismqml/_native/crash/，不进入源码树或 sdist。
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List, Mapping, Optional


logger = logging.getLogger("prismqml.build")
ARTIFACT_ROOT_ENV = "PRISM_ARTIFACT_ROOT"
# Set to "1" in release builds so a missing runtime fails instead of warning
# 发布构建设为 "1"，缺少运行时直接失败而非告警
REQUIRE_RUNTIME_ENV = "PRISM_REQUIRE_CRASH_RUNTIME"
RUNTIME_PACKAGE_DIR = ("prismqml", "_native", "crash")


def crash_runtime_dir(environ: Optional[Mapping[str, str]] = None) -> Path:
    """Return the staged runtime directory. 返回暂存的运行时目录。"""
    env = os.environ if environ is None else environ
    configured = env.get(ARTIFACT_ROOT_ENV)
    root = Path(configured) if configured else Path(__file__).resolve().parent / ".artifacts"
    return root / "cpp" / "sentry-native" / "runtime"


def copy_crash_runtime(source: Path, build_lib: Path, required: bool) -> List[Path]:
    """Replace the wheel's crash runtime with the staged files. 用暂存文件替换 wheel 内运行时。"""
    destination = build_lib.joinpath(*RUNTIME_PACKAGE_DIR)
    if destination.exists():
        shutil.rmtree(destination)
    files = sorted(path for path in source.iterdir() if path.is_file()) if source.is_dir() else []
    if not files:
        message = f"crash runtime not found in {source}; run scripts/build_crash_runtime.py"
        if required:
            raise FileNotFoundError(message)
        logger.warning("%s; the wheel will not include crash reporting", message)
        return []
    destination.mkdir(parents=True)
    copied = []
    for path in files:
        target = destination / path.name
        shutil.copy2(path, target)
        copied.append(target)
    return copied


def build_py_with_crash_runtime():
    """Return a build_py that also bundles the crash runtime. 返回同时打包崩溃运行时的 build_py。

    setuptools is imported here, not at module level, so the helpers above stay
    importable where setuptools is absent (the Python 3.12+ test venvs).
    setuptools 在此导入而非模块顶层，使上面的辅助函数在无 setuptools 的环境中仍可导入。
    """
    from setuptools.command.build_py import build_py

    class BuildPyWithCrashRuntime(build_py):
        def run(self):
            super().run()
            if getattr(self, "editable_mode", False):
                return
            required = os.environ.get(REQUIRE_RUNTIME_ENV) == "1"
            self._crash_runtime_outputs = copy_crash_runtime(
                crash_runtime_dir(), Path(self.build_lib), required
            )
            for path in self._crash_runtime_outputs:
                logger.info("bundled crash runtime file %s", path)

        def get_outputs(self, include_bytecode=1):
            outputs = super().get_outputs(include_bytecode)
            return outputs + [str(path) for path in getattr(self, "_crash_runtime_outputs", [])]

    return BuildPyWithCrashRuntime


if __name__ == "__main__":
    from setuptools import setup

    setup(cmdclass={"build_py": build_py_with_crash_runtime()})
