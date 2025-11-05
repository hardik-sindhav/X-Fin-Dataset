@echo off
echo Uploading project to VPS...
echo IP: 147.93.97.60
echo.
cd /d "C:\Users\HP\Desktop\X Fin Dataset"
echo Uploading files...
scp -r * root@147.93.97.60:/var/www/x-fin-dataset/
echo.
echo Upload complete!
pause

