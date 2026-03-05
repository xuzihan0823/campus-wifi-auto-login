@echo off
chcp 65001 >nul

echo ================================
echo Campus WiFi Auto Login - Upload
echo ================================

cd /d C:\Users\10965\Desktop\login

echo.
echo [1] 初始化 Git 仓库...
git init

echo.
echo [2] 添加所有文件...
git add .

echo.
echo [3] 创建提交...
git commit -m "Initial commit"

echo.
echo [4] 设置主分支...
git branch -M main

echo.
echo [5] 连接 GitHub 仓库...
git remote add origin https://github.com/xuzihan0823/campus-wifi-auto-login.git

echo.
echo [6] 上传代码到 GitHub...
git push -u origin main

echo.
echo ================================
echo 上传完成！
echo 打开你的仓库查看：
echo https://github.com/xuzihan0823/campus-wifi-auto-login
echo ================================

pause