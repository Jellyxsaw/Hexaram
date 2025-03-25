import configparser
import json
import logging
import os
import time
from datetime import datetime

import psycopg2
from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_cors import CORS
from psycopg2.extras import RealDictCursor
from werkzeug.middleware.proxy_fix import ProxyFix

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 建立應用程式
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
CORS(app)  # 啟用CORS支援

# 設定Swagger文檔
app.config['SWAGGER'] = {
    'uiversion': 3,
    'title': 'ARAM 統計 API',
    'version': '1.0.0',
    'description': 'ARAM模式英雄統計數據API',
    'termsOfService': '',
    'contact': {
        'name': 'API Support',
        'email': 'support@example.com'
    },
    'license': {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    },
    'tags': [
        {
            'name': '英雄API',
            'description': '提供英雄相關數據'
        },
        {
            'name': '分析API',
            'description': '提供數據分析與統計'
        },
        {
            'name': '系統API',
            'description': '系統管理相關API'
        },
        {
            'name': '資料API',
            'description': '遊戲基礎資料查詢'
        }
    ]
}
swagger = Swagger(app)

# 設定快取
cache_config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600  # 1小時
}
app.config.from_mapping(cache_config)
cache = Cache(app)


# 讀取設定檔
def load_config():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini', encoding='utf-8')
    except:
        # 如果找不到設定檔，使用環境變數
        pass
    return config


config = load_config()


# 資料庫連線設定
def create_db_connection():
    """建立資料庫連線"""
    try:
        db_config = {
            'host': os.environ.get('DB_HOST', config.get('database', 'host', fallback='localhost')),
            'port': int(os.environ.get('DB_PORT', config.get('database', 'port', fallback='5432'))),
            'user': os.environ.get('DB_USER', config.get('database', 'user', fallback='postgres')),
            'password': os.environ.get('DB_PASSWORD', config.get('database', 'password', fallback='aa030566')),
            'database': os.environ.get('DB_NAME', config.get('database', 'database', fallback='aram'))
        }

        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        return conn
    except Exception as e:
        logging.error(f"資料庫連線錯誤: {e}")
        raise


# 執行SQL查詢
def execute_query(query, params=None):
    """執行SQL查詢並返回結果"""
    conn = None
    try:
        conn = create_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            data = cursor.fetchall()
            return data
    except Exception as e:
        logging.error(f"資料庫查詢錯誤: {query}, {e}")
        return []
    finally:
        if conn:
            conn.close()


# 記錄API請求
def log_api_request(endpoint, params, status_code, execution_time):
    """記錄API請求到資料庫"""
    try:
        conn = create_db_connection()
        with conn.cursor() as cursor:
            query = """
                INSERT INTO api_request_logs 
                (endpoint, ip_address, request_params, response_status, execution_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            ip_address = request.remote_addr
            cursor.execute(
                query,
                (endpoint, ip_address, json.dumps(params), status_code, execution_time)
            )
            conn.commit()
    except Exception as e:
        logging.error(f"記錄API請求時發生錯誤: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


from functools import wraps


def api_logger(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        endpoint = request.path
        params = {}
        params.update(request.args.to_dict())

        if request.method == 'POST' and request.is_json:
            params.update(request.get_json())

        try:
            result = f(*args, **kwargs)
            status_code = 200
            return result
        except Exception as e:
            logging.error(f"API請求處理錯誤: {e}")
            status_code = 500
            return jsonify({"error": str(e)}), 500
        finally:
            execution_time = time.time() - start_time
            log_api_request(endpoint, params, status_code, execution_time)

    return decorated


# 格式化英雄列表數據
def format_champion_list(champions):
    """格式化英雄列表數據"""
    formatted_champions = []

    for champion in champions:
        # 抽取KDA值
        kda = f"{champion['avg_kills']:.1f}/{champion['avg_deaths']:.1f}/{champion['avg_assists']:.1f}"

        formatted_champion = {
            "name": champion['champion_name'],
            "championId": champion['champion_id'],
            "type": champion['champion_type'],
            "winRate": round(champion['win_rate'], 1),
            "pickRate": round(champion['pick_rate'], 1),
            "kda": kda,
            "kdaRatio": round(champion['kda_ratio'], 1),
            "tier": champion['tier'],
            "rank": champion['rank'],
            "key": champion['key']
        }
        formatted_champions.append(formatted_champion)

    return formatted_champions


# 格式化英雄詳細資料
def format_champion_detail(stats, trends, runes, builds, matchups, synergies):
    """格式化英雄詳細資料"""
    if not stats:
        return None

    champion = stats[0]
    champion_id = champion['champion_id']

    # 基本統計資訊
    kda = f"{champion['avg_kills']:.1f}/{champion['avg_deaths']:.1f}/{champion['avg_assists']:.1f}"

    # 格式化符文資料
    formatted_runes = []
    for rune in runes:
        # 解析符文ID
        rune_options = json.loads(rune['rune_options'])
        shard_options = json.loads(rune['shard_options'])

        # 主系符文ID
        primary_path_id = rune_options[0]  # 第一個是主系ID
        primary_rune_id = rune_options[1]  # 第二個是主系核心符文ID

        # 次要符文ID (索引1-3是主系的次要符文)
        secondary_rune_ids = rune_options[2:4]
        
        # 副系符文ID
        secondary_path_id = rune_options[4]  # 第五個是副系ID
        secondary_choice_ids = rune_options[5:7]  # 第六和第七個是副系選擇的符文ID

        # 符文碎片ID
        shard_ids = shard_options

        formatted_runes.append({
            "runes_win_rate": round(rune['win_rate'], 1),
            "primary_path": rune['primary_path'],
            "primary_path_id": primary_path_id,
            "primary_rune": rune['primary_rune'],
            "primary_rune_id": primary_rune_id,
            "secondary_runes": [],  # 名稱列表
            "secondary_rune_ids": secondary_rune_ids,  # ID列表
            "secondary_path": rune['secondary_path'],
            "secondary_path_id": secondary_path_id,
            "secondary_choices": [],  # 名稱列表
            "secondary_choice_ids": secondary_choice_ids,  # ID列表
            "shards": [],  # 名稱列表
            "shard_ids": shard_ids,  # ID列表
            "pick_rate": round(rune['pick_rate'], 1),
            "sample_size": rune['sample_size']
        })

    # 格式化裝備資料
    formatted_builds = []
    for build in builds:
        starting_items = json.loads(build['starting_items'])
        core_items = json.loads(build['core_items'])
        optional_items = json.loads(build['optional_items'])
        item_win_rates = json.loads(build['item_win_rates']) if build.get('item_win_rates') else {}

        formatted_builds.append({
            "build_win_rate": round(build['win_rate'], 1),
            "starting_items": starting_items,
            "core_items": core_items,
            "optional_items": optional_items,
            "item_win_rates": item_win_rates,
            "pick_rate": round(build['pick_rate'], 1),
            "sample_size": build['sample_size']
        })

    # 格式化版本趨勢資料
    trend_data = []
    trend_versions = []
    for trend in trends:
        trend_data.append(round(trend['win_rate'], 1))
        trend_versions.append(trend['version'])

    # 格式化對位資料
    formatted_matchups = []
    for matchup in matchups:
        formatted_matchups.append({
            "opponent_id": matchup['opponent_id'],
            "win_rate": round(matchup['win_rate'], 1),
            "sample_size": matchup['sample_size']
        })

    # 篩選前10個最好的對位和最差的對位
    best_matchups = sorted(formatted_matchups, key=lambda x: x['win_rate'], reverse=True)[:10]
    worst_matchups = sorted(formatted_matchups, key=lambda x: x['win_rate'])[:10]

    # 格式化協同資料
    formatted_synergies = []
    for synergy in synergies:
        formatted_synergies.append({
            "champion_id": synergy['champion1_id'] if synergy['champion2_id'] == champion_id else synergy['champion2_id'],
            "win_rate": round(synergy['win_rate'], 1),
            "synergy_score": round(synergy['synergy_score'], 1),
            "sample_size": synergy['sample_size']
        })

    # 篩選前10個最佳協同英雄
    best_synergies = sorted(formatted_synergies, key=lambda x: x['synergy_score'], reverse=True)[:10]

    # 設定技能順序和首選技能 (範例值，實際應從資料庫獲取)
    skill_order = "R > Q > W > E"
    first_skill = "Q"

    # 組合所有資料
    result = {
        "basic_info": {
            "champion_id": champion_id,
            "champion_name": champion['champion_name'],
            "champion_tw_name": champion.get('champion_tw_name', ''),
            "champion_type": champion['champion_type'],
            "champion_difficulty": champion.get('champion_difficulty', 2),
            "tier": champion['tier'],
            "rank": champion['rank'],
            "key": champion.get('key', 0),
            "rank_desc": f"ARAM 勝率第 {champion['rank']} 名"
        },
        "stats": {
            "win_rate": round(champion['win_rate'], 1),
            "pick_rate": round(champion['pick_rate'], 1),
            "ban_rate": round(champion['ban_rate'], 1),
            "kda": kda,
            "kda_ratio": round(champion['kda_ratio'], 1),
            "damage": f"{champion['avg_damage']:,.0f}",
            "damage_percentage": f"{champion['avg_damage_percentage']:.0f}%",
            "healing": f"{champion['avg_healing']:,.0f}",
            "healing_percentage": f"{champion['avg_healing_percentage']:.0f}%",
            "damage_taken": f"{champion['avg_damage_taken']:,.0f}",
            "damage_taken_percentage": f"{champion['avg_damage_taken_percentage']:.0f}%",
            "trend_data": trend_data,
            "trend_versions": trend_versions
        },
        "runes": formatted_runes[:3],  # 只返回前3個最佳符文配置
        "builds": formatted_builds[:3],  # 只返回前3個最佳裝備配置
        "skills": {
            "skill_order": skill_order,
            "first_skill": first_skill
        },
        "matchups": {
            "best": best_matchups,
            "worst": worst_matchups
        },
        "synergies": best_synergies,
        "tips": [
            f"• {champion_id}在ARAM中是一個{champion['tier']}級英雄，勝率{round(champion['win_rate'], 1)}%",
            f"• 平均每場能造成{int(champion['avg_damage']):,}點傷害，佔隊伍總傷害的{champion['avg_damage_percentage']:.0f}%",
            f"• 選擇合適的隊友來搭配{champion_id}可以大幅提高勝率"
        ]
    }

    return result


# API路由定義
@app.route('/api/champions', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=300)  # 快取5分鐘
def get_champion_list():
    """
    獲取所有英雄統計數據
    ---
    tags:
      - 英雄API
    summary: 英雄列表
    description: 返回英雄統計數據列表，支持分頁、排序和過濾
    parameters:
      - name: type
        in: query
        type: string
        required: false
        description: 按英雄類型過濾
        enum: [全部, 坦克, 戰士, 刺客, 法師, 輔助, 射手]
        default: 全部
      - name: sort
        in: query
        type: string
        required: false
        description: 排序方式
        enum: [勝率, 選用率, KDA]
        default: 勝率
      - name: page
        in: query
        type: integer
        required: false
        description: 頁碼 (從1開始)
        default: 1
        minimum: 1
      - name: limit
        in: query
        type: integer
        required: false
        description: 每頁顯示數量
        default: 12
        minimum: 1
        maximum: 50
    responses:
      200:
        description: 成功返回英雄列表
        schema:
          type: object
          properties:
            champions:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    description: 英雄名稱
                  championId:
                    type: string
                    description: 英雄ID
                  type:
                    type: string
                    description: 英雄類型
                  winRate:
                    type: number
                    format: float
                    description: 勝率百分比
                  pickRate:
                    type: number
                    format: float
                    description: 選用率百分比
                  kda:
                    type: string
                    description: KDA值 (擊殺/死亡/助攻)
                  kdaRatio:
                    type: number
                    format: float
                    description: KDA比率
                  tier:
                    type: string
                    description: 英雄梯隊 (S、A、B、C、D)
                  rank:
                    type: integer
                    description: 英雄排名
                  key:
                    type: integer
                    description: Riot定義的英雄key
            pagination:
              type: object
              properties:
                current_page:
                  type: integer
                  description: 當前頁碼
                total_pages:
                  type: integer
                  description: 總頁數
                total_items:
                  type: integer
                  description: 總項目數
            meta:
              type: object
              properties:
                last_updated:
                  type: string
                  format: date-time
                  description: 資料最後更新時間
      400:
        description: 請求參數錯誤
    """
    # 獲取查詢參數
    champion_type = request.args.get('type')
    sort_by = request.args.get('sort', '勝率')  # 預設按勝率排序
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 12))



    # 處理排序欄位
    sort_column = "win_rate"
    if sort_by == "選用率":
        sort_column = "pick_rate"
    elif sort_by == "KDA":
        sort_column = "kda_ratio"

    # 構建查詢
    query = """
        SELECT c.champion_id, c.champion_name, c.champion_tw_name, c.champion_type, 
               c.champion_difficulty, c.recommended_position, c.key,
               s.win_rate, s.pick_rate, s.ban_rate, 
               s.avg_kills, s.avg_deaths, s.avg_assists, s.kda_ratio,
               s.tier, s.rank
        FROM champions c
        LEFT JOIN champion_stats s ON c.champion_id = s.champion_id
        WHERE s.win_rate IS NOT NULL
    """

    count_query = """
        SELECT COUNT(*) as count 
        FROM champions c
        LEFT JOIN champion_stats s ON c.champion_id = s.champion_id
        WHERE s.win_rate IS NOT NULL
    """

    params = {}

    # 添加過濾條件
    if champion_type and champion_type != "全部":
        query += " AND c.champion_type LIKE %(champion_type)s"
        count_query += " AND c.champion_type LIKE %(champion_type)s"
        params['champion_type'] = f"%{champion_type}%"

    # 添加排序和分頁
    query += f" ORDER BY s.{sort_column} DESC NULLS LAST"
    query += " LIMIT %(limit)s OFFSET %(offset)s"

    # 計算分頁參數
    offset = (page - 1) * limit
    params['offset'] = offset
    params['limit'] = limit

    # 執行查詢
    champions = execute_query(query, params)
    count_result = execute_query(count_query, params)

    print(query)

    total_count = 0
    if count_result and count_result[0]:
        total_count = count_result[0]['count']

    # 計算總頁數
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    # 格式化返回結果
    formatted_champions = format_champion_list(champions)

    response = {
        "champions": formatted_champions,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total_count
        },
        "meta": {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return jsonify(response)


@app.route('/api/champions/<champion_id>', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=300)  # 快取5分鐘
def get_champion_detail(champion_id):
    """
    獲取特定英雄的詳細統計數據
    ---
    tags:
      - 英雄API
    summary: 英雄詳情
    description: 返回指定英雄的詳細統計數據，包括符文配置、裝備選擇、對位資料等
    parameters:
      - name: champion_id
        in: path
        type: string
        required: true
        description: 英雄ID (例如：Aatrox、Ahri)
    responses:
      200:
        description: 成功返回英雄詳細資料
        schema:
          $ref: '#/definitions/ChampionDetail'
      404:
        description: 英雄未找到
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "找不到該英雄資料"
      500:
        description: 伺服器錯誤
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "處理英雄資料時出錯"
    """
    # 1. 獲取基本統計資料
    stats_query = """
        SELECT c.champion_id, c.champion_name, c.champion_tw_name, c.champion_type, 
               c.champion_difficulty, c.recommended_position, c.key,
               s.win_rate, s.pick_rate, s.ban_rate, 
               s.avg_kills, s.avg_deaths, s.avg_assists, s.kda_ratio,
               s.avg_damage, s.avg_damage_percentage, s.avg_healing, s.avg_healing_percentage,
               s.avg_damage_taken, s.avg_damage_taken_percentage, s.tier, s.rank
        FROM champions c
        JOIN champion_stats s ON c.champion_id = s.champion_id
        WHERE c.champion_id = %(champion_id)s
    """
    stats = execute_query(stats_query, {"champion_id": champion_id})

    if not stats:
        return jsonify({"error": "找不到該英雄資料"}), 404

    # 2. 獲取符文資料
    runes_query = """
        SELECT * FROM champion_runes 
        WHERE champion_id = %(champion_id)s
        ORDER BY win_rate DESC
        LIMIT 5
    """
    runes = execute_query(runes_query, {"champion_id": champion_id})

    # 3. 獲取裝備資料
    builds_query = """
        SELECT * FROM champion_builds 
        WHERE champion_id = %(champion_id)s
        ORDER BY win_rate DESC
        LIMIT 5
    """
    builds = execute_query(builds_query, {"champion_id": champion_id})

    # 4. 獲取版本趨勢資料
    trends_query = """
        SELECT * FROM champion_trends 
        WHERE champion_id = %(champion_id)s
        ORDER BY version
        LIMIT 10
    """
    trends = execute_query(trends_query, {"champion_id": champion_id})

    # 5. 獲取對位資料
    matchups_query = """
        SELECT * FROM champion_matchups 
        WHERE champion_id = %(champion_id)s
    """
    matchups = execute_query(matchups_query, {"champion_id": champion_id})

    # 6. 獲取協同資料
    synergies_query = """
        SELECT * FROM team_synergies 
        WHERE champion1_id = %(champion_id)s OR champion2_id = %(champion_id)s
    """
    synergies = execute_query(synergies_query, {"champion_id": champion_id})

    # 格式化返回結果
    result = format_champion_detail(stats, trends, runes, builds, matchups, synergies)

    if not result:
        return jsonify({"error": "處理英雄資料時出錯"}), 500

    return jsonify(result)


@app.route('/api/version', methods=['GET'])
@api_logger
def get_version_info():
    """
    獲取當前資料版本信息
    ---
    tags:
      - 系統API
    summary: 版本信息
    description: 返回API當前資料版本、最後更新時間及樣本數量等信息
    responses:
      200:
        description: 成功返回版本信息
        schema:
          type: object
          properties:
            current_version:
              type: string
              description: 當前遊戲版本
              example: "11.24"
            last_updated:
              type: string
              description: 資料最後更新時間
              example: "2023-12-01 12:00:00"
            total_samples:
              type: integer
              description: 總樣本數量
              example: 1000000
            api_version:
              type: string
              description: API版本
              example: "1.0.0"
    """
    query = """
        SELECT MAX(updated_at) as last_updated
        FROM champion_stats
    """
    result = execute_query(query)

    if result and result[0]['last_updated']:
        last_updated = result[0]['last_updated'].strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_updated = "未知"

    # 獲取資料樣本數
    query = """
        SELECT SUM(sample_size) as total_samples
        FROM champion_stats
    """
    samples_result = execute_query(query)
    total_samples = samples_result[0]['total_samples'] if samples_result and samples_result[0]['total_samples'] else 0

    # 獲取當前版本
    version_query = """
        SELECT DISTINCT version 
        FROM champion_trends 
        ORDER BY version DESC 
        LIMIT 1
    """
    version_result = execute_query(version_query)
    current_version = version_result[0]['version'] if version_result else "未知"

    return jsonify({
        "current_version": current_version,
        "last_updated": last_updated,
        "total_samples": total_samples,
        "api_version": "1.0.0"
    })


@app.route('/api/refresh', methods=['POST'])
@api_logger
def refresh_data():
    """
    手動重新整理資料快取
    ---
    tags:
      - 系統API
    summary: 重整快取
    description: 清除API的所有快取資料，需要API金鑰授權
    parameters:
      - name: X-API-KEY
        in: header
        type: string
        required: true
        description: API金鑰，用於認證
    responses:
      200:
        description: 成功重新整理快取
        schema:
          type: object
          properties:
            message:
              type: string
              description: 操作成功訊息
              example: "快取已重新整理"
      401:
        description: 未授權
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "未授權的請求"
    """
    api_key = request.headers.get('X-API-KEY')
    expected_key = os.environ.get('API_KEY', config.get('security', 'API_KEY', fallback=''))

    if not api_key or api_key != expected_key:
        return jsonify({"error": "未授權的請求"}), 401

    # 清除所有快取
    cache.clear()

    return jsonify({"message": "快取已重新整理"})


@app.route('/api/force-update', methods=['POST'])
@api_logger
def force_update():
    """
    強制更新統計資料
    ---
    tags:
      - 系統API
    summary: 強制更新資料
    description: 觸發資料更新流程，需要API金鑰授權
    parameters:
      - name: X-API-KEY
        in: header
        type: string
        required: true
        description: API金鑰，用於認證
    responses:
      200:
        description: 成功啟動更新流程
        schema:
          type: object
          properties:
            message:
              type: string
              description: 操作成功訊息
              example: "已啟動資料更新程序"
            status:
              type: string
              description: 更新狀態
              example: "processing"
      401:
        description: 未授權
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "未授權的請求"
      500:
        description: 更新失敗
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
    """
    api_key = request.headers.get('X-API-KEY')
    expected_key = os.environ.get('API_KEY', config.get('security', 'API_KEY', fallback=''))

    if not api_key or api_key != expected_key:
        return jsonify({"error": "未授權的請求"}), 401

    try:
        # 在實際應用中，這裡應該異步啟動資料更新程序
        # 例如：subprocess.Popen(['python', 'data_converter.py'])

        # 清除所有快取
        cache.clear()

        return jsonify({
            "message": "已啟動資料更新程序",
            "status": "processing"
        })
    except Exception as e:
        logging.error(f"啟動資料更新程序時發生錯誤: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/update-status', methods=['GET'])
@api_logger
def get_update_status():
    """
    獲取資料更新狀態
    ---
    tags:
      - 系統API
    summary: 更新狀態
    description: 返回最近的資料更新狀態記錄
    responses:
      200:
        description: 成功返回更新狀態
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                properties:
                  update_type:
                    type: string
                    description: 更新類型
                    example: "full"
                  version:
                    type: string
                    description: 版本
                    example: "11.24"
                  records_processed:
                    type: integer
                    description: 處理記錄數
                    example: 1500
                  update_status:
                    type: string
                    description: 狀態
                    enum: [pending, processing, completed, failed]
                    example: "completed"
                  start_time:
                    type: string
                    format: date-time
                    description: 開始時間
                  end_time:
                    type: string
                    format: date-time
                    description: 結束時間
                  error_message:
                    type: string
                    description: 錯誤訊息
            current_time:
              type: string
              format: date-time
              description: 當前時間
    """
    query = """
        SELECT update_type, version, records_processed, update_status, 
               start_time, end_time, error_message
        FROM data_update_logs
        ORDER BY id DESC
        LIMIT 5
    """
    results = execute_query(query)

    return jsonify({
        "updates": results,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/synergy-matrix', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=600)  # 快取10分鐘
def get_synergy_matrix():
    """
    獲取英雄協同矩陣資料
    ---
    tags:
      - 分析API
    summary: 英雄協同矩陣
    description: 返回最熱門英雄之間的協同矩陣資料
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        description: 限制返回的英雄數量
        default: 20
        minimum: 5
        maximum: 50
    responses:
      200:
        description: 成功返回協同矩陣
        schema:
          type: object
          properties:
            champions:
              type: array
              items:
                type: string
              description: 英雄ID列表
            matrix:
              type: array
              items:
                type: array
                items:
                  type: number
                  format: float
              description: 協同評分矩陣
      404:
        description: 找不到英雄資料
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "找不到英雄資料"
    """
    return jsonify({"error": "此API暫時停用"}), 503


@app.route('/api/matchup-matrix', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=600)  # 快取10分鐘
def get_matchup_matrix():
    """
    獲取英雄對位矩陣資料
    ---
    tags:
      - 分析API
    summary: 英雄對位矩陣
    description: 返回最熱門英雄之間的對位矩陣資料
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        description: 限制返回的英雄數量
        default: 20
        minimum: 5
        maximum: 50
    responses:
      200:
        description: 成功返回對位矩陣
        schema:
          type: object
          properties:
            champions:
              type: array
              items:
                type: string
              description: 英雄ID列表
            matrix:
              type: array
              items:
                type: array
                items:
                  type: number
                  format: float
              description: 對位勝率矩陣 (百分比)
      404:
        description: 找不到英雄資料
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "找不到英雄資料"
    """
    return jsonify({"error": "此API暫時停用"}), 503


@app.route('/api/tier-list', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=300)  # 快取5分鐘
def get_tier_list():
    """
    獲取英雄梯隊列表
    ---
    tags:
      - 分析API
    summary: 英雄梯隊列表
    description: 返回英雄梯隊分類列表
    parameters:
      - name: type
        in: query
        type: string
        required: false
        description: 按英雄類型過濾
        enum: [全部, 坦克, 戰士, 刺客, 法師, 輔助, 射手]
        default: 全部
    responses:
      200:
        description: 成功返回梯隊列表
        schema:
          type: object
          properties:
            tier_list:
              type: array
              items:
                type: object
                properties:
                  tier:
                    type: string
                    description: 梯隊級別 (S、A、B、C、D)
                  champions:
                    type: array
                    items:
                      type: object
                      properties:
                        champion_id:
                          type: string
                          description: 英雄ID
                        champion_name:
                          type: string
                          description: 英雄英文名稱
                        champion_tw_name:
                          type: string
                          description: 英雄繁體中文名稱
                        champion_type:
                          type: string
                          description: 英雄類型
                        key:
                          type: integer
                          description: Riot定義的英雄key
                        win_rate:
                          type: number
                          format: float
                          description: 勝率百分比
                        pick_rate:
                          type: number
                          format: float
                          description: 選用率百分比
                        rank:
                          type: integer
                          description: 英雄排名
    """
    champion_type = request.args.get('type')

    query = """
        SELECT c.champion_id, c.champion_name, c.champion_tw_name, c.champion_type, c.key,
               s.win_rate, s.pick_rate, s.tier, s.rank
        FROM champions c
        JOIN champion_stats s ON c.champion_id = s.champion_id
        WHERE s.win_rate IS NOT NULL
    """

    params = {}

    if champion_type and champion_type != "全部":
        query += " AND c.champion_type LIKE %(champion_type)s"
        params['champion_type'] = f"%{champion_type}%"

    query += " ORDER BY s.tier, s.rank"

    champions = execute_query(query, params)

    # 將英雄按梯隊分組
    tiers = {}
    for champion in champions:
        tier = champion['tier']
        if tier not in tiers:
            tiers[tier] = []

        tiers[tier].append({
            "champion_id": champion['champion_id'],
            "champion_name": champion['champion_name'],
            "champion_tw_name": champion['champion_tw_name'],
            "champion_type": champion['champion_type'],
            "key": champion['key'],
            "win_rate": round(champion['win_rate'], 1),
            "pick_rate": round(champion['pick_rate'], 1),
            "rank": champion['rank']
        })

    # 將梯隊轉換為列表
    tier_list = []
    for tier in ['S', 'A', 'B', 'C', 'D']:
        if tier in tiers:
            tier_list.append({
                "tier": tier,
                "champions": tiers[tier]
            })

    return jsonify({
        "tier_list": tier_list
    })


@app.route('/api/champion-search', methods=['GET'])
@api_logger
def search_champions():
    """
    搜索英雄
    ---
    tags:
      - 英雄API
    summary: 英雄搜索
    description: 根據關鍵字搜索英雄
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: 搜索關鍵字
        minimum: 1
    responses:
      200:
        description: 成功返回搜索結果
        schema:
          type: object
          properties:
            results:
              type: array
              items:
                type: object
                properties:
                  champion_id:
                    type: string
                    description: 英雄ID
                  champion_name:
                    type: string
                    description: 英雄英文名稱
                  champion_tw_name:
                    type: string
                    description: 英雄繁體中文名稱
                  champion_type:
                    type: string
                    description: 英雄類型
                  key:
                    type: integer
                    description: Riot定義的英雄key
      400:
        description: 請求參數錯誤
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "請提供搜索關鍵字"
    """
    query_string = request.args.get('q')

    if not query_string or len(query_string) < 1:
        return jsonify({"error": "請提供搜索關鍵字"}), 400

    # 構建搜索查詢
    query = """
        SELECT 
            c.champion_id, 
            c.champion_name, 
            c.champion_tw_name, 
            c.champion_type, 
            c.key,
            s.win_rate,
            s.pick_rate,
            s.kda_ratio,
            s.tier,
            s.rank
        FROM champions c
        LEFT JOIN champion_stats s ON c.champion_id = s.champion_id
        WHERE 
            LOWER(c.champion_id) LIKE LOWER(%(query)s)
            OR LOWER(c.champion_name) LIKE LOWER(%(query)s)
            OR LOWER(c.champion_tw_name) LIKE LOWER(%(query)s)
            OR LOWER(c.champion_type) LIKE LOWER(%(query)s)
        ORDER BY 
            CASE 
                WHEN LOWER(c.champion_id) = LOWER(%(exact)s) THEN 1
                WHEN LOWER(c.champion_name) = LOWER(%(exact)s) THEN 1
                WHEN LOWER(c.champion_tw_name) = LOWER(%(exact)s) THEN 1
                WHEN LOWER(c.champion_id) LIKE LOWER(%(query)s) THEN 2
                WHEN LOWER(c.champion_name) LIKE LOWER(%(query)s) THEN 2
                WHEN LOWER(c.champion_tw_name) LIKE LOWER(%(query)s) THEN 2
                ELSE 3
            END,
            CASE 
                WHEN s.win_rate IS NOT NULL THEN s.win_rate
                ELSE 0
            END DESC,
            length(c.champion_id)
        LIMIT 10
    """

    params = {
        "query": f"%{query_string}%",
        "exact": query_string
    }

    champions = execute_query(query, params)

    # 格式化返回結果
    formatted_results = []
    for champ in champions:
        formatted_results.append({
            'champion_id': champ['champion_id'],
            'champion_name': champ['champion_name'],
            'champion_tw_name': champ['champion_tw_name'],
            'champion_type': champ['champion_type'],
            'key': champ['key'],
            'win_rate': round(champ['win_rate'], 1) if champ['win_rate'] is not None else 0,
            'pick_rate': round(champ['pick_rate'], 1) if champ['pick_rate'] is not None else 0,
            'kda_ratio': round(champ['kda_ratio'], 1) if champ['kda_ratio'] is not None else 0,
            'tier': champ['tier'] if champ['tier'] is not None else '',
            'rank': champ['rank'] if champ['rank'] is not None else 0
        })

    return jsonify({
        "results": formatted_results
    })


@app.route('/api/champion-stats-by-key/<int:key>', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=300)  # 快取5分鐘
def get_champion_by_key(key):
    """
    通過Riot key獲取英雄統計資料
    ---
    tags:
      - 英雄API
    summary: 通過Riot Key獲取英雄資料
    description: 使用Riot官方定義的英雄key獲取英雄詳細資料
    parameters:
      - name: key
        in: path
        type: integer
        required: true
        description: Riot定義的英雄key
    responses:
      200:
        description: 成功返回英雄詳細資料
        schema:
          $ref: '#/definitions/ChampionDetail'
      404:
        description: 英雄未找到
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "找不到該英雄"
    """
    # 1. 先根據key獲取champion_id
    query = """
        SELECT champion_id 
        FROM champions 
        WHERE key = %(key)s
    """
    result = execute_query(query, {"key": key})

    if not result:
        return jsonify({"error": "找不到該英雄"}), 404

    champion_id = result[0]['champion_id']

    # 2. 使用champion_id獲取詳細資料
    return get_champion_detail(champion_id)


@app.route('/api/items', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=3600)  # 快取1小時
def get_items():
    """
    獲取物品定義資料
    ---
    tags:
      - 資料API
    summary: 物品列表
    description: 返回物品定義資料列表
    parameters:
      - name: type
        in: query
        type: string
        required: false
        description: 物品類型過濾
        enum: [消耗品, 首購裝, 基礎裝, 傳說裝, 神話裝]
    responses:
      200:
        description: 成功返回物品列表
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  item_id:
                    type: integer
                    description: 物品ID
                  item_name:
                    type: string
                    description: 物品名稱
                  item_type:
                    type: string
                    description: 物品類型
                  item_description:
                    type: string
                    description: 物品描述
                  item_cost:
                    type: integer
                    description: 物品價格
                  is_mythic:
                    type: boolean
                    description: 是否為神話裝備
    """
    item_type = request.args.get('type')

    query = """
        SELECT item_id, item_name, item_type, item_description, item_cost, is_mythic
        FROM item_definitions
    """

    params = {}

    if item_type:
        query += " WHERE item_type = %(item_type)s"
        params['item_type'] = item_type

    query += " ORDER BY item_id"

    items = execute_query(query, params)

    return jsonify({
        "items": items
    })


@app.route('/api/runes', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串(timeout=3600)  # 快取1小時
def get_runes():
    """
    獲取符文定義資料
    ---
    tags:
      - 資料API
    summary: 符文列表
    description: 返回符文定義資料列表
    parameters:
      - name: path
        in: query
        type: string
        required: false
        description: 符文系別過濾
        enum: [精密, 主宰, 巫術, 堅決, 啟迪]
    responses:
      200:
        description: 成功返回符文列表
        schema:
          type: object
          properties:
            rune_paths:
              type: object
              additionalProperties:
                type: object
                additionalProperties:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: 符文ID
                      name:
                        type: string
                        description: 符文名稱
                      description:
                        type: string
                        description: 符文描述
    """
    rune_path = request.args.get('path')

    query = """
        SELECT rune_id, rune_name, rune_path, rune_slot, rune_description
        FROM rune_definitions
    """

    params = {}

    if rune_path:
        query += " WHERE rune_path = %(rune_path)s"
        params['rune_path'] = rune_path

    query += " ORDER BY rune_path, rune_slot, rune_id"

    runes = execute_query(query, params)

    # 將符文按系別分組
    paths = {}
    for rune in runes:
        path = rune['rune_path']
        if path not in paths:
            paths[path] = {}

        slot = rune['rune_slot']
        if slot not in paths[path]:
            paths[path][slot] = []

        paths[path][slot].append({
            "id": rune['rune_id'],
            "name": rune['rune_name'],
            "description": rune['rune_description']
        })

    return jsonify({
        "rune_paths": paths
    })


@app.route('/')
def home():
    """
    API首頁
    ---
    tags:
      - 系統API
    summary: API首頁
    description: API概覽資訊
    responses:
      200:
        description: 成功返回API概覽
        schema:
          type: object
          properties:
            name:
              type: string
              description: API名稱
              example: "ARAM 統計 API"
            version:
              type: string
              description: API版本
              example: "1.0.0"
            documentation:
              type: string
              description: 文檔URL
              example: "/apidocs/"
            endpoints:
              type: array
              items:
                type: string
              description: 主要端點列表
    """
    return jsonify({
        "name": "ARAM 統計 API",
        "version": "1.0.0",
        "documentation": "/apidocs/",
        "endpoints": [
            "/api/champions",
            "/api/champions/<champion_id>",
            "/api/champion-stats-by-key/<key>",
            "/api/team-winrate",
            "/api/tier-list",
            "/api/synergy-matrix",
            "/api/matchup-matrix",
            "/api/version"
        ]
    })


# 為了避免與已有實現衝突，定義自定義響應模型
"""
definitions:
  ChampionDetail:
    type: object
    properties:
      basic_info:
        type: object
        properties:
          champion_id:
            type: string
          champion_name:
            type: string
          champion_tw_name:
            type: string
          champion_type:
            type: string
          champion_difficulty:
            type: integer
          tier:
            type: string
          rank:
            type: integer
          key:
            type: integer
          rank_desc:
            type: string
      stats:
        type: object
        properties:
          win_rate:
            type: number
            format: float
          pick_rate:
            type: number
            format: float
          ban_rate:
            type: number
            format: float
          kda:
            type: string
          kda_ratio:
            type: number
            format: float
          damage:
            type: string
          damage_percentage:
            type: string
          healing:
            type: string
          healing_percentage:
            type: string
          damage_taken:
            type: string
          damage_taken_percentage:
            type: string
          trend_data:
            type: array
            items:
              type: number
          trend_versions:
            type: array
            items:
              type: string
      runes:
        type: array
        items:
          $ref: '#/definitions/RuneConfig'
      builds:
        type: array
        items:
          $ref: '#/definitions/BuildConfig'
      skills:
        type: object
        properties:
          skill_order:
            type: string
          first_skill:
            type: string
      matchups:
        type: object
        properties:
          best:
            type: array
            items:
              $ref: '#/definitions/Matchup'
          worst:
            type: array
            items:
              $ref: '#/definitions/Matchup'
      synergies:
        type: array
        items:
          $ref: '#/definitions/Synergy'
      tips:
        type: array
        items:
          type: string

  RuneConfig:
    type: object
    properties:
      runes_win_rate:
        type: number
        format: float
      primary_path:
        type: string
      primary_rune:
        type: string
      secondary_runes:
        type: array
        items:
          type: string
      secondary_path:
        type: string
      secondary_choices:
        type: array
        items:
          type: string
      shards:
        type: array
        items:
          type: string
      pick_rate:
        type: number
        format: float
      sample_size:
        type: integer

  BuildConfig:
    type: object
    properties:
      build_win_rate:
        type: number
        format: float
      starting_items:
        type: array
        items:
          type: integer
      core_items:
        type: array
        items:
          type: integer
      optional_items:
        type: array
        items:
          type: integer
      pick_rate:
        type: number
        format: float
      sample_size:
        type: integer

  Matchup:
    type: object
    properties:
      opponent_id:
        type: string
      win_rate:
        type: number
        format: float
      sample_size:
        type: integer

  Synergy:
    type: object
    properties:
      champion_id:
        type: string
      win_rate:
        type: number
        format: float
      synergy_score:
        type: number
        format: float
      sample_size:
        type: integer
"""


@app.route('/api/champion-metrics/<int:key>', methods=['GET'])
@api_logger
@cache.cached(timeout=300, query_string=True)  # 快取5分鐘，且包含查詢字串
def get_champion_metrics_by_key(key):
    """
    通過英雄 key 獲取英雄各項指標數據
    ---
    tags:
      - 英雄API
    summary: 英雄效能指標
    description: 使用英雄 key 獲取該英雄的各項效能指標數據，包括每分鐘傷害、承受傷害、治療量等
    parameters:
      - name: key
        in: path
        type: integer
        required: true
        description: 英雄的 key 值
    responses:
      200:
        description: 成功返回英雄效能指標數據
        schema:
          type: object
          properties:
            champion_name:
              type: string
              description: 英雄名稱
            champion_key:
              type: integer
              description: 英雄 key
            avg_damage_per_min:
              type: number
              format: float
              description: 每分鐘平均傷害量
            avg_damage_taken_per_min:
              type: number
              format: float
              description: 每分鐘平均承受傷害量
            avg_healing_per_min:
              type: number
              format: float
              description: 每分鐘平均治療量
            avg_damage_mitigated_per_min:
              type: number
              format: float
              description: 每分鐘平均緩解傷害量
            avg_time_ccing_per_min:
              type: number
              format: float
              description: 每分鐘平均控制時間
            sample_size:
              type: integer
              description: 樣本數量
      404:
        description: 找不到該英雄的數據
        schema:
          type: object
          properties:
            error:
              type: string
              description: 錯誤訊息
              example: "找不到該英雄的指標數據"
    """
    query = """
        SELECT 
            champion_name,
            champion_key,
            avg_damage_per_min,
            avg_damage_taken_per_min,
            avg_healing_per_min,
            avg_damage_mitigated_per_min,
            avg_time_ccing_per_min,
            sample_size,
            updated_at
        FROM 
            champion_metrics
        WHERE 
            champion_key = %(key)s
    """

    params = {"key": key}
    results = execute_query(query, params)

    if not results or len(results) == 0:
        return jsonify({"error": "找不到該英雄的指標數據"}), 404

    # 格式化結果
    metrics = results[0]
    formatted_metrics = {
        "champion_name": metrics["champion_name"],
        "champion_key": metrics["champion_key"],
        "metrics": {
            "avg_damage_per_min": round(metrics["avg_damage_per_min"], 2),
            "avg_damage_taken_per_min": round(metrics["avg_damage_taken_per_min"], 2),
            "avg_healing_per_min": round(metrics["avg_healing_per_min"], 2),
            "avg_damage_mitigated_per_min": round(metrics["avg_damage_mitigated_per_min"], 2),
            "avg_time_ccing_per_min": round(metrics["avg_time_ccing_per_min"], 2)
        },
        "sample_size": metrics["sample_size"],
        "updated_at": metrics["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if metrics["updated_at"] else None
    }

    return jsonify(formatted_metrics)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
