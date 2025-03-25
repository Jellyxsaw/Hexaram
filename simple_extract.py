import json
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from collections import defaultdict
import logging
import os
from tqdm import tqdm
from difflib import get_close_matches
import multiprocessing
from functools import partial

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定義進程數量 (根據CPU核心數量自動設定或手動指定)
# NUM_PROCESSES = max(1, multiprocessing.cpu_count() - 1)  # 自動設定為CPU核心數-1
NUM_PROCESSES = 8  # 或者直接指定數量


# 解決無法序列化 lambda 函數的問題
def dict_factory():
    """創建初始化的指標記錄"""
    return {
        'total_damage': 0,
        'total_damage_taken': 0,
        'total_healing': 0,
        'total_damage_mitigated': 0,
        'total_time_ccing': 0,
        'total_game_duration': 0,
        'count': 0
    }


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
        return row['match_data']
    except KeyError as e:
        logging.error(f"資料中找不到 match_data 欄位, row_id: {row.get('id', 'unknown')}")
        return None


def fetch_data_in_batches(conn, table_name, batch_size=5000):
    """分批次從資料庫讀取資料"""
    cursor = conn.cursor()
    offset = 0

    # 先獲取總記錄數
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE game_mode = 'ARAM'")
    total_rows = cursor.fetchone()[0]

    # 設定進度條
    with tqdm(total=total_rows, desc=f"讀取 {table_name} 資料") as pbar:
        while True:
            cursor.execute(
                f"SELECT id, match_id, game_mode, game_type, game_version, match_data "
                f"FROM {table_name} "
                f"WHERE game_mode = 'ARAM' "  # 只處理 ARAM 對局
                f"ORDER BY id "
                f"LIMIT {batch_size} OFFSET {offset}"
            )

            rows = cursor.fetchall()
            if not rows:
                break

            # 創建 DataFrame
            columns = ['id', 'match_id', 'game_mode', 'game_type', 'game_version', 'match_data']
            df = pd.DataFrame(rows, columns=columns)

            # 更新進度條
            pbar.update(len(rows))

            # 提供批次資料
            yield df

            # 更新偏移量
            offset += batch_size

    cursor.close()


def normalize_champion_name(champion_name):
    """標準化英雄名稱：轉換為小寫並移除特殊字符"""
    if not champion_name:
        return None
    # 轉換為小寫並移除可能的單引號或其他特殊字符
    return champion_name.lower().replace("'", "").replace(" ", "").strip()


def find_champion_in_champion_map(champion_name, champion_map):
    """在映射表中查找英雄名稱和對應 key"""
    if not champion_name:
        return None, None

    # 創建標準化的字典和鍵的對照表
    normalized_dict = {}
    for name, info in champion_map.items():
        normalized_key = normalize_champion_name(name)
        normalized_dict[normalized_key] = (name, info['key'])

    # 標準化輸入的英雄名稱
    normalized_name = normalize_champion_name(champion_name)

    # 嘗試直接查找
    if normalized_name in normalized_dict:
        return normalized_dict[normalized_name]

    # 嘗試模糊匹配
    possible_matches = get_close_matches(normalized_name, normalized_dict.keys(), n=1, cutoff=0.6)
    if possible_matches:
        closest_match = possible_matches[0]
        original_name, key = normalized_dict[closest_match]
        return original_name, key

    # 沒有找到匹配
    return None, None


def process_match_data_batch(batch_df, champion_map):
    """處理一批次的比賽資料，計算指標"""
    # 初始化指標收集器，使用元組 (champion_name, champion_key) 作為鍵
    champion_metrics = {}

    for _, row in batch_df.iterrows():
        match_data = extract_match_data(row)
        if not match_data:
            continue

        # 獲取基本比賽資訊
        try:
            info = match_data.get('info', {})
            game_duration = info.get('gameDuration', 0)

            # 只處理有效的比賽 (超過5分鐘)
            if game_duration < 300:
                continue

            # 轉換遊戲時長為分鐘
            game_duration_minutes = game_duration / 60

            # 處理每名參與者的詳細數據
            participants = info.get('participants', [])
            for participant in participants:
                # 提取基本資訊
                champion_name = participant.get('championName')
                champion_id = participant.get('championId')  # 這是數字ID

                # 確保championName有效
                if not champion_name:
                    continue

                # 使用查找函數找到標準化的英雄名稱和key
                std_champion_name, champion_key = find_champion_in_champion_map(champion_name, champion_map)
                if not std_champion_name:
                    # 如果無法找到映射但有原始championId，可以使用championId作為key
                    if champion_id:
                        # 在這種情況下，我們使用原始的champion_name而不是None
                        std_champion_name = champion_name
                        champion_key = champion_id
                    else:
                        continue

                # 收集指標
                total_damage = participant.get('totalDamageDealtToChampions', 0)
                total_damage_taken = participant.get('totalDamageTaken', 0)

                # 治癒統計 (自身和給隊友的)
                total_heal = participant.get('totalHeal', 0)
                healing_done = participant.get('totalHealsOnTeammates', 0)
                total_healing = total_heal + healing_done

                # 自我減傷
                damage_mitigated = participant.get('damageSelfMitigated', 0)

                # 控場時間 (秒)
                time_ccing = participant.get('timeCCingOthers', 0)

                # 更新此英雄的指標，使用 (name, key) 的元組作為鍵
                champion_tuple = (std_champion_name, champion_key)

                # 如果這個英雄第一次出現在字典中，初始化它
                if champion_tuple not in champion_metrics:
                    champion_metrics[champion_tuple] = dict_factory()

                # 更新指標
                champion_metrics[champion_tuple]['total_damage'] += total_damage
                champion_metrics[champion_tuple]['total_damage_taken'] += total_damage_taken
                champion_metrics[champion_tuple]['total_healing'] += total_healing
                champion_metrics[champion_tuple]['total_damage_mitigated'] += damage_mitigated
                champion_metrics[champion_tuple]['total_time_ccing'] += time_ccing
                champion_metrics[champion_tuple]['total_game_duration'] += game_duration_minutes
                champion_metrics[champion_tuple]['count'] += 1

        except Exception as e:
            logging.error(f"處理比賽資料錯誤: {e}, match_id: {row.get('match_id', 'unknown')}")
            continue

    return champion_metrics


def worker_process(batch_df, champion_map):
    """
    工作進程函數，處理一個數據批次
    """
    try:
        # 處理批次數據
        return process_match_data_batch(batch_df, champion_map)
    except Exception as e:
        logging.error(f"工作進程處理錯誤: {e}")
        return None


def merge_metrics(metrics_list):
    """合併多個進程返回的指標數據"""
    merged_metrics = {}

    for metrics in metrics_list:
        if not metrics:
            continue

        for champion_tuple, data in metrics.items():
            if champion_tuple not in merged_metrics:
                merged_metrics[champion_tuple] = dict_factory()

            for key, value in data.items():
                merged_metrics[champion_tuple][key] += value

    return merged_metrics


def calculate_final_metrics(champion_metrics):
    """計算最終指標"""
    final_metrics = []

    for (champion_name, champion_key), metrics in champion_metrics.items():
        if metrics['count'] == 0:
            continue

        avg_game_duration = metrics['total_game_duration'] / metrics['count']

        # 計算分均指標
        final_metrics.append({
            'champion_name': champion_name,
            'champion_key': champion_key,
            'avg_damage_per_min': metrics['total_damage'] / metrics['total_game_duration'],
            'avg_damage_taken_per_min': metrics['total_damage_taken'] / metrics['total_game_duration'],
            'avg_healing_per_min': metrics['total_healing'] / metrics['total_game_duration'],
            'avg_damage_mitigated_per_min': metrics['total_damage_mitigated'] / metrics['total_game_duration'],
            'avg_time_ccing_per_min': metrics['total_time_ccing'] / metrics['total_game_duration'],
            'sample_size': metrics['count']
        })

    return final_metrics


def insert_champion_metrics(conn, metrics_data):
    """插入英雄指標資料到資料庫"""
    try:
        cursor = conn.cursor()

        if not metrics_data:
            logging.warning("沒有指標資料可插入")
            return

        logging.info(f"正在插入 {len(metrics_data)} 筆英雄指標資料...")

        insert_query = """
            INSERT INTO champion_metrics
            (champion_name, champion_key, avg_damage_per_min, avg_damage_taken_per_min, avg_healing_per_min, 
            avg_damage_mitigated_per_min, avg_time_ccing_per_min, sample_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (champion_name) DO UPDATE SET
            champion_key = EXCLUDED.champion_key,
            avg_damage_per_min = EXCLUDED.avg_damage_per_min,
            avg_damage_taken_per_min = EXCLUDED.avg_damage_taken_per_min,
            avg_healing_per_min = EXCLUDED.avg_healing_per_min,
            avg_damage_mitigated_per_min = EXCLUDED.avg_damage_mitigated_per_min,
            avg_time_ccing_per_min = EXCLUDED.avg_time_ccing_per_min,
            sample_size = EXCLUDED.sample_size,
            updated_at = CURRENT_TIMESTAMP
        """

        metrics_values = [
            (
                metric['champion_name'],
                metric['champion_key'],
                round(metric['avg_damage_per_min'], 2),
                round(metric['avg_damage_taken_per_min'], 2),
                round(metric['avg_healing_per_min'], 2),
                round(metric['avg_damage_mitigated_per_min'], 2),
                round(metric['avg_time_ccing_per_min'], 2),
                metric['sample_size']
            )
            for metric in metrics_data
        ]

        execute_batch(cursor, insert_query, metrics_values, page_size=100)
        conn.commit()

        logging.info("英雄指標資料已成功插入資料庫")
    except Exception as e:
        conn.rollback()
        logging.error(f"插入資料時發生錯誤: {e}")
        raise
    finally:
        cursor.close()


def load_champion_mapping(conn):
    """從資料庫讀取英雄映射，返回 {champion_name: {'key': key}} 形式"""
    cursor = conn.cursor()
    champion_map = {}

    try:
        # 從champions表格獲取英雄映射
        cursor.execute("SELECT champion_id, champion_name, champion_tw_name, key FROM champions")
        champions = cursor.fetchall()

        for champion_id, champion_name, champion_tw_name, key in champions:
            # 將英文名稱作為鍵，並儲存key值
            champion_map[champion_id] = {'key': key, 'tw_name': champion_tw_name}

            # 也可以為中文名稱建立映射
            if champion_tw_name:
                champion_map[champion_tw_name] = {'key': key, 'original_name': champion_id}

        logging.info(f"已載入 {len(champions)} 個英雄的映射關係")
        return champion_map
    except Exception as e:
        logging.error(f"讀取英雄映射時發生錯誤: {e}")
        return {}
    finally:
        cursor.close()


def log_data_update(conn, update_type, records_processed, status, start_time, end_time, error_message=None):
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
            'current',
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
    from datetime import datetime

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
        champion_map = load_champion_mapping(conn)
        if not champion_map:
            raise ValueError("無法載入英雄映射，請確保 champions 表已正確設定")

        # 初始化多進程池
        pool = multiprocessing.Pool(processes=NUM_PROCESSES)
        logging.info(f"已初始化 {NUM_PROCESSES} 個工作進程")

        # 用於收集所有批次處理結果的列表
        batch_metrics_list = []

        # 分批次讀取資料
        batch_size = 5000  # 每批次處理的記錄數量

        # 檢索總記錄數
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM model_matches WHERE game_mode = 'ARAM'")
        total_records = cursor.fetchone()[0]
        cursor.close()

        # 設定進度條
        progress_bar = tqdm(total=total_records, desc="處理 ARAM 對局資料")

        # 異步批次讀取和處理
        batch_results = []

        # 開始處理數據
        for batch_df in fetch_data_in_batches(conn, 'model_matches', batch_size):
            records_processed += len(batch_df)

            # 非阻塞方式提交任務給進程池
            result = pool.apply_async(worker_process, args=(batch_df, champion_map))
            batch_results.append(result)

            # 檢查已完成的結果
            completed_results = []
            for i, result in enumerate(batch_results):
                if result.ready():
                    try:
                        metric = result.get()
                        if metric:
                            batch_metrics_list.append(metric)
                        completed_results.append(i)
                    except Exception as e:
                        logging.error(f"獲取進程結果時發生錯誤: {e}")

            # 從列表中移除已完成的結果 (從後向前移除，以避免索引問題)
            for i in sorted(completed_results, reverse=True):
                batch_results.pop(i)

            # 更新進度條 (實際進度是根據已處理的記錄數)
            progress_bar.update(len(batch_df))

        # 等待所有剩餘任務完成
        logging.info("等待所有進程完成...")
        pool.close()
        pool.join()

        # 處理所有剩餘結果
        for result in batch_results:
            try:
                metric = result.get()
                if metric:
                    batch_metrics_list.append(metric)
            except Exception as e:
                logging.error(f"獲取進程結果時發生錯誤: {e}")

        # 關閉進度條
        progress_bar.close()

        # 如果沒有處理任何資料，則退出
        if records_processed == 0:
            logging.warning("沒有找到符合條件的ARAM對局資料")
            update_status = "no_data"
        else:
            # 合併所有批次的指標
            logging.info("正在合併所有批次指標...")
            all_champion_metrics = merge_metrics(batch_metrics_list)

            # 計算最終指標
            logging.info("正在計算最終指標...")
            final_metrics = calculate_final_metrics(all_champion_metrics)

            # 插入資料到資料庫
            insert_champion_metrics(conn, final_metrics)
            update_status = "success"

        # 記錄更新
        end_time = datetime.now()
        log_data_update(conn, "aram_metrics", records_processed, update_status, start_time, end_time, error_message)

        logging.info(f"資料處理完成，共處理 {records_processed} 筆記錄，耗時 {end_time - start_time}")

    except Exception as e:
        end_time = datetime.now()
        error_message = str(e)
        logging.error(f"程式執行錯誤: {e}")

        try:
            # 嘗試記錄更新失敗
            if 'conn' in locals() and conn:
                log_data_update(conn, "aram_metrics", records_processed, update_status, start_time, end_time,
                                error_message)
        except:
            pass
    finally:
        # 關閉資料庫連線
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    # 啟用多進程支援 (Windows平台需要)
    multiprocessing.freeze_support()
    main()