import itertools

from flasgger import Swagger
from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from apilogger import register_api_logger
from extensions import db, db_uri
from pureARAMPredictor import ARAMPredictor

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
swagger = Swagger(app)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 SQLAlchemy
db.init_app(app)

# 註冊 API 請求日誌功能
register_api_logger(app)

# 建立模型預測器實例
predictor = ARAMPredictor()


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
