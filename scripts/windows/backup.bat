@echo off
setlocal enabledelayedexpansion

set BACKUP_DIR=data\backups
mkdir %BACKUP_DIR% 2>nul

set DATESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%
set TIMESTAMP=%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo [BACKUP] Creating backup: %DATESTAMP%_%TIMESTAMP%

if exist data\memoria.db (
    copy /Y data\memoria.db "%BACKUP_DIR%\memoria_%DATESTAMP%_%TIMESTAMP%.db"
    echo [BACKUP] memoria.db copied
)

if exist data\memoria.index (
    copy /Y data\memoria.index "%BACKUP_DIR%\memoria.index_%DATESTAMP%_%TIMESTAMP%"
    echo [BACKUP] memoria.index copied
)

if exist data\memoria.index - do (
    copy /Y data\memoria.index "%BACKUP_DIR%\memoria.index_%DATESTAMP%_%TIMESTAMP%"
    echo [BACKUP] memoria.index copied
)

echo [BACKUP] Complete: %BACKUP_DIR%