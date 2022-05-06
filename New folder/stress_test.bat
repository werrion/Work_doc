setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION


set DEF_INSTANCE_COUNT=30
set TEST_WORK_DIR=%TMP%\ABF_STRESS_TEST


set RESULT_SERVER=\\abstorage.ab-games.com\ABgames
set RESULT_FOLDER=\\abstorage.ab-games.com\ABgames\FW\tests

net use %RESULT_SERVER%

set SESSION_RESULT=%RESULT_FOLDER%\%DATE%\%COMPUTERNAME%


if not exist "%SESSION_RESULT%" mkdir "%SESSION_RESULT%"



if "%1"=="" ( 
	set INSTANCE_COUNT=%DEF_INSTANCE_COUNT% 

) else (
	set INSTANCE_COUNT=%1

)


echo Instance count: %INSTANCE_COUNT% > %SESSION_RESULT%/main.log
echo Time:%time%>>%SESSION_RESULT%/main.log


if not exist "%TEST_WORK_DIR%" mkdir "%TEST_WORK_DIR%"

FOR /L %%i IN (1,1,%INSTANCE_COUNT%) DO (
	set CURRENT_DIR="%TEST_WORK_DIR%\%%i"
	echo CURRENT_DIR=!CURRENT_DIR!
	set SCENARIO_FILE=test_stress10.1.txt
	set INSTANCE_RESULT=%SESSION_RESULT%\%%i
	
	if exist "!CURRENT_DIR!" del /Q /S "!CURRENT_DIR!\*"
	if not exist "!CURRENT_DIR!" mkdir !%CURRENT_DIR!"
	
	if not exist "!CURRENT_DIR!/data" mkdir !%CURRENT_DIR!/data"
	
	copy ..\data\ "!CURRENT_DIR!\data"
	copy ..\tests\test_stress10.1.txt "!CURRENT_DIR!"
	copy ..\build\Release\ABUtility.exe "!CURRENT_DIR!"
	copy .\test_instance.bat "!CURRENT_DIR!"
	
	pushd "!CURRENT_DIR!"
	
	echo cmd.exe /C "test_instance.bat !SCENARIO_FILE! !INSTANCE_RESULT! "
	start cmd.exe /C "test_instance.bat !SCENARIO_FILE! !INSTANCE_RESULT!"
	
	SET /A TM=!RANDOM!%%10+1
	
	
	echo !TM!
	timeout !TM!
	
	popd

)