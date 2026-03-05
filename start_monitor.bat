@echo off
chcp 65001 >nul
cd /d %~dp0

REM ===== 账号/密码/运营商（开源时不要写真值）=====
set CAMPUS_USER=你的学号
set CAMPUS_PASS=你的密码
set CAMPUS_ISP=移动
set CAMPUS_PORTAL=http://172.16.54.18/

REM ===== 检测频率（秒）=====
set CAMPUS_CHECK_INTERVAL=30

REM 后台运行，不显示控制台窗口
start "" /min pythonw monitor.py
exit