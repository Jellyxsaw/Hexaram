#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合版 ARAM 陣容強度預測模型：
1. 從 PostgreSQL 資料庫讀取比賽 JSON 資料並訓練模型
2. 模型訓練後，將模型與相關資源上傳至 GCS
3. 提供單筆與批量預測功能
"""

import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine
from tensorflow.keras import layers, models, Input
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

# 載入 GCS 套件（請先安裝 google-cloud-storage 套件）
from google.cloud import storage


# -------------------- 資源路徑輔助函式 --------------------
def resource_path(relative_path):
    """
    取得資源檔案的絕對路徑，適用於開發及 PyInstaller 環境
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# -------------------- 英雄名稱正規化類別 --------------------
class ChampionNormalizer:
    def __init__(self):
        self.name_map = {}
        self._load_champion_list()
        self._add_special_cases()

    def _load_champion_list(self):
        # 從 champion_mapping.json 讀取資料
        with open(resource_path("champion_mapping.json"), "r", encoding="utf-8") as f:
            champion_data = json.load(f)
        # 從 chinese_mapping.json 讀取中文對應資料
        with open(resource_path("chinese_mapping.json"), "r", encoding="utf-8") as f:
            chinese_data = json.load(f)

        # 根據 champion_mapping 資料加入映射
        for champion, info in champion_data.items():
            self._add_mapping(champion)
            # 若有中文對應則加入
            if champion in chinese_data:
                self._add_mapping(chinese_data[champion])
            # 將 key (數字) 轉為字串後也加入映射
            self._add_mapping(str(info["key"]))

    def _add_mapping(self, name):
        # 標準化字串處理：轉小寫、移除空格、連字符與單引號
        standardized = name.lower().replace("'", "").replace(" ", "").replace("-", "")
        self.name_map[standardized] = name

    def _add_special_cases(self):
        special_cases = {
            'chogath': "Cho'Gath",
            'ambessa': 'AmbessaMedarda',
            'mf': 'MissFortune',
            'kogmaw': "Kog'Maw",
            'wukong': 'MonkeyKing',
            'drmundo': 'Dr. Mundo'
        }
        self.name_map.update(special_cases)

    def normalize(self, name):
        cleaned = name.strip().lower().replace("'", "").replace(" ", "").replace("-", "")
        if cleaned in self.name_map:
            return self.name_map[cleaned]
        # 嘗試模糊比對：取前三個字母比對
        for k in self.name_map:
            if k.startswith(cleaned[:3]):
                return self.name_map[k]
        raise ValueError(f"無法識別英雄名稱: {name}，可用名稱：{list(self.name_map.values())}")


# -------------------- 資料讀取與處理函數 --------------------
def fetch_data_from_pgsql():
    DATABASE_URI = "postgresql://postgres:aa030566@localhost:5432/aram"
    engine = create_engine(DATABASE_URI)
    query = "SELECT extract_data FROM model_matches WHERE game_duration > 480;"
    df = pd.read_sql(query, engine)
    return df


def process_game_data(df):
    """
    解析 JSON 資料，整理格式：
    每筆樣本為字典：{'champions': sorted([英雄名稱列表]), 'win': 1/0}
    同時收集每位英雄的統計數據
    """
    samples = []
    champion_participant_stats = []
    for index, row in df.iterrows():
        data = row['extract_data']
        if isinstance(data, str):
            try:
                game = json.loads(data)
            except Exception as e:
                print("JSON 解析錯誤:", e)
                continue
        elif isinstance(data, dict):
            game = data
        else:
            print("未知資料格式:", type(data))
            continue

        for team_id in ['100', '200']:
            team_info = game.get('teams', {}).get(team_id, {})
            team_win = team_info.get('win', False)
            champions = []
            for participant in game.get('participants', []):
                if str(participant.get('teamId')) == team_id:
                    champion_name = participant.get('championName')
                    if not champion_name:
                        continue
                    champions.append(champion_name)
                    champion_participant_stats.append({
                        'championName': champion_name,
                        'kda': participant.get('kda', 0),
                        'kills': participant.get('kills', 0),
                        'deaths': participant.get('deaths', 0),
                        'assists': participant.get('assists', 0),
                        'gold_spent': participant.get('gold_spent', 0),
                        'gold_earned': participant.get('gold_earned', 0),
                        'damage_per_minute': participant.get('damage_per_minute', 0),
                        'total_damage_taken': participant.get('total_damage_taken', 0),
                        'total_heals_on_teammates': participant.get('total_heals_on_teammates', 0),
                        'damage_self_mitigated': participant.get('damage_self_mitigated', 0),
                        'time_ccing_others': participant.get('time_ccing_others', 0),
                        'total_damage_shielded_on_teammates': participant.get('total_damage_shielded_on_teammates', 0)
                    })
            if len(champions) == 5:
                samples.append({
                    'champions': sorted(champions),  # 保持順序一致
                    'win': 1 if team_win else 0
                })
    return samples, champion_participant_stats


def compute_champion_stats(champion_stats_list):
    """
    計算各英雄統計數據的歷史平均值
    採用分批處理方式以減少記憶體使用
    """
    if not champion_stats_list:
        raise ValueError("沒有成功解析到任何英雄數據")

    print(f"正在處理 {len(champion_stats_list)} 筆英雄數據...")

    # 定義要處理的特徵欄位
    feature_columns = [
        'kda', 'kills', 'deaths', 'assists',
        'gold_spent', 'gold_earned', 'damage_per_minute',
        'total_damage_taken', 'total_heals_on_teammates',
        'damage_self_mitigated', 'time_ccing_others',
        'total_damage_shielded_on_teammates'
    ]

    # 初始化結果字典
    champion_stats_aggregated = {}
    champion_counts = {}

    # 分批處理數據
    batch_size = 100000  # 每批次處理的記錄數量
    total_batches = (len(champion_stats_list) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(champion_stats_list))

        batch = champion_stats_list[start_idx:end_idx]
        print(f"處理批次 {batch_idx + 1}/{total_batches}，共 {len(batch)} 筆記錄")

        # 批次處理
        for record in batch:
            champ_name = record.get('championName')
            if not champ_name:
                continue

            # 初始化該英雄的統計數據
            if champ_name not in champion_stats_aggregated:
                champion_stats_aggregated[champ_name] = {feature: 0.0 for feature in feature_columns}
                champion_counts[champ_name] = 0

            # 累加每個特徵的值
            for feature in feature_columns:
                value = record.get(feature, 0)
                if value is not None:  # 確保值不是 None
                    champion_stats_aggregated[champ_name][feature] += float(value)

            # 增加該英雄的計數
            champion_counts[champ_name] += 1

    # 計算平均值
    champion_stats_dict = {}
    for champ_name, stats in champion_stats_aggregated.items():
        count = champion_counts[champ_name]
        if count > 0:
            feature_values = []
            for feature in feature_columns:
                # 計算平均值
                feature_values.append(stats[feature] / count)
            champion_stats_dict[champ_name] = np.array(feature_values, dtype=np.float32)

    print(f"成功計算 {len(champion_stats_dict)} 個英雄的統計數據")

    return champion_stats_dict, feature_columns


def prepare_dataset_v2(samples, champion_stats_dict, feature_columns):
    """
    為優化版模型準備資料：
    - X_ids：英雄 ID 陣列，shape=(樣本數, 5)
    - X_stats：英雄統計數據矩陣，shape=(樣本數, 5, 特徵數)
      ※此處不取平均，而是保留原始 5 位英雄的數據
    - y：勝敗標籤
    並對英雄統計數據進行正規化（先展平再還原）
    """
    champion_set = set()
    for sample in samples:
        champion_set.update(sample['champions'])
    champion_list = sorted(list(champion_set))
    champion_to_idx = {champ: idx for idx, champ in enumerate(champion_list)}

    X_ids = []
    X_stats = []
    y = []
    for sample in samples:
        ids = [champion_to_idx[champ] for champ in sample['champions']]
        X_ids.append(ids)
        stats = []
        for champ in sample['champions']:
            if champ in champion_stats_dict:
                stats.append(champion_stats_dict[champ])
            else:
                stats.append(np.zeros(len(feature_columns), dtype=np.float32))
        X_stats.append(stats)
        y.append(sample['win'])
    X_ids = np.array(X_ids, dtype=np.int32)
    X_stats = np.array(X_stats, dtype=np.float32)  # shape: (樣本數, 5, 特徵數)
    y = np.array(y, dtype=np.float32)

    # 對英雄統計數據展平後正規化，再還原成原矩陣形狀
    num_samples, num_champs, num_features = X_stats.shape
    X_stats_flat = X_stats.reshape(-1, num_features)
    scaler = StandardScaler()
    X_stats_flat = scaler.fit_transform(X_stats_flat)
    X_stats = X_stats_flat.reshape(num_samples, num_champs, num_features)

    return X_ids, X_stats, y, champion_to_idx, scaler


# -------------------- 建立進階神經網路模型（優化版） --------------------
def build_advanced_model_v2(num_champions, num_stats_features, embedding_dim=16):
    # 分支 1：英雄 ID 輸入，利用 Embedding 與 MultiHeadAttention 捕捉英雄間關聯
    input_ids = Input(shape=(5,), name="champion_ids", dtype=tf.int32)
    embeddings = layers.Embedding(input_dim=num_champions, output_dim=embedding_dim)(input_ids)
    attention_output = layers.MultiHeadAttention(num_heads=2, key_dim=embedding_dim)(embeddings, embeddings)
    x1 = layers.Flatten()(attention_output)
    x1 = layers.Dense(32, activation='relu')(x1)
    x1 = layers.BatchNormalization()(x1)

    # 分支 2：英雄統計數據輸入，形狀 (5, num_stats_features)
    input_stats = Input(shape=(5, num_stats_features), name="champion_stats")
    x2 = layers.Flatten()(input_stats)
    x2 = layers.Dense(64, activation='relu')(x2)
    x2 = layers.BatchNormalization()(x2)
    x2 = layers.Dropout(0.3)(x2)

    # 融合兩個分支
    x = layers.concatenate([x1, x2])

    # 殘差區塊
    x_res = layers.Dense(64, activation='relu')(x)
    x = layers.Dense(64, activation='relu')(x)
    x = layers.add([x, x_res])
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)

    x = layers.Dense(32, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)

    # 輸出層：勝率預測（0~1之間）
    output = layers.Dense(1, activation='sigmoid',
                          bias_initializer=tf.keras.initializers.Constant(0.0))(x)

    model = models.Model(inputs=[input_ids, input_stats], outputs=output)
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])
    return model


# -------------------- 模型訓練與儲存（優化版） --------------------
def train_advanced_model_v2():
    print("從資料庫讀取資料...")
    df = fetch_data_from_pgsql()

    print("解析並處理遊戲資料...")
    samples, champion_participant_stats = process_game_data(df)
    print(f"成功解析樣本數: {len(samples)}，收集英雄數據筆數: {len(champion_participant_stats)}")

    print("計算各英雄歷史平均統計數據...")
    champion_stats_dict, feature_columns = compute_champion_stats(champion_participant_stats)

    print("準備訓練資料並進行正規化...")
    X_ids, X_stats, y, champion_to_idx, scaler = prepare_dataset_v2(samples, champion_stats_dict, feature_columns)

    X_ids_train, X_ids_test, X_stats_train, X_stats_test, y_train, y_test = train_test_split(
        X_ids, X_stats, y, test_size=0.2, random_state=42
    )

    print("建立進階神經網路模型（優化版）...")
    num_champions = len(champion_to_idx)
    num_stats_features = len(feature_columns)
    model = build_advanced_model_v2(num_champions, num_stats_features, embedding_dim=16)
    model.summary()

    # 設定回呼函數
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    checkpoint = ModelCheckpoint("advanced_aram_model_v2.h5", monitor='val_loss', save_best_only=True, verbose=1)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1, min_lr=1e-6)

    print("開始訓練模型...")
    model.fit(
        [X_ids_train, X_stats_train], y_train,
        epochs=100,
        batch_size=32,
        validation_data=([X_ids_test, X_stats_test], y_test),
        callbacks=[early_stop, checkpoint, reduce_lr]
    )

    # 儲存模型及輔助資料
    model.save("advanced_aram_model_v2.h5")
    with open("champion_to_idx_v2.pkl", "wb") as f:
        pickle.dump(champion_to_idx, f)
    with open("scaler_v2.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open("champion_stats_dict_v2.pkl", "wb") as f:
        pickle.dump(champion_stats_dict, f)
    print("進階模型與輔助資料已儲存！")


# -------------------- GCS 下載相關函式 --------------------
def download_blob(bucket_name, source_blob_name, destination_file_name):
    """
    從指定的 GCS Bucket 下載檔案
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    if not blob.exists():
        raise FileNotFoundError(f"GCS 中不存在檔案: {bucket_name}/{source_blob_name}")

    blob.download_to_filename(destination_file_name)
    print(f"檔案 {bucket_name}/{source_blob_name} 已下載到 {destination_file_name}")


def download_resource_if_needed(local_path, bucket_name, gcs_blob_path):
    """
    檢查本機是否有檔案，若無則從 GCS 下載
    """
    if not os.path.exists(local_path):
        print(f"{local_path} 不存在，開始從 GCS 下載...")
        download_blob(bucket_name, gcs_blob_path, local_path)
    else:
        print(f"{local_path} 已存在。")


# -------------------- GCS 上傳相關函式 --------------------
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """
    上傳本地檔案到指定的 GCS Bucket 中
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    print(f"檔案 {source_file_name} 已成功上傳到 {bucket_name}/{destination_blob_name}。")


def upload_all_resources(bucket_name, gcs_prefix=""):
    """
    上傳模型與所有相關資源檔案到 GCS
    """
    resources = [
        "advanced_aram_model_v2.h5",
        "champion_to_idx_v2.pkl",
        "scaler_v2.pkl",
        "champion_stats_dict_v2.pkl",
        "champion_mapping.json",
        "chinese_mapping.json"
    ]
    for local_file in resources:
        local_path = resource_path(local_file)
        destination_path = os.path.join(gcs_prefix, local_file)
        if not os.path.exists(local_path):
            print(f"本機檔案 {local_path} 不存在，無法上傳。")
        else:
            upload_blob(bucket_name, local_path, destination_path)


# -------------------- ARAM 勝率預測器類別 --------------------
class ARAMPredictor:
    def __init__(self):
        """
        下載資源（若本機不存在則從 GCS 下載），並載入模型與相關資源
        """
        # 請設定你的 GCS Bucket 名稱
        self.bucket_name = "hexaram"

        # 定義本機檔案名稱與 GCS 上的對應檔案路徑
        self.model_file = "advanced_aram_model_v2.h5"
        self.mapping_file = "champion_to_idx_v2.pkl"
        self.scaler_file = "scaler_v2.pkl"
        self.champion_stats_file = "champion_stats_dict_v2.pkl"

        # 下載資源（注意：第三個參數要與檔案名稱一致）
        download_resource_if_needed(resource_path(self.model_file), self.bucket_name, self.model_file)
        download_resource_if_needed(resource_path(self.mapping_file), self.bucket_name, self.mapping_file)
        download_resource_if_needed(resource_path(self.scaler_file), self.bucket_name, self.scaler_file)
        download_resource_if_needed(resource_path(self.champion_stats_file), self.bucket_name, self.champion_stats_file)

        # 取得正確的本機路徑
        model_full_path = resource_path(self.model_file)
        mapping_full_path = resource_path(self.mapping_file)
        scaler_full_path = resource_path(self.scaler_file)
        champion_stats_full_path = resource_path(self.champion_stats_file)

        # 檢查檔案是否存在
        for path in [model_full_path, mapping_full_path, scaler_full_path, champion_stats_full_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"檔案 {path} 不存在，請確認 GCS 上有對應檔案並檢查下載權限。")

        # 載入模型與資源
        self.model = tf.keras.models.load_model(model_full_path)
        with open(mapping_full_path, "rb") as f:
            self.champion_to_idx = pickle.load(f)
        with open(scaler_full_path, "rb") as f:
            self.scaler = pickle.load(f)
        with open(champion_stats_full_path, "rb") as f:
            self.champion_stats_dict = pickle.load(f)

        # 建立名稱正規化器
        self.normalizer = ChampionNormalizer()
        # 建立正規化後名稱對應到英雄索引的字典
        self.norm_to_idx = {}
        for champ, idx in self.champion_to_idx.items():
            norm_name = self.normalizer.normalize(champ)
            self.norm_to_idx[norm_name] = idx

    def predict_team_strength(self, champion_names):
        """
        單筆預測：
        輸入包含 5 位英雄名稱的列表，先正規化後查找 ID 與統計數據，
        再透過模型預測勝率
        """
        if len(champion_names) != 5:
            raise ValueError("請輸入五位英雄的名稱")
        norm_names = [self.normalizer.normalize(name) for name in champion_names]
        comp_sorted = sorted(norm_names)
        try:
            ids = [self.norm_to_idx[champ] for champ in comp_sorted]
        except KeyError as e:
            raise ValueError(f"未知的英雄名稱: {e}")
        X_ids = np.array([ids], dtype=np.int32)
        stats = []
        for champ in comp_sorted:
            if champ in self.champion_stats_dict:
                stats.append(self.champion_stats_dict[champ])
            else:
                stats.append(np.zeros(len(next(iter(self.champion_stats_dict.values()))), dtype=np.float32))
        stats = np.array(stats, dtype=np.float32)
        stats = self.scaler.transform(stats)
        X_stats = np.expand_dims(stats, axis=0)
        prediction = self.model.predict([X_ids, X_stats])
        score = prediction[0][0]
        return score

    def batch_predict(self, compositions):
        """
        批量預測：
        輸入多組陣容（每組包含 5 位英雄名稱），返回預測結果列表
        """
        X_ids = []
        X_stats = []
        for comp in compositions:
            if len(comp) != 5:
                raise ValueError("每個陣容必須包含五位英雄")
            norm_names = [self.normalizer.normalize(name) for name in comp]
            comp_sorted = sorted(norm_names)
            try:
                ids = [self.norm_to_idx[champ] for champ in comp_sorted]
            except KeyError as e:
                raise ValueError(f"未知的英雄名稱: {e}")
            X_ids.append(ids)
            stats = []
            for champ in comp_sorted:
                if champ in self.champion_stats_dict:
                    stats.append(self.champion_stats_dict[champ])
                else:
                    stats.append(np.zeros(len(next(iter(self.champion_stats_dict.values()))), dtype=np.float32))
            X_stats.append(stats)
        X_ids = np.array(X_ids, dtype=np.int32)
        X_stats = np.array(X_stats, dtype=np.float32)
        batch_size, num_champs, num_features = X_stats.shape
        X_stats_flat = X_stats.reshape(-1, num_features)
        X_stats_flat = self.scaler.transform(X_stats_flat)
        X_stats = X_stats_flat.reshape(batch_size, num_champs, num_features)
        predictions = self.model.predict([X_ids, X_stats])
        results = predictions[:, 0].tolist()
        return results


# -------------------- 主程式 --------------------
if __name__ == "__main__":
    # 先訓練模型
    train_advanced_model_v2()

    # 上傳所有資源至 GCS（請確認 BUCKET_NAME 是否正確）
    BUCKET_NAME = "hexaram"
    upload_all_resources(BUCKET_NAME)

    # 建立 ARAMPredictor 並進行單筆預測範例
    predictor = ARAMPredictor()
    example_team = ["Ahri", "Lee Sin", "Garen", "Lux", "Ezreal"]
    try:
        win_rate = predictor.predict_team_strength(example_team)
        print(f"預測勝率: {win_rate:.2%}")
    except ValueError as e:
        print(f"預測錯誤: {e}")
