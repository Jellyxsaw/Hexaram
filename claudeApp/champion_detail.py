import tkinter as tk
import logging
import threading
from typing import Dict, Any, Optional
from PIL import Image, ImageTk

from api_client import AramAPIClient

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChampionDetailFrame(tk.Frame):
    def __init__(self, parent, controller, champion_id):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller
        self.champion_id = champion_id

        # 初始化API客戶端
        self.api_client = AramAPIClient()

        # 創建載入中狀態
        self.loading = False

        # 創建載入指示器
        self.create_loading_indicator()

        # 創建主要容器
        self.main_container = tk.Frame(self, bg="#1a1a2e")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 顯示載入指示器
        self.show_loading()

        # 載入英雄詳細資料
        self.champion_data = None
        self.load_champion_detail()

    def create_loading_indicator(self):
        """創建載入指示器"""
        self.loading_frame = tk.Frame(self, bg="#1a1a2e")
        self.loading_frame.pack(fill="both", expand=True)

        self.loading_label = tk.Label(
            self.loading_frame,
            text="載入中...",
            bg="#1a1a2e",
            fg="white",
            font=("Arial", 14)
        )
        self.loading_label.pack(expand=True, pady=100)

    def show_loading(self):
        """顯示載入指示器"""
        self.loading = True
        self.main_container.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

    def hide_loading(self):
        """隱藏載入指示器"""
        self.loading = False
        self.loading_frame.pack_forget()
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

    def load_champion_detail(self):
        """載入英雄詳細資料"""

        def fetch_data():
            try:
                # 從API獲取英雄詳細資料
                champion_data = self.api_client.get_champion_detail(self.champion_id)
                self.champion_data = champion_data

                # 在主執行緒中更新UI
                if not self._is_destroyed():
                    self.after(0, self.create_champion_detail_page)

            except Exception as e:
                logger.error(f"載入英雄詳細資料失敗: {str(e)}")

                # 顯示錯誤訊息
                if not self._is_destroyed():
                    self.after(0, lambda: self.show_error(f"載入資料失敗: {str(e)}"))

        # 在背景執行緒中獲取資料
        threading.Thread(target=fetch_data, daemon=True).start()

    def show_error(self, message):
        """
        顯示錯誤訊息

        Args:
            message: 錯誤訊息
        """
        # 清空主容器
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # 添加返回按鈕
        back_button = tk.Button(
            self.main_container,
            text="返回列表",
            bg="#0f3460",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=self.controller.show_champion_list
        )
        back_button.pack(anchor="nw", pady=10)

        # 顯示錯誤訊息
        error_label = tk.Label(
            self.main_container,
            text=message,
            bg="#1a1a2e",
            fg="#e94560",
            font=("Arial", 12)
        )
        error_label.pack(expand=True, pady=50)

        # 隱藏載入指示器
        self.hide_loading()

    def create_champion_detail_page(self):
        """創建英雄詳細頁面"""
        if not self.champion_data:
            self.show_error("無法載入英雄資料")
            return

        # 清空主容器
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # 返回按鈕
        back_button = tk.Button(
            self.main_container,
            text="返回列表",
            bg="#0f3460",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=self.controller.show_champion_list
        )
        back_button.pack(anchor="nw", pady=10)

        # 上方英雄資訊區
        self.create_hero_info_section(self.main_container)

        # 下方分為左右兩個區域
        lower_container = tk.Frame(self.main_container, bg="#1a1a2e")
        lower_container.pack(fill="both", expand=True, pady=10)

        # 左側數據顯示區域
        self.create_stats_section(lower_container)

        # 右側推薦區域
        self.create_recommendations_section(lower_container)

        # 隱藏載入指示器
        self.hide_loading()

    def create_hero_info_section(self, parent):
        """創建英雄資訊區域"""
        basic_info = self.champion_data.get('basic_info', {})

        hero_info_frame = tk.Frame(parent, bg="#16213e", height=120)
        hero_info_frame.pack(fill="x", pady=10)
        hero_info_frame.pack_propagate(False)

        # 英雄圖示
        icon_frame = tk.Frame(hero_info_frame, bg="#0f3460", width=100, height=100)
        icon_frame.place(x=30, y=10)

        # 嘗試載入英雄圖示
        champion_id = basic_info.get('champion_id', '')
        champion_key = basic_info.get('key', 0)

        # 檢查控制器是否有champ_images屬性和對應的圖片
        if hasattr(self.controller, 'champ_images'):
            # 優先使用championId查找
            if champion_id in self.controller.champ_images:
                icon = self.controller.champ_images[champion_id]
                icon_label = tk.Label(icon_frame, image=icon, bg="#0f3460")
                icon_label.place(relx=0.5, rely=0.5, anchor="center")
            # 然後嘗試使用key查找
            elif str(champion_key) in self.controller.champ_images:
                icon = self.controller.champ_images[str(champion_key)]
                icon_label = tk.Label(icon_frame, image=icon, bg="#0f3460")
                icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # 英雄名稱
        champion_name = basic_info.get('champion_name', '')
        champion_tw_name = basic_info.get('champion_tw_name', '')
        display_name = champion_name
        if champion_tw_name:
            display_name = f"{champion_name} {champion_tw_name}"

        hero_name = tk.Label(
            hero_info_frame,
            text=display_name,
            bg="#16213e",
            fg="white",
            font=("Arial", 16, "bold")
        )
        hero_name.place(x=150, y=25)

        # 英雄類型和難度
        champion_type = basic_info.get('champion_type', '')
        champion_difficulty = basic_info.get('champion_difficulty', 2)

        # 生成難度星級
        difficulty_stars = "★" * champion_difficulty + "☆" * (3 - champion_difficulty)

        type_text = f"{champion_type} • 難度: {difficulty_stars}"

        hero_type = tk.Label(
            hero_info_frame,
            text=type_text,
            bg="#16213e",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        hero_type.place(x=150, y=55)

        # 英雄等級指示
        rank_frame = tk.Frame(hero_info_frame, bg="#0f3460", width=200, height=80)
        rank_frame.place(x=950, y=20)

        tier = basic_info.get('tier', '')
        tier_text = f"{tier} 級英雄" if tier else "未分級"

        rank_label = tk.Label(
            rank_frame,
            text=tier_text,
            bg="#0f3460",
            fg="white",
            font=("Arial", 14, "bold")
        )
        rank_label.pack(pady=(15, 0))

        rank_desc = tk.Label(
            rank_frame,
            text=basic_info.get('rank_desc', ''),
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10)
        )
        rank_desc.pack()

    def create_stats_section(self, parent):
        """創建左側數據顯示區域"""
        stats = self.champion_data.get('stats', {})

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
            text=f"{stats.get('win_rate', 0)}%",
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
            text=f"{stats.get('pick_rate', 0)}%",
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
            text=f"{stats.get('ban_rate', 0)}%",
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
            text=stats.get("kda", "0/0/0"),
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        kda_label2.place(x=110, y=50)

        kda_ratio = tk.Label(
            metrics_frame,
            text=f"KDA比: {stats.get('kda_ratio', 0)}",
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
            text=stats.get("damage", "0"),
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        damage_label2.place(x=110, y=80)

        damage_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {stats.get('damage_percentage', '0%')}",
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
            text=stats.get("healing", "0"),
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        healing_label2.place(x=110, y=110)

        healing_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {stats.get('healing_percentage', '0%')}",
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
            text=stats.get("damage_taken", "0"),
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        taken_label2.place(x=110, y=140)

        taken_ratio = tk.Label(
            metrics_frame,
            text=f"隊伍占比: {stats.get('damage_taken_percentage', '0%')}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        taken_ratio.place(x=260, y=140)

        # 勝率趨勢
        trend_title = tk.Label(
            stats_frame,
            text=f"勝率趨勢 (最近{len(stats.get('trend_versions', []))}個版本)",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        trend_title.pack(anchor="w", padx=20, pady=(20, 0))

        trend_frame = tk.Frame(stats_frame, bg="#0f3460", height=160)
        trend_frame.pack(fill="x", padx=20, pady=10)

        # 繪製趨勢圖
        trend_canvas = tk.Canvas(trend_frame, bg="#0f3460", highlightthickness=0)
        trend_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 取得趨勢資料
        trend_data = stats.get("trend_data", [])
        versions = stats.get("trend_versions", [])

        # 確保有資料可繪製
        if trend_data and versions:
            # 水平網格線
            for i in range(5):
                y = 20 + i * 25
                trend_canvas.create_line(20, y, 400, y, fill="#ffffff", width=1, dash=(2, 2))
                win_rate = int(max(trend_data)) + 5 - i * 5
                trend_canvas.create_text(18, y, text=f"{win_rate}%", anchor="e", fill="white", font=("Arial", 8))

            # 垂直標籤 (版本號)
            for i, version in enumerate(versions):
                if i < len(trend_data):  # 確保有對應的資料點
                    x = 20 + i * (380 / (len(versions) - 1 if len(versions) > 1 else 1))
                    trend_canvas.create_text(x, 130, text=version, anchor="n", fill="white", font=("Arial", 8))

            # 繪製趨勢線
            points = []
            max_value = max(trend_data)
            min_value = min(trend_data)
            range_value = max(10, max_value - min_value + 10)  # 確保有適當的範圍

            for i, value in enumerate(trend_data):
                x = 20 + i * (380 / (len(trend_data) - 1 if len(trend_data) > 1 else 1))
                y = 120 - ((value - min_value) / range_value) * 100
                points.append((x, y))

            if len(points) > 1:
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
        self.create_runes_section(recommendations_frame)

        # 裝備建議
        self.create_items_section(recommendations_frame)

        # 技能加點順序
        self.create_skills_section(recommendations_frame)

        # ARAM 攻略要點
        self.create_tips_section(recommendations_frame)

    def create_runes_section(self, parent):
        """創建符文配置區域"""
        runes = self.champion_data.get('runes', [])

        if not runes:
            return

        # 使用第一個符文配置
        rune_data = runes[0] if runes else {}

        runes_title = tk.Label(
            parent,
            text=f"符文配置 (勝率: {rune_data.get('runes_win_rate', 0)}%)",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        runes_title.pack(anchor="w", padx=20, pady=(20, 0))

        runes_frame = tk.Frame(parent, bg="#0f3460", height=120)
        runes_frame.pack(fill="x", padx=20, pady=10)

        # 主系符文
        primary_rune_frame = tk.Frame(runes_frame, bg="#16213e", width=50, height=50)
        primary_rune_frame.place(x=40, y=35)

        primary_label = tk.Label(
            runes_frame,
            text=rune_data.get('primary_rune', ''),
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        primary_label.place(x=40, y=90)

        # 次要符文 (簡化版)
        secondary_runes = rune_data.get('secondary_runes', [])
        for i, rune in enumerate(secondary_runes[:3]):  # 限制最多顯示3個
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
        secondary_title_frame = tk.Frame(runes_frame, bg="#16213e", width=40, height=40)
        secondary_title_frame.place(x=280, y=35)

        secondary_title_label = tk.Label(
            runes_frame,
            text=rune_data.get('secondary_path', ''),
            bg="#0f3460",
            fg="white",
            font=("Arial", 8)
        )
        secondary_title_label.place(x=280, y=80)

        # 副系符文選擇
        secondary_choices = rune_data.get('secondary_choices', [])
        for i, choice in enumerate(secondary_choices[:2]):  # 限制最多顯示2個
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
        shards = rune_data.get('shards', [])
        for i, shard in enumerate(shards[:3]):  # 限制最多顯示3個
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

    def create_items_section(self, parent):
        """創建裝備建議區域"""
        builds = self.champion_data.get('builds', [])

        if not builds:
            return

        # 使用第一個裝備配置
        build_data = builds[0] if builds else {}

        items_title = tk.Label(
            parent,
            text="最佳裝備構建",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        items_title.pack(anchor="w", padx=20, pady=(20, 0))

        items_frame = tk.Frame(parent, bg="#0f3460", height=110)
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

        starting_items = build_data.get('starting_items', [])
        for i, item in enumerate(starting_items[:2]):  # 限制最多顯示2個
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

        core_items = build_data.get('core_items', [])
        for i, item in enumerate(core_items[:4]):  # 限制最多顯示4個
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

        optional_items = build_data.get('optional_items', [])
        for i, item in enumerate(optional_items[:4]):  # 限制最多顯示4個
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
            text=f"{build_data.get('build_win_rate', 0)}%",
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10, "bold")
        )
        win_rate_value.place(x=120, y=90)

    def create_skills_section(self, parent):
        """創建技能加點順序區域"""
        skills = self.champion_data.get('skills', {})

        skills_title = tk.Label(
            parent,
            text="技能加點順序",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        skills_title.pack(anchor="w", padx=20, pady=(20, 0))

        skills_frame = tk.Frame(parent, bg="#0f3460", height=80)
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
            text=f"加點順序: {skills.get('skill_order', 'R > Q > W > E')}",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        order_label.place(x=240, y=20)

        first_label = tk.Label(
            skills_frame,
            text=f"首選: {skills.get('first_skill', 'Q')}",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10)
        )
        first_label.place(x=240, y=45)

    def create_tips_section(self, parent):
        """創建攻略要點區域"""
        tips = self.champion_data.get('tips', [])

        tips_title = tk.Label(
            parent,
            text="ARAM 攻略要點",
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold")
        )
        tips_title.pack(anchor="w", padx=20, pady=(20, 0))

        tips_frame = tk.Frame(parent, bg="#0f3460", height=80)
        tips_frame.pack(fill="x", padx=20, pady=10)

        # 攻略要點
        for i, tip in enumerate(tips[:3]):  # 限制最多顯示3個提示
            tip_label = tk.Label(
                tips_frame,
                text=tip,
                bg="#0f3460",
                fg="white",
                font=("Arial", 10),
                anchor="w"
            )
            tip_label.place(x=20, y=15 + i * 25)

    def _is_destroyed(self):
        """檢查視窗是否已被銷毀"""
        try:
            return not self.winfo_exists()
        except:
            return True