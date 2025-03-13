import configparser
import itertools

from flasgger import Swagger
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from apilogger import register_api_logger
from extensions import db, db_uri
from pureARAMPredictor import ARAMPredictor

# 讀取 config.ini 設定檔
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
bucket_name = config['gcs']['BUCKET_NAME']

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.config['SWAGGER'] = {
    'uiversion': 3,
    'info': {
        'title': 'pinkyJelly 的 hexaram API',
        'version': '1.0.0',
        'description': '主要開發文檔放在 https://github.com/Jellyxsaw/Hexaram/'
    }
}

swagger = Swagger(app)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 SQLAlchemy
db.init_app(app)

# 註冊 API 請求日誌功能
register_api_logger(app)

# 建立模型預測器實例
predictor = ARAMPredictor(bucket_name)


@app.route('/predict_team', methods=['POST'])
def predict_team():
    """
    預測隊伍勝率
    ---
    tags:
      - 預測 API
    parameters:
      - in: body
        name: body
        description: 輸入的英雄列表（5~15位）
        required: true
        schema:
          type: object
          properties:
            heroes:
              type: array
              items:
                type: string
              example: ["Ahri", "Garen", "Lux", "Yasuo", "Ezreal"]
    responses:
      200:
        description: 勝率最高的前 10 組隊伍
        schema:
          type: object
          properties:
            top_teams:
              type: array
              items:
                type: object
                properties:
                  team:
                    type: array
                    items:
                      type: string
                  win_rate:
                    type: number
    """
    data = request.get_json()
    if not data or "heroes" not in data:
        return jsonify({"error": "請提供英雄列表，格式：{'heroes': ['英雄1', '英雄2', ...]}"}), 400

    heroes = data["heroes"]
    if not isinstance(heroes, list):
        return jsonify({"error": "heroes 必須是一個列表"}), 400

    n = len(heroes)
    if n < 5 or n > 15:
        return jsonify({"error": "請提供 5 至 15 位英雄"}), 400

    try:
        # 如果只有 5 位英雄，直接單筆預測
        if n == 5:
            win_rate = predictor.predict_team_strength(heroes)
            result = [{"team": heroes, "win_rate": float(win_rate)}]
        else:
            # 產生所有 5 人組合（注意：15 人時共有 3003 組）
            teams = list(itertools.combinations(heroes, 5))
            team_lists = [list(team) for team in teams]
            win_rates = predictor.batch_predict(team_lists)
            results = [{"team": team, "win_rate": float(rate)} for team, rate in zip(team_lists, win_rates)]
            # 根據勝率由高至低排序，取前 10 組
            results_sorted = sorted(results, key=lambda x: x["win_rate"], reverse=True)
            result = results_sorted[:10]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"top_teams": result})


@app.route('/example', methods=['GET'])
def example():
    return jsonify({'message': '這是一個 API 回應'})


@app.route('/reload_model', methods=['POST'])
def reload_model():
    """
    重新加載模型與資源 (需驗證密碼)
    ---
    tags:
      - 管理 API
    parameters:
      - in: header
        name: X-API-PASSWORD
        type: string
        required: true
        description: 驗證密碼
    responses:
      200:
        description: 模型重新加載成功
        schema:
          type: object
          properties:
            message:
              type: string
      401:
        description: 未授權的訪問
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: 模型重新加載失敗
        schema:
          type: object
          properties:
            error:
              type: string
    """
    global predictor
    # 從 config.ini 讀取預設的 API 密碼
    expected_password = config['security']['API_PASSWORD']
    # 從 HTTP Header 中獲取使用者提供的密碼
    provided_password = request.headers.get('X-API-PASSWORD')

    # 驗證密碼
    if provided_password != expected_password:
        return jsonify({"error": "未授權的訪問"}), 401

    try:
        # 密碼驗證成功後，重新建立新的預測器實例
        predictor = ARAMPredictor(bucket_name)
        return jsonify({"message": "模型已成功重新加載"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
