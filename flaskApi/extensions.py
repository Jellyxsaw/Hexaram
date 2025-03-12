# extensions.py
import configparser

from flask_sqlalchemy import SQLAlchemy

# 讀取 config.ini 設定檔
config = configparser.ConfigParser()
config.read('config.ini',encoding='utf-8')

# 從設定檔中取得資料庫連線參數
db_host = config['database']['DB_HOST']
db_port = config['database']['DB_PORT']
db_name = config['database']['DB_NAME']
db_user = config['database']['DB_USER']
db_password = config['database']['DB_PASSWORD']

# 組成 SQLAlchemy 連線字串
db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# 建立 SQLAlchemy 實例
db = SQLAlchemy()
