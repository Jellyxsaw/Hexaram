import base64
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox
from functools import lru_cache

import requests
import urllib3
import yaml


def get_resource_path(relative_path):
    # 如果被打包，sys._MEIPASS 會指向臨時目錄
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# 載入 JSON 設定檔
config_path = get_resource_path("config.json")
try:
    with open(config_path, "r", encoding="utf-8") as f:
        JSON_CONFIG = json.load(f)
except Exception as e:
    messagebox.showerror("設定檔錯誤", f"無法讀取設定檔：{config_path}\n錯誤：{e}\n\n將使用默認設定。")
    JSON_CONFIG = {
        "lockfile_path": "C:/Riot Games/League of Legends/lockfile"
    }

LOCKFILE_PATH = JSON_CONFIG.get("lockfile_path")
if not LOCKFILE_PATH:
    messagebox.showerror("設定檔錯誤", "設定檔中缺少 lockfile_path 設定。\n\n將使用默認路徑：C:/Riot Games/League of Legends/lockfile")
    LOCKFILE_PATH = "C:/Riot Games/League of Legends/lockfile"


class DataFetcher:
    def __init__(self, lockfile_path=LOCKFILE_PATH):
        self.lockfile_path = lockfile_path
        self.id_mapping, self.tw_mapping = get_champion_mappings()
        # 建立從英文名稱到 key 的反向映射，用於取得圖片
        self.name_to_key = {v: k for k, v in self.id_mapping.items()}

    def fetch_live_data(self):
        try:
            lock_info = self.read_lockfile()
            session = self.get_champ_select_session(lock_info)
            return self.parse_session_data(session) if session else None
        except Exception as e:
            # messagebox.showerror("數據獲取錯誤", f"無法獲取即時數據\n\n錯誤：{e}\n\n請確認：\n1. 英雄聯盟是否正在運行\n2. 是否正在進行英雄選擇\n3. Lockfile 路徑是否正確 目前的lockfile路徑為{self.lockfile_path}")
            return None

    def read_lockfile(self):
        try:
            with open(self.lockfile_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            parts = content.split(':')
            return {
                'port': parts[2],
                'password': parts[3],
                'protocol': parts[4]
            }
        except Exception as e:
            raise Exception(f"Lockfile讀取失敗: {e}")

    def get_champ_select_session(self, lock_info):
        urllib3.disable_warnings()
        url = f"{lock_info['protocol']}://127.0.0.1:{lock_info['port']}/lol-champ-select/v1/session"
        auth_str = f"riot:{lock_info['password']}"
        headers = {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=3)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            messagebox.showerror("API 請求錯誤",
                                 f"無法連接到英雄聯盟客戶端 API\n\n錯誤：{e}\n\n請確認：\n1. 英雄聯盟是否正在運行\n2. 是否正在進行英雄選擇\n3. 客戶端是否正常運作")
            raise Exception(f"API請求失敗: {e}")

    def parse_session_data(self, session):
        # 解析已選英雄
        selected_ids = [
            player['championId']
            for player in session.get('myTeam', [])
            if player.get('championId', 0) > 0
        ]
        # 解析候選池
        bench_ids = [
            champ['championId']
            for champ in session.get('benchChampions', [])
            if champ.get('championId', 0) > 0
        ]
        selected_heroes = [id_to_name(cid, self.id_mapping) for cid in selected_ids]
        candidate_pool = [id_to_name(cid, self.id_mapping) for cid in bench_ids]
        all_pool = selected_heroes + candidate_pool
        return {
            'selected': selected_heroes,
            'candidates': candidate_pool,
            'all_pool': all_pool
        }

    def load_local_data(self):
        local_data_path = get_resource_path('local_session.json')
        try:
            with open(local_data_path, 'r', encoding='utf-8') as f:
                return self.parse_session_data(json.load(f))
        except Exception as e:
            print(f"本地數據加載失敗: {e}")
            return None


# ------------------ 工具函數 ------------------
@lru_cache(maxsize=1)
def get_champion_mappings():
    # 優先檢查本地 JSON 文件
    champ_mapping_path = get_resource_path('champion_mapping.json')
    chinese_mapping_path = get_resource_path('chinese_mapping.json')

    if os.path.exists(champ_mapping_path) and os.path.exists(chinese_mapping_path):
        try:
            with open(champ_mapping_path, 'r', encoding='utf-8') as f:
                champ_data = json.load(f)
                id_to_en = {str(v['key']): k for k, v in champ_data.items()}

            with open(chinese_mapping_path, 'r', encoding='utf-8') as f:
                en_to_tw = json.load(f)

            return id_to_en, en_to_tw
        except Exception as e:
            print(f"本地JSON文件讀取失敗: {e}")
            return {}, {}
    return {}, {}


def id_to_name(champion_id, id_mapping):
    return id_mapping.get(str(champion_id), "未知英雄")
