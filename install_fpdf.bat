@echo off
echo Installing fpdf2...
python -m pip install fpdf2
if %errorlevel% neq 0 (
    echo Failed to install fpdf2, trying alternative...
    py -m pip install fpdf2
)
echo Done!
pause