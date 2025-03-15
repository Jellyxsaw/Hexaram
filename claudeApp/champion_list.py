import math
import tkinter as tk
from tkinter import ttk


class ChampionListFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller

        # 創建搜索和過濾區域
        self.create_search_area()

        # 創建英雄網格顯示區域
        self.create_champion_grid()

        # 創建分頁區域
        self.create_pagination()

        # 載入英雄資料
        self.load_champion_data()

    def create_search_area(self):
        """創建搜索和過濾區域"""
        search_frame = tk.Frame(self, bg="#16213e", height=60)
        search_frame.pack(fill="x", padx=10, pady=10)

        # 搜索框
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            bg="#0f3460",
            fg="#8b8b8b",
            insertbackground="white",
            relief="flat",
            font=("Arial", 10),
            width=30
        )
        search_entry.insert(0, "搜索英雄...")
        search_entry.pack(side="left", padx=10, pady=15)

        # 搜索按鈕
        search_button = tk.Button(
            search_frame,
            text="🔍",
            bg="#e94560",
            fg="white",
            relief="flat",
            font=("Arial", 10, "bold"),
            command=lambda: self.search_champions(search_var.get())
        )
        search_button.pack(side="left", padx=5, pady=15)

        # 過濾按鈕
        filter_options = ["全部", "坦克", "戰士", "刺客", "法師", "輔助", "射手"]
        self.filter_buttons = {}

        for i, option in enumerate(filter_options):
            button = tk.Button(
                search_frame,
                text=option,
                bg="#0f3460" if i == 0 else "#1a1a2e",
                fg="white",
                relief="flat",
                font=("Arial", 10),
                command=lambda o=option: self.filter_champions(o)
            )
            button.pack(side="left", padx=5, pady=15)
            self.filter_buttons[option] = button

        # 排序選項
        sort_label = tk.Label(
            search_frame,
            text="排序: ",
            bg="#16213e",
            fg="white",
            font=("Arial", 10)
        )
        sort_label.pack(side="left", padx=(20, 5), pady=15)

        self.sort_var = tk.StringVar(value="勝率")
        sort_dropdown = ttk.Combobox(
            search_frame,
            textvariable=self.sort_var,
            values=["勝率", "選用率", "KDA"],
            width=10,
            state="readonly"
        )
        sort_dropdown.pack(side="left", padx=5, pady=15)
        sort_dropdown.bind("<<ComboboxSelected>>", self.sort_champions)

    def create_champion_grid(self):
        """創建英雄網格顯示區域"""
        self.grid_frame = tk.Frame(self, bg="#1a1a2e")
        self.grid_frame.pack(fill="both", expand=True, padx=10)

        # 創建卡片的容器
        self.champion_cards = []

    def create_pagination(self):
        """創建分頁區域"""
        pagination_frame = tk.Frame(self, bg="#1a1a2e")
        pagination_frame.pack(fill="x", side="bottom", pady=10)

        pagination_container = tk.Frame(pagination_frame, bg="#16213e", height=40)
        pagination_container.pack(pady=10)

        # 上一頁按鈕
        prev_button = tk.Button(
            pagination_container,
            text="◀ 上一頁",
            bg="#16213e",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=self.prev_page
        )
        prev_button.pack(side="left", padx=10, pady=5)

        # 頁碼顯示
        self.page_label = tk.Label(
            pagination_container,
            text="1/8",
            bg="#16213e",
            fg="white",
            font=("Arial", 10)
        )
        self.page_label.pack(side="left", padx=10, pady=5)

        # 下一頁按鈕
        next_button = tk.Button(
            pagination_container,
            text="下一頁 ▶",
            bg="#16213e",
            fg="white",
            relief="flat",
            font=("Arial", 10),
            command=self.next_page
        )
        next_button.pack(side="left", padx=10, pady=5)

        # 資料來源和時間戳記
        data_source_label = tk.Label(
            pagination_frame,
            text="資料來源: 基於最近版本100,000+場ARAM對戰",
            bg="#1a1a2e",
            fg="#8b8b8b",
            font=("Arial", 8)
        )
        data_source_label.pack(side="left", padx=20, pady=5)

        update_time_label = tk.Label(
            pagination_frame,
            text="最後更新: 2025.03.15",
            bg="#1a1a2e",
            fg="#8b8b8b",
            font=("Arial", 8)
        )
        update_time_label.pack(side="right", padx=20, pady=5)

    def load_champion_data(self):
        """載入英雄資料"""
        # TODO: 從API獲取英雄資料
        # 這裡使用模擬資料
        self.champions = [
            {
                "name": "Sona 索娜",
                "type": "輔助",
                "winRate": 65.2,
                "pickRate": 8.5,
                "kda": "6.3/4.8/22.1",
                "kdaRatio": 5.9
            },
            {
                "name": "Seraphine 瑟菈紛",
                "type": "輔助/法師",
                "winRate": 63.7,
                "pickRate": 9.2,
                "kda": "5.8/5.2/19.3",
                "kdaRatio": 4.8
            },
            {
                "name": "Ziggs 希格斯",
                "type": "法師",
                "winRate": 62.4,
                "pickRate": 11.7,
                "kda": "7.6/5.9/15.2",
                "kdaRatio": 3.9
            },
            {
                "name": "Ashe 艾希",
                "type": "射手",
                "winRate": 61.8,
                "pickRate": 14.5,
                "kda": "6.8/6.2/14.8",
                "kdaRatio": 3.5
            },
            {
                "name": "Maokai 茂凱",
                "type": "坦克",
                "winRate": 60.7,
                "pickRate": 7.3,
                "kda": "5.2/6.1/18.6",
                "kdaRatio": 3.9
            },
            {
                "name": "Kayle 凱爾",
                "type": "戰士/法師",
                "winRate": 59.5,
                "pickRate": 6.8,
                "kda": "8.2/6.9/10.7",
                "kdaRatio": 2.7
            },
            {
                "name": "Brand 布蘭德",
                "type": "法師",
                "winRate": 58.9,
                "pickRate": 12.2,
                "kda": "8.9/7.2/13.5",
                "kdaRatio": 3.1
            },
            {
                "name": "Swain 斯溫",
                "type": "法師/戰士",
                "winRate": 58.2,
                "pickRate": 9.1,
                "kda": "7.5/5.9/15.4",
                "kdaRatio": 3.9
            },
            {
                "name": "Veigar 維迦",
                "type": "法師",
                "winRate": 57.8,
                "pickRate": 10.7,
                "kda": "7.3/6.7/14.9",
                "kdaRatio": 3.3
            },
            {
                "name": "Nasus 納瑟斯",
                "type": "戰士/坦克",
                "winRate": 57.3,
                "pickRate": 8.3,
                "kda": "6.4/7.2/13.8",
                "kdaRatio": 2.8
            },
            {
                "name": "Xerath 齊勒斯",
                "type": "法師",
                "winRate": 56.9,
                "pickRate": 11.3,
                "kda": "7.8/6.5/15.6",
                "kdaRatio": 3.6
            },
            {
                "name": "Leona 雷歐娜",
                "type": "坦克/輔助",
                "winRate": 56.4,
                "pickRate": 7.9,
                "kda": "4.2/6.8/21.3",
                "kdaRatio": 3.8
            }
        ]

        # 設置分頁變數
        self.current_page = 1
        self.items_per_page = 12
        self.total_pages = math.ceil(len(self.champions) / self.items_per_page)
        self.page_label.config(text=f"{self.current_page}/{self.total_pages}")

        # 顯示英雄
        self.display_champions()

    def display_champions(self):
        """顯示英雄資料"""
        # 清空網格
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # 計算當前頁面需要顯示的英雄
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_champions = self.champions[start_idx:end_idx]

        # 顯示英雄卡片
        row, col = 0, 0
        for i, champion in enumerate(page_champions):
            self.create_champion_card(champion, row, col)

            # 更新行列位置
            col += 1
            if col > 3:  # 每行4個英雄
                col = 0
                row += 1

    def create_champion_card(self, champion, row, col):
        """創建英雄卡片"""
        card_frame = tk.Frame(self.grid_frame, bg="#16213e", width=280, height=180)
        card_frame.grid(row=row, column=col, padx=10, pady=10)
        card_frame.pack_propagate(False)  # 防止框架自動調整大小

        # 英雄圖示
        icon_frame = tk.Frame(card_frame, bg="#0f3460", width=60, height=60)
        icon_frame.place(x=20, y=20)

        # 英雄名稱
        name_label = tk.Label(
            card_frame,
            text=champion["name"],
            bg="#16213e",
            fg="white",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.place(x=90, y=20)

        # 英雄類型
        type_label = tk.Label(
            card_frame,
            text=champion["type"],
            bg="#16213e",
            fg="#8b8b8b",
            font=("Arial", 10),
            anchor="w"
        )
        type_label.place(x=90, y=45)

        # 統計資料框
        stats_frame = tk.Frame(card_frame, bg="#0f3460", width=220, height=80)
        stats_frame.place(x=30, y=80)

        # 勝率
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
            text=f"{champion['winRate']}%",
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        win_rate_label2.place(x=90, y=10)

        # 選用率
        pick_rate_label1 = tk.Label(
            stats_frame,
            text="選用率:",
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        pick_rate_label1.place(x=10, y=30)

        pick_rate_label2 = tk.Label(
            stats_frame,
            text=f"{champion['pickRate']}%",
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
            text=champion["kda"],
            bg="#0f3460",
            fg="white",
            font=("Arial", 10),
            anchor="w"
        )
        kda_label2.place(x=90, y=50)

        # KDA比
        kda_ratio_label = tk.Label(
            stats_frame,
            text=str(champion["kdaRatio"]),
            bg="#0f3460",
            fg="#4ecca3",
            font=("Arial", 10, "bold"),
            anchor="e"
        )
        kda_ratio_label.place(x=190, y=50)

        # 點擊英雄卡片時的事件
        card_frame.bind("<Button-1>", lambda e, name=champion["name"]: self.controller.show_champion_detail(name))
        name_label.bind("<Button-1>", lambda e, name=champion["name"]: self.controller.show_champion_detail(name))
        type_label.bind("<Button-1>", lambda e, name=champion["name"]: self.controller.show_champion_detail(name))
        stats_frame.bind("<Button-1>", lambda e, name=champion["name"]: self.controller.show_champion_detail(name))

    def search_champions(self, query):
        """搜索英雄"""
        print(f"搜索英雄: {query}")
        # TODO: 實現搜索邏輯
        # 重新載入並顯示符合條件的英雄
        self.current_page = 1
        self.display_champions()

    def filter_champions(self, filter_type):
        """過濾英雄類型"""
        print(f"過濾英雄類型: {filter_type}")

        # 更新按鈕樣式
        for button_type, button in self.filter_buttons.items():
            if button_type == filter_type:
                button.config(bg="#0f3460")
            else:
                button.config(bg="#1a1a2e")

        # TODO: 實現過濾邏輯
        # 重新載入並顯示符合條件的英雄
        self.current_page = 1
        self.display_champions()

    def sort_champions(self, event=None):
        """排序英雄"""
        sort_by = self.sort_var.get()
        print(f"排序英雄: {sort_by}")

        # TODO: 實現排序邏輯
        # 重新載入並顯示排序後的英雄
        self.display_champions()

    def prev_page(self):
        """上一頁"""
        if self.current_page > 1:
            self.current_page -= 1
            self.page_label.config(text=f"{self.current_page}/{self.total_pages}")
            self.display_champions()

    def next_page(self):
        """下一頁"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_label.config(text=f"{self.current_page}/{self.total_pages}")
            self.display_champions()
