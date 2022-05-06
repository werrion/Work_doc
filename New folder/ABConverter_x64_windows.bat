@echo on

python --version 3>NUL
if NOT %ERRORLEVEL% == 0 exit /B 1

pip --version 3>NUL
if NOT %ERRORLEVEL% == 0 exit /B 1

pip install requests
pip install py7zr

python %~dp0..\impl\decompressDependencies.py %~dp0..

RMDIR /S /Q -rf %~dp0..\..\..\..\utils\ABConverter\build

"%~dp0..\..\download\cmake-3.21.4-windows-x86_64\bin\cmake.exe" ^
    -S "%~dp0..\..\..\..\utils\ABConverter" ^
    -B "%~dp0..\..\..\..\utils\ABConverter\build" ^
    -DABG_WINDOWS=ON ^
    -DVCPKG_TARGET_TRIPLET=x64-windows-static ^
    -DBUILD_TESTS=ON ^
    -DVCPKG_CRT_LINKAGE=static ^
    -DVCPKG_CHAINLOAD_TOOLCHAIN_FILE="%~dp0..\toolchains\windows.cmake" ^
    -DCMAKE_TOOLCHAIN_FILE="%~dp0..\..\3rd_party\scripts\buildsystems\vcpkg.cmake" ^
    -DABG_WINDOWS=ON ^
    -DCMAKE_GENERATOR_PLATFORM=x64 ^
    -DCMAKE_BUILD_TYPE=Release
	
if NOT %ERRORLEVEL% == 0 exit /B 1
	
"%~dp0..\..\download\cmake-3.21.4-windows-x86_64\bin\cmake.exe" ^
    --build "%~dp0..\..\..\..\utils\ABConverter\build" ^
    --config Release ^

    "%~dp0..\..\download\cmake-3.21.4-windows-x86_64\bin\cmake.exe" ^
    -S "%~dp0..\..\..\..\utils\ABConverter" ^
    -B "%~dp0..\..\..\..\utils\ABConverter\build" ^
    -DABG_WINDOWS=ON ^
    -DVCPKG_TARGET_TRIPLET=x64-windows-static ^
    -DBUILD_TESTS=ON ^
    -DVCPKG_CRT_LINKAGE=static ^
    -DVCPKG_CHAINLOAD_TOOLCHAIN_FILE="%~dp0..\toolchains\windows.cmake" ^
    -DCMAKE_TOOLCHAIN_FILE="%~dp0..\..\3rd_party\scripts\buildsystems\vcpkg.cmake" ^
    -DCMAKE_GENERATOR_PLATFORM=x64 ^
    -DCMAKE_BUILD_TYPE=Debug

if NOT %ERRORLEVEL% == 0 exit /B 1

"%~dp0..\..\download\cmake-3.21.4-windows-x86_64\bin\cmake.exe" ^
    --build "%~dp0..\..\..\..\utils\ABConverter\build" ^
    --config Debug ^
    --target install

