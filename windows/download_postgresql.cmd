@echo off
setlocal
chcp 65001 >nul
title Download PostgreSQL 17
set "PG_DOWNLOAD_DIR=%~dp0"
set "PG_INSTALLER_NAME=postgresql-17.11-5-windows-x64.exe"
set "PG_DOWNLOAD_URL=https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64.exe"
set "PG_DOWNLOAD_SHA256=612C7F5400A003AAFFA0372CB273EED52278F93C680AB911EB9CB2229E329072"

echo Скачивание официального установщика PostgreSQL 17 для Windows x64.
echo Файл большой. Дождитесь завершения загрузки.
echo.

powershell.exe -NoLogo -NoProfile -Command ^
 "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';" ^
 "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
 "$target = Join-Path $env:PG_DOWNLOAD_DIR $env:PG_INSTALLER_NAME;" ^
 "$partial = $target + '.' + [guid]::NewGuid().ToString('N') + '.download';" ^
 "try {" ^
 "  if (Test-Path -LiteralPath $target) {" ^
 "    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $env:PG_DOWNLOAD_SHA256) {" ^
 "      throw 'An existing installer has a different SHA256. Move it to another folder and retry.';" ^
 "    };" ^
 "    Write-Host ('Verified installer already exists: ' + $target); exit 0;" ^
 "  };" ^
 "  Invoke-WebRequest -UseBasicParsing -Uri $env:PG_DOWNLOAD_URL -OutFile $partial;" ^
 "  if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $env:PG_DOWNLOAD_SHA256) {" ^
 "    throw 'SHA256 mismatch. The downloaded file was not saved as an executable.';" ^
 "  };" ^
 "  Move-Item -LiteralPath $partial -Destination $target;" ^
 "  Write-Host ('Downloaded and verified: ' + $target);" ^
 "  exit 0;" ^
 "} catch {" ^
 "  if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue };" ^
 "  [Console]::Error.WriteLine($_.Exception.Message); exit 1;" ^
 "}"

if errorlevel 1 goto download_failed
echo.
echo Готово. Установщик сохранен рядом с этим файлом:
echo %PG_INSTALLER_NAME%
echo Дважды щелкните по установщику для начала установки.
echo Затем следуйте инструкции INSTALL_POSTGRESQL.txt.
pause
exit /b 0

:download_failed
echo.
echo Загрузка не завершилась. Сообщение об ошибке находится выше.
echo Повторите запуск или откройте ссылку в браузере:
echo %PG_DOWNLOAD_URL%
pause
exit /b 1
