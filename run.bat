rem ========== BASE ENV ==========
SET INTERNAL=%~dp0
SET INTERNAL=%INTERNAL:~0,-1%

rem ========== PYTHON ENV ==========
set CONDA_PATH1=C:\Anaconda\condabin\conda
SET PYTHON_PATH1=C:\Anaconda\envs\envJarvis\python.exe

echo %INTERNAL%

call "%CONDA_PATH1%" activate
"%PYTHON_PATH1%" "%INTERNAL%\main.py" 

 
pause
