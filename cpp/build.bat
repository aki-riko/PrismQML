@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 (echo VCVARS_FAIL & exit /b 10)

set "QTDIR=D:\Qt\6.11.1\msvc2022_64"
set "PATH=%QTDIR%\bin;%PATH%"

cd /d D:\PrismQML\PrismQML\cpp

cmake -S . -B build -G "NMake Makefiles" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_PREFIX_PATH=%QTDIR% ^
  -DQt6_DIR=%QTDIR%\lib\cmake\Qt6
if errorlevel 1 (echo CMAKE_CONFIG_FAIL & exit /b 11)

cmake --build build
if errorlevel 1 (echo BUILD_FAIL & exit /b 12)

echo PRISM_BUILD_DONE
