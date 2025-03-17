import json
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import logging
import os
from tqdm import tqdm

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 資料庫連線設定
def create_db_connection(config):
    """建立 PostgreSQL 資料庫連線"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        return conn
    except Exception as e:
        logging.error(f"資料庫連線錯誤: {e}")
        raise


def extract_match_data(row):
    """從match_data欄位提取JSON資料"""
    try:
        # 直接回傳取出的資料，假設已是 dict
        return row['match_data']
    except KeyError as e:
        logging.error(f"資料中找不到 match_data 欄位, row_id: {row.get('id', 'unknown')}")
        return None


def fetch_data_in_batches(conn, table_name, batch_size=5000):
    """分批次從資料庫讀取資料"""
    cursor = conn.cursor()
    offset = 0

    # 先獲取總記錄數
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cursor.fetchone()[0]

    # 設定進度條
    with tqdm(total=total_rows, desc=f"讀取 {table_name} 資料") as pbar:
        while True:
            cursor.execute(
                f"SELECT id, is_searched_summoners, match_id, game_mode, game_type, "
                f"game_version, match_data FROM {table_name} "
                f"WHERE game_mode = 'ARAM' "  # 只處理 ARAM 對局
                f"ORDER BY id "
                f"LIMIT {batch_size} OFFSET {offset}"
            )

            rows = cursor.fetchall()
            if not rows:
                break

            # 創建 DataFrame
            columns = ['id', 'is_searched_summoners', 'match_id', 'game_mode',
                       'game_type', 'game_version', 'match_data']
            df = pd.DataFrame(rows, columns=columns)

            # 更新進度條
            pbar.update(len(rows))

            # 提供批次資料
            yield df

            # 更新偏移量
            offset += batch_size

    cursor.close()


from collections import defaultdict
import logging
from difflib import get_close_matches


def normalize_champion_name(champion_name):
    """
    標準化英雄名稱：轉換為小寫並移除特殊字符
    """
    if not champion_name:
        return None
    # 轉換為小寫並移除可能的單引號或其他特殊字符
    return champion_name.lower().replace("'", "").replace(" ", "").strip()


def find_champion_in_dict(champion_name, champion_dict):
    """
    在字典中查找英雄，先嘗試精確匹配，然後是模糊匹配

    Args:
        champion_name: 要查找的英雄名稱
        champion_dict: 英雄字典，包含標準化的英雄名稱

    Returns:
        找到的標準英雄ID或None
    """
    if not champion_name:
        return None

    # 創建標準化的字典和鍵的對照表
    normalized_dict = {}
    for key in champion_dict:
        normalized_key = normalize_champion_name(key)
        normalized_dict[normalized_key] = key

    # 標準化輸入的英雄名稱
    normalized_name = normalize_champion_name(champion_name)

    # 嘗試直接查找
    if normalized_name in normalized_dict:
        return champion_dict[normalized_dict[normalized_name]]

    # 嘗試模糊匹配
    possible_matches = get_close_matches(normalized_name, normalized_dict.keys(), n=1, cutoff=0.6)
    if possible_matches:
        closest_match = possible_matches[0]
        original_key = normalized_dict[closest_match]
        logging.info(f"模糊匹配: '{champion_name}' 匹配到 '{original_key}'")
        return champion_dict[original_key]

    # 沒有找到匹配
    logging.error(f"無法找到英雄: '{champion_name}'，沒有可用的匹配")
    return None


def process_match_data_batch(batch_df, champion_dict):
    """處理一批次的比賽資料"""
    processed_stats = {
        'champions': {},  # 英雄基本統計
        'runes': defaultdict(list),  # 符文構建
        'builds': defaultdict(list),  # 裝備構建
        'skills': defaultdict(list),  # 技能順序
        'versions': defaultdict(lambda: defaultdict(list)),  # 版本資料
        'matchups': defaultdict(lambda: defaultdict(list)),  # 對位資料
        'synergies': defaultdict(lambda: defaultdict(list))  # 協同資料
    }

    for _, row in batch_df.iterrows():
        match_data = extract_match_data(row)
        if not match_data:
            continue

        # 獲取基本比賽資訊
        try:
            info = match_data.get('info', {})
            game_version = info.get('gameVersion', '')
            game_duration = info.get('gameDuration', 0)

            # 只處理有效的比賽 (超過5分鐘)
            if game_duration < 300:
                continue

            # 獲取勝利隊伍ID
            winning_team_id = None
            for team in info.get('teams', []):
                if team.get('win') == True:
                    winning_team_id = team.get('teamId')
                    break

            if not winning_team_id:
                continue

            # 處理參與者資料
            participants = info.get('participants', [])

            # 獲取比賽中的所有英雄ID列表 (依隊伍分組)
            team_champions = {100: [], 200: []}
            for participant in participants:
                team_id = participant.get('teamId')
                champion_id = participant.get('championId')
                champion_name = participant.get('championName')

                # 確保championId和championName有效
                if not champion_id or not champion_name:
                    continue

                # 使用新的查找函數找到標準化的英雄ID
                std_champion_id = find_champion_in_dict(champion_name, champion_dict)
                if std_champion_id:
                    team_champions[team_id].append(std_champion_id)

            # 計算英雄協同統計
            for team_id, champions in team_champions.items():
                win = (team_id == winning_team_id)
                # 為所有英雄對組合計算協同
                for i in range(len(champions)):
                    for j in range(i + 1, len(champions)):
                        champ1 = champions[i]
                        champ2 = champions[j]

                        # 確保順序一致 (字母順序)
                        if champ1 > champ2:
                            champ1, champ2 = champ2, champ1

                        # 記錄協同資料
                        processed_stats['synergies'][champ1][champ2].append(win)

            # 處理每名參與者的詳細數據
            for participant in participants:
                # 提取基本資訊
                champion_id = participant.get('championId')
                champion_name = participant.get('championName')

                # 確保championId和championName有效
                if not champion_id or not champion_name:
                    continue

                # 使用新的查找函數找到標準化的英雄ID
                std_champion_id = find_champion_in_dict(champion_name, champion_dict)
                if not std_champion_id:
                    logging.warning(f"找不到英雄字典對應: {champion_name} (ID:{champion_id})")
                    continue

                team_id = participant.get('teamId')
                win = (team_id == winning_team_id)

                # 計算英雄對位資料
                opponent_team_id = 200 if team_id == 100 else 100
                for opponent in participants:
                    if opponent.get('teamId') == opponent_team_id:
                        opponent_champion = opponent.get('championName')
                        if opponent_champion:
                            opponent_std_id = find_champion_in_dict(opponent_champion, champion_dict)
                            if opponent_std_id:
                                processed_stats['matchups'][std_champion_id][opponent_std_id].append(win)

                # 累積基本統計
                if std_champion_id not in processed_stats['champions']:
                    processed_stats['champions'][std_champion_id] = {
                        'games': 0,
                        'wins': 0,
                        'kills': 0,
                        'deaths': 0,
                        'assists': 0,
                        'damage_dealt': 0,
                        'damage_taken': 0,
                        'healing': 0,
                        'healing_done': 0,
                        'team_damage_percentage': 0,
                        'team_damage_taken_percentage': 0,
                        'team_healing_percentage': 0
                    }

                champ_stats = processed_stats['champions'][std_champion_id]
                champ_stats['games'] += 1
                champ_stats['wins'] += 1 if win else 0
                champ_stats['kills'] += participant.get('kills', 0)
                champ_stats['deaths'] += participant.get('deaths', 0)
                champ_stats['assists'] += participant.get('assists', 0)
                champ_stats['damage_dealt'] += participant.get('totalDamageDealtToChampions', 0)
                champ_stats['damage_taken'] += participant.get('totalDamageTaken', 0)

                # 治療統計 (自身和給隊友的)
                total_heal = participant.get('totalHeal', 0)
                healing_done = participant.get('totalHealsOnTeammates', 0)
                champ_stats['healing'] += total_heal
                champ_stats['healing_done'] += healing_done

                # 獲取隊伍的傷害佔比數據
                if 'challenges' in participant:
                    challenges = participant['challenges']
                    damage_percent = challenges.get('teamDamagePercentage', 0)
                    damage_taken_percent = challenges.get('damageTakenOnTeamPercentage', 0)

                    champ_stats['team_damage_percentage'] += damage_percent
                    champ_stats['team_damage_taken_percentage'] += damage_taken_percent

                # 處理符文資料
                if 'perks' in participant:
                    perks = participant['perks']
                    rune_data = {
                        'champion_id': std_champion_id,
                        'version': game_version,
                        'win': win,
                        'perks': perks
                    }
                    processed_stats['runes'][std_champion_id].append(rune_data)

                # 處理裝備資料
                items = []
                for i in range(7):  # item0 - item6
                    item_id = participant.get(f'item{i}', 0)
                    if item_id and item_id > 0:
                        items.append(item_id)

                build_data = {
                    'champion_id': std_champion_id,
                    'version': game_version,
                    'win': win,
                    'items': items
                }
                processed_stats['builds'][std_champion_id].append(build_data)

                # 處理版本資料
                # 只保留主版本號，例如 "15.1.649.4112" -> "15.1"
                if game_version and '.' in game_version:
                    version_short = '.'.join(game_version.split('.')[:2])
                    version_data = processed_stats['versions'][std_champion_id][version_short]
                    version_data.append({
                        'win': win,
                        'damage_dealt': participant.get('totalDamageDealtToChampions', 0),
                        'damage_taken': participant.get('totalDamageTaken', 0),
                        'healing': total_heal + healing_done
                    })

        except Exception as e:
            logging.error(f"處理比賽資料錯誤: {e}, match_id: {row.get('match_id', 'unknown')}")
            continue

    return processed_stats


def calculate_final_stats(processed_stats):
    """計算最終統計數據"""
    # 英雄統計
    champions_final = []
    for champion_id, stats in processed_stats['champions'].items():
        if stats['games'] == 0:
            continue

        win_rate = stats['wins'] / stats['games'] * 100

        # 計算所有英雄遊戲場次總和 (用於計算選用率)
        total_games = sum(c['games'] for c in processed_stats['champions'].values())

        champions_final.append({
            'champion_id': champion_id,
            'win_rate': win_rate,
            'pick_rate': stats['games'] / total_games * 100 if total_games > 0 else 0,
            'ban_rate': 0,  # ARAM通常沒有禁選
            'avg_kills': stats['kills'] / stats['games'],
            'avg_deaths': stats['deaths'] / stats['games'],
            'avg_assists': stats['assists'] / stats['games'],
            'kda_ratio': (stats['kills'] + stats['assists']) / max(1, stats['deaths']),
            'avg_damage': stats['damage_dealt'] / stats['games'],
            'avg_damage_percentage': stats['team_damage_percentage'] / stats['games'] * 100,
            'avg_healing': (stats['healing'] + stats['healing_done']) / stats['games'],
            'avg_healing_percentage': 0,  # 需要另外計算
            'avg_damage_taken': stats['damage_taken'] / stats['games'],
            'avg_damage_taken_percentage': stats['team_damage_taken_percentage'] / stats['games'] * 100,
            'sample_size': stats['games']
        })

    # 按勝率排序
    champions_final.sort(key=lambda x: x['win_rate'], reverse=True)

    # 添加排名和層級
    for i, champion in enumerate(champions_final):
        champion['rank'] = i + 1
        if i < len(champions_final) * 0.1:
            champion['tier'] = 'S'
        elif i < len(champions_final) * 0.3:
            champion['tier'] = 'A'
        elif i < len(champions_final) * 0.6:
            champion['tier'] = 'B'
        elif i < len(champions_final) * 0.9:
            champion['tier'] = 'C'
        else:
            champion['tier'] = 'D'

    # 版本趨勢
    trends_final = []
    for champion_id, versions in processed_stats['versions'].items():
        for version, data_list in versions.items():
            if not data_list:
                continue

            games = len(data_list)
            wins = sum(1 for d in data_list if d['win'])
            win_rate = wins / games * 100 if games > 0 else 0

            # 計算這個版本的總遊戲場次 (用於計算選用率)
            version_total_games = sum(
                len(v) for champ_versions in processed_stats['versions'].values() for ver, v in champ_versions.items()
                if ver == version)

            trends_final.append({
                'champion_id': champion_id,
                'version': version,
                'win_rate': win_rate,
                'pick_rate': games / version_total_games * 100 if version_total_games > 0 else 0,
                'sample_size': games
            })

    # 符文統計
    runes_final = []
    for champion_id, rune_list in processed_stats['runes'].items():
        # 按照符文配置分組
        rune_configs = defaultdict(list)
        for rune_data in rune_list:
            # 簡化的符文鍵生成 (實際應用中應更精確)
            try:
                primary_style = rune_data['perks']['styles'][0]['style']
                primary_selection = rune_data['perks']['styles'][0]['selections'][0]['perk']
                secondary_style = rune_data['perks']['styles'][1]['style']
                key = f"{primary_style}_{primary_selection}_{secondary_style}"
                rune_configs[key].append(rune_data)
            except (KeyError, IndexError):
                continue

        # 計算每種符文配置的勝率
        for config_key, config_data in rune_configs.items():
            if len(config_data) < 5:  # 樣本太小跳過
                continue

            games = len(config_data)
            wins = sum(1 for d in config_data if d['win'])
            win_rate = wins / games * 100 if games > 0 else 0

            # 解析符文配置
            try:
                example = config_data[0]
                primary_path = example['perks']['styles'][0]['style']
                primary_rune = example['perks']['styles'][0]['selections'][0]['perk']
                secondary_path = example['perks']['styles'][1]['style']

                # 簡化的符文選項提取 (實際應用中應映射到名稱)
                rune_options = []
                for style in example['perks']['styles']:
                    for selection in style['selections']:
                        rune_options.append(selection['perk'])

                shard_options = []
                if 'statPerks' in example['perks']:
                    statPerks = example['perks']['statPerks']
                    shard_options = [
                        statPerks.get('offense', 0),
                        statPerks.get('flex', 0),
                        statPerks.get('defense', 0)
                    ]

                runes_final.append({
                    'champion_id': champion_id,
                    'primary_path': str(primary_path),
                    'primary_rune': str(primary_rune),
                    'secondary_path': str(secondary_path),
                    'rune_options': json.dumps(rune_options),
                    'shard_options': json.dumps(shard_options),
                    'win_rate': win_rate,
                    'pick_rate': games / len(rune_list) * 100,
                    'sample_size': games,
                    'version': 'aggregate'  # 簡化版本處理
                })
            except (KeyError, IndexError):
                continue

    # 裝備統計
    builds_final = []
    for champion_id, build_list in processed_stats['builds'].items():
        # 簡化的裝備處理: 只考慮前三件核心裝備
        build_configs = defaultdict(list)
        for build_data in build_list:
            items = build_data['items']
            if len(items) >= 3:  # 至少有3件裝備
                key = '_'.join(str(item) for item in sorted(items[:3]))
                build_configs[key].append(build_data)

        # 計算每種裝備配置的勝率
        for config_key, config_data in build_configs.items():
            if len(config_data) < 5:  # 樣本太小跳過
                continue

            games = len(config_data)
            wins = sum(1 for d in config_data if d['win'])
            win_rate = wins / games * 100 if games > 0 else 0

            # 解析裝備配置
            example = config_data[0]

            # 簡單區分起始、核心和選擇性裝備
            items = example['items']
            starting_items = []
            core_items = []
            optional_items = []

            # 簡化的裝備分類規則 (實際應用中應更精確)
            for item in items:
                if item < 2000:  # 假設小於2000的物品ID為起始物品
                    starting_items.append(item)
                elif item < 4000:  # 假設2000-4000的物品ID為核心物品
                    core_items.append(item)
                else:  # 其他為選擇性物品
                    optional_items.append(item)

            builds_final.append({
                'champion_id': champion_id,
                'starting_items': json.dumps(starting_items),
                'core_items': json.dumps(core_items if core_items else items[:3]),  # 至少有3件核心裝備
                'optional_items': json.dumps(optional_items),
                'win_rate': win_rate,
                'pick_rate': games / len(build_list) * 100,
                'sample_size': games,
                'version': 'aggregate'  # 簡化版本處理
            })

    # 英雄對位統計
    matchups_final = []
    for champ1, opponents in processed_stats['matchups'].items():
        for champ2, results in opponents.items():
            if len(results) < 5:  # 樣本太小跳過
                continue

            games = len(results)
            wins = sum(1 for result in results if result)
            win_rate = wins / games * 100 if games > 0 else 0

            matchups_final.append({
                'champion_id': champ1,
                'opponent_id': champ2,
                'win_rate': win_rate,
                'sample_size': games
            })

    # 英雄協同統計
    synergies_final = []
    for champ1, allies in processed_stats['synergies'].items():
        for champ2, results in allies.items():
            if len(results) < 5:  # 樣本太小跳過
                continue

            games = len(results)
            wins = sum(1 for result in results if result)
            win_rate = wins / games * 100 if games > 0 else 0

            # 基於勝率計算協同分數 (簡單模型)
            # 協同分數 = 一起出場時的勝率 - (champ1的平均勝率 + champ2的平均勝率)/2
            # 正值表示協同效果好，負值表示協同效果差
            champ1_win_rate = processed_stats['champions'][champ1]['wins'] / processed_stats['champions'][champ1][
                'games'] * 100 if processed_stats['champions'][champ1]['games'] > 0 else 50
            champ2_win_rate = processed_stats['champions'][champ2]['wins'] / processed_stats['champions'][champ2][
                'games'] * 100 if processed_stats['champions'][champ2]['games'] > 0 else 50
            expected_win_rate = (champ1_win_rate + champ2_win_rate) / 2
            synergy_score = win_rate - expected_win_rate

            synergies_final.append({
                'champion1_id': champ1,
                'champion2_id': champ2,
                'win_rate': win_rate,
                'synergy_score': synergy_score,
                'sample_size': games
            })

    return {
        'champions': champions_final,
        'trends': trends_final,
        'runes': runes_final,
        'builds': builds_final,
        'matchups': matchups_final,
        'synergies': synergies_final
    }


def load_champion_mapping(conn):
    """從資料庫讀取英雄ID映射"""
    cursor = conn.cursor()
    champion_dict = {}

    try:
        # 從champions表格獲取英雄映射
        cursor.execute("SELECT champion_id, champion_name, champion_tw_name, key FROM champions")
        champions = cursor.fetchall()

        for champion_id, champion_name, champion_tw_name, key in champions:
            # 將英文名稱和中文名稱都映射到標準化的champion_id
            champion_dict[champion_id] = champion_id
            # 額外處理特殊情況
            if "'" in champion_id:  # 例如 Kai'Sa
                simple_name = champion_id.replace("'", "")
                champion_dict[simple_name] = champion_id
            if " " in champion_id:  # 例如 Aurelion Sol
                simple_name = champion_id.replace(" ", "")
                champion_dict[simple_name] = champion_id

        logging.info(f"已載入 {len(champions)} 個英雄的映射關係")
        return champion_dict
    except Exception as e:
        logging.error(f"讀取英雄映射時發生錯誤: {e}")
        return {}
    finally:
        cursor.close()


def insert_champion_stats(conn, data):
    """插入英雄統計資料到資料庫"""
    try:
        cursor = conn.cursor()

        # 插入英雄統計資料
        if data['champions']:
            logging.info(f"正在插入 {len(data['champions'])} 筆英雄統計資料...")

            insert_query = """
                INSERT INTO champion_stats 
                (champion_id, win_rate, pick_rate, ban_rate, avg_kills, avg_deaths, avg_assists, 
                kda_ratio, avg_damage, avg_damage_percentage, avg_healing, avg_healing_percentage,
                avg_damage_taken, avg_damage_taken_percentage, tier, rank, sample_size, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (champion_id) DO UPDATE SET
                win_rate = EXCLUDED.win_rate,
                pick_rate = EXCLUDED.pick_rate,
                ban_rate = EXCLUDED.ban_rate,
                avg_kills = EXCLUDED.avg_kills,
                avg_deaths = EXCLUDED.avg_deaths,
                avg_assists = EXCLUDED.avg_assists,
                kda_ratio = EXCLUDED.kda_ratio,
                avg_damage = EXCLUDED.avg_damage,
                avg_damage_percentage = EXCLUDED.avg_damage_percentage,
                avg_healing = EXCLUDED.avg_healing,
                avg_healing_percentage = EXCLUDED.avg_healing_percentage,
                avg_damage_taken = EXCLUDED.avg_damage_taken,
                avg_damage_taken_percentage = EXCLUDED.avg_damage_taken_percentage,
                tier = EXCLUDED.tier,
                rank = EXCLUDED.rank,
                sample_size = EXCLUDED.sample_size,
                version = EXCLUDED.version,
                updated_at = CURRENT_TIMESTAMP
            """

            stats_data = [
                (
                    champ['champion_id'],
                    champ['win_rate'],
                    champ['pick_rate'],
                    champ['ban_rate'],
                    champ['avg_kills'],
                    champ['avg_deaths'],
                    champ['avg_assists'],
                    champ['kda_ratio'],
                    champ['avg_damage'],
                    champ['avg_damage_percentage'],
                    champ['avg_healing'],
                    champ.get('avg_healing_percentage', 0),
                    champ['avg_damage_taken'],
                    champ['avg_damage_taken_percentage'],
                    champ['tier'],
                    champ['rank'],
                    champ['sample_size'],
                    'current'
                )
                for champ in data['champions']
            ]

            execute_batch(cursor, insert_query, stats_data, page_size=100)

        # 插入版本趨勢資料
        if data['trends']:
            logging.info(f"正在插入 {len(data['trends'])} 筆版本趨勢資料...")

            insert_query = """
                INSERT INTO champion_trends 
                (champion_id, version, win_rate, pick_rate, sample_size)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (champion_id, version) DO UPDATE SET
                win_rate = EXCLUDED.win_rate,
                pick_rate = EXCLUDED.pick_rate,
                sample_size = EXCLUDED.sample_size,
                updated_at = CURRENT_TIMESTAMP
            """

            trends_data = [
                (
                    trend['champion_id'],
                    trend['version'],
                    trend['win_rate'],
                    trend['pick_rate'],
                    trend['sample_size']
                )
                for trend in data['trends']
            ]

            execute_batch(cursor, insert_query, trends_data, page_size=100)

        # 插入符文資料
        if data['runes']:
            logging.info(f"正在插入 {len(data['runes'])} 筆符文資料...")

            # 先刪除現有的資料 (因為沒有唯一鍵可以用於UPSERT)
            cursor.execute("TRUNCATE TABLE champion_runes RESTART IDENTITY")

            insert_query = """
                INSERT INTO champion_runes 
                (champion_id, primary_path, primary_rune, secondary_path, rune_options, shard_options,
                win_rate, pick_rate, sample_size, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            runes_data = [
                (
                    rune['champion_id'],
                    rune['primary_path'],
                    rune['primary_rune'],
                    rune['secondary_path'],
                    rune['rune_options'],
                    rune['shard_options'],
                    rune['win_rate'],
                    rune['pick_rate'],
                    rune['sample_size'],
                    rune['version']
                )
                for rune in data['runes']
            ]

            execute_batch(cursor, insert_query, runes_data, page_size=100)

        # 插入裝備資料
        if data['builds']:
            logging.info(f"正在插入 {len(data['builds'])} 筆裝備構建資料...")

            # 先刪除現有的資料 (因為沒有唯一鍵可以用於UPSERT)
            cursor.execute("TRUNCATE TABLE champion_builds RESTART IDENTITY")

            insert_query = """
                INSERT INTO champion_builds 
                (champion_id, starting_items, core_items, optional_items,
                win_rate, pick_rate, sample_size, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            builds_data = [
                (
                    build['champion_id'],
                    build['starting_items'],
                    build['core_items'],
                    build['optional_items'],
                    build['win_rate'],
                    build['pick_rate'],
                    build['sample_size'],
                    build['version']
                )
                for build in data['builds']
            ]

            execute_batch(cursor, insert_query, builds_data, page_size=100)

        # 插入對位資料
        if data['matchups']:
            logging.info(f"正在插入 {len(data['matchups'])} 筆對位資料...")

            insert_query = """
                INSERT INTO champion_matchups 
                (champion_id, opponent_id, win_rate, sample_size)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (champion_id, opponent_id) DO UPDATE SET
                win_rate = EXCLUDED.win_rate,
                sample_size = EXCLUDED.sample_size,
                updated_at = CURRENT_TIMESTAMP
            """

            matchups_data = [
                (
                    matchup['champion_id'],
                    matchup['opponent_id'],
                    matchup['win_rate'],
                    matchup['sample_size']
                )
                for matchup in data['matchups']
            ]

            execute_batch(cursor, insert_query, matchups_data, page_size=100)

        # 插入協同資料
        if data['synergies']:
            logging.info(f"正在插入 {len(data['synergies'])} 筆協同資料...")

            insert_query = """
                INSERT INTO team_synergies 
                (champion1_id, champion2_id, win_rate, synergy_score, sample_size)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (champion1_id, champion2_id) DO UPDATE SET
                win_rate = EXCLUDED.win_rate,
                synergy_score = EXCLUDED.synergy_score,
                sample_size = EXCLUDED.sample_size,
                updated_at = CURRENT_TIMESTAMP
            """

            synergies_data = [
                (
                    synergy['champion1_id'],
                    synergy['champion2_id'],
                    synergy['win_rate'],
                    synergy['synergy_score'],
                    synergy['sample_size']
                )
                for synergy in data['synergies']
            ]

            execute_batch(cursor, insert_query, synergies_data, page_size=100)

        conn.commit()
        logging.info("所有資料已成功插入資料庫")
    except Exception as e:
        conn.rollback()
        logging.error(f"插入資料時發生錯誤: {e}")
        raise
    finally:
        cursor.close()


def log_data_update(conn, update_type, version, records_processed, status, start_time, end_time, error_message=None):
    """記錄資料更新日誌"""
    try:
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO data_update_logs
            (update_type, version, records_processed, update_status, start_time, end_time, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            update_type,
            version,
            records_processed,
            status,
            start_time,
            end_time,
            error_message
        ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"記錄更新日誌時發生錯誤: {e}")
    finally:
        cursor.close()


def main():
    """主程式流程"""
    start_time = datetime.now()
    records_processed = 0
    update_status = "failed"
    error_message = None

    try:
        # 設定資料庫連線資訊，實際使用時應從環境變數或設定檔讀取
        db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD', 'aa030566'),
            'database': os.environ.get('DB_NAME', 'aram')
        }

        # 建立資料庫連線
        conn = create_db_connection(db_config)
        logging.info("已連接到資料庫")

        # 載入英雄映射
        champion_dict = load_champion_mapping(conn)
        if not champion_dict:
            raise ValueError("無法載入英雄映射，請確保 champions 表已正確設定")

        # 初始化合併統計資料的容器
        all_processed_stats = {
            'champions': {},
            'runes': defaultdict(list),
            'builds': defaultdict(list),
            'versions': defaultdict(lambda: defaultdict(list)),
            'matchups': defaultdict(lambda: defaultdict(list)),
            'synergies': defaultdict(lambda: defaultdict(list))
        }

        # 分批次讀取和處理資料
        for batch_df in fetch_data_in_batches(conn, 'model_matches', 1000):
            records_processed += len(batch_df)

            # 處理這一批次的資料
            batch_stats = process_match_data_batch(batch_df, champion_dict)

            # 合併到總統計資料中
            for champion_id, stats in batch_stats['champions'].items():
                if champion_id not in all_processed_stats['champions']:
                    all_processed_stats['champions'][champion_id] = stats
                else:
                    for key, value in stats.items():
                        all_processed_stats['champions'][champion_id][key] += value

            for champion_id, rune_list in batch_stats['runes'].items():
                all_processed_stats['runes'][champion_id].extend(rune_list)

            for champion_id, build_list in batch_stats['builds'].items():
                all_processed_stats['builds'][champion_id].extend(build_list)

            for champion_id, versions in batch_stats['versions'].items():
                for version, data_list in versions.items():
                    all_processed_stats['versions'][champion_id][version].extend(data_list)

            for champ1, opponents in batch_stats['matchups'].items():
                for champ2, results in opponents.items():
                    all_processed_stats['matchups'][champ1][champ2].extend(results)

            for champ1, allies in batch_stats['synergies'].items():
                for champ2, results in allies.items():
                    all_processed_stats['synergies'][champ1][champ2].extend(results)

        # 如果沒有處理任何資料，則退出
        if records_processed == 0:
            logging.warning("沒有找到符合條件的ARAM對局資料")
            update_status = "no_data"
        else:
            # 計算最終統計資料
            logging.info("正在計算最終統計資料...")
            final_stats = calculate_final_stats(all_processed_stats)

            # 插入資料到資料庫
            insert_champion_stats(conn, final_stats)
            update_status = "success"

        # 記錄更新
        end_time = datetime.now()
        current_version = "current"
        log_data_update(conn, "aram_stats", current_version, records_processed, update_status, start_time, end_time,
                        error_message)

        logging.info(f"資料處理完成，共處理 {records_processed} 筆記錄，耗時 {end_time - start_time}")

    except Exception as e:
        end_time = datetime.now()
        error_message = str(e)
        logging.error(f"程式執行錯誤: {e}")

        try:
            # 嘗試記錄更新失敗
            if 'conn' in locals() and conn:
                log_data_update(conn, "aram_stats", "current", records_processed, update_status, start_time, end_time,
                                error_message)
        except:
            pass
    finally:
        # 關閉資料庫連線
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    main()