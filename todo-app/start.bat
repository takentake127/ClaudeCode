@echo off
:: Todoアプリ起動スクリプト
:: ブラウザを開いてからFlaskサーバーを起動する

start http://127.0.0.1:5000

call C:\Users\G7sco\anaconda3\Scripts\activate.bat claude-env
cd /d E:\ClaudeCode\todo-app
python app.py
