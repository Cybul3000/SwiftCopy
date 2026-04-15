@echo off
echo Installing/updating PyInstaller...
.venv\Scripts\pip install -r requirements-dev.txt --quiet
echo Building SwiftCopy...
.venv\Scripts\pyinstaller build.spec --clean --noconfirm
if %ERRORLEVEL% neq 0 (
    echo Build failed.
    exit /b %ERRORLEVEL%
)
echo.
echo Done! Output: dist\SwiftCopy.exe
