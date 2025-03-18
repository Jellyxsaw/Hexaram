import logging
import threading
import tkinter as tk
from tkinter import ttk

from api_client import AramAPIClient

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChampionListFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller

        # 初始化API客戶端
        self.api_client = AramAPIClient()

        # 設置分頁變數
        self.current_page = 1
        self.items_per_page = 12
        self.total_pages = 1
        self.total_items = 0

        # 設置過濾和排序變數
        self.current_filter = "全部"
        self.current_sort = "勝率"

        # 載入中狀態
        self.loading = False

        # 創建版本資訊變數
        self.version_info = {
            "current_version": "未知",
            "last_updated": "未知",
            "total_samples": 0
        }

        # 動畫任務 ID
        self.animation_after_id = None

        # 創建搜索和過濾區域
        self.create_search_area()

        # 創建英雄網格顯示區域
        self.create_champion_grid()

        # 創建分頁區域
        self.create_pagination()

        # 創建載入指示器
        self.create_loading_indicator()

        # 獲取版本資訊
        self.get_version_info()

        # 載入英雄資料
        self.load_champion_data()

    def create_search_area(self):
        """創建搜索和過濾區域"""
        search_frame = tk.Frame(self, bg="#16213e", height=60)
        search_frame.pack(fill="x", padx=10, pady=10)

        # 搜索區域容器 - 使用圓角邊框
        search_container = tk.Frame(search_frame, bg="#0f3460", bd=0, highlightthickness=1,
                                    highlightbackground="#0f3460")
        search_container.pack(side="left", padx=10, pady=15)

        # 搜索圖標
        search_icon_label = tk.Label(
            search_container,
            text="🔍",
            bg="#0f3460",
            fg="#8b8b8b",
            font=("Arial", 10)
        )
        search_icon_label.pack(side="left", padx=(5, 0))

        # 搜索框
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            bg="#0f3460",
            fg="#8b8b8b",
            insertbackground="white",
            relief="flat",
            font=("Arial", 10),
            width=30,
            bd=0
        )
        self.search_entry.insert(0, "搜索英雄...")
        self.search_entry.pack(side="left", padx=(0, 5), pady=5, ipady=3)

        # 清除搜索框預設文字的事件處理
        def on_entry_click(event):
            if self.search_entry.get() == "搜索英雄...":
                self.search_entry.delete(0, "end")
                self.search_entry.config(fg="white")
                search_icon_label.config(fg="white")

        def on_entry_leave(event):
            if self.search_entry.get() == "":
                self.search_entry.insert(0, "搜索英雄...")
                self.search_entry.config(fg="#8b8b8b")
                search_icon_label.config(fg="#8b8b8b")

        self.search_entry.bind("<FocusIn>", on_entry_click)
        self.search_entry.bind("<FocusOut>", on_entry_leave)
        self.search_entry.bind("<Return>", lambda e: self.search_champions())

        # 搜索按鈕 - 使用更現代的設計
        search_button = tk.Button(
            search_frame,
            text="搜尋",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=3,
            bd=0,
            command=self.search_champions
        )
        search_button.pack(side="left", padx=5, pady=15)

        # 增加懸停效果
        def on_search_enter(e):
            search_button.config(bg="#e92550")

        def on_search_leave(e):
            search_button.config(bg="#e94560")

        search_button.bind("<Enter>", on_search_enter)
        search_button.bind("<Leave>", on_search_leave)

        # 過濾按鈕 - 使用更現代的標籤設計
        filter_frame = tk.Frame(search_frame, bg="#16213e")
        filter_frame.pack(side="left", padx=(20, 5), pady=15)

        filter_options = ["全部", "坦克", "戰士", "刺客", "法師", "輔助", "射手"]
        self.filter_buttons = {}

        for i, option in enumerate(filter_options):
            button = tk.Button(
                filter_frame,
                text=option,
                bg="#0f3460" if i == 0 else "#1a1a2e",
                fg="white",
                relief="flat",
                font=("Arial", 10),
                padx=8,
                pady=2,
                bd=0,
                command=lambda o=option: self.filter_champions(o)
            )
            button.pack(side="left", padx=3)
            self.filter_buttons[option] = button

            # 添加懸停效果
            def on_filter_enter(e, btn=button):
                if btn.cget("bg") != "#0f3460":  # 如果不是已選擇按鈕
                    btn.config(bg="#24365a")

            def on_filter_leave(e, btn=button, is_selected=(i == 0)):
                if not is_selected:  # 如果不是已選擇按鈕
                    btn.config(bg="#1a1a2e")

            button.bind("<Enter>", lambda e, b=button: on_filter_enter(e, b))
            button.bind("<Leave>", lambda e, b=button, sel=(i == 0): on_filter_leave(e, b, sel))

        # 排序選項
        sort_frame = tk.Frame(search_frame, bg="#16213e")
        sort_frame.pack(side="right", padx=10, pady=15)

        sort_label = tk.Label(
            sort_frame,
            text="排序: ",
            bg="#16213e",
            fg="white",
            font=("Arial", 10)
        )
        sort_label.pack(side="left", padx=(0, 5))

        self.sort_var = tk.StringVar(value="勝率")

        # 客製化下拉選單樣式
        style = ttk.Style()
        style.configure("Custom.TCombobox",
                        fieldbackground="#0f3460",
                        background="#0f3460",
                        foreground="white",
                        arrowcolor="white",
                        relief="flat")

        sort_dropdown = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["勝率", "選用率", "KDA"],
            width=8,
            state="readonly",
            style="Custom.TCombobox"
        )
        sort_dropdown.pack(side="left")
        sort_dropdown.bind("<<ComboboxSelected>>", self.sort_champions)

    def create_champion_grid(self):
        """創建英雄網格顯示區域"""
        # 創建網格容器的外部框架，使其可以滾動
        self.outer_frame = tk.Frame(self, bg="#1a1a2e")
        self.outer_frame.pack(fill="both", expand=True, padx=10)

        # 設置列配置以確保自適應佈局
        self.outer_frame.grid_columnconfigure(0, weight=1)
        self.outer_frame.grid_rowconfigure(0, weight=1)

        # 創建網格框架
        self.grid_frame = tk.Frame(self.outer_frame, bg="#1a1a2e")
        self.grid_frame.pack(fill="both", expand=True)

        # 設置網格布局的配置，確保能夠自適應視窗大小
        for i in range(4):  # 4列
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="column")

        # 添加一個訊息標籤，用於顯示沒有結果的情況
        self.message_label = tk.Label(
            self.grid_frame,
            text="",
            bg="#1a1a2e",
            fg="white",
            font=("Arial", 12)
        )

        # 創建卡片的容器
        self.champion_cards = []

    def create_pagination(self):
        """創建分頁區域"""
        pagination_frame = tk.Frame(self, bg="#1a1a2e")
        pagination_frame.pack(fill="x", side="bottom", pady=10)

        # 創建更現代的分頁容器
        pagination_container = tk.Frame(pagination_frame, bg="#16213e", height=40, bd=0, highlightthickness=1,
                                        highlightbackground="#0f3460")
        pagination_container.pack(pady=10)

        # 上一頁按鈕 - 改進設計
        self.prev_button = tk.Button(
            pagination_container,
            text="◀ 上一頁",
            bg="#16213e",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            bd=0,
            padx=10,
            command=self.prev_page
        )
        self.prev_button.pack(side="left", padx=10, pady=5)

        # 添加懸停效果
        def on_prev_enter(e):
            if self.prev_button.cget("state") == "normal":
                self.prev_button.config(bg="#0f3460")

        def on_prev_leave(e):
            self.prev_button.config(bg="#16213e")

        self.prev_button.bind("<Enter>", on_prev_enter)
        self.prev_button.bind("<Leave>", on_prev_leave)

        # 頁碼顯示 - 使用更明顯的設計
        self.page_label = tk.Label(
            pagination_container,
            text="1/1",
            bg="#16213e",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.page_label.pack(side="left", padx=10, pady=5)

        # 下一頁按鈕 - 改進設計
        self.next_button = tk.Button(
            pagination_container,
            text="下一頁 ▶",
            bg="#16213e",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            bd=0,
            padx=10,
            command=self.next_page
        )
        self.next_button.pack(side="left", padx=10, pady=5)

        # 添加懸停效果
        def on_next_enter(e):
            if self.next_button.cget("state") == "normal":
                self.next_button.config(bg="#0f3460")

        def on_next_leave(e):
            self.next_button.config(bg="#16213e")

        self.next_button.bind("<Enter>", on_next_enter)
        self.next_button.bind("<Leave>", on_next_leave)

        # 資料來源和時間戳記 - 改進格式
        stats_frame = tk.Frame(pagination_frame, bg="#1a1a2e")
        stats_frame.pack(fill="x", side="bottom", pady=(0, 5))

        self.data_source_label = tk.Label(
            stats_frame,
            text="資料來源: 基於最近版本的ARAM對戰",
            bg="#1a1a2e",
            fg="#8b8b8b",
            font=("Arial", 8)
        )
        self.data_source_label.pack(side="left", padx=20, pady=5)

        self.update_time_label = tk.Label(
            stats_frame,
            text="最後更新: 載入中...",
            bg="#1a1a2e",
            fg="#8b8b8b",
            font=("Arial", 8)
        )
        self.update_time_label.pack(side="right", padx=20, pady=5)

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
        self.grid_frame.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

        # 啟動載入動畫
        def animate_loading():
            self.current_dot = (self.current_dot + 1) % len(self.loading_dots)
            self.loading_label.config(text=f"{self.loading_dots[self.current_dot]} 載入中...")
            self.animation_after_id = self.after(150, animate_loading)

        # 取消先前的動畫（如果有）
        if self.animation_after_id:
            self.after_cancel(self.animation_after_id)

        # 啟動新的動畫
        animate_loading()

    def hide_loading(self):
        """隱藏載入指示器"""
        self.loading = False

        # 停止載入動畫
        if self.animation_after_id:
            self.after_cancel(self.animation_after_id)
            self.animation_after_id = None

        self.loading_frame.pack_forget()
        self.grid_frame.pack(fill="both", expand=True)

    def get_version_info(self):
        """獲取版本資訊"""

        def fetch_version():
            try:
                version_info = self.api_client.get_version_info()
                self.version_info = version_info

                # 更新UI
                def update_ui():
                    # 更新資料來源標籤
                    samples = f"{version_info['total_samples']:,}" if 'total_samples' in version_info else "未知"
                    self.data_source_label.config(
                        text=f"資料來源: 基於最近版本{samples}+場ARAM對戰"
                    )

                    # 更新時間標籤
                    last_updated = version_info.get('last_updated', "未知")
                    self.update_time_label.config(
                        text=f"最後更新: {last_updated}"
                    )

                # 在主執行緒中更新UI
                if not self._is_destroyed():
                    self.after(0, update_ui)

            except Exception as e:
                logger.error(f"獲取版本資訊失敗: {str(e)}")

        # 在背景執行緒中獲取版本資訊
        threading.Thread(target=fetch_version, daemon=True).start()

    def load_champion_data(self, reset_page=True):
        """
        載入英雄資料

        Args:
            reset_page: 是否重設頁碼到第一頁，預設為True
        """
        if reset_page:
            self.current_page = 1

        self.show_loading()

        def fetch_data():
            try:
                query = self.search_var.get()
                if query and query != "搜索英雄...":
                    # 搜索模式
                    result = self.api_client.search_champions(query)
                    champions = result.get('results', [])

                    # 轉換搜索結果為統一格式
                    formatted_champions = []
                    for champ in champions:
                        formatted_champions.append({
                            'championId': champ.get('champion_id', ''),
                            'name': champ.get('champion_name', ''),
                            'type': champ.get('champion_type', ''),
                            'winRate': 0,  # 搜索結果沒有這些數據
                            'pickRate': 0,
                            'kda': '0/0/0',
                            'kdaRatio': 0,
                            'tier': '',
                            'rank': 0,
                            'key': champ.get('key', 0),
                            'championTwName': champ.get('champion_tw_name', '')
                        })

                    self.champions = formatted_champions
                    self.total_pages = 1
                    self.total_items = len(formatted_champions)

                else:
                    # 正常模式：從API獲取英雄列表
                    result = self.api_client.get_champion_list(
                        champion_type=self.current_filter if self.current_filter != "全部" else None,
                        sort_by=self.current_sort,
                        page=self.current_page,
                        limit=self.items_per_page
                    )

                    self.champions = result.get('champions', [])
                    pagination = result.get('pagination', {})
                    self.total_pages = pagination.get('total_pages', 1)
                    self.total_items = pagination.get('total_items', 0)

                # 在主執行緒中更新UI
                if not self._is_destroyed():
                    self.after(0, self.update_ui)

            except Exception as e:
                logger.error(f"載入英雄資料失敗: {str(e)}")

                # 顯示錯誤訊息
                if not self._is_destroyed():
                    self.after(0, lambda: self.show_error(f"載入資料失敗: {str(e)}"))

        # 在背景執行緒中獲取資料
        threading.Thread(target=fetch_data, daemon=True).start()

    def update_ui(self):
        """更新UI顯示"""
        # 更新分頁資訊
        self.page_label.config(text=f"{self.current_page}/{self.total_pages}")

        # 更新分頁按鈕狀態
        if self.current_page <= 1:
            self.prev_button.config(state="disabled")
        else:
            self.prev_button.config(state="normal")

        if self.current_page >= self.total_pages:
            self.next_button.config(state="disabled")
        else:
            self.next_button.config(state="normal")

        # 顯示英雄資料
        self.display_champions()

        # 隱藏載入指示器
        self.hide_loading()

    def show_error(self, message):
        """
        顯示錯誤訊息

        Args:
            message: 錯誤訊息
        """
        # 清空網格
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # 創建錯誤容器
        error_container = tk.Frame(self.grid_frame, bg="#1a1a2e", padx=20, pady=20)
        error_container.pack(expand=True, fill="both")

        # 錯誤圖標
        error_icon = tk.Label(
            error_container,
            text="⚠️",
            bg="#1a1a2e",
            fg="#e94560",
            font=("Arial", 48)
        )
        error_icon.pack(pady=(20, 10))

        # 錯誤標題
        error_title = tk.Label(
            error_container,
            text="發生錯誤",
            bg="#1a1a2e",
            fg="#e94560",
            font=("Arial", 16, "bold")
        )
        error_title.pack(pady=(0, 10))

        # 顯示錯誤訊息
        error_label = tk.Label(
            error_container,
            text=message,
            bg="#1a1a2e",
            fg="white",
            font=("Arial", 12),
            wraplength=500  # 文字超過此寬度時將自動換行
        )
        error_label.pack(pady=10)

        # 重試按鈕
        retry_button = tk.Button(
            error_container,
            text="重試",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5,
            bd=0,
            command=self.refresh_data
        )
        retry_button.pack(pady=20)

        # 添加懸停效果
        def on_retry_enter(e):
            retry_button.config(bg="#e92550")

        def on_retry_leave(e):
            retry_button.config(bg="#e94560")

        retry_button.bind("<Enter>", on_retry_enter)
        retry_button.bind("<Leave>", on_retry_leave)

        # 隱藏載入指示器
        self.hide_loading()

    def display_champions(self):
        """顯示英雄資料"""
        # 清空網格
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        if not self.champions:
            self.message_label = tk.Label(
                self.grid_frame,
                text="沒有找到符合條件的英雄",
                bg="#1a1a2e",
                fg="white",
                font=("Arial", 12)
            )
            self.message_label.grid(row=0, column=0, columnspan=4, pady=50, sticky="nsew")
            return

        # 計算每行可以放置多少卡片，基於目前視窗寬度
        # 理想情況下每個卡片寬度為280 + padding
        window_width = self.winfo_width()
        cards_per_row = max(1, min(4, window_width // 300))

        # 顯示英雄卡片
        row, col = 0, 0
        for i, champion in enumerate(self.champions):
            self.create_champion_card(champion, row, col)

            # 更新行列位置
            col += 1
            if col >= cards_per_row:  # 每行卡片數量自適應
                col = 0
                row += 1

    def create_champion_card(self, champion, row, col):
        """
        創建英雄卡片

        Args:
            champion: 英雄資料字典
            row: 行索引
            col: 列索引
        """
        # 使用更現代的圓角卡片設計
        card_frame = tk.Frame(self.grid_frame, bg="#16213e", width=280, height=180, bd=0, highlightthickness=1,
                              highlightbackground="#0f3460")
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.grid_frame.grid_rowconfigure(row, weight=1, uniform="row")
        card_frame.pack_propagate(False)  # 防止框架自動調整大小

        # 儲存原始卡片引用，以便之後可以引用它
        self.champion_cards.append(card_frame)

        # 為卡片添加懸停效果
        def on_enter(e):
            card_frame.config(highlightbackground="#e94560", highlightthickness=2)

        def on_leave(e):
            card_frame.config(highlightbackground="#0f3460", highlightthickness=1)

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # 英雄圖示框架 - 使用圓形設計
        icon_frame = tk.Frame(card_frame, bg="#0f3460", width=60, height=60, bd=0)
        icon_frame.place(x=20, y=20)

        # 嘗試載入英雄圖示
        champion_id = champion.get('championId', '')
        champion_key = champion.get('key', 0)
        icon_loaded = False

        # 檢查控制器是否有champ_images屬性和對應的圖片
        if hasattr(self.controller, 'champ_images'):
            # 優先使用championId查找
            if champion_id in self.controller.champ_images:
                icon = self.controller.champ_images[champion_id]
                icon_label = tk.Label(icon_frame, image=icon, bg="#0f3460", bd=0)
                icon_label.place(relx=0.5, rely=0.5, anchor="center")
                icon_loaded = True
            # 然後嘗試使用key查找
            elif str(champion_key) in self.controller.champ_images:
                icon = self.controller.champ_images[str(champion_key)]
                icon_label = tk.Label(icon_frame, image=icon, bg="#0f3460", bd=0)
                icon_label.place(relx=0.5, rely=0.5, anchor="center")
                icon_loaded = True

        # 如果沒有找到圖片，顯示佔位符
        if not icon_loaded:
            placeholder = tk.Label(icon_frame, text=champion.get('name', '')[:1],
                                   bg="#e94560", fg="white", font=("Arial", 18, "bold"),
                                   width=3, height=1)
            placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # 英雄名稱 - 使用更好的字體樣式
        # 組合英文名稱和中文名稱（如果有）
        name_text = champion.get('name', '')
        if 'championTwName' in champion and champion['championTwName']:
            name_text = f"{name_text} {champion['championTwName']}"

        name_label = tk.Label(
            card_frame,
            text=name_text,
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.place(x=90, y=20)

        # 英雄類型 - 使用標籤樣式
        type_text = champion.get('type', '')
        type_frame = tk.Frame(card_frame, bg="#e94560", bd=0)
        type_frame.place(x=90, y=45)

        type_label = tk.Label(
            type_frame,
            text=type_text,
            bg="#e94560",
            fg="white",
            font=("Arial", 9),
            anchor="center",
            padx=5,
            pady=1
        )
        type_label.pack()

        # 統計資料框 - 改進設計
        stats_frame = tk.Frame(card_frame, bg="#0f3460", width=220, height=80)
        stats_frame.place(x=30, y=80)

        # 勝率 - 添加對勝率優劣的視覺提示
        win_rate_value = champion.get('winRate', 0)
        win_rate_color = "#4ecca3" if win_rate_value >= 50 else "#e94560"

        win_rate_label1 = tk.Label(
            stats_frame,
            text="勝率:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        win_rate_label1.place(x=10, y=10)

        win_rate_label2 = tk.Label(
            stats_frame,
            text=f"{win_rate_value}%",
            bg="#0f3460",
            fg=win_rate_color,
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        win_rate_label2.place(x=90, y=10)

        # 選用率
        pick_rate_label2 = tk.Label(
            stats_frame,
            text=f"{champion.get('pickRate', 0)}%",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        pick_rate_label2.place(x=90, y=30)

        # KDA
        kda_label1 = tk.Label(
            stats_frame,
            text="KDA:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        kda_label1.place(x=10, y=50)

        kda_label2 = tk.Label(
            stats_frame,
            text=champion.get("kda", "0/0/0"),
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        kda_label2.place(x=90, y=50)

        # KDA比 - 使用顏色指示優劣
        kda_ratio = champion.get("kdaRatio", 0)
        kda_color = "#4ecca3" if kda_ratio >= 2.5 else ("#e9d362" if kda_ratio >= 1.5 else "#e94560")

        kda_ratio_label = tk.Label(
            stats_frame,
            text=str(kda_ratio),
            bg="#0f3460",
            fg=kda_color,
            font=("Arial", 10, "bold"),
            anchor="e"
        )
        kda_ratio_label.place(x=190, y=50)

        # 點擊英雄卡片時的事件
        champion_id = champion.get('championId', '')

        def open_champion_detail(event=None):
            if champion_id:
                self.controller.show_champion_detail(champion_id)

        # 添加點擊效果
        def on_click(e):
            card_frame.config(highlightbackground="#4ecca3", highlightthickness=2)
            self.after(100, lambda: card_frame.config(highlightbackground="#e94560", highlightthickness=2))
            open_champion_detail()

        # 為所有元素添加點擊事件
        card_frame.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        stats_frame.bind("<Button-1>", on_click)
        if 'icon_label' in locals():
            icon_label.bind("<Button-1>", on_click)
        if 'placeholder' in locals():
            placeholder.bind("<Button-1>", on_click)
        if 'type_label' in locals():
            type_label.bind("<Button-1>", on_click)
        if 'type_frame' in locals():
            type_frame.bind("<Button-1>", on_click)

    def search_champions(self, event=None):
        """根據搜索框內容搜索英雄"""
        query = self.search_var.get()

        # 如果是預設文字，則忽略
        if query == "搜索英雄...":
            query = ""

        # 顯示載入指示器
        self.show_loading()

        # 重置分頁並重新載入數據
        self.current_page = 1
        self.load_champion_data()

    def filter_champions(self, filter_type):
        """
        過濾英雄類型

        Args:
            filter_type: 英雄類型
        """
        # 如果點擊相同的過濾按鈕，則忽略
        if self.current_filter == filter_type:
            return

        logger.info(f"過濾英雄類型: {filter_type}")

        # 更新按鈕樣式
        for button_type, button in self.filter_buttons.items():
            if button_type == filter_type:
                button.config(bg="#0f3460")
            else:
                button.config(bg="#1a1a2e")

        # 更新過濾變數
        self.current_filter = filter_type

        # 重置搜索
        self.search_var.set("")
        if not self._is_destroyed():
            # 修正錯誤：改為直接使用已保存的 Entry widget
            if hasattr(self, 'search_entry'):
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "搜索英雄...")
                self.search_entry.config(fg="#8b8b8b")

        # 顯示載入指示器
        self.show_loading()

        # 重置分頁並重新載入數據
        self.current_page = 1
        self.load_champion_data()

    def sort_champions(self, event=None):
        """
        排序英雄

        Args:
            event: 事件對象，預設為None
        """
        new_sort = self.sort_var.get()

        # 如果選擇相同的排序方式，則忽略
        if new_sort == self.current_sort:
            return

        logger.info(f"排序英雄: {new_sort}")

        # 更新排序變數
        self.current_sort = new_sort

        # 顯示載入指示器
        self.show_loading()

        # 重置分頁並重新載入數據
        self.current_page = 1
        self.load_champion_data()

    def prev_page(self):
        """轉到上一頁"""
        if self.current_page > 1:
            self.current_page -= 1
            self.show_loading()
            self.load_champion_data(reset_page=False)

    def next_page(self):
        """轉到下一頁"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.show_loading()
            self.load_champion_data(reset_page=False)

    def refresh_data(self):
        """刷新英雄資料"""
        # 清除API快取
        if hasattr(self, 'api_client'):
            self.api_client.clear_cache()

        # 顯示載入指示器
        self.show_loading()

        # 重新獲取版本資訊
        self.get_version_info()

        # 重新載入英雄資料
        self.load_champion_data()

    def _is_destroyed(self):
        """檢查視窗是否已被銷毀"""
        try:
            return not self.winfo_exists()
        except:
            return True