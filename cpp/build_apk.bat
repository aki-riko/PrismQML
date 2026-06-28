@echo off
set "JAVA_HOME=D:\Qt\_tools\jdk17_extract\jdk-17.0.19+10"
set "ANDROID_SDK_ROOT=D:\Qt\_tools\android-sdk"
set "ANDROID_NDK_ROOT=D:\Qt\_tools\android-sdk\ndk\27.2.12479018"
set "CMAKEBIN=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
set "PATH=%JAVA_HOME%\bin;%CMAKEBIN%;%PATH%"
set "NINJA=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
cd /d D:\PrismQML\PrismQML\cpp
"%NINJA%" -C build-android prism_demo_make_apk
echo APK_BUILD_EXIT=%errorlevel%
