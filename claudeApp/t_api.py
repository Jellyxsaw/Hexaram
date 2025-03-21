import base64
import json
import os
import requests
import urllib3
from typing import Dict, Optional

urllib3.disable_warnings()


class LOLAPITester:
    def __init__(self, lockfile_path: str = "C:/Riot Games/League of Legends/lockfile"):
        self.lockfile_path = lockfile_path
        self.lock_info = None

    def read_lockfile(self) -> Optional[Dict]:
        """讀取lockfile並返回連接信息"""
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
            print(f"Lockfile讀取失敗: {e}")
            return None

    def make_request(self, endpoint: str) -> Optional[Dict]:
        """發送API請求"""
        if not self.lock_info:
            self.lock_info = self.read_lockfile()
            if not self.lock_info:
                return None

        url = f"{self.lock_info['protocol']}://127.0.0.1:{self.lock_info['port']}{endpoint}"
        auth_str = f"riot:{self.lock_info['password']}"
        headers = {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}

        try:
            response = requests.get(url, headers=headers, verify=False, timeout=3)
            if response.status_code == 200:
                print(f"\n成功獲取端點: {endpoint}")
                print(f"響應數據: {response.json()}")
                return response.json()
            else:
                print(f"端點請求失敗: {endpoint}, 狀態碼: {response.status_code}")
            return None
        except Exception as e:
            print(f"請求異常: {endpoint}, 錯誤: {e}")
            return None

    def test_game_flow(self):
        """測試遊戲流程相關API"""
        print("\n=== 測試遊戲流程API ===")

        # 測試遊戲狀態
        game_phase = self.make_request("/lol-gameflow/v1/gameflow-phase")
        print(f"當前遊戲階段: {game_phase}")

        if game_phase and game_phase == "InProgress":
            print("\n遊戲進行中，開始測試遊戲相關API...")

            # 測試關鍵遊戲數據端點
            endpoints = [
                # 遊戲狀態
                "/lol-gameflow/v1/gameflow-phase",

                # 遊戲數據
                "/lol-game-data/v1/current-game",
                "/lol-game-data/v1/current-game/participants",

                # 遊戲狀態
                "/lol-game-state/v1/game-state",
                "/lol-game-state/v1/current-game",

                # 觀戰數據
                "/lol-spectator/v1/current-game",
                "/lol-spectator/v1/current-game/participants",

                # 遊戲流程
                "/lol-gameflow/v1/gameflow-metadata",
                "/lol-gameflow/v1/gameflow-metadata/player-champion",

                # 隊伍信息
                "/lol-game-data/v1/current-game/teams",
                "/lol-game-state/v1/current-game/teams",
                "/lol-spectator/v1/current-game/teams"
            ]

            failed_endpoints = []
            for endpoint in endpoints:
                if not self.make_request(endpoint):
                    failed_endpoints.append(endpoint)

            if failed_endpoints:
                print("\n=== 404的API端點列表 ===")
                for endpoint in failed_endpoints:
                    print(endpoint)

            # 嘗試 Live Client Data API
            print("\n=== 嘗試 Live Client Data API ===")
            live_endpoints = [
                "/lol-live-client-data/v1/active-player",
                "/lol-live-client-data/v1/game-data",
                "/lol-live-client-data/v1/player-list",
                "/lol-live-client-data/v1/player-scores",
                "/lol-live-client-data/v1/player-items",
                "/lol-live-client-data/v1/player-spells",
                "/lol-live-client-data/v1/event-data"
            ]

            for endpoint in live_endpoints:
                self.make_request(endpoint)

            # 嘗試直接訪問遊戲實時數據（不需要認證）
            print("\n=== 嘗試訪問遊戲實時數據API (端口2999) ===")
            try:
                live_game_url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
                response = requests.get(live_game_url, verify=False, timeout=3)
                if response.status_code == 200:
                    print(f"\n成功獲取實時遊戲數據!")
                    game_data = response.json()
                    # 提取所有英雄資料並顯示
                    if 'allPlayers' in game_data:
                        print("\n=== 遊戲中的英雄資料 ===")
                        for player in game_data['allPlayers']:
                            print(f"玩家: {player.get('summonerName', 'Unknown')}")
                            print(f"  英雄: {player.get('championName', 'Unknown')}")
                            print(f"  等級: {player.get('level', 'Unknown')}")
                            print(f"  隊伍: {player.get('team', 'Unknown')}")
                            print("---")
                else:
                    print(f"實時遊戲數據請求失敗, 狀態碼: {response.status_code}")
            except Exception as e:
                print(f"請求實時遊戲數據異常: {e}")

            # 備用方案：嘗試從遊戲狀態取得玩家英雄資訊
            print("\n嘗試使用備用端點...")
            backup_endpoints = [
                "/lol-game-data/v1/current-game/player",
                "/lol-game-state/v1/current-game/player",
                "/lol-gameflow/v1/session",
                "/lol-game-data/v1/current-game/player/champion",
                "/lol-game-state/v1/current-game/player/champion",
                "/lol-pregame-events/v1/session"
            ]

            for endpoint in backup_endpoints:
                self.make_request(endpoint)

    def test_champ_select(self):
        """測試英雄選擇相關API"""
        print("\n=== 測試英雄選擇API ===")
        endpoints = [
            "/lol-champ-select/v1/session",
            "/lol-champ-select/v1/current-champion",
            "/lol-champ-select/v1/pickable-champions",
            "/lol-champ-select/v1/bannable-champions",
            "/lol-champ-select/v1/current-champion-skin",
            "/lol-champ-select/v1/current-champion-summoner-spells"
        ]

        for endpoint in endpoints:
            self.make_request(endpoint)

    def test_summoner(self):
        """測試召喚師相關API"""
        print("\n=== 測試召喚師API ===")
        endpoints = [
            "/lol-summoner/v1/current-summoner",
            "/lol-summoner/v1/current-summoner/account",
            "/lol-summoner/v1/current-summoner/summoner-profile",
            "/lol-summoner/v1/current-summoner/status"
        ]

        for endpoint in endpoints:
            self.make_request(endpoint)


def main():
    tester = LOLAPITester()

    # 測試遊戲流程
    tester.test_game_flow()

    # 測試英雄選擇
    tester.test_champ_select()

    # 測試召喚師信息
    tester.test_summoner()


if __name__ == "__main__":
    main()