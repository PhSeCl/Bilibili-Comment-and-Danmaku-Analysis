@echo off
REM 启动 Bilibili 评论与弹幕情感分析系统
cd /d %~dp0
streamlit run app.py
pause