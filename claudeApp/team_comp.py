import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, font

# 導入 API 相關模組
from apiWorker import recommend_compositions_api, recommend_worst_compositions_api
# 導入圓角小部件
from rounded_widgets import RoundedFrame, RoundedButton


class TeamCompFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller
        self.root = controller.root  # 存儲根窗口，用於後續 after 方法

        # 獲取 fetcher 實例（如果控制器有的話）
        self.fetcher = None
        if hasattr(controller, 'fetcher'):
            self.fetcher = controller.fetcher

        # 設置字體
        self.setup_fonts()

        # 設置圓角半徑
        self.corner_radius = 10  # 預設圓角半徑
        if hasattr(controller, 'corner_radius'):
            self.corner_radius = controller.corner_radius

        # 已選英雄和推薦陣容數據
        self.recommendation_data = []
        self.worst_recommendation_data = []  # 添加最不推薦陣容數據屬性

        # 創建兩欄佈局
        self.create_two_column_layout()

        # 載入資料
        self.load_team_comp_data()

    def create_current_comp_winrate_section(self):
        """創建當前陣容勝率區塊"""
        # 標題
        title_label = tk.Label(
            self.left_panel.interior,
            text="當前陣容勝率",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 12),
            anchor="w"
        )
        title_label.pack(anchor="w", padx=20, pady=(15, 0))

        # 分隔線
        separator = tk.Frame(self.left_panel.interior, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 勝率顯示框架
        self.current_winrate_frame = RoundedFrame(
            self.left_panel.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius,
            height=60
        )
        self.current_winrate_frame.pack(fill="x", padx=20, pady=10)

        # 勝率標籤
        self.current_winrate_label = tk.Label(
            self.current_winrate_frame.interior,
            text="計算中...",
            bg="#0f3460",
            fg="#4ecca3",
            font=(self.font_family_bold, 16),
            height=2
        )
        self.current_winrate_label.pack(fill="both", expand=True)

    def setup_fonts(self):
        """設置字體"""
        # 從控制器獲取字體家族 (如果有的話)
        if hasattr(self.controller, 'font_family'):
            self.font_family = self.controller.font_family
            self.font_family_bold = self.controller.font_family_bold
            self.font_family_medium = self.controller.font_family_medium
        else:
            # 優先選擇微軟正黑體
            self.font_family = "Microsoft JhengHei UI"
            self.font_family_bold = "Microsoft JhengHei UI"
            self.font_family_medium = "Microsoft JhengHei UI"

            # 檢查系統中可用的字體
            available_fonts = font.families()

            # 如果微軟正黑體不可用，尋找其他中文字體
            if self.font_family not in available_fonts:
                font_options = [
                    "Microsoft JhengHei", "Noto Sans TC", "Microsoft YaHei UI",
                    "PingFang TC", "Heiti TC", "SimHei", "Arial Unicode MS", "Arial"
                ]

                for option in font_options:
                    if option in available_fonts:
                        self.font_family = option
                        self.font_family_bold = option
                        self.font_family_medium = option
                        break

            # 如果仍然沒有找到合適的字體，使用默認字體
            if self.font_family not in available_fonts:
                self.font_family = "TkDefaultFont"
                self.font_family_bold = "TkDefaultFont"
                self.font_family_medium = "TkDefaultFont"

    def create_two_column_layout(self):
        """創建兩欄佈局"""
        # 左側面板 - 選擇英雄和可用英雄池
        self.left_panel = RoundedFrame(
            self,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            width=360,
            height=700
        )
        self.left_panel.interior.config(width=360, height=700)
        self.left_panel.pack(side="left", fill="both", expand=False, padx=10, pady=10)
        self.left_panel.pack_propagate(False)  # 防止框架自動調整大小

        # 已選英雄部分
        self.create_selected_champions_section()

        self.create_current_comp_winrate_section()

        # 可用英雄池部分
        self.create_available_champions_section()

        # 右側面板 - 推薦陣容和其他分析
        self.right_panel = RoundedFrame(
            self,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            width=780,
            height=700
        )
        self.right_panel.interior.config(width=780, height=700)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 創建選項卡
        self.create_tabs()

    def create_selected_champions_section(self):
        """創建已選英雄部分"""
        # 標題
        title_label = tk.Label(
            self.left_panel.interior,
            text="已選英雄",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 12),
            anchor="w"
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(self.left_panel.interior, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 已選英雄網格
        self.selected_champions_frame = tk.Frame(self.left_panel.interior, bg="#16213e", height=100)
        self.selected_champions_frame.pack(fill="x", padx=20, pady=10)

        # 創建5個圓角空位置
        self.selected_champion_slots = []
        for i in range(5):
            # 創建固定大小的圓角框架
            champion_frame = RoundedFrame(
                self.selected_champions_frame,
                bg_color="#0f3460",
                corner_radius=self.corner_radius,
                width=55,
                height=90
            )
            champion_frame.grid(row=0, column=i, padx=5, pady=5)
            champion_frame.grid_propagate(False)  # 防止調整大小

            # 確保內部框架不會覆蓋圓角
            champion_frame.interior.config(width=55, height=90, bg="#0f3460")

            # 頭像圓圈 - 增加大小
            icon_canvas = tk.Canvas(
                champion_frame.interior,
                width=40,
                height=40,
                bg="#0f3460",
                highlightthickness=0
            )
            icon_canvas.create_oval(5, 5, 35, 35, fill="#16213e", outline="#16213e")
            icon_canvas.pack(pady=(5, 0))

            # 名稱標籤 - 固定高度并自動調整字體大小
            name_frame = RoundedFrame(
                champion_frame.interior,
                bg_color="#0f3460",
                corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                width=55,
                height=30
            )
            name_frame.interior.config(width=55, height=30)
            name_frame.pack(fill="x", expand=True, pady=2)
            name_frame.pack_propagate(False)  # 防止調整大小

            name_label = tk.Label(
                name_frame.interior,
                text="",
                bg="#0f3460",
                fg="white",
                font=(self.font_family, 8),
                wraplength=50  # 允許文字換行
            )
            name_label.pack(fill="both", expand=True)

            self.selected_champion_slots.append({
                "frame": champion_frame,
                "canvas": icon_canvas,
                "label": name_label,
                "selected": False,
                "champion_id": None,
                "champion_name": None,
                "image_id": None
            })

    def create_available_champions_section(self):
        """創建可用英雄池部分"""
        # 標題
        title_label = tk.Label(
            self.left_panel.interior,
            text="可用英雄池",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 12),
            anchor="w"
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 0))

        # 分隔線
        separator = tk.Frame(self.left_panel.interior, bg="#e94560", height=1)
        separator.pack(fill="x", padx=20, pady=5)

        # 創建圓角捲動區域的容器
        self.available_container = RoundedFrame(
            self.left_panel.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        self.available_container.pack(fill="both", expand=True, padx=20, pady=10)

        # 創建 Canvas 和捲動條
        self.canvas = tk.Canvas(
            self.available_container.interior,
            bg="#16213e",
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.available_container.interior,
            orient="vertical",
            command=self.canvas.yview
        )

        # 配置佈局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 將 canvas 連接到捲動條
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 創建內部框架來放置英雄網格
        self.available_champions_frame = tk.Frame(self.canvas, bg="#16213e")
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.available_champions_frame, anchor="nw")

        # 更新捲動區域
        self.available_champions_frame.bind("<Configure>", self.update_scrollregion)
        self.canvas.bind("<Configure>", self.update_canvas_width)

        # 英雄網格將在 update_available_champions 方法中動態創建
        self.available_champion_slots = []

    def update_scrollregion(self, event):
        """更新捲動區域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_canvas_width(self, event):
        """更新 Canvas 寬度以適應容器"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def create_tabs(self):
        """創建選項卡"""
        # 選項卡框架
        self.tabs_frame = RoundedFrame(
            self.right_panel.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        self.tabs_frame.pack(fill="x", pady=(0, 10))

        # 選項卡按鈕
        self.tab_buttons = {}
        tab_options = ["推薦陣容", "最不推薦陣容", "即時勝率分析"]
        # tab_options = ["推薦陣容", "最不推薦陣容", "即時勝率分析", "測試即時數據"]

        for i, option in enumerate(tab_options):
            button = RoundedButton(
                self.tabs_frame.interior,
                text=option,
                bg="#0f3460" if i == 0 else "#16213e",
                fg="white",
                highlight_color="#e94560",
                command=lambda o=option: self.switch_tab(o),
                font=(self.font_family, 10),
                radius=self.corner_radius,
                padx=15,
                pady=5,
                width=150,
                height=30
            )
            button.grid(row=0, column=i, padx=5, pady=5)
            self.tab_buttons[option] = button

        # 內容框架
        self.content_frame = RoundedFrame(
            self.right_panel.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        self.content_frame.pack(fill="both", expand=True)

        # 預設顯示推薦陣容
        self.create_recommendation_tab()

    def switch_tab(self, tab_name):
        """切換選項卡"""
        # 更新按鈕樣式
        for name, button in self.tab_buttons.items():
            if name == tab_name:
                button.configure(bg="#0f3460")
            else:
                button.configure(bg="#16213e")

        # 清除內容框架
        for widget in self.content_frame.interior.winfo_children():
            widget.destroy()

        # 根據選項卡顯示內容
        if tab_name == "推薦陣容":
            self.create_recommendation_tab()
        elif tab_name == "最不推薦陣容":
            self.create_worst_recommendation_tab()
        elif tab_name == "即時勝率分析":
            self.create_live_winrate_tab()
        elif tab_name == "測試即時數據":
            self.create_test_data_tab()

    def create_recommendation_tab(self):
        """創建推薦陣容選項卡"""
        # 創建表格
        table_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 表頭
        header_frame = RoundedFrame(
            table_frame.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=40
        )
        header_frame.interior.config(height=40)
        header_frame.pack(fill="x")

        # 勝率列
        win_rate_header = tk.Label(
            header_frame.interior,
            text="勝率",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=10,
            height=2
        )
        win_rate_header.pack(side="left", padx=(20, 0))

        # 陣容組合列
        comp_header = tk.Label(
            header_frame.interior,
            text="陣容組合",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=50,
            height=2
        )
        comp_header.pack(side="left", fill="x", expand=True)

        # 創建捲動容器
        scroll_container = RoundedFrame(
            table_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        scroll_container.pack(fill="both", expand=True)

        # 創建 Canvas 和捲動條
        canvas = tk.Canvas(
            scroll_container.interior,
            bg="#0f3460",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_container.interior,
            orient="vertical",
            command=canvas.yview
        )

        # 配置佈局
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 將 canvas 連接到捲動條
        canvas.configure(yscrollcommand=scrollbar.set)

        # 創建內部框架來放置表格內容
        self.table_content_frame = tk.Frame(canvas, bg="#0f3460")
        canvas_frame = canvas.create_window((0, 0), window=self.table_content_frame, anchor="nw")

        # 更新捲動區域
        self.table_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # 添加表格行
        self.update_recommendation_table()

    # 最不推薦陣容 架構和推薦陣容一樣 只是API_URL換成predict_worst_team

    def create_worst_recommendation_tab(self):
        """創建最不推薦陣容選項卡"""
        # 創建表格
        table_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 表頭
        header_frame = RoundedFrame(
            table_frame.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=40
        )
        header_frame.interior.config(height=40)
        header_frame.pack(fill="x")

        # 勝率列
        win_rate_header = tk.Label(
            header_frame.interior,
            text="勝率",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=10,
            height=2
        )
        win_rate_header.pack(side="left", padx=(20, 0))

        # 陣容組合列
        comp_header = tk.Label(
            header_frame.interior,
            text="陣容組合",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=50,
            height=2
        )
        comp_header.pack(side="left", fill="x", expand=True)

        # 創建捲動容器
        scroll_container = RoundedFrame(
            table_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        scroll_container.pack(fill="both", expand=True)

        # 創建 Canvas 和捲動條
        canvas = tk.Canvas(
            scroll_container.interior,
            bg="#0f3460",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_container.interior,
            orient="vertical",
            command=canvas.yview
        )

        # 配置佈局
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 將 canvas 連接到捲動條
        canvas.configure(yscrollcommand=scrollbar.set)

        # 創建內部框架來放置表格內容
        self.table_content_frame = tk.Frame(canvas, bg="#0f3460")
        canvas_frame = canvas.create_window((0, 0), window=self.table_content_frame, anchor="nw")

        # 更新捲動區域
        self.table_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # 修復: 添加視窗寬度調整綁定
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # 添加表格行
        self.update_worst_recommendation_table()

    def update_worst_recommendation_table(self):
        """更新最不推薦陣容表格"""
        # 清除現有內容
        for widget in self.table_content_frame.winfo_children():
            widget.destroy()

        # 如果沒有最不推薦數據，顯示提示信息
        if not self.worst_recommendation_data:
            empty_label = tk.Label(
                self.table_content_frame,
                text="請選擇英雄或刷新數據以獲取最不推薦陣容",
                bg="#0f3460",
                fg="white",
                font=(self.font_family, 12),
                height=4
            )
            empty_label.pack(fill="x", pady=20)
            return

        # 添加表格行
        for i, (comp, win_rate) in enumerate(self.worst_recommendation_data):
            # 創建圓角行框架
            row_frame = RoundedFrame(
                self.table_content_frame,
                bg_color="#0c2b52" if i % 2 == 0 else "#0f3460",
                corner_radius=self.corner_radius,
                height=60
            )
            row_frame.interior.config(height=60)
            row_frame.pack(fill="x", pady=2)  # 增加間距使圓角明顯
            row_frame.pack_propagate(False)

            # 勝率
            win_rate_label = tk.Label(
                row_frame.interior,
                text=f"{win_rate:.2%}",
                bg=row_frame.interior["bg"],
                fg="#4ecca3",
                font=(self.font_family_bold, 12),
                width=10,
                height=2
            )
            win_rate_label.pack(side="left", padx=(20, 0))

            # 陣容組合 - 使用更大的區域
            comp_frame = tk.Frame(row_frame.interior, bg=row_frame.interior["bg"])
            comp_frame.pack(side="left", fill="both", expand=True, padx=(10, 10))

            # 英雄圖標和名稱 - 使用固定尺寸的框架
            icons_container = tk.Frame(comp_frame, bg=row_frame.interior["bg"])
            icons_container.pack(side="left", fill="y")

            # 英雄圖標
            for j, champ_name in enumerate(comp):
                # 使用圓角框架
                icon_frame = RoundedFrame(
                    icons_container,
                    bg_color="#16213e",
                    corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                    width=40,
                    height=40
                )
                icon_frame.interior.config(width=40, height=40)
                icon_frame.pack(side="left", padx=3)
                icon_frame.pack_propagate(False)

                # 顯示英雄圖標（如果有）
                image = None
                if hasattr(self.controller, 'champ_images'):
                    if champ_name in self.controller.champ_images:
                        image = self.controller.champ_images[champ_name]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        key = self.fetcher.get_champ_key(champ_name)
                        if key in self.controller.champ_images:
                            image = self.controller.champ_images[key]

                if image:
                    champ_icon = tk.Label(
                        icon_frame.interior,
                        image=image,
                        bg="#16213e",
                        borderwidth=0
                    )
                    champ_icon.image = image  # 保留引用防止垃圾回收
                    champ_icon.pack(fill="both", expand=True)

            # 計算名稱框架的最大寬度
            # 獲取當前窗口寬度
            window_width = self.right_panel.winfo_width()
            if window_width <= 1:  # 如果還沒有實際寬度
                window_width = 780  # 使用默認值

            # 計算名稱區域的最大寬度
            # 減去勝率區域、左右間距和圖標區域的寬度
            max_names_width = window_width - 150 - 40 - 20 - (len(comp) * 46)

            # 名稱區域 - 使用圓角框架
            names_frame = RoundedFrame(
                comp_frame,
                bg_color=row_frame.interior["bg"],
                corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                height=40,
                width=max_names_width
            )
            names_frame.interior.config(height=40, width=max_names_width)
            names_frame.pack(side="left", fill="both", expand=True, padx=(10, 5))
            names_frame.pack_propagate(False)  # 防止大小調整

            # 顯示英雄名稱（以中文顯示）並增加字體大小
            chinese_names = [self._get_display_name(name) for name in comp]
            name_label = tk.Label(
                names_frame.interior,
                text="、".join(chinese_names),
                bg=row_frame.interior["bg"],
                fg="white",
                font=(self.font_family, 11),  # 增加字體大小
                anchor="w",
                justify="left"
            )
            name_label.pack(side="left", fill="both", expand=True)

            # 根據文本長度自動調整字體大小
            self.dynamic_font_resize(name_label, max_names_width, initial_size=11)

    def update_recommendation_table(self):
        """更新推薦陣容表格"""
        # 清除現有內容
        for widget in self.table_content_frame.winfo_children():
            widget.destroy()

        # 如果沒有推薦數據，顯示提示信息
        if not self.recommendation_data:
            empty_label = tk.Label(
                self.table_content_frame,
                text="請選擇英雄或刷新數據以獲取推薦陣容",
                bg="#0f3460",
                fg="white",
                font=(self.font_family, 12),
                height=4
            )
            empty_label.pack(fill="x", pady=20)
            return

        # 添加表格行
        for i, (comp, win_rate) in enumerate(self.recommendation_data):
            # 創建圓角行框架
            row_frame = RoundedFrame(
                self.table_content_frame,
                bg_color="#0c2b52" if i % 2 == 0 else "#0f3460",
                corner_radius=self.corner_radius,
                height=60
            )
            row_frame.interior.config(height=60)
            row_frame.pack(fill="x", pady=2)  # 增加間距使圓角明顯
            row_frame.pack_propagate(False)

            # 勝率
            win_rate_label = tk.Label(
                row_frame.interior,
                text=f"{win_rate:.2%}",
                bg=row_frame.interior["bg"],
                fg="#4ecca3",
                font=(self.font_family_bold, 12),
                width=10,
                height=2
            )
            win_rate_label.pack(side="left", padx=(20, 0))

            # 陣容組合 - 使用更大的區域
            comp_frame = tk.Frame(row_frame.interior, bg=row_frame.interior["bg"])
            comp_frame.pack(side="left", fill="both", expand=True, padx=(10, 10))

            # 英雄圖標和名稱 - 使用固定尺寸的框架
            icons_container = tk.Frame(comp_frame, bg=row_frame.interior["bg"])
            icons_container.pack(side="left", fill="y")

            # 英雄圖標
            for j, champ_name in enumerate(comp):
                # 使用圓角框架
                icon_frame = RoundedFrame(
                    icons_container,
                    bg_color="#16213e",
                    corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                    width=40,
                    height=40
                )
                icon_frame.interior.config(width=40, height=40)
                icon_frame.pack(side="left", padx=3)
                icon_frame.pack_propagate(False)

                # 顯示英雄圖標（如果有）
                image = None
                if hasattr(self.controller, 'champ_images'):
                    if champ_name in self.controller.champ_images:
                        image = self.controller.champ_images[champ_name]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        key = self.fetcher.get_champ_key(champ_name)
                        if key in self.controller.champ_images:
                            image = self.controller.champ_images[key]

                if image:
                    champ_icon = tk.Label(
                        icon_frame.interior,
                        image=image,
                        bg="#16213e",
                        borderwidth=0
                    )
                    champ_icon.image = image  # 保留引用防止垃圾回收
                    champ_icon.pack(fill="both", expand=True)

            # 計算名稱框架的最大寬度
            # 獲取當前窗口寬度
            window_width = self.right_panel.winfo_width()
            if window_width <= 1:  # 如果還沒有實際寬度
                window_width = 780  # 使用默認值

            # 計算名稱區域的最大寬度
            # 減去勝率區域、左右間距和圖標區域的寬度
            max_names_width = window_width - 150 - 40 - 20 - (len(comp) * 46)

            # 名稱區域 - 使用圓角框架
            names_frame = RoundedFrame(
                comp_frame,
                bg_color=row_frame.interior["bg"],
                corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                height=40,
                width=max_names_width
            )
            names_frame.interior.config(height=40, width=max_names_width)
            names_frame.pack(side="left", fill="both", expand=True, padx=(10, 5))
            names_frame.pack_propagate(False)  # 防止大小調整

            # 顯示英雄名稱（以中文顯示）並增加字體大小
            chinese_names = [self._get_display_name(name) for name in comp]
            name_label = tk.Label(
                names_frame.interior,
                text="、".join(chinese_names),
                bg=row_frame.interior["bg"],
                fg="white",
                font=(self.font_family, 11),  # 增加字體大小
                anchor="w",
                justify="left"
            )
            name_label.pack(side="left", fill="both", expand=True)

            # 根據文本長度自動調整字體大小
            self.dynamic_font_resize(name_label, max_names_width, initial_size=11)

    def dynamic_font_resize(self, label, max_width, initial_size=11, min_size=7):
        """根據文本長度和框架寬度動態調整字體大小"""
        text = label.cget("text")
        if not text:
            return

        # 獲取當前字體
        current_font = label.cget("font")
        if isinstance(current_font, str):
            font_name = current_font
        else:
            font_name = current_font[0] if isinstance(current_font, tuple) else self.font_family

        # 創建臨時標籤來測量文本寬度
        test_label = tk.Label(self.root, text=text)
        test_label.pack_forget()  # 不顯示，只用於計算

        size = initial_size
        test_font = font.Font(family=font_name, size=size)
        text_width = test_font.measure(text)

        # 二分法查找合適的字體大小
        while size > min_size and text_width > max_width:
            size -= 1
            test_font = font.Font(family=font_name, size=size)
            text_width = test_font.measure(text)

        # 銷毀測試標籤
        test_label.destroy()

        # 設置新字體
        label.config(font=(font_name, size))

    def create_live_winrate_tab(self):
        """創建即時勝率分析頁面"""
        print("\n=== 開始創建即時勝率分析頁面 ===")

        # 檢查遊戲狀態
        if not self.fetcher:
            print("錯誤: fetcher 未初始化")
            self._create_error_display(error_message="系統未正確初始化")
            return

        print("檢查遊戲狀態...")
        game_status = self.fetcher.check_game_status()
        print(f"遊戲狀態: {game_status}")

        if not game_status:
            print("錯誤: 尚未進入遊戲")
            self._create_error_display(error_message="尚未進入遊戲")
            return

        # 獲取遊戲數據
        print("\n嘗試獲取遊戲數據...")
        try:
            game_data = self.fetcher.fetch_in_game_data()
            print(f"獲取到的遊戲數據: {game_data}")
        except Exception as e:
            print(f"獲取遊戲數據時出錯: {e}")
            self._create_error_display(error_message="無法獲取遊戲數據")
            return

        if not game_data or 'players' not in game_data:
            print("錯誤: 遊戲數據格式不正確")
            print(f"遊戲數據: {game_data}")
            self._create_error_display(error_message="無法獲取遊戲數據")
            return

        # 分離及處理雙方陣容
        print("\n開始處理雙方陣容...")
        blue_team, red_team = self._extract_team_compositions(game_data)
        print(f"藍方陣容: {blue_team}")
        print(f"紅方陣容: {red_team}")

        # 創建團隊顯示UI
        print("\n開始創建團隊顯示UI...")
        self._create_team_display_ui(blue_team, red_team)
        print("=== 即時勝率分析頁面創建完成 ===\n")

    def _extract_team_compositions(self, game_data):
        """從遊戲數據中提取藍方和紅方陣容"""
        print("\n=== 開始提取團隊陣容 ===")

        # 分離雙方陣容
        blue_team = []
        red_team = []

        print("處理玩家數據...")
        for player in game_data['players']:
            print(f"處理玩家: {player}")
            if player['team'] == 'ORDER':
                blue_team.append(player['championName'])
                print(f"藍方英雄: {player['championName']}")
            else:
                red_team.append(player['championName'])
                print(f"紅方英雄: {player['championName']}")

        # 確保每隊最多 5 個英雄
        blue_team = blue_team[:5]
        red_team = red_team[:5]

        print(f"\n最終陣容:")
        print(f"藍方: {blue_team}")
        print(f"紅方: {red_team}")
        print("=== 團隊陣容提取完成 ===\n")

        return blue_team, red_team

    def _create_team_display_ui(self, blue_team, red_team):
        """創建團隊顯示UI"""
        print("\n=== 開始創建團隊顯示UI ===")

        # 創建主框架
        print("創建主框架...")
        main_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0F172A",
            corner_radius=self.corner_radius
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 創建雙方陣容顯示區域
        print("創建陣容顯示區域...")
        teams_frame = tk.Frame(main_frame.interior, bg="#0F172A")
        teams_frame.pack(fill="both", expand=True, pady=10)

        # 創建藍方團隊框架和UI
        print("\n創建藍方團隊框架...")
        blue_frame = self._create_team_frame(teams_frame, "藍方陣營", "#1A2744", "#0F2B5B", "left")

        # 創建紅方團隊框架和UI
        print("創建紅方團隊框架...")
        red_frame = self._create_team_frame(teams_frame, "紅方陣營", "#2A1A1A", "#7F1D1D", "right")

        # 為藍方添加英雄卡片
        print("\n添加藍方英雄卡片...")
        for i, champ in enumerate(blue_team):
            print(f"添加藍方英雄 {i + 1}: {champ}")
            self._create_test_champion_card(blue_frame.interior, champ, "blue", i)

        # 為紅方添加英雄卡片
        print("\n添加紅方英雄卡片...")
        for i, champ in enumerate(red_team):
            print(f"添加紅方英雄 {i + 1}: {champ}")
            self._create_test_champion_card(red_frame.interior, champ, "red", i)

        # 創建勝率顯示框架
        print("\n創建勝率顯示框架...")
        blue_winrate_frame, blue_winrate_label = self._create_test_winrate_display(blue_frame, "blue")
        red_winrate_frame, red_winrate_label = self._create_test_winrate_display(red_frame, "red")

        # 保存引用供後續更新使用
        self.current_winrate_display = {
            "blue_frame": blue_frame,
            "red_frame": red_frame,
            "blue_label": blue_winrate_label,
            "red_label": red_winrate_label
        }

        # 計算並顯示勝率預測
        print("\n開始計算勝率預測...")
        self._calculate_team_winrates(blue_team, red_team)
        print("=== 團隊顯示UI創建完成 ===\n")

    def _create_team_frame(self, parent, title_text, bg_color, title_bg_color, side):
        """創建團隊框架"""
        # 團隊陣容框架
        team_frame = RoundedFrame(
            parent,
            bg_color=bg_color,
            corner_radius=25,
            width=400,
            height=480
        )
        team_frame.pack(side=side, fill="both", expand=True, padx=10)
        team_frame.pack_propagate(False)

        # 標題區域
        title_frame = RoundedFrame(
            team_frame.interior,
            bg_color=title_bg_color,
            corner_radius=15,
            height=50
        )
        title_frame.pack(fill="x", padx=30, pady=(20, 10))
        title_frame.pack_propagate(False)

        # 標題
        title_label = tk.Label(
            title_frame.interior,
            text=title_text,
            bg=title_bg_color,
            fg="white",
            font=(self.font_family_bold, 22)
        )
        title_label.pack(fill="both", expand=True)

        return team_frame

    def create_test_data_tab(self):
        """創建測試即時數據頁面"""
        # 獲取測試數據
        game_data = self.fetcher.fetch_test_data()

        if not game_data or 'players' not in game_data:
            self._create_error_display(error_message="無法獲取測試數據")
            return

        # 分離及處理雙方陣容
        blue_team, red_team = self._extract_team_compositions(game_data)

        # 創建團隊顯示UI
        self._create_team_display_ui(blue_team, red_team)

    def _calculate_team_winrates(self, blue_team, red_team):
        """計算雙方陣容的勝率"""
        # 如果沒有保存勝率顯示的引用，則不繼續執行
        if not hasattr(self, 'current_winrate_display'):
            print("錯誤: 勝率顯示框架未創建")
            return

        # 在背景線程中計算勝率
        threading.Thread(
            target=self._calculate_team_winrates_thread,
            args=(blue_team, red_team),
            daemon=True
        ).start()

    def _calculate_team_winrates_thread(self, blue_team, red_team):
        """在背景線程中計算勝率"""
        try:
            print("=== 開始計算團隊勝率 ===")
            print(f"藍隊原始陣容: {blue_team}")
            print(f"紅隊原始陣容: {red_team}")

            print("\n開始轉換英雄名稱")
            # 轉換英雄名稱為英文
            blue_team_en = []
            red_team_en = []

            for champ in blue_team:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champ in reverse_mapping:
                        blue_team_en.append(reverse_mapping[champ])
                        print(f"藍隊英雄轉換: {champ} -> {reverse_mapping[champ]}")
                        continue
                blue_team_en.append(champ)
                print(f"藍隊英雄保持原樣: {champ}")

            for champ in red_team:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champ in reverse_mapping:
                        red_team_en.append(reverse_mapping[champ])
                        print(f"紅隊英雄轉換: {champ} -> {reverse_mapping[champ]}")
                        continue
                red_team_en.append(champ)
                print(f"紅隊英雄保持原樣: {champ}")

            print(f"\n轉換後的英雄名稱:")
            print(f"藍隊: {blue_team_en}")
            print(f"紅隊: {red_team_en}")

            # 計算藍方勝率
            print("\n開始計算藍方勝率")
            try:
                blue_result = recommend_compositions_api(blue_team_en)
                print(f"藍方API返回結果: {blue_result}")
                blue_winrate = blue_result[0][1] if blue_result else 0
                print(f"藍方勝率計算結果: {blue_winrate}")
            except Exception as e:
                print(f"藍方勝率計算出錯: {e}")
                blue_winrate = 0

            # 計算紅方勝率
            print("\n開始計算紅方勝率")
            try:
                red_result = recommend_compositions_api(red_team_en)
                print(f"紅方API返回結果: {red_result}")
                red_winrate = red_result[0][1] if red_result else 0
                print(f"紅方勝率計算結果: {red_winrate}")
            except Exception as e:
                print(f"紅方勝率計算出錯: {e}")
                red_winrate = 0

            # 正規化勝率，使其總和為100%
            print("\n開始正規化勝率")
            total_winrate = blue_winrate + red_winrate
            if total_winrate > 0:
                blue_winrate = blue_winrate / total_winrate
                red_winrate = red_winrate / total_winrate
                print(f"正規化後 - 藍方勝率: {blue_winrate:.2%}, 紅方勝率: {red_winrate:.2%}")
            else:
                print("總勝率為0，無法進行正規化")
                blue_winrate = 0.5  # 設置為50-50
                red_winrate = 0.5

            # 更新 UI
            print("\n準備更新UI顯示")
            print(f"最終結果 - 藍方勝率: {blue_winrate:.2%}, 紅方勝率: {red_winrate:.2%}")
            self.root.after(0, lambda: self._update_winrate_display(blue_winrate, red_winrate))
            print("已發送UI更新請求")

        except Exception as e:
            print(f"\n計算勝率時發生嚴重錯誤: {e}")
            print("錯誤詳情:", str(e))
            self.root.after(0, lambda: self._update_winrate_display(0, 0, error=True))

    def _update_winrate_display(self, blue_winrate, red_winrate, error=False):
        """更新勝率顯示"""
        print("\n=== 開始更新UI顯示 ===")

        # 檢查是否有保存勝率顯示的引用
        if not hasattr(self, 'current_winrate_display'):
            print("錯誤: 沒有找到勝率顯示引用")
            return

        # 直接使用保存的引用來更新勝率顯示
        try:
            if error:
                self.current_winrate_display["blue_label"].config(text="勝率計算失敗")
                self.current_winrate_display["red_label"].config(text="勝率計算失敗")
            else:
                self.current_winrate_display["blue_label"].config(text=f"勝率: {blue_winrate:.0%}")
                self.current_winrate_display["red_label"].config(text=f"勝率: {red_winrate:.0%}")
            print("勝率顯示更新成功")
        except Exception as e:
            print(f"更新勝率顯示時出錯: {e}")

        print("=== UI更新完成 ===\n")

    def load_team_comp_data(self):
        """從 API 載入陣容推薦資料"""
        try:
            if self.fetcher:
                # 嘗試使用 fetcher 獲取即時數據
                data = None
                try:
                    data = self.fetcher.fetch_live_data()
                except Exception as e:
                    print(f"無法獲取即時數據: {e}")

                if not data:
                    try:
                        data = self.fetcher.load_local_data()
                        print("使用本地測試數據")
                    except Exception as e:
                        print(f"無法載入本地數據: {e}")

                if data:
                    # 更新可用英雄池
                    self.update_available_champions(data)

                    # 計算當前五位英雄的勝率
                    self.calculate_current_comp_winrate(data.get('selected', []))
            else:
                print("沒有可用的數據獲取器")

        except Exception as e:
            print(f"載入陣容數據時出錯: {e}")

    def calculate_current_comp_winrate(self, selected_champions):
        """計算當前五位英雄的勝率"""
        # 如果沒有五位英雄，顯示提示訊息
        if not selected_champions or len(selected_champions) != 5:
            self.current_winrate_label.config(text="等待選出五位英雄")
            return

        # 為了確保每个英雄名稱為英文，進行轉換
        english_champions = []
        for champion in selected_champions:
            # 檢查是否是中文名稱，如果是則轉為英文
            if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                # 從 tw_mapping 中尋找對應的英文名稱
                reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                if champion in reverse_mapping:
                    english_champions.append(reverse_mapping[champion])
                    continue
            # 如果不是中文或找不到對應的英文，則使用原名
            english_champions.append(champion)

        # 開始計算當前五位英雄的勝率 (在背景執行)
        threading.Thread(target=self._calculate_current_comp_winrate_thread,
                         args=(english_champions,), daemon=True).start()

    def _calculate_current_comp_winrate_thread(self, champions):
        """在背景執行勝率計算"""
        try:
            # 使用 recommend_compositions_api 獲取勝率
            # 由於我們只傳遞這五位英雄，API 應該只返回一個組合
            self.root.after(0, lambda: self.current_winrate_label.config(
                text="計算中...", fg="#e94560"))

            # 調用 API
            sorted_compositions = recommend_compositions_api(champions)

            # 處理結果
            if sorted_compositions and len(sorted_compositions) > 0:
                # 第一個組合就是我們需要的
                comp, winrate = sorted_compositions[0]
                self.root.after(0, lambda: self.current_winrate_label.config(
                    text=f"{winrate:.2%}", fg="#4ecca3"))
            else:
                self.root.after(0, lambda: self.current_winrate_label.config(
                    text="無法計算勝率", fg="#e94560"))
        except Exception as e:
            print(f"計算當前陣容勝率時出錯: {e}")
            self.root.after(0, lambda: self.current_winrate_label.config(
                text="計算失敗", fg="#e94560"))

    def update_available_champions(self, data):
        """更新可用英雄池"""
        # 清除現有內容
        for widget in self.available_champions_frame.winfo_children():
            widget.destroy()

        # 清空槽位列表
        self.available_champion_slots = []

        # 處理已選英雄和候選英雄
        selected_champions = data.get('selected', [])
        all_pool = data.get('all_pool', [])

        # 計算每行顯示的英雄數量並確保統一大小
        champs_per_row = 5

        # 獲取可用英雄（排除已選英雄）
        available_champions = [champ for champ in all_pool if champ not in selected_champions]

        # 創建英雄網格
        for i, champion_name in enumerate(available_champions):
            row = i // champs_per_row
            col = i % champs_per_row

            # 創建圓角英雄框架
            champion_frame = RoundedFrame(
                self.available_champions_frame,
                bg_color="#0f3460",
                corner_radius=self.corner_radius,
                width=55,
                height=90
            )
            champion_frame.grid(row=row, column=col, padx=5, pady=5)
            champion_frame.grid_propagate(False)  # 防止調整大小

            # 確保內部框架不會覆蓋圓角
            champion_frame.interior.config(width=55, height=90, bg="#0f3460")

            # 頭像圓圈或圖像 - 增加大小
            icon_canvas = tk.Canvas(
                champion_frame.interior,
                width=40,
                height=40,
                bg="#0f3460",
                highlightthickness=0
            )

            # 檢查是否有圖像
            image = None
            if hasattr(self.controller, 'champ_images'):
                if champion_name in self.controller.champ_images:
                    image = self.controller.champ_images[champion_name]
                elif hasattr(self.fetcher, 'get_champ_key'):
                    key = self.fetcher.get_champ_key(champion_name)
                    if key in self.controller.champ_images:
                        image = self.controller.champ_images[key]

            # 先清空畫布
            icon_canvas.delete("all")

            if image:
                # 使用圖像 - 在中心位置顯示
                icon_canvas.create_image(20, 20, image=image)
            else:
                # 使用圓形 - 確保圓形大小與圖片協調
                icon_canvas.create_oval(5, 5, 35, 35, fill="#16213e", outline="#16213e")

            icon_canvas.pack(pady=(5, 0))

            # 獲取顯示名稱 - 優先使用中文
            display_name = self._get_display_name(champion_name)

            # 使用圓角框架來包含名稱標籤
            name_frame = RoundedFrame(
                champion_frame.interior,
                bg_color="#0f3460",
                corner_radius=self.corner_radius // 2,  # 使用較小的圓角
                width=55,
                height=30
            )
            name_frame.interior.config(width=55, height=30)
            name_frame.pack(fill="x", expand=True, pady=2)
            name_frame.pack_propagate(False)  # 防止調整大小

            # 名稱標籤
            name_label = tk.Label(
                name_frame.interior,
                text=display_name,
                bg="#0f3460",
                fg="white",
                font=(self.font_family, 8),
                wraplength=50  # 允許文字換行
            )
            name_label.pack(fill="both", expand=True)

            # 調整字體大小以適應文本
            self.adjust_font_size(name_label)

            # 綁定點擊事件 - 需要綁定到圓角框架和其內部元素
            champion_frame.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))
            champion_frame.interior.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))
            icon_canvas.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))
            name_frame.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))
            name_frame.interior.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))
            name_label.bind("<Button-1>", lambda e, c=champion_name: self.select_champion(c))

            self.available_champion_slots.append({
                "frame": champion_frame,
                "canvas": icon_canvas,
                "label": name_label,
                "champion_name": champion_name
            })
        # 更新已選英雄
        for i, champion_name in enumerate(selected_champions):
            if i < 5:  # 最多 5 個英雄
                self.selected_champion_slots[i]["selected"] = True
                self.selected_champion_slots[i]["champion_name"] = champion_name
                self.selected_champion_slots[i]["label"].config(text=self._get_display_name(champion_name))

                # 調整字體大小
                self.adjust_font_size(self.selected_champion_slots[i]["label"])

                # 更新圖像
                canvas = self.selected_champion_slots[i]["canvas"]
                image = None
                if hasattr(self.controller, 'champ_images'):
                    if champion_name in self.controller.champ_images:
                        image = self.controller.champ_images[champion_name]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        key = self.fetcher.get_champ_key(champion_name)
                        if key in self.controller.champ_images:
                            image = self.controller.champ_images[key]

                # 清除舊圖像
                canvas.delete("all")

                if image:
                    # 創建新圖像 - 確保位置正確
                    image_id = canvas.create_image(20, 20, image=image)
                    self.selected_champion_slots[i]["image_id"] = image_id
                else:
                    # 如果沒有圖像，創建圓形
                    canvas.create_oval(5, 5, 35, 35, fill="#16213e", outline="#16213e")

        # 如果有選中的英雄，刷新推薦
        if selected_champions:
            self.refresh_recommendations()

    def _get_display_name(self, hero_name):
        """根據語言設定獲取顯示名稱"""
        # 優先使用中文名稱
        if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
            chinese_name = self.fetcher.tw_mapping.get(hero_name, "")
            if chinese_name:  # 如果有中文名稱，則返回
                return chinese_name

        # 如果沒有中文名稱，返回原名
        return hero_name

    def select_champion(self, champion_name):
        """選擇可用英雄池中的英雄"""
        print(f"選擇英雄: {champion_name}")

        # 檢查英雄是否已被選中
        already_selected = False
        selected_index = -1

        for i, slot in enumerate(self.selected_champion_slots):
            if slot["selected"] and slot["champion_name"] == champion_name:
                already_selected = True
                selected_index = i
                break

        if already_selected:
            # 如果已選中，則取消選擇
            self.deselect_champion(selected_index)
        else:
            # 確定還有空位
            empty_slot = None
            for i, slot in enumerate(self.selected_champion_slots):
                if not slot["selected"]:
                    empty_slot = i
                    break

            if empty_slot is not None:
                # 更新已選英雄
                self.selected_champion_slots[empty_slot]["selected"] = True
                self.selected_champion_slots[empty_slot]["champion_name"] = champion_name

                # 更新 UI
                self.selected_champion_slots[empty_slot]["label"].config(text=self._get_display_name(champion_name))

                # 調整字體大小以適應文本
                self.adjust_font_size(self.selected_champion_slots[empty_slot]["label"])

                # 如果有圖像，顯示圖像
                image = None
                if hasattr(self.controller, 'champ_images'):
                    if champion_name in self.controller.champ_images:
                        image = self.controller.champ_images[champion_name]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        key = self.fetcher.get_champ_key(champion_name)
                        if key in self.controller.champ_images:
                            image = self.controller.champ_images[key]

                if image:
                    canvas = self.selected_champion_slots[empty_slot]["canvas"]
                    # 清除舊圖像
                    canvas.delete("all")
                    # 創建新圖像
                    image_id = canvas.create_image(20, 20, image=image)
                    self.selected_champion_slots[empty_slot]["image_id"] = image_id

                # 更新推薦陣容
                self.refresh_recommendations()

    def deselect_champion(self, index):
        """取消選擇已選英雄"""
        if 0 <= index < len(self.selected_champion_slots):
            slot = self.selected_champion_slots[index]
            # 清除選擇
            slot["selected"] = False
            slot["champion_name"] = None
            slot["label"].config(text="")

            # 清除圖像
            canvas = slot["canvas"]
            canvas.delete("all")
            canvas.create_oval(5, 5, 35, 35, fill="#16213e", outline="#16213e")
            slot["image_id"] = None

            # 更新推薦陣容
            self.refresh_recommendations()

    def clear_selected_champions(self):
        """清除所有已選英雄"""
        # 取消所有選擇
        for i in range(len(self.selected_champion_slots)):
            if self.selected_champion_slots[i]["selected"]:
                self.deselect_champion(i)

    def refresh_recommendations(self):
        """刷新推薦陣容"""
        # 獲取已選英雄名稱列表
        selected_names = []

        for slot in self.selected_champion_slots:
            if slot["selected"] and slot["champion_name"] is not None:
                selected_names.append(slot["champion_name"])

        # 如果選擇的英雄不足，顯示提示信息
        if len(selected_names) < 1:
            self.recommendation_data = []
            self.update_recommendation_table()
            return

        # 獲取所有可用英雄名稱
        all_champion_names = []

        # 如果有 fetcher，嘗試獲取完整的可用英雄池
        if self.fetcher:
            try:
                data = self.fetcher.fetch_live_data() or self.fetcher.load_local_data()
                if data and 'all_pool' in data:
                    all_champion_names = data['all_pool']
            except Exception as e:
                print(f"獲取英雄池時出錯: {e}")

        # 如果沒有獲取到數據，使用可用英雄槽中的數據
        if not all_champion_names:
            all_champion_names = [slot["champion_name"] for slot in self.available_champion_slots]
            # 添加已選英雄
            for name in selected_names:
                if name not in all_champion_names:
                    all_champion_names.append(name)

        # 開始計算推薦陣容 (使用 API)
        threading.Thread(target=self._calculate_recommendations_api, args=(all_champion_names,), daemon=True).start()

    def _calculate_recommendations_api(self, champion_pool):
        """使用 API 在後台執行推薦計算"""
        try:
            print(f"開始API調用，英雄池大小: {len(champion_pool)}")
            start_time = time.time()

            # 轉換為英文名稱
            english_champions = []
            for champion in champion_pool:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champion in reverse_mapping:
                        english_champions.append(reverse_mapping[champion])
                        continue
                english_champions.append(champion)

            print(f"準備調用API，轉換後的英雄名稱: {english_champions}")

            # 使用英文名稱調用 API
            sorted_compositions = recommend_compositions_api(english_champions)
            worst_sorted_compositions = recommend_worst_compositions_api(english_champions)
            print(f"API返回結果數量: {len(sorted_compositions) if sorted_compositions else 0}")

            elapsed = time.time() - start_time
            print(f"API 計算完成，耗時: {elapsed:.2f}秒")

            # 處理 API 返回的結果
            if not sorted_compositions:
                print("API 返回空結果")
                self.root.after(0, lambda: self._update_recommendations([]))
                return

            # 轉換 API 結果格式為我們需要的格式
            recommendations = []
            worst_recommendations = []  # 添加最不推薦陣容列表

            # 顯示推薦的前10個最佳陣容（勝率最高）
            for comp, prob in sorted_compositions[-10:][::-1]:
                recommendations.append((list(comp), prob))

            # 顯示前10個最差陣容（勝率最低）
            for comp, prob in worst_sorted_compositions[-10:][::-1]:
                worst_recommendations.append((list(comp), prob))

            # 更新 UI (在主線程中)
            self.root.after(0, lambda: self._update_recommendations(recommendations, worst_recommendations))

        except Exception as e:
            print(f"計算推薦時出錯: {e}")
            self.root.after(0, lambda: self._update_recommendations([]))
            messagebox.showerror("錯誤", f"推薦計算失敗: {str(e)}")

    def _update_recommendations(self, recommendations, worst_recommendations=None):
        """更新推薦結果到 UI"""
        self.recommendation_data = recommendations
        if worst_recommendations is not None:
            self.worst_recommendation_data = worst_recommendations
        self.update_recommendation_table()

    def adjust_font_size(self, label, initial_size=8, min_size=6):
        """根據文本長度自動調整字體大小"""
        text = label.cget("text")
        if not text:
            return

        # 獲取當前字體
        current_font = label.cget("font")
        if isinstance(current_font, str):
            font_name = current_font
        else:
            font_name = current_font[0] if isinstance(current_font, tuple) else self.font_family

        # 嘗試使用 Font 對象進行測量
        try:
            test_font = font.Font(family=font_name, size=initial_size)
            text_width = test_font.measure(text)

            # 取得標籤寬度
            label_width = label.winfo_width()
            # 如果標籤還沒有寬度，使用父容器的寬度估計
            if label_width <= 1:
                label_width = label.master.winfo_width()
            # 如果仍然沒有合理的寬度，使用預設值
            if label_width <= 1:
                label_width = 50  # 預設寬度

            # 如果文本太寬，減小字體大小
            size = initial_size
            while size > min_size and text_width > label_width:
                size -= 1
                test_font = font.Font(family=font_name, size=size)
                text_width = test_font.measure(text)

            # 設置調整後的字體
            label.config(font=(font_name, size))

        except Exception as e:
            # 如果 Font 對象方法失敗，使用替代方法
            print(f"字體測量失敗，使用替代方法: {e}")

            # 創建臨時標籤來測試不同字體大小
            test_label = tk.Label(self.root, text=text)
            test_label.pack_forget()  # 不顯示，只用於計算

            # 取得標籤寬度
            label_width = label.winfo_width()
            if label_width <= 1:
                label_width = label.master.winfo_width()
            if label_width <= 1:
                label_width = 50  # 預設寬度

            # 嘗試不同的字體大小
            size = initial_size
            while size > min_size:
                test_label.config(font=(font_name, size))
                test_label.update_idletasks()
                text_width = test_label.winfo_width()

                if text_width <= label_width:
                    break

                size -= 1

            # 銷毀測試標籤
            test_label.destroy()

            # 設置調整後的字體
            label.config(font=(font_name, size))

    def _create_test_champion_card(self, parent, champion_name, team_color, index):
        """創建英雄卡片"""
        print(f"\n=== 開始創建英雄卡片 ===")
        print(f"英雄名稱: {champion_name}")
        print(f"隊伍顏色: {team_color}")
        print(f"索引位置: {index}")

        # 設置顏色
        if team_color == "blue":
            bg_color = "#1E293B"
            icon_bg = "#3B5998"
            icon_stroke = "#5F9DF7"
        else:
            bg_color = "#2D1E1E"
            icon_bg = "#983B3B"
            icon_stroke = "#F75F5F"

        # 創建卡片框架
        card_frame = RoundedFrame(
            parent,
            bg_color=bg_color,
            corner_radius=10,
            height=50
        )
        card_frame.pack(fill="x", padx=30, pady=5)
        card_frame.pack_propagate(False)

        # 英雄圖標框架
        icon_frame = RoundedFrame(
            card_frame.interior,
            bg_color=icon_bg,
            corner_radius=20,
            width=40,
            height=40
        )
        icon_frame.pack(side="left", padx=(10, 0), pady=5)
        icon_frame.pack_propagate(False)

        # 獲取英雄圖像
        print("\n嘗試獲取英雄圖像:")
        image = None

        # 先嘗試直接使用原始名稱
        if hasattr(self.controller, 'champ_images'):
            print("控制器中有 champ_images 屬性")
            if champion_name in self.controller.champ_images:
                print(f"直接找到英雄圖像: {champion_name}")
                image = self.controller.champ_images[champion_name]

            # 如果沒有找到，嘗試使用 fetcher 轉換名稱
            if not image and hasattr(self.fetcher, 'tw_mapping'):
                print("嘗試使用 fetcher 轉換英雄名稱")
                reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                if champion_name in reverse_mapping:
                    english_name = reverse_mapping[champion_name]
                    print(f"轉換後的英文名稱: {english_name}")
                    if english_name in self.controller.champ_images:
                        print(f"使用英文名稱找到英雄圖像: {english_name}")
                        image = self.controller.champ_images[english_name]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        print("嘗試使用 fetcher 獲取英雄 key")
                        key = self.fetcher.get_champ_key(english_name)
                        print(f"獲取到的 key: {key}")
                        if key in self.controller.champ_images:
                            print(f"使用 key 找到英雄圖像: {key}")
                            image = self.controller.champ_images[key]
        else:
            print("控制器中沒有 champ_images 屬性")

        if image:
            print("成功獲取到英雄圖像")
            icon_label = tk.Label(
                icon_frame.interior,
                image=image,
                bg=icon_bg,
                borderwidth=0
            )
            icon_label.image = image  # 保留引用防止垃圾回收
            icon_label.pack(fill="both", expand=True)
        else:
            print("未能獲取到英雄圖像，使用默認圓形")
            # 創建默認圓形
            icon_canvas = tk.Canvas(
                icon_frame.interior,
                width=40,
                height=40,
                bg=icon_bg,
                highlightthickness=0
            )
            icon_canvas.create_oval(5, 5, 35, 35, fill=icon_bg, outline=icon_stroke)
            icon_canvas.pack(fill="both", expand=True)

        # 英雄名稱
        display_name = self._get_display_name(champion_name)
        print(f"顯示名稱: {display_name}")

        name_label = tk.Label(
            card_frame.interior,
            text=display_name,
            bg=bg_color,
            fg="white",
            font=(self.font_family, 16),
            anchor="center"
        )
        name_label.pack(fill="both", expand=True, padx=(20, 10))

        print("=== 英雄卡片創建完成 ===\n")

    def _create_test_winrate_display(self, parent_frame, team_color):
        """創建測試頁面的勝率顯示框架並返回框架和標籤的引用"""
        if team_color == "blue":
            bg_color = "#152544"
            fg_color = "#5F9DF7"
        else:
            bg_color = "#441515"
            fg_color = "#F75F5F"

        # 勝率框架
        winrate_frame = RoundedFrame(
            parent_frame.interior,
            bg_color=bg_color,
            corner_radius=10,
            height=60
        )
        winrate_frame.pack(fill="x", padx=30, pady=(10, 20))
        winrate_frame.pack_propagate(False)

        # 勝率標籤
        winrate_label = tk.Label(
            winrate_frame.interior,
            text="勝率: 計算中...",
            bg=bg_color,
            fg=fg_color,
            font=(self.font_family_bold, 24)
        )
        winrate_label.pack(fill="both", expand=True, padx=20)

        return winrate_frame, winrate_label

    def _create_error_display(self, error_message="無法獲取數據"):
        """創建錯誤顯示"""
        print(f"\n=== 顯示錯誤信息: {error_message} ===")

        # 創建主框架
        main_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0F172A",
            corner_radius=self.corner_radius
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 錯誤訊息
        status_label = tk.Label(
            main_frame.interior,
            text=error_message,
            bg="#0F172A",
            fg="#e94560",
            font=(self.font_family, 16)
        )
        status_label.pack(expand=True)

        print("=== 錯誤信息顯示完成 ===\n")
