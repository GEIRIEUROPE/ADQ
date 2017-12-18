@ECHO OFF

IF DEFINED ProgramW6432 (
SET SPDDIR="%ProgramW6432%\SP Devices"
) ELSE (
SET SPDDIR="%ProgramFiles%\SP Devices"
)

IF EXIST ..\Release\adqapi.dll GOTO COPY_DEV_FILES
IF EXIST %SPDDIR%\ADQAPI\adqapi.dll GOTO COPY_INSTALLED_FILES
GOTO ERROR

:COPY_DEV_FILES
ECHO Copying development ADQAPI...
copy ..\Release\adqapi.dll .\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy ..\Release\adqapi.lib .\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy ..\Release\adqapi.h .
IF NOT ERRORLEVEL 0 GOTO ERROR
GOTO END

:COPY_INSTALLED_FILES
ECHO Copying installed ADQAPI...
copy %SPDDIR%\ADQAPI\adqapi.dll .\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy %SPDDIR%\ADQAPI\adqapi.lib .\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy %SPDDIR%\ADQAPI\adqapi.h .
IF NOT ERRORLEVEL 0 GOTO ERROR
GOTO END

:ERROR
ECHO Error, missing ADQAPI files!
EXIT /B 1

:END
ECHO ...done!
EXIT /B 0
