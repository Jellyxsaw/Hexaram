import tkinter as tk


class ChampionDetailFrame(tk.Frame):
    def __init__(self, parent, controller, champion_name):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller
        self.champion_name = champion_name

        # 創建英雄詳細頁面
        self.create_champion_detail_page()

    def create_champion_detail_page(self):
        """創建英雄詳細頁面"""
        # 主要容器
        main_container = tk.Frame(self, bg="#1a1a2e")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 返回按鈕
        back_button = tk.Button(
            main_container,
            text="返回列表",
            bg="#0f3460",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=self.controller.show_champion_list
        )
        back_button.pack(anchor="nw", pady=10)

        # 上方英雄資訊區
        self.create_hero_info_section(main_container)

        # 下方分為左右兩個區域
        lower_container = tk.Frame(main_container, bg="#1a1a2e")
        lower_container.pack(fill="both", expand=True, pady=10)

        # 左側數據顯示區域
        self.create_stats_section(lower_container)

        # 右側推薦區域
        self.create_recommendations_section(lower_container)

    def create_hero_info_section(self, parent):
        """創建英雄資訊區域"""
        hero_info_frame = tk.Frame(parent, bg="#16213e", height=120)
        hero_info_frame.pack(fill="x", pady=10)
        hero_info_frame.pack_propagate(False)

        # 英雄圖示
        icon_frame = tk.Frame(hero_info_frame, bg="#0f3460", width=100, height=100)
        icon_frame.place(x=30, y=10)

        # 英雄名稱和類型
        hero_name = tk.Label(
            hero_info_frame,
            text=self.champion_name,
            bg="#16213e",
            fg="white",
            font=("Arial", 16, "bold")
        )
        hero_name.place(x=150, y=25)

        # 獲取英雄類型
        champion_type = self.get_champion_type(self.champion_name)

        hero_type = tk.Label(
            hero_info_frame,
            text=champion_type,
            bg="#16213e",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        hero_type.place(x=150, y=55)

        # 英雄等級指示
        rank_frame = tk.Frame(hero_info_frame, bg="#0f3460", width=200, height=80)
        rank_frame.place(x=950, y=20)

        # 獲取英雄排名信息
        rank_info = self.get_champion_rank(self.champion_name)

        rank_label = tk.Label(
            rank_frame,
            text=rank_info["tier"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 14, "bold")
        )
        rank_label.pack(pady=(15, 0))

        rank_desc = tk.Label(
            rank_frame,
            text=rank_info["desc"],
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10)
        )
        rank_desc.pack()

    def create_stats_section(self, parent):
        """創建左側數據顯示區域"""
        stats_frame = tk.Frame(parent, bg="#16213e", width=460)
        stats_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 標題
        title_label = tk.Label(
            stats_frame,
            text="數據表現",
            bg="#16213e",
            fg="white",
            font=("Arial", 14, "bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(stats_frame, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 獲取英雄統計數據
        champion_stats = self.get_champion_stats(self.champion_name)

        # 關鍵數據
        key_stats_frame = tk.Frame(stats_frame, bg="#0f3460", height=100)
        key_stats_frame.pack(fill="x", padx=20, pady=10)

        # 勝率
        win_rate_label1 = tk.Label(
            key_stats_frame,
            text="勝率",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        win_rate_label1.place(x=20, y=20)

        win_rate_label2 = tk.Label(
            key_stats_frame,
            text=f"{champion_stats['win_rate']}%",
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 16, "bold")
        )
        win_rate_label2.place(x=20, y=50)

        # 選用率
        pick_rate_label1 = tk.Label(
            key_stats_frame,
            text="選用率",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        pick_rate_label1.place(x=160, y=20)

        pick_rate_label2 = tk.Label(
            key_stats_frame,
            text=f"{champion_stats['pick_rate']}%",
            bg="#0f3460",
            fg="white",
            font=("Arial", 16, "bold")
        )
        pick_rate_label2.place(x=160, y=50)

        # 禁用率
        ban_rate_label1 = tk.Label(
            key_stats_frame,
            text="禁用率",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        ban_rate_label1.place(x=300, y=20)

        ban_rate_label2 = tk.Label(
            key_stats_frame,
            text=f"{champion_stats['ban_rate']}%",
            bg="#0f3460",
            fg="white",
            font=("Arial", 16, "bold")
        )
        ban_rate_label2.place(x=300, y=50)

        # 表現指標
        metrics_frame = tk.Frame(stats_frame, bg="#0f3460", height=160)
        metrics_frame.pack(fill="x", padx=20, pady=10)

        metrics_title = tk.Label(
            metrics_frame,
            text="平均表現 (每場比賽)",
            bg="#0f3460",
            fg="white",
            font=("Arial", 12, "bold")
        )
        metrics_title.place(x=20, y=20)

        # KDA
        kda_label1 = tk.Label(
            metrics_frame,
            text="KDA:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        kda_label1.place(x=20, y=50)

        kda_label2 = tk.Label(
            metrics_frame,
            text=champion_stats["kda"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        kda_label2.place(x=110, y=50)

        kda_ratio = tk.Label(
            metrics_frame,
            text=f"KDA比: {champion_stats['kda_ratio']}",
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10, "bold")
        )
        kda_ratio.place(x=260, y=50)

        # 輸出傷害
        damage_label1 = tk.Label(
            metrics_frame,
            text="輸出傷害:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        damage_label1.place(x=20, y=80)

        damage_label2 = tk.Label(
            metrics_frame,
            text=champion_stats["damage"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        damage_label2.place(x=110, y=80)

        damage_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {champion_stats['damage_percentage']}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        damage_ratio.place(x=260, y=80)

        # 治療量
        healing_label1 = tk.Label(
            metrics_frame,
            text="治療量:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        healing_label1.place(x=20, y=110)

        healing_label2 = tk.Label(
            metrics_frame,
            text=champion_stats["healing"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        healing_label2.place(x=110, y=110)

        healing_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {champion_stats['healing_percentage']}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        healing_ratio.place(x=260, y=110)

        # 承受傷害
        taken_label1 = tk.Label(
            metrics_frame,
            text="承受傷害:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        taken_label1.place(x=20, y=140)

        taken_label2 = tk.Label(
            metrics_frame,
            text=champion_stats["damage_taken"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        taken_label2.place(x=110, y=140)

        taken_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {champion_stats['damage_taken_percentage']}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        taken_ratio.place(x=260, y=140)

        # 勝率趨勢
        trend_title = tk.Label(
            stats_frame,
            text="勝率趨勢 (最近5個版本)",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        trend_title.pack(anchor="w", padx=20, pady=(20, 0))

        trend_frame = tk.Frame(stats_frame, bg="#0f3460", height=160)
        trend_frame.pack(fill="x", padx=20, pady=10)

        # 在這裡繪製趨勢圖
        # 簡單模擬一個趨勢圖區域
        trend_canvas = tk.Canvas(trend_frame, bg="#0f3460", highlightthickness=0)
        trend_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 水平網格線
        for i in range(5):
            y = 20 + i * 25
            trend_canvas.create_line(20, y, 400, y, fill="#ffffff", width=1, dash=(2, 2))
            trend_canvas.create_text(18, y, text=f"{75 - i * 5}%", anchor="e", fill="white", font=("Arial", 8))

        # 垂直標籤 (版本號)
        versions = ["14.3", "14.4", "14.5", "14.6", "14.7", "14.8"]
        for i, version in enumerate(versions):
            x = 20 + i * 76
            trend_canvas.create_text(x, 130, text=version, anchor="n", fill="white", font=("Arial", 8))

        # 趨勢線
        trend_data = champion_stats["trend_data"]
        points = []
        for i, value in enumerate(trend_data):
            x = 20 + i * 76
            y = 120 - value * 1.2  # 簡單映射到畫布高度
            points.append((x, y))

        trend_canvas.create_line(points, fill="#4ecca3", width=2, smooth=True)

        for x, y in points:
            trend_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#4ecca3", outline="#4ecca3")

    def create_recommendations_section(self, parent):
        """創建右側推薦區域"""
        recommendations_frame = tk.Frame(parent, bg="#16213e", width=680)
        recommendations_frame.pack(side="right", fill="both", expand=True)

        # 標題
        title_label = tk.Label(
            recommendations_frame,
            text="推薦構建",
            bg="#16213e",
            fg="white",
            font=("Arial", 14, "bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(recommendations_frame, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 獲取推薦構建數據
        recommendations = self.get_champion_recommendations(self.champion_name)

        # 符文配置
        runes_title = tk.Label(
            recommendations_frame,
            text=f"符文配置 (勝率: {recommendations['runes_win_rate']}%)",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        runes_title.pack(anchor="w", padx=20, pady=(20, 0))

        runes_frame = tk.Frame(recommendations_frame, bg="#0f3460", height=120)
        runes_frame.pack(fill="x", padx=20, pady=10)

        # 主系符文
        primary_rune = tk.Frame(runes_frame, bg="#16213e", width=50, height=50)
        primary_rune.place(x=40, y=35)

        primary_label = tk.Label(
            runes_frame,
            text=recommendations["primary_rune"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        primary_label.place(x=40, y=90)

        # 次要符文 (簡化版)
        for i, rune in enumerate(recommendations["secondary_runes"]):
            rune_frame = tk.Frame(runes_frame, bg="#16213e", width=30, height=30)
            rune_frame.place(x=100 + i * 50, y=35)

            rune_label = tk.Label(
                runes_frame,
                text=rune,
                bg="#0f3460",
                fg="white",
                font=("Arial", 8)
            )
            rune_label.place(x=100 + i * 50, y=70, anchor="center")

        # 副系符文
        secondary_title = tk.Frame(runes_frame, bg="#16213e", width=40, height=40)
        secondary_title.place(x=280, y=35)

        secondary_title_label = tk.Label(
            runes_frame,
            text=recommendations["secondary_path"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        secondary_title_label.place(x=280, y=80)

        # 副系符文選擇
        for i, choice in enumerate(recommendations["secondary_choices"]):
            choice_frame = tk.Frame(runes_frame, bg="#16213e", width=30, height=30)
            choice_frame.place(x=330 + i * 50, y=35)

            choice_label = tk.Label(
                runes_frame,
                text=choice,
                bg="#0f3460",
                fg="white",
                font=("Arial", 8)
            )
            choice_label.place(x=330 + i * 50, y=70, anchor="center")

        # 符文碎片
        for i, shard in enumerate(recommendations["shards"]):
            shard_frame = tk.Frame(runes_frame, bg="#16213e", width=15, height=15)
            shard_frame.place(x=430, y=20 + i * 20)

            shard_label = tk.Label(
                runes_frame,
                text=shard,
                bg="#0f3460",
                fg="white",
                font=("Arial", 8)
            )
            shard_label.place(x=455, y=20 + i * 20)

        # 裝備建議
        items_title = tk.Label(
            recommendations_frame,
            text="最佳裝備構建",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        items_title.pack(anchor="w", padx=20, pady=(20, 0))

        items_frame = tk.Frame(recommendations_frame, bg="#0f3460", height=110)
        items_frame.pack(fill="x", padx=20, pady=10)

        # 起始裝備
        start_label = tk.Label(
            items_frame,
            text="起始裝備:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        start_label.place(x=20, y=15)

        for i, item in enumerate(recommendations["starting_items"]):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=20 + i * 50, y=40)

            # 顯示裝備 ID (實際應用中應顯示圖標)
            item_label = tk.Label(
                item_frame,
                text=item,
                bg="#16213e",
                fg="white",
                font=("Arial", 8)
            )
            item_label.place(relx=0.5, rely=0.5, anchor="center")

        # 核心裝備
        core_label = tk.Label(
            items_frame,
            text="核心裝備:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        core_label.place(x=150, y=15)

        for i, item in enumerate(recommendations["core_items"]):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=150 + i * 50, y=40)

            # 顯示裝備 ID (實際應用中應顯示圖標)
            item_label = tk.Label(
                item_frame,
                text=item,
                bg="#16213e",
                fg="white",
                font=("Arial", 8)
            )
            item_label.place(relx=0.5, rely=0.5, anchor="center")

        # 可選裝備
        optional_label = tk.Label(
            items_frame,
            text="可選裝備:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        optional_label.place(x=380, y=15)

        for i, item in enumerate(recommendations["optional_items"]):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=380 + i * 50, y=40)

            # 顯示裝備 ID (實際應用中應顯示圖標)
            item_label = tk.Label(
                item_frame,
                text=item,
                bg="#16213e",
                fg="white",
                font=("Arial", 8)
            )
            item_label.place(relx=0.5, rely=0.5, anchor="center")

        # 勝率
        win_rate_label = tk.Label(
            items_frame,
            text="完整構建勝率: ",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        win_rate_label.place(x=20, y=90)

        win_rate_value = tk.Label(
            items_frame,
            text=f"{recommendations['build_win_rate']}%",
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10, "bold")
        )
        win_rate_value.place(x=120, y=90)

        # 技能加點順序
        skills_title = tk.Label(
            recommendations_frame,
            text="技能加點順序",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        skills_title.pack(anchor="w", padx=20, pady=(20, 0))

        skills_frame = tk.Frame(recommendations_frame, bg="#0f3460", height=80)
        skills_frame.pack(fill="x", padx=20, pady=10)

        # 技能按鈕
        skill_labels = ["Q", "W", "E", "R"]
        for i, skill in enumerate(skill_labels):
            skill_frame = tk.Frame(skills_frame, bg="#16213e", width=40, height=40)
            skill_frame.place(x=20 + i * 50, y=20)

            skill_label = tk.Label(
                skill_frame,
                text=skill,
                bg="#16213e",
                fg="white",
                font=("Arial", 12, "bold")
            )
            skill_label.place(relx=0.5, rely=0.5, anchor="center")

        # 加點說明
        order_label = tk.Label(
            skills_frame,
            text=f"加點順序: {recommendations['skill_order']}",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        order_label.place(x=240, y=20)

        first_label = tk.Label(
            skills_frame,
            text=f"首選: {recommendations['first_skill']}",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        first_label.place(x=240, y=45)

        # ARAM 攻略要點
        tips_title = tk.Label(
            recommendations_frame,
            text="ARAM 攻略要點",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        tips_title.pack(anchor="w", padx=20, pady=(20, 0))

        tips_frame = tk.Frame(recommendations_frame, bg="#0f3460", height=80)
        tips_frame.pack(fill="x", padx=20, pady=10)

        # 攻略要點
        for i, tip in enumerate(recommendations["tips"]):
            tip_label = tk.Label(
                tips_frame,
                text=tip,
                bg="#0f3460",
                fg="white",
                font=("Arial", 10),
                anchor="w"
            )
            tip_label.place(x=20, y=15 + i * 25)

    def get_champion_type(self, champion_name):
        """獲取英雄類型 (模擬數據)"""
        champion_types = {
            "Sona 索娜": "輔助 • 難度: ★☆☆ • 推薦位置: 後排支援",
            "Seraphine 瑟菈紛": "輔助/法師 • 難度: ★★☆ • 推薦位置: 後排支援",
            "Ziggs 希格斯": "法師 • 難度: ★★☆ • 推薦位置: 後排輸出",
            "Ashe 艾希": "射手 • 難度: ★☆☆ • 推薦位置: 後排輸出",
            "Maokai 茂凱": "坦克 • 難度: ★★☆ • 推薦位置: 前排肉盾",
            "Kayle 凱爾": "戰士/法師 • 難度: ★★★ • 推薦位置: 中後排漸進式輸出",
            "Brand 布蘭德": "法師 • 難度: ★★☆ • 推薦位置: 後排AOE輸出",
            "Swain 斯溫": "法師/戰士 • 難度: ★★★ • 推薦位置: 中排持續輸出",
            "Veigar 維迦": "法師 • 難度: ★★☆ • 推薦位置: 後排爆發控制",
            "Nasus 納瑟斯": "戰士/坦克 • 難度: ★★☆ • 推薦位置: 前排輸出",
            "Xerath 齊勒斯": "法師 • 難度: ★★★ • 推薦位置: 後排長距離輸出",
            "Leona 雷歐娜": "坦克/輔助 • 難度: ★★☆ • 推薦位置: 前排開團控制"
        }

        # 如果找不到特定英雄，返回一個默認值
        return champion_types.get(champion_name, "未知 • 難度: ★★☆ • 推薦位置: 未知")

    def get_champion_rank(self, champion_name):
        """獲取英雄排名信息 (模擬數據)"""
        champion_ranks = {
            "Sona 索娜": {"tier": "S 級英雄", "desc": "ARAM 勝率第 1 名"},
            "Seraphine 瑟菈紛": {"tier": "S 級英雄", "desc": "ARAM 勝率第 2 名"},
            "Ziggs 希格斯": {"tier": "S 級英雄", "desc": "ARAM 勝率第 3 名"},
            "Ashe 艾希": {"tier": "S 級英雄", "desc": "ARAM 勝率第 4 名"},
            "Maokai 茂凱": {"tier": "S 級英雄", "desc": "ARAM 勝率第 5 名"},
            "Kayle 凱爾": {"tier": "A 級英雄", "desc": "ARAM 勝率第 6 名"},
            "Brand 布蘭德": {"tier": "A 級英雄", "desc": "ARAM 勝率第 7 名"},
            "Swain 斯溫": {"tier": "A 級英雄", "desc": "ARAM 勝率第 8 名"},
            "Veigar 維迦": {"tier": "A 級英雄", "desc": "ARAM 勝率第 9 名"},
            "Nasus 納瑟斯": {"tier": "A 級英雄", "desc": "ARAM 勝率第 10 名"},
            "Xerath 齊勒斯": {"tier": "A 級英雄", "desc": "ARAM 勝率第 11 名"},
            "Leona 雷歐娜": {"tier": "A 級英雄", "desc": "ARAM 勝率第 12 名"}
        }

        # 如果找不到特定英雄，返回一個默認值
        return champion_ranks.get(champion_name, {"tier": "未知", "desc": "排名未知"})

    def get_champion_stats(self, champion_name):
        """獲取英雄統計數據 (模擬數據)"""
        champion_stats = {
            "Sona 索娜": {
                "win_rate": 65.2,
                "pick_rate": 8.5,
                "ban_rate": 2.3,
                "kda": "6.3 / 4.8 / 22.1",
                "kda_ratio": "5.9",
                "damage": "18,500",
                "damage_percentage": "17%",
                "healing": "25,600",
                "healing_percentage": "65%",
                "damage_taken": "16,200",
                "damage_taken_percentage": "14%",
                "trend_data": [60, 62, 63, 67, 70, 72]
            },
            "Seraphine 瑟菈紛": {
                "win_rate": 63.7,
                "pick_rate": 9.2,
                "ban_rate": 3.1,
                "kda": "5.8 / 5.2 / 19.3",
                "kda_ratio": "4.8",
                "damage": "20,100",
                "damage_percentage": "19%",
                "healing": "22,300",
                "healing_percentage": "59%",
                "damage_taken": "17,500",
                "damage_taken_percentage": "15%",
                "trend_data": [59, 61, 62, 63, 64, 65]
            },
            "Ziggs 希格斯": {
                "win_rate": 62.4,
                "pick_rate": 11.7,
                "ban_rate": 4.2,
                "kda": "7.6 / 5.9 / 15.2",
                "kda_ratio": "3.9",
                "damage": "32,400",
                "damage_percentage": "31%",
                "healing": "0",
                "healing_percentage": "0%",
                "damage_taken": "18,900",
                "damage_taken_percentage": "16%",
                "trend_data": [58, 59, 60, 61, 62, 63]
            },
            "Ashe 艾希": {
                "win_rate": 61.8,
                "pick_rate": 14.5,
                "ban_rate": 3.8,
                "kda": "6.8 / 6.2 / 14.8",
                "kda_ratio": "3.5",
                "damage": "28,200",
                "damage_percentage": "27%",
                "healing": "0",
                "healing_percentage": "0%",
                "damage_taken": "19,300",
                "damage_taken_percentage": "16%",
                "trend_data": [57, 58, 59, 60, 61, 62]
            }
        }

        # 為其他英雄創建默認數據
        default_stats = {
            "win_rate": 55.0,
            "pick_rate": 7.0,
            "ban_rate": 2.0,
            "kda": "6.0 / 6.0 / 15.0",
            "kda_ratio": "3.5",
            "damage": "20,000",
            "damage_percentage": "20%",
            "healing": "8,000",
            "healing_percentage": "25%",
            "damage_taken": "18,000",
            "damage_taken_percentage": "15%",
            "trend_data": [54, 55, 55, 56, 56, 57]
        }

        return champion_stats.get(champion_name, default_stats)

    def get_champion_recommendations(self, champion_name):
        """獲取英雄推薦構建 (模擬數據)"""
        recommendations = {
            "Sona 索娜": {
                "runes_win_rate": 68.7,
                "primary_rune": "聚星",
                "secondary_runes": ["法力環", "超然", "風暴聚集"],
                "secondary_path": "啟迪",
                "secondary_choices": ["餅乾配送", "宇宙洞悉"],
                "shards": ["+8魔法攻擊", "+9適應之力", "+6護甲"],
                "starting_items": ["S1", "S2"],
                "core_items": ["C1", "C2", "C3", "C4"],
                "optional_items": ["O1", "O2", "O3", "O4"],
                "build_win_rate": 71.2,
                "skill_order": "R > Q > W > E",
                "first_skill": "Q",
                "tips": [
                    "• 盡可能地使用Q騷擾敵方英雄，尤其是在前期",
                    "• 靈活使用W治療隊友，優先考慮生命值較低的隊友",
                    "• 使用E進行團隊機動性增加，可以配合強大的進攻或撤退"
                ]
            },
            "Seraphine 瑟菈紛": {
                "runes_win_rate": 67.3,
                "primary_rune": "奧術彗星",
                "secondary_runes": ["法力環", "超然", "暴風驟雨"],
                "secondary_path": "啟迪",
                "secondary_choices": ["餅乾配送", "宇宙洞悉"],
                "shards": ["+8魔法攻擊", "+9適應之力", "+6護甲"],
                "starting_items": ["S1", "S2"],
                "core_items": ["C1", "C2", "C3", "C4"],
                "optional_items": ["O1", "O2", "O3", "O4"],
                "build_win_rate": 69.8,
                "skill_order": "R > Q > E > W",
                "first_skill": "Q",
                "tips": [
                    "• 使用Q進行安全的線上消耗",
                    "• 在團戰中儘量為多名隊友提供W的護盾和治療",
                    "• 利用E的長距離打斷和控制敵方關鍵目標"
                ]
            }
        }

        # 為其他英雄創建默認推薦
        default_recommendations = {
            "runes_win_rate": 60.0,
            "primary_rune": "征服者",
            "secondary_runes": ["凱旋", "傳說：韌性", "致命一擊"],
            "secondary_path": "精密",
            "secondary_choices": ["飢餓獵手", "無情獵手"],
            "shards": ["+9適應之力", "+9適應之力", "+6護甲"],
            "starting_items": ["S1", "S2"],
            "core_items": ["C1", "C2", "C3"],
            "optional_items": ["O1", "O2", "O3", "O4"],
            "build_win_rate": 62.5,
            "skill_order": "R > Q > W > E",
            "first_skill": "Q",
            "tips": [
                "• 保持與隊友的適當距離",
                "• 合理利用技能，避免浪費能量",
                "• 在團戰中注意站位，避免被敵方集火"
            ]
        }

        return recommendations.get(champion_name, default_recommendations)
