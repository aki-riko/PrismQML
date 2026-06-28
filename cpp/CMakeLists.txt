# PrismQML C++ 宿主层 (prism)
# 与 PySide6 宿主平行: 让 C++ 应用以对称 API 调用同一套 QML 引擎。
# 目标 Qt: 6.11.1 (D:\Qt\6.11.1\msvc2022_64, 与 PySide6 对齐)
cmake_minimum_required(VERSION 3.16)
project(prism LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick)

qt_standard_project_setup()

# ==================== prism 静态库 ====================
add_library(prism STATIC
    src/Theme.cpp
    src/ThemeManager.cpp
    src/Registry.cpp
    src/App.cpp
    src/Window.cpp
    # 头文件显式列入: 确保 AUTOMOC 扫描到含 Q_OBJECT 的 ThemeManager.h
    include/prism/Theme.h
    include/prism/ThemeManager.h
    include/prism/Registry.h
    include/prism/App.h
    include/prism/Window.h
)

target_include_directories(prism PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(prism PUBLIC
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick
)

# ==================== demo 可执行 ====================
option(PRISM_BUILD_DEMO "Build the C++ demo app" ON)
if(PRISM_BUILD_DEMO)
    qt_add_executable(prism_demo demo/main.cpp)
    target_link_libraries(prism_demo PRIVATE prism)
endif()
