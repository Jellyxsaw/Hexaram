import tkinter as tk
from tkinter import ttk


class TeammateStatsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller

        # 創建隊友戰績頁面
        self.create_teammate_stats_page()

    def create_teammate_stats_page(self):
        """創建隊友戰績頁面"""
        # 主要容器
        main_container = tk.Frame(self, bg="#16213e")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 標題
        title_label = tk.Label(
            main_container,
            text="目前隊友",
            bg="#16213e",
            fg="white",
            font=("Arial", 14, "bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(main_container, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 搜索框
        search_frame = tk.Frame(main_container, bg="#16213e")
        search_frame.pack(anchor="e", padx=20, pady=10)

        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            bg="#0f3460",
            fg="#8b8b8b",
            insertbackground="white",
            font=("Arial", 10),
            width=40
        )
        search_entry.insert(0, "搜索玩家...")
        search_entry.pack(side="left", padx=5)

        search_button = tk.Button(
            search_frame,
            text="🔍",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 10, "bold"),
            command=lambda: self.search_player(search_var.get())
        )
        search_button.pack(side="left", padx=5)

        # 玩家卡片容器
        self.players_container = tk.Frame(main_container, bg="#16213e")
        self.players_container.pack(fill="both", expand=True, padx=20, pady=10)

        # 載入玩家資料
        self.load_player_data()

    def load_player_data(self):
        """載入玩家資料"""
        # TODO: 從API獲取玩家資料
        # 使用模擬資料
        self.players = [
            {
                "id": "Player1",
                "name": "玩家一",
                "level": 120,
                "rank": "鑽石 IV",
                "aram_games": "500+",
                "win_rate": "58%",
                "champions": ["", "", "", "", ""],
                "kda": "8.2 / 5.4 / 15.6",
                "kda_ratio": "4.4",
                "team_participation": "68%",
                "vision_score": "42"
            },
            {
                "id": "Player2",
                "name": "玩家二",
                "level": 95,
                "rank": "白金 II",
                "aram_games": "320+",
                "win_rate": "52%",
                "champions": ["", "", "", "", ""],
                "kda": "6.7 / 6.2 / 17.8",
                "kda_ratio": "3.9",
                "team_participation": "75%",
                "vision_score": "38"
            },
            {
                "id": "Player3",
                "name": "玩家三",
                "level": 150,
                "rank": "大師",
                "aram_games": "850+",
                "win_rate": "62%",
                "champions": ["", "", "", "", ""],
                "kda": "9.2 / 4.3 / 16.1",
                "kda_ratio": "5.9",
                "team_participation": "71%",
                "vision_score": "53"
            },
            {
                "id": "Player4",
                "name": "玩家四",
                "level": 72,
                "rank": "黃金 I",
                "aram_games": "210+",
                "win_rate": "50%",
                "champions": ["", "", "", "", ""],
                "kda": "7.1 / 7.8 / 13.5",
                "kda_ratio": "2.6",
                "team_participation": "62%",
                "vision_score": "29"
            }
        ]

        # 顯示玩家卡片
        self.display_player_cards()

        # 團隊協同分析
        self.create_team_synergy_analysis()

    def display_player_cards(self):
        """顯示玩家卡片"""
        # 清空容器
        for widget in self.players_container.winfo_children():
            widget.destroy()

        # 為每個玩家創建卡片
        for i, player in enumerate(self.players):
            self.create_player_card(player, i)

    def create_player_card(self, player, index):
        """創建玩家卡片"""
        # 卡片背景色交替
        bg_color = "#0f3460" if index % 2 == 0 else "#122b4d"

        card_frame = tk.Frame(self.players_container, bg=bg_color, height=120)
        card_frame.pack(fill="x", pady=5)
        card_frame.pack_propagate(False)

        # 玩家頭像
        icon_frame = tk.Frame(card_frame, bg="#16213e", width=80, height=80)
        icon_frame.place(x=20, y=20)

        icon_label = tk.Label(
            icon_frame,
            text=f"P{index + 1}",
            bg="#16213e",
            fg="#e94560",
            font=("Arial", 20, "bold")
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # 玩家資訊
        info_frame = tk.Frame(card_frame, bg=bg_color, width=200, height=80)
        info_frame.place(x=120, y=20)

        name_label = tk.Label(
            info_frame,
            text=f"{player['name']} ({player['id']})",
            bg=bg_color,
            fg="white",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")

        level_label = tk.Label(
            info_frame,
            text=f"Lv. {player['level']} | {player['rank']}",
            bg=bg_color,
            fg="#8b8b8b",
            font=("Arial", 10),
            anchor="w"
        )
        level_label.pack(anchor="w", pady=3)

        games_label = tk.Label(
            info_frame,
            text=f"ARAM場次: {player['aram_games']} | 勝率: {player['win_rate']}",
            bg=bg_color,
            fg="#8b8b8b",
            font=("Arial", 10),
            anchor="w"
        )
        games_label.pack(anchor="w")

        # 常用英雄
        champ_frame = tk.Frame(card_frame, bg=bg_color, width=300, height=80)
        champ_frame.place(x=350, y=20)

        champ_label = tk.Label(
            champ_frame,
            text="常用英雄:",
            bg=bg_color,
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        champ_label.pack(anchor="w")

        champ_icons_frame = tk.Frame(champ_frame, bg=bg_color)
        champ_icons_frame.pack(anchor="w", pady=5)

        for i in range(5):
            champ_icon = tk.Frame(champ_icons_frame, bg="#16213e", width=40, height=40)
            champ_icon.pack(side="left", padx=5)

        # 統計數據
        stats_frame = tk.Frame(card_frame, bg=bg_color, width=300, height=80)
        stats_frame.place(x=670, y=20)

        stats_title = tk.Label(
            stats_frame,
            text="ARAM平均數據:",
            bg=bg_color,
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        stats_title.pack(anchor="w")

        kda_label = tk.Label(
            stats_frame,
            text=f"KDA: {player['kda']} ({player['kda_ratio']})",
            bg=bg_color,
            fg="#8b8b8b",
            font=("Arial", 10),
            anchor="w"
        )
        kda_label.pack(anchor="w", pady=3)

        participation_label = tk.Label(
            stats_frame,
            text=f"參團率: {player['team_participation']} | 視野得分: {player['vision_score']}",
            bg=bg_color,
            fg="#8b8b8b",
            font=("Arial", 10),
            anchor="w"
        )
        participation_label.pack(anchor="w")

        # 操作按鈕
        button_frame = tk.Frame(card_frame, bg=bg_color, width=150, height=40)
        button_frame.place(x=970, y=40)

        detail_button = tk.Button(
            button_frame,
            text="查看詳細數據",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=lambda player_id=player['id']: self.view_player_details(player_id)
        )
        detail_button.pack()

    def create_team_synergy_analysis(self):
        """創建團隊協同分析區域"""
        synergy_frame = tk.Frame(self.players_container, bg="#0f3460", height=90)
        synergy_frame.pack(fill="x", pady=10)
        synergy_frame.pack_propagate(False)

        title_label = tk.Label(
            synergy_frame,
            text="團隊協同分析",
            bg="#0f3460",
            fg="white",
            font=("Arial", 12, "bold")
        )
        title_label.place(x=20, y=20)

        analysis_label = tk.Label(
            synergy_frame,
            text="團隊評級: A- | ARAM協同性: 高 | 戰鬥風格: 持續消耗型 | 建議策略: 中期團戰, 保持消耗",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        analysis_label.place(x=20, y=50)

        share_button = tk.Button(
            synergy_frame,
            text="分享團隊分析結果",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 12, "bold"),
            width=20,
            command=self.share_team_analysis
        )
        share_button.place(x=900, y=30)

    def search_player(self, query):
        """搜索玩家"""
        print(f"搜索玩家: {query}")
        # TODO: 實現搜索邏輯

    def view_player_details(self, player_id):
        """查看玩家詳細資料"""
        print(f"查看玩家詳細資料: {player_id}")
        # TODO: 實現查看玩家詳細資料的邏輯

    def share_team_analysis(self):
        """分享團隊分析結果"""
        print("分享團隊分析結果")
        # TODO: 實現分享團隊分析結果的邏輯