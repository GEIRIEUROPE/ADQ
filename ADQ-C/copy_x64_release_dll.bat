@ECHO OFF

IF DEFINED ProgramW6432 (
SET SPDDIR="%ProgramW6432%\SP Devices"
) ELSE (
SET SPDDIR="%ProgramFiles%\SP Devices"
)

IF EXIST ..\x64\Release\adqapi.dll GOTO COPY_DEV_FILES
IF EXIST %SPDDIR%\ADQAPI_x64\adqapi.dll GOTO COPY_INSTALLED_FILES
GOTO ERROR

:COPY_DEV_FILES
ECHO Copying development ADQAPI...
copy ..\x64\Release\adqapi.dll .\x64\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy ..\x64\Release\adqapi.lib .\x64\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy ..\Release\adqapi.h .
IF NOT ERRORLEVEL 0 GOTO ERROR
GOTO END

:COPY_INSTALLED_FILES
ECHO Copying installed ADQAPI...
copy %SPDDIR%\ADQAPI_x64\adqapi.dll .\x64\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy %SPDDIR%\ADQAPI_x64\adqapi.lib .\x64\Release\
IF NOT ERRORLEVEL 0 GOTO ERROR
copy %SPDDIR%\ADQAPI_x64\adqapi.h .
IF NOT ERRORLEVEL 0 GOTO ERROR
GOTO END

:ERROR
ECHO Error, missing ADQAPI files!
EXIT /B 1

:END
ECHO ...done!
EXIT /B 0
