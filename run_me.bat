@ECHO OFF
FOR /L %%i IN (0,1,1000) DO (
	taskkill /F /IM rdi_xsct.exe
	python.exe .\fi.py)
PAUSE