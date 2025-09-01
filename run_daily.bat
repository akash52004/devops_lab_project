@echo off
REM Navigate to project folder
cd /d "C:\Users\varshitha korepu\Downloads\offline-news-sms-bot\offline-news-sms-bot"

REM Activate virtual environment
call .venv\Scripts\activate

REM Run daily SMS script
python send_daily.py
