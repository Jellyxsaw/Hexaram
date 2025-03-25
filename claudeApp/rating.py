import requests
import json
import time
import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from urllib3.exceptions import InsecureRequestWarning
import random

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("rating_system.log"), logging.StreamHandler()]
)
logger = logging.getLogger("LOL評分系統")

# 抑制不安全請求的警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# API配置
API_KEY = "RGAPI-bf9f5dd1-fe15-4707-9d09-d52011fa4e21"  # 請替換為您的實際API金鑰
ASIA_SERVER = "asia.api.riotgames.com"
SEA_SERVER = "sea.api.riotgames.com"
CHAMPION_METRICS_API = "https://api.pinkyjelly.work/api/champion-metrics/"

# API請求相關設定
MAX_RETRIES = 5  # 最大重試次數
BASE_DELAY = 1  # 基礎延遲時間(秒)
MAX_DELAY = 60  # 最大延遲時間(秒)
RATE_LIMIT_WINDOW = 10  # 速率限制窗口(秒)
MAX_REQUESTS_PER_WINDOW = 20  # 每個窗口最大請求數量


class RateLimiter:
    """請求速率限制控制器"""

    def __init__(self, max_requests=MAX_REQUESTS_PER_WINDOW, time_window=RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps = []

    def wait_if_needed(self):
        """檢查並等待，如果需要限制請求速率"""
        current_time = time.time()

        # 清理超過時間窗口的舊請求時間戳
        self.request_timestamps = [ts for ts in self.request_timestamps
                                   if current_time - ts < self.time_window]

        # 如果當前窗口中的請求數已達到上限，則等待
        if len(self.request_timestamps) >= self.max_requests:
            oldest_timestamp = min(self.request_timestamps)
            sleep_time = self.time_window - (current_time - oldest_timestamp)

            if sleep_time > 0:
                logger.info(f"達到速率限制，等待 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)

        # 添加當前請求的時間戳
        self.request_timestamps.append(time.time())

        # 添加小隨機延遲，避免所有請求同時發送
        jitter = random.uniform(0.1, 0.5)
        time.sleep(jitter)


class PlayerRatingSystem:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.current_game_data = None
        self.player_data = {}
        self.rate_limiter = RateLimiter()

    def api_request(self, url, max_retries=MAX_RETRIES):
        """發送API請求，包含重試邏輯和速率限制處理"""
        retry_count = 0
        delay = BASE_DELAY

        while retry_count < max_retries:
            try:
                # 請求前檢查速率限制
                self.rate_limiter.wait_if_needed()

                # 發送請求
                response = requests.get(url, timeout=10)

                # 處理成功響應
                if response.status_code == 200:
                    return response.json()

                # 處理速率限制錯誤
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', delay))
                    logger.warning(f"速率限制(429)錯誤，等待 {retry_after} 秒後重試 ({retry_count + 1}/{max_retries})")
                    time.sleep(retry_after)
                    delay = min(MAX_DELAY, delay * 2)  # 指數退避

                # 處理伺服器錯誤
                elif 500 <= response.status_code < 600:
                    logger.warning(f"伺服器錯誤({response.status_code})，等待 {delay} 秒後重試 ({retry_count + 1}/{max_retries})")
                    time.sleep(delay)
                    delay = min(MAX_DELAY, delay * 2)  # 指數退避

                # 處理其他錯誤
                else:
                    logger.error(f"API請求失敗: {response.status_code} - {response.text}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.warning(f"請求異常: {e}，等待 {delay} 秒後重試 ({retry_count + 1}/{max_retries})")
                time.sleep(delay)
                delay = min(MAX_DELAY, delay * 2)  # 指數退避

            retry_count += 1

        logger.error(f"達到最大重試次數，請求失敗: {url}")
        return None

    def get_current_game_data(self):
        """獲取當前遊戲數據"""
        try:
            live_game_url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
            logger.info(f"請求遊戲數據 URL: {live_game_url}")
            response = requests.get(live_game_url, verify=False, timeout=3)
            logger.info(f"遊戲數據響應: {response.status_code}")

            if response.status_code != 200:
                logger.error("獲取遊戲數據失敗")
                return None

            self.current_game_data = response.json()
            logger.info(f"成功獲取遊戲數據")

            # 解析玩家信息
            players_data = []
            for player in self.current_game_data.get('allPlayers', []):
                player_info = {
                    'riotIdGameName': player.get('riotIdGameName', ''),
                    'riotIdTagLine': player.get('riotIdTagLine', ''),
                    'championName': player.get('championName', ''),
                    'championId': player.get('championId', 0),
                    'team': player.get('team', '')
                }
                players_data.append(player_info)
            logger.info(f"成功解析玩家數據，玩家數量: {len(players_data)}")
            return players_data
        except Exception as e:
            logger.error(f"獲取當前遊戲數據時出錯: {e}")
            return None

    def get_puuid_by_riot_id(self, game_name, tag_line):
        """透過Riot ID獲取PUUID"""
        try:
            url = f"https://{ASIA_SERVER}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={self.api_key}"
            logger.info(f"請求PUUID: {game_name}#{tag_line}")

            data = self.api_request(url)
            if not data:
                logger.error(f"獲取PUUID失敗: {game_name}#{tag_line}")
                return None

            logger.info(f"成功獲取PUUID: {data.get('puuid')}")
            return data.get('puuid')
        except Exception as e:
            logger.error(f"獲取PUUID時出錯: {e}")
            return None

    def get_recent_aram_matches(self, puuid, count=20):
        """獲取玩家最近的ARAM對局ID"""
        try:
            url = f"https://{SEA_SERVER}/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=450&start=0&count={count}&api_key={self.api_key}"
            logger.info(f"請求最近ARAM對局: {puuid}")

            match_ids = self.api_request(url)
            if not match_ids:
                logger.error(f"獲取最近對局失敗: {puuid}")
                return []

            logger.info(f"成功獲取{len(match_ids)}場對局ID")
            return match_ids
        except Exception as e:
            logger.error(f"獲取最近對局時出錯: {e}")
            return []

    def get_match_details(self, match_id):
        """獲取對局詳細信息"""
        try:
            url = f"https://{SEA_SERVER}/lol/match/v5/matches/{match_id}?api_key={self.api_key}"
            logger.info(f"請求對局詳情: {match_id}")

            match_details = self.api_request(url)
            if not match_details:
                logger.error(f"獲取對局詳情失敗: {match_id}")
                return None

            logger.info(f"成功獲取對局詳情: {match_id}")
            return match_details
        except Exception as e:
            logger.error(f"獲取對局詳情時出錯: {e}")
            return None

    def calculate_match_rating(self, participant_data, champion_metrics):
        """根據對局數據計算評分，使用從API獲取的英雄基準數據進行標準化"""
        try:
            # 獲取對局時長（分鐘）
            game_duration_min = participant_data.get('timePlayed', 0) / 60
            if game_duration_min <= 0:
                logger.error("對局時長為零或負數，無法計算評分")
                return 0

            # 計算每分鐘數據
            dmg_per_min = participant_data.get('totalDamageDealtToChampions', 0) / game_duration_min
            tank_per_min = participant_data.get('totalDamageTaken', 0) / game_duration_min
            heal_per_min = (participant_data.get('totalHeal', 0) + participant_data.get('totalHealsOnTeammates',
                                                                                        0)) / game_duration_min
            mitigate_per_min = participant_data.get('damageSelfMitigated', 0) / game_duration_min
            cc_per_min = participant_data.get('timeCCingOthers', 0) / game_duration_min

            # 獲取英雄基準數據 (與SQL表結構匹配)
            std_dmg = champion_metrics.get('avg_damage_per_min', 1500)
            std_tank = champion_metrics.get('avg_damage_taken_per_min', 1500)
            std_heal = champion_metrics.get('avg_healing_per_min', 200)
            std_mitigate = champion_metrics.get('avg_damage_mitigated_per_min', 1000)
            std_cc = champion_metrics.get('avg_time_ccing_per_min', 1.5)

            # 日誌記錄實際值與基準值
            logger.info(
                f"玩家表現: 傷害={dmg_per_min:.1f}/min, 承傷={tank_per_min:.1f}/min, 治療={heal_per_min:.1f}/min, 免傷={mitigate_per_min:.1f}/min, 控場={cc_per_min:.1f}/min")
            logger.info(
                f"英雄基準: 傷害={std_dmg:.1f}/min, 承傷={std_tank:.1f}/min, 治療={std_heal:.1f}/min, 免傷={std_mitigate:.1f}/min, 控場={std_cc:.1f}/min")

            # 計算標準化得分 (比率 * 100，限制在0-200範圍內)
            # 使用 sigmoid 函數可以產生更平滑的評分曲線
            def calculate_score(actual, standard):
                if standard <= 0:
                    return 100  # 避免除以零
                ratio = actual / standard
                # 使用 sigmoid 函數將比率映射到 0-200 範圍
                # ratio=1 時得分為 100，ratio=2 時接近 200，ratio=0.5 時接近 0
                return 200 / (1 + np.exp(-3 * (ratio - 0.8)))

            dmg_score = calculate_score(dmg_per_min, std_dmg)
            tank_score = calculate_score(tank_per_min, std_tank)
            heal_score = calculate_score(heal_per_min, std_heal)
            mitigate_score = calculate_score(mitigate_per_min, std_mitigate)
            cc_score = calculate_score(cc_per_min, std_cc)

            # 使用固定權重，不依據英雄類型
            weights = [0.35, 0.20, 0.15, 0.15, 0.15]  # 傷害、承傷、治療、免傷、控場的權重

            # 綜合評分計算 (表現分數加權平均)
            scores = [dmg_score, tank_score, heal_score, mitigate_score, cc_score]
            weighted_avg_score = sum(score * weight for score, weight in zip(scores, weights))

            # 勝負加權 (勝利加成、失敗減益)
            win_weight = 1.2 if participant_data.get('win', False) else 0.8
            final_score = weighted_avg_score * win_weight

            # 分數控制在0-1000範圍內
            final_score = min(1000, max(0, final_score))

            # 輸出計算過程
            logger.info(
                f"對局評分計算: 傷害={dmg_score:.1f}，承傷={tank_score:.1f}，治療={heal_score:.1f}，免傷={mitigate_score:.1f}，控場={cc_score:.1f}")
            logger.info(f"權重={weights}，勝負權重={win_weight}，綜合評分={final_score:.1f}")

            return round(final_score, 1)
        except Exception as e:
            logger.error(f"計算對局評分時出錯: {e}")
            return 0

    def get_champion_metrics(self, champion_id):
        """獲取英雄基準數據，修改為與SQL表結構匹配的欄位名"""
        try:
            # 由於這個API不是Riot的，不需要經過限速控制器
            url = f"{CHAMPION_METRICS_API}{champion_id}"
            logger.info(f"請求英雄基準數據: {champion_id}")

            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                logger.error(f"獲取英雄基準數據失敗: {response.status_code} - {response.text}")
                return {
                    'avg_damage_per_min': 1500,  # 平均每分鐘傷害
                    'avg_damage_taken_per_min': 1500,  # 平均每分鐘承傷
                    'avg_healing_per_min': 200,  # 平均每分鐘治療
                    'avg_damage_mitigated_per_min': 1000,  # 平均每分鐘免傷
                    'avg_time_ccing_per_min': 1.5  # 平均每分鐘控場時間
                }

            metrics = response.json()
            logger.info(f"成功獲取英雄基準數據: {champion_id},{metrics}")

            # 如果API返回的欄位與SQL表不同，進行映射
            return {
                'avg_damage_per_min': metrics.get('avg_damage_per_min'),
                'avg_damage_taken_per_min': metrics.get('avg_damage_taken_per_min'),
                'avg_healing_per_min': metrics.get('avg_healing_per_min'),
                'avg_damage_mitigated_per_min': metrics.get('avg_damage_mitigated_per_min'),
                'avg_time_ccing_per_min': metrics.get('avg_time_ccing_per_min')
            }
        except Exception as e:
            logger.error(f"獲取英雄基準數據時出錯: {e}")
            return {
                'avg_damage_per_min': 1500,  # 平均每分鐘傷害
                'avg_damage_taken_per_min': 1500,  # 平均每分鐘承傷
                'avg_healing_per_min': 200,  # 平均每分鐘治療
                'avg_damage_mitigated_per_min': 1000,  # 平均每分鐘免傷
                'avg_time_ccing_per_min': 1.5  # 平均每分鐘控場時間
            }

    def get_player_rating(self, game_name, tag_line, champion_name=None):
        """獲取玩家評分"""
        try:
            # 獲取PUUID
            puuid = self.get_puuid_by_riot_id(game_name, tag_line)
            if not puuid:
                logger.error(f"無法獲取玩家PUUID: {game_name}#{tag_line}")
                return None

            # 獲取最近對局列表
            match_ids = self.get_recent_aram_matches(puuid)
            if not match_ids:
                logger.error(f"無法獲取玩家最近對局: {game_name}#{tag_line}")
                return None

            # 分析每個對局
            matches_analyzed = 0
            total_rating = 0
            match_ratings = []

            for match_id in match_ids:
                # 獲取對局詳情
                match_details = self.get_match_details(match_id)
                if not match_details:
                    continue

                # 在對局中查找該玩家
                for participant in match_details.get('info', {}).get('participants', []):
                    if participant.get('puuid') == puuid:
                        # 獲取英雄ID
                        champion_id = participant.get('championId')
                        current_champion_name = participant.get('championName')

                        # 如果指定了英雄，只分析該英雄的對局
                        if champion_name and current_champion_name != champion_name:
                            continue

                        # 獲取英雄基準數據
                        champion_metrics = self.get_champion_metrics(champion_id)

                        # 計算評分
                        match_rating = self.calculate_match_rating(participant, champion_metrics)

                        match_data = {
                            'match_id': match_id,
                            'champion': current_champion_name,
                            'kills': participant.get('kills', 0),
                            'deaths': participant.get('deaths', 0),
                            'assists': participant.get('assists', 0),
                            'damage': participant.get('totalDamageDealtToChampions', 0),
                            'win': participant.get('win', False),
                            'rating': match_rating
                        }

                        match_ratings.append(match_data)
                        total_rating += match_rating
                        matches_analyzed += 1
                        break

                # 分析足夠數量的對局後停止
                if matches_analyzed >= 20:
                    break

            # 計算平均評分
            if matches_analyzed > 0:
                average_rating = total_rating / matches_analyzed
                logger.info(f"玩家 {game_name}#{tag_line} 的平均評分: {average_rating:.1f} (基於{matches_analyzed}場對局)")

                return {
                    'player': f"{game_name}#{tag_line}",
                    'average_rating': round(average_rating, 1),
                    'matches_analyzed': matches_analyzed,
                    'match_ratings': match_ratings
                }
            else:
                logger.error(f"沒有可用的對局數據來計算評分: {game_name}#{tag_line}")
                return None
        except Exception as e:
            logger.error(f"獲取玩家評分時出錯: {e}")
            return None

    def analyze_current_game(self):
        """分析當前遊戲中的所有玩家"""
        try:
            # 獲取當前遊戲數據
            players_data = self.get_current_game_data()
            if not players_data:
                logger.error("無法獲取當前遊戲數據")
                return None

            # 分析每個玩家
            player_ratings = []

            for player in players_data:
                game_name = player.get('riotIdGameName')
                tag_line = player.get('riotIdTagLine')
                champion_name = player.get('championName')
                team = player.get('team')

                logger.info(f"分析玩家: {game_name}#{tag_line} 使用英雄: {champion_name} 隊伍: {team}")

                # 檢查是否已有該玩家的數據
                player_key = f"{game_name}#{tag_line}"
                if player_key in self.player_data:
                    player_rating = self.player_data[player_key]
                else:
                    player_rating = self.get_player_rating(game_name, tag_line)
                    if player_rating:
                        self.player_data[player_key] = player_rating

                if player_rating:
                    player_ratings.append({
                        'player': player_key,
                        'champion': champion_name,
                        'team': team,
                        'rating': player_rating.get('average_rating', 0),
                        'matches_analyzed': player_rating.get('matches_analyzed', 0)
                    })

            # 按隊伍分組
            team_ratings = {'100': [], '200': []}
            for rating in player_ratings:
                team = rating.get('team', '')
                if team in team_ratings:
                    team_ratings[team].append(rating)

            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'player_ratings': player_ratings,
                'team_ratings': team_ratings
            }
        except Exception as e:
            logger.error(f"分析當前遊戲時出錯: {e}")
            return None

    def export_to_json(self, data, filename='player_ratings.json'):
        """將評分數據匯出到JSON檔案"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"數據已匯出到 {filename}")
            return True
        except Exception as e:
            logger.error(f"匯出數據時出錯: {e}")
            return False

    def cache_data(self, cache_file='rating_system_cache.json'):
        """將玩家數據緩存到文件"""
        try:
            cache_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'player_data': self.player_data
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"緩存數據已保存到 {cache_file}")
            return True
        except Exception as e:
            logger.error(f"緩存數據時出錯: {e}")
            return False

    def load_cache(self, cache_file='rating_system_cache.json'):
        """從文件加載緩存的玩家數據"""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                self.player_data = cache_data.get('player_data', {})
                logger.info(f"已從 {cache_file} 加載緩存數據，包含 {len(self.player_data)} 名玩家")
                return True
            else:
                logger.info(f"緩存文件 {cache_file} 不存在")
                return False
        except Exception as e:
            logger.error(f"加載緩存數據時出錯: {e}")
            return False


# 從JSON檔案讀取對戰數據（範例，用於開發測試）
def parse_json_match_data(json_file):
    """從JSON檔案讀取和解析對局數據"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
        return match_data
    except Exception as e:
        logger.error(f"讀取JSON檔案時出錯: {e}")
        return None


# 如果是直接執行此腳本
if __name__ == "__main__":
    # 初始化評分系統
    rating_system = PlayerRatingSystem()

    # 嘗試加載緩存數據
    rating_system.load_cache()

    # 示範：從JSON檔案分析對局數據
    sample_data_path = 'sample_data/aram_api_data.json'
    if not os.path.exists(sample_data_path):
        sample_data_path = 'paste.txt'  # 嘗試使用備用路徑

    sample_data = parse_json_match_data(sample_data_path)

    if sample_data:
        # 使用示例：分析JSON文件中的玩家數據
        participants = sample_data.get('info', {}).get('participants', [])
        for participant in participants[:2]:  # 只分析前兩名玩家作為示例
            puuid = participant.get('puuid')
            champion_id = participant.get('championId')
            champion_name = participant.get('championName')
            riotIdGameName = participant.get('riotIdGameName')
            riotIdTagline = participant.get('riotIdTagline')

            print(f"\n分析玩家: {riotIdGameName}#{riotIdTagline} ({champion_name})")

            player_rating = rating_system.get_player_rating(riotIdGameName, riotIdTagline)
            if player_rating:
                print(f"玩家評分: {player_rating['average_rating']}")

    # 保存緩存數據
    rating_system.cache_data()

    print("\n如果要在遊戲中使用，請調用 analyze_current_game() 方法")
