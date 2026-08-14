@echo off
setlocal
REM Build APK from an existing configured tree 从已配置构建树生成 APK

call "%~dp0build_env.bat" require-file NINJA
if errorlevel 1 exit /b 10
if not defined PRISM_ARTIFACT_ROOT set "PRISM_ARTIFACT_ROOT=%~dp0..\.artifacts"
if not defined PRISM_ANDROID_BUILD_DIR set "PRISM_ANDROID_BUILD_DIR=%PRISM_ARTIFACT_ROOT%\cpp\android-arm64"

pushd "%~dp0"
if errorlevel 1 (echo CPP_DIR_FAIL & exit /b 10)
call "%NINJA%" -C "%PRISM_ANDROID_BUILD_DIR%" prism_demo_make_apk
if errorlevel 1 (popd & echo APK_BUILD_FAIL & exit /b 12)

popd
echo APK_BUILD_OK
exit /b 0
