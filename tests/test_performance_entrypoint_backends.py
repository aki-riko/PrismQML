# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Manual performance entrypoint backend contracts. 手工性能入口后端合同。"""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CPP_HOST = ROOT / "cpp" / "src" / "App.cpp"
PYTHON_HOST = ROOT / "prismqml" / "python" / "window" / "app.py"
PERFORMANCE_ENTRYPOINTS = (
    ROOT / "scripts" / "fps_probe.py",
    ROOT / "scripts" / "run_with_fps.py",
    ROOT / "tests" / "qml" / "bench_skin_frames.py",
    ROOT / "tests" / "qml" / "bench_calendar_range_bars.py",
    ROOT / "tests" / "qml" / "bench_windows_bar_content.py",
    ROOT / "tests" / "qml" / "bench_progress_ring_visibility.py",
)


def test_cpp_host_requests_direct3d11_as_its_only_graphics_backend():
    source = CPP_HOST.read_text(encoding="utf-8")

    assert "QSGRendererInterface::Direct3D11" in source
    assert "QSGRendererInterface::OpenGL" not in source
    windows_guard = source.index("#if defined(Q_OS_WIN)")
    direct3d11_request = source.index("QSGRendererInterface::Direct3D11")
    guard_end = source.index("#endif", direct3d11_request)
    assert windows_guard < direct3d11_request < guard_end


def test_python_host_requests_direct3d11_as_its_only_graphics_backend():
    source = PYTHON_HOST.read_text(encoding="utf-8")

    assert "QSGRendererInterface.GraphicsApi.Direct3D11" in source
    assert "QSGRendererInterface.OpenGL" not in source
    assert "GraphicsApi.OpenGL" not in source
    assert "configure_graphics_api" not in source


@pytest.mark.parametrize("entrypoint", PERFORMANCE_ENTRYPOINTS)
def test_manual_performance_entrypoint_rejects_non_direct3d11(entrypoint):
    source = entrypoint.read_text(encoding="utf-8")

    assert 'actual_api_name != "Direct3D11"' in source
    assert "QSGRendererInterface.OpenGL" not in source
    assert "GraphicsApi.OpenGL" not in source


@pytest.mark.parametrize("entrypoint", PERFORMANCE_ENTRYPOINTS[:2])
def test_gallery_performance_entrypoint_reuses_the_only_main(entrypoint):
    source = entrypoint.read_text(encoding="utf-8")

    assert "import examples.main as gallery" in source
    assert "gallery.QQmlApplicationEngine" in source
    assert "gallery.main()" in source
    assert "QQuickWindow.setGraphicsApi" not in source


@pytest.mark.parametrize("entrypoint", PERFORMANCE_ENTRYPOINTS[2:])
def test_standalone_benchmark_requests_direct3d11(entrypoint):
    source = entrypoint.read_text(encoding="utf-8")

    assert "QSGRendererInterface.GraphicsApi.Direct3D11" in source


def test_scroll_fps_probe_has_no_backend_override_or_silent_exception_path():
    source = PERFORMANCE_ENTRYPOINTS[0].read_text(encoding="utf-8")

    assert "PROBE_BACKEND" not in source
    assert "except Exception" not in source
    assert "except:" not in source


def test_fps_overlay_has_no_silent_exception_path():
    source = PERFORMANCE_ENTRYPOINTS[1].read_text(encoding="utf-8")

    assert "except Exception" not in source
    assert "except:" not in source
