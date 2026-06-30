# PrismQML C++ 宿主层 (prism)
# 与 PySide6 宿主平行: 让 C++ 应用以对称 API 调用同一套 QML 引擎。
# 目标 Qt: 6.11.1 (D:\Qt\6.11.1\msvc2022_64, 与 PySide6 对齐)
cmake_minimum_required(VERSION 3.16)
project(prism LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql
    QuickControls2 QuickLayouts QuickEffects)

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
    src/Icon.cpp
    src/DataModels.cpp
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
    include/prism/Accessors.h
    include/prism/Icon.h
    include/prism/DataModels.h
    include/prism/Registry.h
    include/prism/App.h
    include/prism/Window.h
)

target_include_directories(prism PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(prism PUBLIC
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Svg Qt6::Widgets Qt6::Network Qt6::Sql
    Qt6::QuickControls2 Qt6::QuickLayouts Qt6::QuickEffects
)

# Windows: 链接 DWM API (Shadow/Mica) + user32 (NativeWindow)
if(WIN32)
    target_link_libraries(prism PUBLIC dwmapi user32)
endif()

# 编译期默认 QML import 目录(开发树): 未设 PRISMQML_QML_DIR 环境变量时 resolveImportPath
# 兜底用它, 使 demo/gallery 等无需手动设环境变量即可 import PrismQML。指向含 PrismQML
# 子目录的父目录(addImportPath 约定)。安装后用户经 find_package(prism) 的 prism_QML_DIR。
if(NOT ANDROID AND NOT IOS)
    target_compile_definitions(prism PRIVATE
        PRISM_QML_DIR_DEFAULT="${CMAKE_CURRENT_SOURCE_DIR}/../prismqml")
endif()

# ==================== demo 可执行 ====================
option(PRISM_BUILD_DEMO "Build the C++ demo app" ON)
if(PRISM_BUILD_DEMO)
    qt_add_executable(prism_demo demo/main.cpp)
    target_link_libraries(prism_demo PRIVATE prism)
    # 桌面: 注入源码树页面默认路径, 使 demo 无需手动设 PRISM_DEMO_PAGES 即可运行
    if(NOT ANDROID AND NOT IOS)
        target_compile_definitions(prism_demo PRIVATE
            PRISM_DEMO_PAGES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/demo/pages")
    endif()

    # Android/iOS: QML 资源必须打进 bundle(无磁盘路径)。glob PrismQML 引擎 QML + svg +
    # i18n + demo pages 生成 qrc, prefix "/" 使 addImportPath("qrc:/") 能找到
    # qrc:/PrismQML/qmldir。demo main.cpp 在移动端走 qrc import path。
    if(ANDROID OR IOS)
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
        # 用 rcc 显式预编译 qrc -> cpp (最可控, 不依赖 AUTORCC 对生成qrc的处理)
        # rcc 在 host Qt 的 libexec 或 bin
        find_program(PRISM_RCC NAMES rcc
            PATHS "${QT_HOST_PATH}/bin" "${QT_HOST_PATH}/libexec"
            NO_DEFAULT_PATH)
        if(NOT PRISM_RCC)
            find_program(PRISM_RCC NAMES rcc)
        endif()
        set(_qrc_cpp "${CMAKE_CURRENT_BINARY_DIR}/qrc_prism_qml.cpp")
        add_custom_command(
            OUTPUT "${_qrc_cpp}"
            # --no-zstd: 不用 zstd 压缩资源, 避免链接时 undefined symbol
            # qt_resourceFeatureZstd(CI Android 链接配置下该符号未拉入 Qt6Core)
            COMMAND "${PRISM_RCC}" --name prism_qml --no-zstd
                    -o "${_qrc_cpp}" "${CMAKE_CURRENT_BINARY_DIR}/prism_qml.qrc"
            DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/prism_qml.qrc"
            VERBATIM)
        target_sources(prism_demo PRIVATE "${_qrc_cpp}")
        target_compile_definitions(prism_demo PRIVATE PRISM_QML_FROM_QRC)
    endif()

    # iOS: 可执行需为 app bundle + bundle identifier(否则 Xcode 无法生成 .app)
    if(IOS)
        set_target_properties(prism_demo PROPERTIES
            MACOSX_BUNDLE TRUE
            MACOSX_BUNDLE_GUI_IDENTIFIER "life.9li.prism.demo"
            MACOSX_BUNDLE_BUNDLE_NAME "PrismDemo"
            MACOSX_BUNDLE_SHORT_VERSION_STRING "1.0"
            MACOSX_BUNDLE_BUNDLE_VERSION "1"
            XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"  # iPhone+iPad
        )
    endif()
endif()

# ==================== gallery 可执行 (纯 C++ 完整组件画廊) ====================
# 加载 examples/pages 的 13 个组件展示页, 让纯 C++ 用户(无 Python)也能看到完整画廊。
# 桌面: 从磁盘加载 examples/pages (与 Python gallery 共享同一份页面源)。
option(PRISM_BUILD_GALLERY "Build the C++ gallery app" ON)
if(PRISM_BUILD_GALLERY AND NOT ANDROID AND NOT IOS)
    qt_add_executable(prism_gallery gallery/main.cpp)
    target_link_libraries(prism_gallery PRIVATE prism)
    # 注入源码树默认路径(开发树), 使 gallery 无需手动设环境变量即可运行。
    # 用户分发时可设 PRISM_GALLERY_PAGES / PRISM_GALLERY_ICON 环境变量覆盖。
    target_compile_definitions(prism_gallery PRIVATE
        PRISM_GALLERY_PAGES_DIR="${CMAKE_CURRENT_SOURCE_DIR}/../examples/pages"
        PRISM_GALLERY_ICON_DEFAULT="${CMAKE_CURRENT_SOURCE_DIR}/../examples/resources/app_icon.svg")
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

# QML 组件模块: 把 PrismQML 引擎 QML 源安装到 <prefix>/qml/PrismQML/, 使纯 C++ 用户
# find_package(prism) 后 addImportPath(prism_QML_DIR) 即可 `import PrismQML`。
# (引擎内部 249 个组件用相对 import 互引, 故按目录原样安装, 不做 qt_add_qml_module 重构)
set(PRISM_QML_INSTALL_DIR "${CMAKE_INSTALL_DATADIR}/prism/qml")
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../prismqml/PrismQML"
    DESTINATION "${PRISM_QML_INSTALL_DIR}"
    FILES_MATCHING
        PATTERN "*.qml"
        PATTERN "qmldir"
        PATTERN "*.js"
        PATTERN "*.json"
        PATTERN "*.svg"
        PATTERN "*.png"
        PATTERN "*.frag"
        PATTERN "*.qsb"
        PATTERN "__pycache__" EXCLUDE
)

# 随 QML 一并安装 LICENSE (MIT 合规: 分发的 QML 组件需附带许可证)
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../LICENSE"
    DESTINATION "${PRISM_QML_INSTALL_DIR}/PrismQML")

install(EXPORT prismTargets
    FILE prismTargets.cmake
    NAMESPACE prism::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)

# 生成 prismConfig.cmake (转发 Qt6 依赖查找 + 暴露 QML import 路径)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
"@PACKAGE_INIT@\n\
include(CMakeFindDependencyMacro)\n\
find_dependency(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Svg Widgets Network Sql QuickControls2 QuickLayouts QuickEffects)\n\
include(\"\${CMAKE_CURRENT_LIST_DIR}/prismTargets.cmake\")\n\
# QML 组件 import 路径: engine->addImportPath(prism_QML_DIR) 后即可 import PrismQML\n\
set_and_check(prism_QML_DIR \"@PACKAGE_PRISM_QML_INSTALL_DIR@\")\n")

set(PACKAGE_PRISM_QML_INSTALL_DIR "${PRISM_QML_INSTALL_DIR}")
configure_package_config_file(
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
    PATH_VARS PRISM_QML_INSTALL_DIR
)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/prismConfig.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/prism
)
