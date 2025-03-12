# apilogger.py
import json

from flask import request, g

from extensions import db
from models import APIRequestLog

# 要過濾的噪音路徑（完全匹配）
NOISE_PATHS = ['/', '/favicon.ico']
# 過濾 Swagger 相關請求
SWAGGER_PREFIXES = ['/apidocs', '/flasgger_static', '/apispec']


def log_request():
    # 過濾基本噪音路徑
    if request.path in NOISE_PATHS:
        return
    # 過濾 Swagger 相關請求
    if any(request.path.startswith(prefix) for prefix in SWAGGER_PREFIXES):
        return

    ip = request.remote_addr
    method = request.method
    endpoint = request.path
    data = request.get_json() if request.is_json else request.values.to_dict()
    user_agent = request.headers.get('User-Agent')

    log = APIRequestLog(
        ip_address=ip,
        request_method=method,
        endpoint=endpoint,
        request_data=str(data),
        user_agent=user_agent
    )
    try:
        db.session.add(log)
        db.session.commit()
        # 將 log 的 id 暫存到 g 中，方便後續更新回應資料
        g.api_log_id = log.id
    except Exception as e:
        db.session.rollback()
        print(f"記錄 API log 發生錯誤：{e}")


def log_response(response):
    # 僅對 /predict_team 路徑記錄回應資料
    if request.path == '/predict_team' and hasattr(g, 'api_log_id'):
        try:
            log = APIRequestLog.query.get(g.api_log_id)
            response_text = response.get_data(as_text=True)
            print(f"回應內容: {response_text[:200]}")  # 除錯印出部分內容

            if log:
                # 嘗試將回應資料解析成 JSON，若失敗則存為 None 或空值
                try:
                    json_data = json.loads(response_text)
                except Exception as e:
                    print(f"解析回應 JSON 失敗：{e}")
                    json_data = None
                log.response_data = json_data
                db.session.commit()
                print("成功更新 response_data")
            else:
                print("無法找到對應的 log 記錄")
        except Exception as e:
            db.session.rollback()
            print(f"更新 response log 發生錯誤：{e}")
    return response


def register_api_logger(app):
    # 註冊 before_request 與 after_request 處理
    app.before_request(log_request)
    app.after_request(log_response)
