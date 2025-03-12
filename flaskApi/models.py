# models.py
from datetime import datetime

from extensions import db


class APIRequestLog(db.Model):
    __tablename__ = 'api_requests'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    request_method = db.Column(db.String(10))
    endpoint = db.Column(db.Text)
    request_data = db.Column(db.Text)
    response_data = db.Column(db.JSON)  # 新增欄位，使用 db.JSON 對應 PostgreSQL 的 JSONB
    user_agent = db.Column(db.Text)
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
