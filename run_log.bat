@echo off
chcp 65001 >nul
cd /d %~dp0

set CAMPUS_USER=2510631109
set CAMPUS_PASS=08230837
set CAMPUS_ISP=移动
set CAMPUS_PORTAL=http://172.16.54.18/

REM 睡眠唤醒后建议短时巡检（默认5分钟）
set CAMPUS_MONITOR_SECONDS=300
set CAMPUS_CHECK_INTERVAL=60
set CAMPUS_RETRY_TIMES=3
set CAMPUS_RETRY_BACKOFF=3

python login.py --monitor
pause