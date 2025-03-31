import configparser
import time
from datetime import datetime

import psycopg2
import requests
from psycopg2.extras import Json

# 建立設定解析器
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# =========== API 參數 ===========
API_KEY = config.get('api-key', 'API_KEY')
REGION_ACCOUNT = config.get('api-key', 'REGION_ACCOUNT')
REGION_MATCH = config.get('api-key', 'REGION_MATCH')
GAME_NAME = config.get('api-key', 'GAME_NAME')
TAG_LINE = config.get('api-key', 'TAG_LINE')

# =========== 資料庫連線參數 ===========
DB_HOST = config.get('database', 'DB_HOST')
DB_PORT = config.getint('database', 'DB_PORT')
DB_NAME = config.get('database', 'DB_NAME')
DB_USER = config.get('database', 'DB_USER')
DB_PASSWORD = config.get('database', 'DB_PASSWORD')


# =========== DB 函式 ===========
def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    return conn


def get_first_unsearched_summoner(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT puuid FROM summoners WHERE is_searched = FALSE ORDER BY created_at LIMIT 1")
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            return None


def mark_summoner_as_searched(conn, puuid):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE summoners 
            SET is_searched = TRUE, last_searched = NOW()
            WHERE puuid = %s
        """, (puuid,))
    conn.commit()


def insert_summoner_if_not_exists(conn, puuid, summoner_name=None, riot_id_game_name=None, riot_id_tagline=None):
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO summoners (puuid, summoner_name, riot_id_game_name, riot_id_tagline)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (puuid) DO NOTHING
            """, (puuid, summoner_name, riot_id_game_name, riot_id_tagline))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("insert_summoner_if_not_exists error:", e)


def match_exists(conn, match_id):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM model_matches WHERE match_id = %s", (match_id,))
        return cur.fetchone() is not None


def count_matches(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM model_matches")
        return cur.fetchone()[0]


# =========== API 函式 ===========
def get_account_data(game_name, tag_line):
    url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("取得帳戶資料錯誤:", response.status_code, response.text)
        return None


def get_match_ids(puuid, count=200, queue=450):
    """
    取得前N筆兩個月內的對局 id
    """
    url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    two_months_ago = int(time.time() - 60 * 24 * 3600)  # 60 天前的 epoch timestamp
    current_time = int(time.time())
    params = {
        "start": 0,
        "count": count,
        "queue": queue,
        "startTime": two_months_ago,
        "endTime": current_time,
        "api_key": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("取得比賽 id 錯誤:", response.status_code, response.text)
        return None


def get_match_details(match_id):
    url = f"https://{REGION_MATCH}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"取得比賽 {match_id} 詳細資料錯誤:", response.status_code, response.text)
        return None


# =========== 資料擷取函式 ===========
def extract_features(match_data):
    """
    從原始對局資料中擷取精細的特徵數據
    """
    features = {}
    game_duration = match_data["info"].get("gameDuration", 0)
    features["game_duration"] = game_duration

    # 初始化隊伍統計（假設隊伍 ID 為 100 與 200）
    team_features = {
        100: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0},
        200: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0}
    }

    participant_features = []
    cc_scale = 100.0

    for participant in match_data["info"]["participants"]:
        p_feats = {}
        p_feats["puuid"] = participant.get("puuid", "")
        p_feats["championName"] = participant.get("championName", "")
        p_feats["teamId"] = participant.get("teamId", 0)

        challenges = participant.get("challenges", {})
        if "damagePerMinute" in challenges:
            p_feats["damage_per_minute"] = challenges["damagePerMinute"]
        else:
            total_damage = participant.get("totalDamageDealtToChampions", 0)
            p_feats["damage_per_minute"] = total_damage / (game_duration / 60.0) if game_duration > 0 else 0

        p_feats["total_damage_dealt_to_champions"] = participant.get("totalDamageDealtToChampions", 0)
        p_feats["total_damage_taken"] = participant.get("totalDamageTaken", 0)
        p_feats["physical_damage_dealt_to_champions"] = participant.get("physicalDamageDealtToChampions", 0)
        p_feats["magic_damage_dealt_to_champions"] = participant.get("magicDamageDealtToChampions", 0)
        p_feats["damage_self_mitigated"] = participant.get("damageSelfMitigated", 0)
        p_feats["total_heal"] = participant.get("totalHeal", 0)
        p_feats["total_heals_on_teammates"] = participant.get("totalHealsOnTeammates", 0)
        p_feats["total_damage_shielded_on_teammates"] = participant.get("totalDamageShieldedOnTeammates", 0)
        p_feats["time_ccing_others"] = participant.get("timeCCingOthers", 0)
        p_feats["gold_earned"] = participant.get("goldEarned", 0)
        p_feats["gold_spent"] = participant.get("goldSpent", 0)

        total_damage_output = p_feats["total_damage_dealt_to_champions"]
        if total_damage_output > 0:
            p_feats["gold_per_damage_dealt"] = p_feats["gold_earned"] / total_damage_output
        else:
            p_feats["gold_per_damage_dealt"] = 0

        total_effort = (
                p_feats["total_damage_dealt_to_champions"] +
                p_feats["total_damage_taken"] +
                (p_feats["time_ccing_others"] * cc_scale) +
                (p_feats["total_heal"] + p_feats["total_heals_on_teammates"] + p_feats[
                    "total_damage_shielded_on_teammates"]) +
                p_feats["damage_self_mitigated"]
        )
        if total_effort > 0:
            p_feats["gold_conversion_efficiency"] = p_feats["gold_earned"] / total_effort
        else:
            p_feats["gold_conversion_efficiency"] = 0

        p_feats["kills"] = participant.get("kills", 0)
        p_feats["deaths"] = participant.get("deaths", 0)
        p_feats["assists"] = participant.get("assists", 0)
        if p_feats["deaths"] > 0:
            p_feats["kda"] = (p_feats["kills"] + p_feats["assists"]) / p_feats["deaths"]
        else:
            p_feats["kda"] = p_feats["kills"] + p_feats["assists"]

        participant_features.append(p_feats)

        team_id = participant.get("teamId", 0)
        if team_id in team_features:
            team_features[team_id]["total_gold"] += p_feats["gold_earned"]
            team_features[team_id]["total_damage_dealt"] += p_feats["total_damage_dealt_to_champions"]
            team_features[team_id]["total_kills"] += p_feats["kills"]
            team_features[team_id]["total_assists"] += p_feats["assists"]
            team_features[team_id]["total_deaths"] += p_feats["deaths"]

    features["participants"] = participant_features

    for team in match_data["info"].get("teams", []):
        team_id = team.get("teamId")
        if team_id in team_features:
            team_features[team_id]["win"] = team.get("win", False)
    features["teams"] = team_features

    if 100 in team_features and 200 in team_features:
        features["team_gold_diff"] = team_features[100]["total_gold"] - team_features[200]["total_gold"]
        features["team_damage_diff"] = team_features[100]["total_damage_dealt"] - team_features[200][
            "total_damage_dealt"]

    return features


# =========== 資料庫資料插入函式 ===========
def extract_match_info(raw_match):
    """
    從原始的 Riot 對局資料中擷取基本資訊
    """
    info = raw_match.get("info", {})
    metadata = raw_match.get("metadata", {})
    match_info = {
        "matchId": metadata.get("matchId"),
        "gameMode": info.get("gameMode"),
        "gameType": info.get("gameType"),
        "gameVersion": info.get("gameVersion"),
        "mapId": info.get("mapId"),
        "queueId": info.get("queueId"),
        "platformId": info.get("platformId"),
        "tournamentCode": info.get("tournamentCode"),
        "gameName": info.get("gameName"),
        "gameCreation": datetime.fromtimestamp(info.get("gameCreation", 0) / 1000).strftime(
            '%Y-%m-%d %H:%M:%S') if info.get("gameCreation") else None,
        "gameDuration": info.get("gameDuration"),
        "gameStartTimestamp": datetime.fromtimestamp(info.get("gameStartTimestamp", 0) / 1000).strftime(
            '%Y-%m-%d %H:%M:%S') if info.get("gameStartTimestamp") else None,
        "gameEndTimestamp": datetime.fromtimestamp(info.get("gameEndTimestamp", 0) / 1000).strftime(
            '%Y-%m-%d %H:%M:%S') if info.get("gameEndTimestamp") else None,
    }
    return match_info


def insert_match(conn, raw_match):
    """
    將從 Riot 取得的原始對局資料連同擷取出的精細資料，
    一併插入 model_matches 表中
    """
    match_info = extract_match_info(raw_match)
    features = extract_features(raw_match)
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO model_matches (
                    is_searched_summoners, match_id, game_mode, game_type, game_version, map_id, queue_id, 
                    platform_id, tournament_code, game_name, game_creation, game_duration, game_start_timestamp, 
                    game_end_timestamp, match_data, extract_data
                ) VALUES (
                    FALSE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (match_id) DO NOTHING
            """, (
                match_info.get("matchId"),
                match_info.get("gameMode"),
                match_info.get("gameType"),
                match_info.get("gameVersion"),
                match_info.get("mapId"),
                match_info.get("queueId"),
                match_info.get("platformId"),
                match_info.get("tournamentCode"),
                match_info.get("gameName"),
                match_info.get("gameCreation"),
                match_info.get("gameDuration"),
                match_info.get("gameStartTimestamp"),
                match_info.get("gameEndTimestamp"),
                Json(raw_match),  # 儲存原始 JSON 資料
                Json(features)  # 儲存擷取後的精細資料
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("insert_match error:", e)


# =========== 主流程 ===========
def main():
    conn = get_db_connection()
    target_matches = 5_000_000
    consecutive_errors = 0  # 連續錯誤計數器

    while count_matches(conn) < target_matches:
        try:
            current_count = count_matches(conn)
            print("目前 matches 數量:", current_count)

            # 1. 取得 summoners 表中 is_searched = FALSE 的第一筆 summoner
            summoner_puuid = get_first_unsearched_summoner(conn)
            if not summoner_puuid:
                # 若找不到，則使用初始種子召喚師並插入 summoners 表（若尚未存在）
                account_data = get_account_data(GAME_NAME, TAG_LINE)
                if account_data is None:
                    print("初始召喚師資料取得失敗，結束")
                    break
                summoner_puuid = account_data.get("puuid")
                insert_summoner_if_not_exists(conn, summoner_puuid, GAME_NAME, GAME_NAME, TAG_LINE)
            print("處理召喚師 puuid:", summoner_puuid)

            # 2. 將該召喚師設為已搜尋過
            mark_summoner_as_searched(conn, summoner_puuid)

            # 3. 依據此 summoner_puuid 取得前100筆兩個月內的 ARAM 對局 id
            match_ids = get_match_ids(summoner_puuid, count=100)
            if match_ids is None:
                print("無法取得對局 id，跳過此召喚師")
                continue

            # 4. 依序處理每一筆對局
            for match_id in match_ids:
                if match_exists(conn, match_id):
                    print("對局已存在:", match_id)
                    continue
                print("取得對局資料:", match_id)
                raw_match = get_match_details(match_id)
                if raw_match is None:
                    continue

                # 插入原始資料與精細資料到 model_matches 表中
                insert_match(conn, raw_match)

                # 將對局中所有參與者 puuid 寫入 summoners 表（若不存在）
                for p_puuid in raw_match.get("metadata", {}).get("participants", []):
                    insert_summoner_if_not_exists(conn, p_puuid)
                # 暫停 1 秒以避免 API 請求過快
                time.sleep(1)

            # 每輪處理後暫停 2 秒
            time.sleep(2)
            # 本輪成功執行後，重置連續錯誤計數器
            consecutive_errors = 0

        except Exception as e:
            print("發生異常：", e)
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print("連續異常達5次，程式停止。")
                break
            print("等待1分鐘後再繼續...")
            time.sleep(60)

    print("達到目標對局數量:", count_matches(conn))
    conn.close()


if __name__ == "__main__":
    main()
