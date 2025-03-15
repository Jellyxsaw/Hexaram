import tkinter as tk
from tkinter import ttk


class StatsAnalysisFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller

        # 創建英雄分析頁面
        self.create_hero_analysis_page()

    def create_hero_analysis_page(self):
        """創建英雄分析頁面"""
        # 主要容器
        main_container = tk.Frame(self, bg="#1a1a2e")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

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
            text="Sona 索娜",
            bg="#16213e",
            fg="white",
            font=("Arial", 16, "bold")
        )
        hero_name.place(x=150, y=25)

        hero_type = tk.Label(
            hero_info_frame,
            text="輔助 • 難度: ★☆☆ • 推薦位置: 後排支援",
            bg="#16213e",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        hero_type.place(x=150, y=55)

        # 英雄等級指示
        rank_frame = tk.Frame(hero_info_frame, bg="#0f3460", width=200, height=80)
        rank_frame.place(x=950, y=20)

        rank_label = tk.Label(
            rank_frame,
            text="S 級英雄",
            bg="#0f3460",
            fg="white",
            font=("Arial", 14, "bold")
        )
        rank_label.pack(pady=(15, 0))

        rank_desc = tk.Label(
            rank_frame,
            text="ARAM 勝率第 1 名",
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
            text="65.2%",
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
            text="8.5%",
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
            text="2.3%",
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
            text="6.3 / 4.8 / 22.1",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        kda_label2.place(x=110, y=50)

        kda_ratio = tk.Label(
            metrics_frame,
            text="KDA比: 5.9",
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
            text="18,500",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        damage_label2.place(x=110, y=80)

        damage_ratio = tk.Label(
            metrics_frame,
            text="隊伍占比: 17%",
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
            text="25,600",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        healing_label2.place(x=110, y=110)

        healing_ratio = tk.Label(
            metrics_frame,
            text="隊伍占比: 65%",
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
            text="16,200",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        taken_label2.place(x=110, y=140)

        taken_ratio = tk.Label(
            metrics_frame,
            text="隊伍占比: 14%",
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
        points = [(20, 70), (96, 60), (172, 65), (248, 40), (324, 30), (400, 20)]
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

        # 符文配置
        runes_title = tk.Label(
            recommendations_frame,
            text="符文配置 (勝率: 68.7%)",
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
            text="聚星",
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        primary_label.place(x=40, y=90)

        # 次要符文 (簡化版)
        secondary_runes = ["法力環", "超然", "風暴聚集"]
        for i, rune in enumerate(secondary_runes):
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
            text="啟迪",
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        secondary_title_label.place(x=280, y=80)

        # 副系符文選擇
        secondary_choices = ["餅乾配送", "宇宙洞悉"]
        for i, choice in enumerate(secondary_choices):
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
        shard_labels = ["+8魔法攻擊", "+9適應之力", "+6護甲"]
        for i, shard in enumerate(shard_labels):
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

        for i in range(2):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=20 + i * 50, y=40)

        # 核心裝備
        core_label = tk.Label(
            items_frame,
            text="核心裝備:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        core_label.place(x=150, y=15)

        for i in range(4):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=150 + i * 50, y=40)

        # 可選裝備
        optional_label = tk.Label(
            items_frame,
            text="可選裝備:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        optional_label.place(x=380, y=15)

        for i in range(4):
            item_frame = tk.Frame(items_frame, bg="#16213e", width=40, height=40)
            item_frame.place(x=380 + i * 50, y=40)

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
            text="71.2%",
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
            text="加點順序: R > Q > W > E",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        order_label.place(x=240, y=20)

        first_label = tk.Label(
            skills_frame,
            text="首選: Q",
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
        tips = [
            "• 盡可能地使用Q騷擾敵方英雄，尤其是在前期",
            "• 靈活使用W治療隊友，優先考慮生命值較低的隊友",
            "• 使用E進行團隊機動性增加，可以配合強大的進攻或撤退"
        ]

        for i, tip in enumerate(tips):
            tip_label = tk.Label(
                tips_frame,
                text=tip,
                bg="#0f3460",
                fg="white",
                font=("Arial", 10),
                anchor="w"
            )
            tip_label.place(x=20, y=15 + i * 25)