echo off
echo.
echo PyGMI
echo =====
echo.
echo This console window is used to display error messages. 
echo If you do have any errors, you can send the message to:
echo pcole@geoscience.org.za
echo.
echo Loading PyGMI...
.\python\python.exe quickstart.py > err.log 2>&1
echo.
echo Latest Errors and Messages (also stored in %cd%\err.log):
type err.log
pause