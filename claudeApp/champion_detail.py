import tkinter as tk
import logging
import threading
from typing import Dict, Any, Optional
from PIL import Image, ImageTk
from pathlib import Path
import os

from api_client import AramAPIClient
from rounded_widgets import RoundedFrame, RoundedButton
from utils.chart_utils import ChartGenerator

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
        self.main_container = RoundedFrame(
            self,
            bg_color="#1a1a2e",
            corner_radius=10,
            border_width=0
        )
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 顯示載入指示器
        self.show_loading()

        # 載入英雄詳細資料
        self.champion_data = None
        self.load_champion_detail()

    def create_loading_indicator(self):
        """創建載入指示器"""
        self.loading_frame = tk.Frame(self, bg="#1a1a2e")

        # 創建更現代的載入指示器
        loading_container = tk.Frame(self.loading_frame, bg="#1a1a2e", padx=20, pady=20)
        loading_container.pack(expand=True)

        # 加入轉動動畫效果
        self.loading_dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_dot = 0

        self.loading_label = tk.Label(
            loading_container,
            text=f"{self.loading_dots[0]} 載入中...",
            bg="#1a1a2e",
            fg="#e94560",
            font=("Arial", 14, "bold")
        )
        self.loading_label.pack(pady=20)

        # 初始時不顯示載入指示器
        self.loading_frame.pack_forget()

    def show_loading(self):
        """顯示載入指示器"""
        self.loading = True
        self.main_container.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

        # 啟動載入動畫
        def animate_loading():
            self.current_dot = (self.current_dot + 1) % len(self.loading_dots)
            self.loading_label.config(text=f"{self.loading_dots[self.current_dot]} 載入中...")
            self.animation_after_id = self.after(150, animate_loading)

        # 取消先前的動畫（如果有）
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.after_cancel(self.animation_after_id)

        # 啟動新的動畫
        animate_loading()

    def hide_loading(self):
        """隱藏載入指示器"""
        self.loading = False

        # 停止載入動畫
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.after_cancel(self.animation_after_id)
            self.animation_after_id = None

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

        # 使用 RoundedFrame 創建英雄資訊框架
        hero_info_frame = RoundedFrame(
            parent,
            bg_color="#16213e",
            corner_radius=10,
            border_width=1,
            border_color="#0f3460"
        )
        hero_info_frame.pack(fill="x", pady=10)
        hero_info_frame.interior.configure(height=120)
        hero_info_frame.interior.pack_propagate(False)

        # 英雄圖示框架 - 使用圓形設計
        icon_frame = RoundedFrame(
            hero_info_frame.interior,
            bg_color="#0f3460",
            corner_radius=30,
            border_width=0
        )
        icon_frame.place(x=30, y=10)
        icon_frame.interior.configure(width=100, height=100)
        icon_frame.interior.pack_propagate(False)

        # 嘗試載入英雄圖示
        champion_id = basic_info.get('champion_id', '')
        champion_key = basic_info.get('key', 0)

        # 檢查控制器是否有champ_images屬性和對應的圖片
        if hasattr(self.controller, 'champ_images'):
            # 優先使用championId查找
            if champion_id in self.controller.champ_images:
                icon = self.controller.champ_images[champion_id]
                icon_label = tk.Label(icon_frame.interior, image=icon, bg="#0f3460")
                icon_label.place(relx=0.5, rely=0.5, anchor="center")
            # 然後嘗試使用key查找
            elif str(champion_key) in self.controller.champ_images:
                icon = self.controller.champ_images[str(champion_key)]
                icon_label = tk.Label(icon_frame.interior, image=icon, bg="#0f3460")
                icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # 英雄名稱
        champion_name = basic_info.get('champion_name', '')
        champion_tw_name = basic_info.get('champion_tw_name', '')
        display_name = champion_name
        if champion_tw_name:
            display_name = f"{champion_name} {champion_tw_name}"

        hero_name = tk.Label(
            hero_info_frame.interior,
            text=display_name,
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 16, "bold")
        )
        hero_name.place(x=150, y=25)

        # 英雄類型和難度
        champion_type = basic_info.get('champion_type', '')
        champion_difficulty = basic_info.get('champion_difficulty', 2)

        # 生成難度星級
        difficulty_stars = "★" * champion_difficulty + "☆" * (3 - champion_difficulty)

        type_text = f"{champion_type} • 難度: {difficulty_stars}"

        hero_type = tk.Label(
            hero_info_frame.interior,
            text=type_text,
            bg="#16213e",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        hero_type.place(x=150, y=55)

        # 英雄等級指示
        rank_frame = RoundedFrame(
            hero_info_frame.interior,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        rank_frame.place(x=950, y=20)
        rank_frame.interior.configure(width=200, height=80)
        rank_frame.interior.pack_propagate(False)

        tier = basic_info.get('tier', '')
        tier_text = f"{tier} 級英雄" if tier else "未分級"

        rank_label = tk.Label(
            rank_frame.interior,
            text=tier_text,
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 14, "bold")
        )
        rank_label.pack(pady=(15, 0))

        rank_desc = tk.Label(
            rank_frame.interior,
            text=basic_info.get('rank_desc', ''),
            bg="#0f3460",
            fg="#4ecca3",
            font=("Microsoft JhengHei", 10)
        )
        rank_desc.pack()

    def create_stats_section(self, parent):
        """創建左側數據顯示區域"""
        stats = self.champion_data.get('stats', {})

        # 使用 RoundedFrame 創建統計資料框架
        stats_frame = RoundedFrame(
            parent,
            bg_color="#16213e",
            corner_radius=10,
            border_width=1,
            border_color="#0f3460"
        )
        stats_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 標題
        title_label = tk.Label(
            stats_frame.interior,
            text="數據表現",
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 14, "bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(stats_frame.interior, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 關鍵數據
        key_stats_frame = RoundedFrame(
            stats_frame.interior,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        key_stats_frame.pack(fill="x", padx=20, pady=10)
        key_stats_frame.interior.configure(height=100)
        key_stats_frame.interior.pack_propagate(False)

        # 勝率
        win_rate_label1 = tk.Label(
            key_stats_frame.interior,
            text="勝率",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        win_rate_label1.place(x=20, y=20)

        win_rate_value = stats.get('win_rate', 0)
        win_rate_color = "#4ecca3" if win_rate_value >= 50 else "#fc5185"

        win_rate_label2 = tk.Label(
            key_stats_frame.interior,
            text=f"{win_rate_value}%",
            bg="#0f3460",
            fg=win_rate_color,
            font=("Microsoft JhengHei", 16, "bold")
        )
        win_rate_label2.place(x=20, y=50)

        # 選用率
        pick_rate_label1 = tk.Label(
            key_stats_frame.interior,
            text="選用率",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        pick_rate_label1.place(x=160, y=20)

        pick_rate_label2 = tk.Label(
            key_stats_frame.interior,
            text=f"{stats.get('pick_rate', 0)}%",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 16, "bold")
        )
        pick_rate_label2.place(x=160, y=50)

        # 禁用率
        ban_rate_label1 = tk.Label(
            key_stats_frame.interior,
            text="禁用率",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        ban_rate_label1.place(x=300, y=20)

        ban_rate_label2 = tk.Label(
            key_stats_frame.interior,
            text=f"{stats.get('ban_rate', 0)}%",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 16, "bold")
        )
        ban_rate_label2.place(x=300, y=50)

        # 表現指標
        metrics_frame = RoundedFrame(
            stats_frame.interior,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        metrics_frame.pack(fill="x", padx=20, pady=10)
        metrics_frame.interior.configure(height=160)
        metrics_frame.interior.pack_propagate(False)

        metrics_title = tk.Label(
            metrics_frame.interior,
            text="平均表現 (每場比賽)",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 12, "bold")
        )
        metrics_title.place(x=20, y=20)

        # KDA
        kda_label1 = tk.Label(
            metrics_frame.interior,
            text="KDA:",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        kda_label1.place(x=20, y=50)

        kda_label2 = tk.Label(
            metrics_frame.interior,
            text=stats.get("kda", "0/0/0"),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        kda_label2.place(x=110, y=50)

        kda_ratio = stats.get('kda_ratio', 0)
        kda_color = "#4ecca3" if kda_ratio >= 3.0 else ("#ffd369" if kda_ratio >= 2.0 else "#fc5185")

        kda_ratio_label = tk.Label(
            metrics_frame.interior,
            text=f"KDA比: {kda_ratio}",
            bg="#0f3460",
            fg=kda_color,
            font=("Microsoft JhengHei", 10, "bold")
        )
        kda_ratio_label.place(x=260, y=50)

        # 輸出傷害
        damage_label1 = tk.Label(
            metrics_frame.interior,
            text="輸出傷害:",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        damage_label1.place(x=20, y=80)

        damage_label2 = tk.Label(
            metrics_frame.interior,
            text=stats.get("damage", "0"),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        damage_label2.place(x=110, y=80)

        damage_ratio = tk.Label(
            metrics_frame.interior,
            text=f"隊伍占比: {stats.get('damage_percentage', '0%')}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        damage_ratio.place(x=260, y=80)

        # 治療量
        healing_label1 = tk.Label(
            metrics_frame.interior,
            text="治療量:",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        healing_label1.place(x=20, y=110)

        healing_label2 = tk.Label(
            metrics_frame.interior,
            text=stats.get("healing", "0"),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        healing_label2.place(x=110, y=110)

        healing_ratio = tk.Label(
            metrics_frame.interior,
            text=f"隊伍占比: {stats.get('healing_percentage', '0%')}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        healing_ratio.place(x=260, y=110)

        # 承受傷害
        taken_label1 = tk.Label(
            metrics_frame.interior,
            text="承受傷害:",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        taken_label1.place(x=20, y=140)

        taken_label2 = tk.Label(
            metrics_frame.interior,
            text=stats.get("damage_taken", "0"),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        taken_label2.place(x=110, y=140)

        taken_ratio = tk.Label(
            metrics_frame.interior,
            text=f"隊伍占比: {stats.get('damage_taken_percentage', '0%')}",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        taken_ratio.place(x=260, y=140)

        # 勝率趨勢
        trend_title = tk.Label(
            stats_frame.interior,
            text=f"勝率趨勢 (最近{len(stats.get('trend_versions', []))}個版本)",
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 12, "bold")
        )
        trend_title.pack(anchor="w", padx=20, pady=(20, 0))

        trend_frame = RoundedFrame(
            stats_frame.interior,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        trend_frame.pack(fill="x", padx=20, pady=10)
        trend_frame.interior.configure(height=250)  # 增加高度
        trend_frame.interior.pack_propagate(False)

        # 使用ChartGenerator生成趨勢圖
        chart_generator = ChartGenerator()
        champion_name = self.champion_data.get('basic_info', {}).get('champion_name', '')
        trend_data = stats.get("trend_data", [])
        versions = stats.get("trend_versions", [])

        if trend_data and versions:
            # 生成趨勢圖
            chart_path = chart_generator.create_trend_chart(trend_data, versions, champion_name)
            
            # 載入並顯示圖片
            try:
                image = Image.open(chart_path)
                # 調整圖片大小以適應框架，保持寬高比
                display_width = 500  # 增加顯示寬度
                ratio = image.size[1] / image.size[0]
                display_height = int(display_width * ratio)
                
                image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # 創建標籤顯示圖片
                image_label = tk.Label(
                    trend_frame.interior,
                    image=photo,
                    bg="#0f3460"
                )
                image_label.image = photo  # 保持引用
                image_label.pack(pady=10)
            except Exception as e:
                logger.error(f"載入趨勢圖失敗: {str(e)}")
                error_label = tk.Label(
                    trend_frame.interior,
                    text="無法載入趨勢圖",
                    bg="#0f3460",
                    fg="#e94560",
                    font=("Microsoft JhengHei", 10)
                )
                error_label.pack(pady=10)
        else:
            no_data_label = tk.Label(
                trend_frame.interior,
                text="暫無趨勢數據",
                bg="#0f3460",
                fg="#8b8b8b",
                font=("Microsoft JhengHei", 10)
            )
            no_data_label.pack(pady=10)

    def create_recommendations_section(self, parent):
        """創建右側推薦區域"""
        # 使用 RoundedFrame 創建推薦框架
        recommendations_frame = RoundedFrame(
            parent,
            bg_color="#16213e",
            corner_radius=10,
            border_width=1,
            border_color="#0f3460"
        )
        recommendations_frame.pack(side="right", fill="both", expand=True)

        # 標題
        title_label = tk.Label(
            recommendations_frame.interior,
            text="推薦構建",
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 14, "bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(recommendations_frame.interior, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 符文配置
        self.create_runes_section(recommendations_frame.interior)

        # 裝備建議
        self.create_items_section(recommendations_frame.interior)

        # 技能加點順序
        self.create_skills_section(recommendations_frame.interior)

        # ARAM 攻略要點
        self.create_tips_section(recommendations_frame.interior)

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
            font=("Microsoft JhengHei", 12, "bold")
        )
        runes_title.pack(anchor="w", padx=20, pady=(20, 0))

        # 使用 RoundedFrame 創建符文框架
        runes_frame = RoundedFrame(
            parent,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        runes_frame.pack(fill="x", padx=20, pady=10)
        runes_frame.interior.configure(height=120)
        runes_frame.interior.pack_propagate(False)

        def load_rune_image(rune_id):
            """載入符文圖片"""
            try:
                # 使用绝对路径
                image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "runes", f"{rune_id}.png")
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    return ImageTk.PhotoImage(image)
            except Exception as e:
                logger.error(f"載入符文圖片失敗 {rune_id}: {e}")
            return None

        # 主系符文
        primary_rune_frame = RoundedFrame(
            runes_frame.interior,
            bg_color="#16213e",
            corner_radius=25,
            border_width=0
        )
        primary_rune_frame.place(x=40, y=35)
        primary_rune_frame.interior.configure(width=50, height=50)
        primary_rune_frame.interior.pack_propagate(False)

        # 載入主系符文圖片
        primary_path_id = rune_data.get('primary_path_id')
        if primary_path_id:
            primary_photo = load_rune_image(primary_path_id)
            if primary_photo:
                primary_label = tk.Label(
                    primary_rune_frame.interior,
                    image=primary_photo,
                    bg="#16213e"
                )
                primary_label.image = primary_photo  # 保持引用
                primary_label.place(relx=0.5, rely=0.5, anchor="center")

        primary_text_label = tk.Label(
            runes_frame.interior,
            text=rune_data.get('primary_rune', ''),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 8)
        )
        primary_text_label.place(x=40, y=90)

        # 次要符文
        secondary_runes = rune_data.get('secondary_runes', [])
        secondary_rune_ids = rune_data.get('secondary_rune_ids', [])
        
        for i, (rune_name, rune_id) in enumerate(zip(secondary_runes[:3], secondary_rune_ids[:3])):
            rune_frame = RoundedFrame(
                runes_frame.interior,
                bg_color="#16213e",
                corner_radius=15,
                border_width=0
            )
            rune_frame.place(x=100 + i * 50, y=35)
            rune_frame.interior.configure(width=30, height=30)
            rune_frame.interior.pack_propagate(False)

            # 載入次要符文圖片
            rune_photo = load_rune_image(rune_id)
            if rune_photo:
                rune_label = tk.Label(
                    rune_frame.interior,
                    image=rune_photo,
                    bg="#16213e"
                )
                rune_label.image = rune_photo  # 保持引用
                rune_label.place(relx=0.5, rely=0.5, anchor="center")

            rune_text_label = tk.Label(
                runes_frame.interior,
                text=rune_name,
                bg="#0f3460",
                fg="white",
                font=("Microsoft JhengHei", 8)
            )
            rune_text_label.place(x=100 + i * 50, y=70, anchor="center")

        # 副系符文
        secondary_path_frame = RoundedFrame(
            runes_frame.interior,
            bg_color="#16213e",
            corner_radius=20,
            border_width=0
        )
        secondary_path_frame.place(x=280, y=35)
        secondary_path_frame.interior.configure(width=40, height=40)
        secondary_path_frame.interior.pack_propagate(False)

        # 載入副系符文圖片
        secondary_path_id = rune_data.get('secondary_path_id')
        if secondary_path_id:
            secondary_path_photo = load_rune_image(secondary_path_id)
            if secondary_path_photo:
                secondary_path_label = tk.Label(
                    secondary_path_frame.interior,
                    image=secondary_path_photo,
                    bg="#16213e"
                )
                secondary_path_label.image = secondary_path_photo  # 保持引用
                secondary_path_label.place(relx=0.5, rely=0.5, anchor="center")

        secondary_path_text = tk.Label(
            runes_frame.interior,
            text=rune_data.get('secondary_path', ''),
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 8)
        )
        secondary_path_text.place(x=280, y=80)

        # 副系符文選擇
        secondary_choices = rune_data.get('secondary_choices', [])
        secondary_choice_ids = rune_data.get('secondary_choice_ids', [])
        
        for i, (choice_name, choice_id) in enumerate(zip(secondary_choices[:2], secondary_choice_ids[:2])):
            choice_frame = RoundedFrame(
                runes_frame.interior,
                bg_color="#16213e",
                corner_radius=15,
                border_width=0
            )
            choice_frame.place(x=330 + i * 50, y=35)
            choice_frame.interior.configure(width=30, height=30)
            choice_frame.interior.pack_propagate(False)

            # 載入副系選擇符文圖片
            choice_photo = load_rune_image(choice_id)
            if choice_photo:
                choice_label = tk.Label(
                    choice_frame.interior,
                    image=choice_photo,
                    bg="#16213e"
                )
                choice_label.image = choice_photo  # 保持引用
                choice_label.place(relx=0.5, rely=0.5, anchor="center")

            choice_text = tk.Label(
                runes_frame.interior,
                text=choice_name,
                bg="#0f3460",
                fg="white",
                font=("Microsoft JhengHei", 8)
            )
            choice_text.place(x=330 + i * 50, y=70, anchor="center")

        # 符文碎片
        shards = rune_data.get('shards', [])
        shard_ids = rune_data.get('shard_ids', [])
        
        for i, (shard_name, shard_id) in enumerate(zip(shards[:3], shard_ids[:3])):
            shard_frame = RoundedFrame(
                runes_frame.interior,
                bg_color="#16213e",
                corner_radius=7,
                border_width=0
            )
            shard_frame.place(x=430, y=20 + i * 20)
            shard_frame.interior.configure(width=15, height=15)
            shard_frame.interior.pack_propagate(False)

            # 載入符文碎片圖片
            shard_photo = load_rune_image(shard_id)
            if shard_photo:
                shard_label = tk.Label(
                    shard_frame.interior,
                    image=shard_photo,
                    bg="#16213e"
                )
                shard_label.image = shard_photo  # 保持引用
                shard_label.place(relx=0.5, rely=0.5, anchor="center")

            shard_text = tk.Label(
                runes_frame.interior,
                text=shard_name,
                bg="#0f3460",
                fg="white",
                font=("Microsoft JhengHei", 8)
            )
            shard_text.place(x=455, y=20 + i * 20)

    def create_items_section(self, parent):
        """創建裝備建議區域"""
        builds = self.champion_data.get('builds', [])

        if not builds:
            return

        # 使用第一個裝備配置
        build_data = builds[0] if builds else {}

        items_title = tk.Label(
            parent,
            text=f"最佳裝備構建 (勝率: {build_data.get('build_win_rate', 0)}%)",
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 12, "bold")
        )
        items_title.pack(anchor="w", padx=20, pady=(20, 0))

        # 使用 RoundedFrame 創建裝備框架
        items_frame = RoundedFrame(
            parent,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        items_frame.pack(fill="x", padx=20, pady=10)
        items_frame.interior.configure(height=160)
        items_frame.interior.pack_propagate(False)

        def load_item_image(item_id):
            """載入裝備圖片"""
            try:
                # 使用绝对路径
                image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "items", f"{item_id}.png")
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    # 調整圖片大小
                    image = image.resize((40, 40), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(image)
            except Exception as e:
                logger.error(f"載入裝備圖片失敗 {item_id}: {e}")
            return None

        def create_item_frame(parent, item_id, x, y, show_win_rate=False):
            """創建單個裝備框架"""
            frame = RoundedFrame(
                parent,
                bg_color="#16213e",
                corner_radius=5,
                border_width=1,
                border_color="#1a1a2e"
            )
            frame.place(x=x, y=y)
            frame.interior.configure(width=45, height=45)
            frame.interior.pack_propagate(False)

            # 載入裝備圖片
            if item_id:
                item_photo = load_item_image(item_id)
                if item_photo:
                    item_label = tk.Label(
                        frame.interior,
                        image=item_photo,
                        bg="#16213e"
                    )
                    item_label.image = item_photo  # 保持引用
                    item_label.place(relx=0.5, rely=0.5, anchor="center")

                    if show_win_rate and 'item_win_rates' in build_data:
                        win_rate = build_data['item_win_rates'].get(str(item_id), 0)
                        if win_rate > 0:
                            win_rate_label = tk.Label(
                                frame.interior,
                                text=f"{win_rate}%",
                                bg="#16213e",
                                fg="#4ecca3",
                                font=("Microsoft JhengHei", 8)
                            )
                            win_rate_label.place(relx=0.5, rely=0.9, anchor="center")

            return frame

        # 起始裝備
        start_label = tk.Label(
            items_frame.interior,
            text="起始裝備",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        start_label.place(x=20, y=10)

        starting_items = build_data.get('starting_items', [])
        for i, item in enumerate(starting_items[:2]):
            create_item_frame(items_frame.interior, item, 20 + i * 55, 35)

        # 核心裝備
        core_label = tk.Label(
            items_frame.interior,
            text="核心裝備",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        core_label.place(x=150, y=10)

        core_items = build_data.get('core_items', [])
        for i, item in enumerate(core_items[:3]):
            create_item_frame(items_frame.interior, item, 150 + i * 55, 35, show_win_rate=True)

        # 可選裝備
        optional_label = tk.Label(
            items_frame.interior,
            text="情況選擇",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Microsoft JhengHei", 10)
        )
        optional_label.place(x=20, y=90)

        optional_items = build_data.get('optional_items', [])
        for i, item in enumerate(optional_items[:6]):
            row = i // 3
            col = i % 3
            create_item_frame(items_frame.interior, item, 20 + col * 55, 115 + row * 55, show_win_rate=True)

        # 如果沒有裝備數據，顯示提示文字
        if not any([starting_items, core_items, optional_items]):
            no_data_label = tk.Label(
                items_frame.interior,
                text="暫無裝備數據",
                bg="#0f3460",
                fg="#8b8b8b",
                font=("Microsoft JhengHei", 12)
            )
            no_data_label.place(relx=0.5, rely=0.5, anchor="center")

    def create_skills_section(self, parent):
        """創建技能加點順序區域"""
        skills = self.champion_data.get('skills', {})

        skills_title = tk.Label(
            parent,
            text="技能加點順序",
            bg="#16213e",
            fg="white",
            font=("Microsoft JhengHei", 12, "bold")
        )
        skills_title.pack(anchor="w", padx=20, pady=(20, 0))

        # 使用 RoundedFrame 創建技能框架
        skills_frame = RoundedFrame(
            parent,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        skills_frame.pack(fill="x", padx=20, pady=10)
        skills_frame.interior.configure(height=80)
        skills_frame.interior.pack_propagate(False)

        # 技能按鈕
        skill_labels = ["Q", "W", "E", "R"]
        for i, skill in enumerate(skill_labels):
            skill_frame = RoundedFrame(
                skills_frame.interior,
                bg_color="#16213e",
                corner_radius=20,
                border_width=0
            )
            skill_frame.place(x=20 + i * 50, y=20)
            skill_frame.interior.configure(width=40, height=40)
            skill_frame.interior.pack_propagate(False)

            skill_label = tk.Label(
                skill_frame.interior,
                text=skill,
                bg="#16213e",
                fg="white",
                font=("Microsoft JhengHei", 12, "bold")
            )
            skill_label.place(relx=0.5, rely=0.5, anchor="center")

        # 加點說明
        order_label = tk.Label(
            skills_frame.interior,
            text=f"加點順序: {skills.get('skill_order', 'R > Q > W > E')}",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
        )
        order_label.place(x=240, y=20)

        first_label = tk.Label(
            skills_frame.interior,
            text=f"首選: {skills.get('first_skill', 'Q')}",
            bg="#0f3460",
            fg="white",
            font=("Microsoft JhengHei", 10)
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
            font=("Microsoft JhengHei", 12, "bold")
        )
        tips_title.pack(anchor="w", padx=20, pady=(20, 0))

        # 使用 RoundedFrame 創建提示框架
        tips_frame = RoundedFrame(
            parent,
            bg_color="#0f3460",
            corner_radius=5,
            border_width=0
        )
        tips_frame.pack(fill="x", padx=20, pady=10)
        tips_frame.interior.configure(height=80)
        tips_frame.interior.pack_propagate(False)

        # 攻略要點
        for i, tip in enumerate(tips[:3]):  # 限制最多顯示3個提示
            tip_label = tk.Label(
                tips_frame.interior,
                text=tip,
                bg="#0f3460",
                fg="white",
                font=("Microsoft JhengHei", 10),
                anchor="w"
            )
            tip_label.place(x=20, y=15 + i * 25)

    def _is_destroyed(self):
        """檢查視窗是否已被銷毀"""
        try:
            return not self.winfo_exists()
        except:
            return True