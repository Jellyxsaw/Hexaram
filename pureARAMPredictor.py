# 新增 resource_path 函數，處理 PyInstaller 資源路徑問題
import json
import os
import pickle
import sys

import numpy as np
import tensorflow as tf


# -------------------- 英雄名稱正規化類別 --------------------
class ChampionNormalizer:
    def __init__(self):
        self.name_map = {}
        self._load_champion_list()
        self._add_special_cases()

    def _load_champion_list(self):
        # 從 champion_mapping.json 讀取資料
        with open("champion_mapping.json", "r", encoding="utf-8") as f:
            champion_data = json.load(f)
        # 從 chinese_mapping.json 讀取中文對應資料
        with open("chinese_mapping.json", "r", encoding="utf-8") as f:
            chinese_data = json.load(f)

        # 依據 champion_mapping 的資料來加入映射
        for champion, info in champion_data.items():
            # 加入英文名稱
            self._add_mapping(champion)
            # 若有對應的中文名稱則加入
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
        self.name_map.update({k: v for k, v in special_cases.items()})

    def normalize(self, name):
        cleaned = name.strip().lower().replace("'", "").replace(" ", "").replace("-", "")
        if cleaned in self.name_map:
            return self.name_map[cleaned]
        # 嘗試模糊匹配：取前三個字母比對
        for k in self.name_map:
            if k.startswith(cleaned[:3]):
                return self.name_map[k]
        raise ValueError(f"無法識別英雄名稱: {name}，可用名稱：{list(self.name_map.values())}")


def resource_path(relative_path):
    """取得資源檔案的絕對路徑，適用於開發及 PyInstaller環境"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ARAMPredictor:
    def __init__(self, model_path="advanced_aram_model_v2.h5",
                 mapping_path="champion_to_idx_v2.pkl",
                 scaler_path="scaler_v2.pkl",
                 champion_stats_path="champion_stats_dict_v2.pkl"):
        # 使用 resource_path 取得正確路徑
        model_full_path = resource_path(model_path)
        mapping_full_path = resource_path(mapping_path)
        scaler_full_path = resource_path(scaler_path)
        champion_stats_full_path = resource_path(champion_stats_path)

        for path in [model_full_path, mapping_full_path, scaler_full_path, champion_stats_full_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"檔案 {path} 不存在，請先運行 train_advanced_model_v2() 以生成所需檔案。")
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
        透過模型預測勝率
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
        stats = np.array(stats, dtype=np.float32)  # shape: (5, 特徵數)
        # 對每位英雄的統計數據進行正規化
        stats = self.scaler.transform(stats)
        X_stats = np.expand_dims(stats, axis=0)  # shape: (1, 5, 特徵數)
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
        X_stats = np.array(X_stats, dtype=np.float32)  # shape: (批次數, 5, 特徵數)
        # 將統計數據展平後進行正規化，再還原原矩陣形狀
        batch_size, num_champs, num_features = X_stats.shape
        X_stats_flat = X_stats.reshape(-1, num_features)
        X_stats_flat = self.scaler.transform(X_stats_flat)
        X_stats = X_stats_flat.reshape(batch_size, num_champs, num_features)
        predictions = self.model.predict([X_ids, X_stats])
        results = predictions[:, 0].tolist()

        return results