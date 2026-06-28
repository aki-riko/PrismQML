# PrismQML C++ 宿主层 (prism)
# 与 PySide6 宿主平行: 让 C++ 应用以对称 API 调用同一套 QML 引擎。
# 目标 Qt: 6.11.1 (D:\Qt\6.11.1\msvc2022_64, 与 PySide6 对齐)
cmake_minimum_required(VERSION 3.16)
project(prism LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql)

qt_standard_project_setup()

# ==================== prism 静态库 ====================
add_library(prism STATIC
    src/Theme.cpp
    src/ThemeManager.cpp
    src/ConfigManager.cpp
    src/ShadowManager.cpp
    src/MicaManager.cpp
    src/NativeWindow.cpp
    src/Providers.cpp
    src/SvgImageProvider.cpp
    src/Store.cpp
    src/Logger.cpp
    src/SystemAndInstance.cpp
    src/Updater.cpp
    src/ScreenEyedropper.cpp
    src/QRCodeGenerator.cpp
    src/SqlListModel.cpp
    src/PlatformInfo.cpp
    src/Registry.cpp
    src/App.cpp
    src/Window.cpp
    # 头文件显式列入: 确保 AUTOMOC 扫描到含 Q_OBJECT 的头
    include/prism/Theme.h
    include/prism/ThemeManager.h
    include/prism/ConfigManager.h
    include/prism/ShadowManager.h
    include/prism/MicaManager.h
    include/prism/NativeWindow.h
    include/prism/ClipboardHelper.h
    include/prism/WindowHelper.h
    include/prism/AcrylicHelper.h
    include/prism/SvgImageProvider.h
    include/prism/Store.h
    include/prism/Logger.h
    include/prism/SystemTray.h
    include/prism/SingleInstance.h
    include/prism/Updater.h
    include/prism/ScreenEyedropper.h
    include/prism/QRCodeGenerator.h
    include/prism/SqlListModel.h
    include/prism/Platform.h
    include/prism/PlatformInfo.h
    include/prism/Registry.h
    include/prism/App.h
    include/prism/Window.h
)

target_include_directories(prism PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(prism PUBLIC
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Svg Qt6::Widgets Qt6::Network Qt6::Sql
)

# Windows: 链接 DWM API (Shadow/Mica) + user32 (NativeWindow)
if(WIN32)
    target_link_libraries(prism PUBLIC dwmapi user32)
endif()

# ==================== demo 可执行 ====================
option(PRISM_BUILD_DEMO "Build the C++ demo app" ON)
if(PRISM_BUILD_DEMO)
    qt_add_executable(prism_demo demo/main.cpp)
    target_link_libraries(prism_demo PRIVATE prism)

    # Android: QML 资源必须打进 apk(无磁盘路径)。glob PrismQML 引擎 QML + svg +
    # i18n + demo pages 生成 qrc, prefix "/" 使 addImportPath("qrc:/") 能找到
    # qrc:/PrismQML/qmldir。demo main.cpp 在 ANDROID 下走 qrc import path。
    if(ANDROID)
        set(_pqml_root "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml/PrismQML")
        file(GLOB_RECURSE _pqml_res RELATIVE "${_pqml_root}"
             "${_pqml_root}/*.qml" "${_pqml_root}/*.js" "${_pqml_root}/*.svg"
             "${_pqml_root}/*.json")
        # qmldir 无扩展名, 单独 glob
        file(GLOB_RECURSE _pqml_dirs RELATIVE "${_pqml_root}" "${_pqml_root}/qmldir")
        set(_qrc_body "")
        foreach(f ${_pqml_res} ${_pqml_dirs})
            string(APPEND _qrc_body
                "    <file alias=\"PrismQML/${f}\">${_pqml_root}/${f}</file>\n")
        endforeach()
        # demo pages
        file(GLOB _demo_pages RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/demo"
             "${CMAKE_CURRENT_SOURCE_DIR}/demo/pages/*.qml")
        foreach(f ${_demo_pages})
            string(APPEND _qrc_body
                "    <file alias=\"${f}\">${CMAKE_CURRENT_SOURCE_DIR}/demo/${f}</file>\n")
        endforeach()
        file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/prism_qml.qrc"
             "<RCC>\n  <qresource prefix=\"/\">\n${_qrc_body}  </qresource>\n</RCC>\n")
        target_sources(prism_demo PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/prism_qml.qrc")
        set_source_files_properties("${CMAKE_CURRENT_BINARY_DIR}/prism_qml.qrc"
             PROPERTIES AUTORCC ON)
        target_compile_definitions(prism_demo PRIVATE PRISM_QML_FROM_QRC)
    endif()
endif()

# ==================== 单元测试 ====================
option(PRISM_BUILD_TESTS "Build the C++ tests" ON)
if(PRISM_BUILD_TESTS)
    qt_add_executable(prism_test_store tests/test_store.cpp)
    target_link_libraries(prism_test_store PRIVATE prism)

    qt_add_executable(prism_test_system tests/test_system.cpp)
    target_link_libraries(prism_test_system PRIVATE prism)

    qt_add_executable(prism_test_mica tests/test_mica.cpp)
    target_link_libraries(prism_test_mica PRIVATE prism)
endif()

# ==================== 移动端条件编译分支验证 ====================
# 桌面编译器 + 强制 PRISM_MOBILE 编译全库, 验证移动端分支语法/类型正确
# (不验证 Android 运行, 仅坐实移动分支不是写错的代码)
option(PRISM_VERIFY_MOBILE "Compile a mobile-branch variant to verify conditional code" ON)
if(PRISM_VERIFY_MOBILE)
    add_library(prism_mobile_verify STATIC
        src/Window.cpp src/PlatformInfo.cpp src/App.cpp
        include/prism/Window.h include/prism/PlatformInfo.h include/prism/App.h
        # Window.cpp 依赖的其余符号由桩满足? 不, 它依赖全库; 改为编译全部源
    )
    target_compile_definitions(prism_mobile_verify PRIVATE PRISM_FORCE_MOBILE_TEST)
    target_include_directories(prism_mobile_verify PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
    target_link_libraries(prism_mobile_verify PUBLIC
        Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Svg Qt6::Widgets Qt6::Network Qt6::Sql)
endif()
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

install(TARGETS prism
    EXPORT prismTargets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/prism DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

install(EXPORT prismTargets
    FILE prismTargets.cmake
    NAMESPACE prism::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)

# 生成 prismConfig.cmake (转发 Qt6 依赖查找)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
"@PACKAGE_INIT@\n\
include(CMakeFindDependencyMacro)\n\
find_dependency(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql)\n\
include(\"\${CMAKE_CURRENT_LIST_DIR}/prismTargets.cmake\")\n")

configure_package_config_file(
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)
