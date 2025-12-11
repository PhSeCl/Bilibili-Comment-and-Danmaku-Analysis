@echo off
REM 一键创建并激活 Python 虚拟环境，并安装依赖
cd /d %~dp0
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pause