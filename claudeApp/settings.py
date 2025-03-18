import tkinter as tk
from tkinter import ttk, filedialog
from rounded_widgets import RoundedFrame, RoundedButton


class SettingsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1a1a2e")
        self.controller = controller

        # 設定初始值
        self.lockfile_path = tk.StringVar(value="C:\\Riot Games\\League of Legends\\lockfile")
        self.language = tk.StringVar(value="中文")
        self.theme = tk.StringVar(value="暗色主題")
        self.auto_detect = tk.BooleanVar(value=True)
        self.refresh_rate = tk.StringVar(value="高 (5秒)")
        self.enable_cache = tk.BooleanVar(value=True)

        # 創建設定頁面
        self.create_settings_page()

    def create_settings_page(self):
        """創建設定頁面"""
        # 主要容器
        main_container = tk.Frame(self, bg="#0f172a")
        main_container.pack(fill="both", expand=True)

        # 設定表單容器
        form_container = RoundedFrame(
            main_container,
            bg_color="#1e293b",
            corner_radius=15,
            border_color="#e94560",
            border_width=1
        )
        form_container.pack(padx=250, pady=100)
        
        # 配置内部框架
        form_container.interior.configure(width=700, height=600)
        form_container.interior.pack_propagate(False)

        # 標題
        title_label = tk.Label(
            form_container.interior,
            text="設定",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 24, "bold")
        )
        title_label.pack(anchor="w", padx=50, pady=(40, 0))

        # 分隔線
        separator = tk.Frame(form_container.interior, bg="#e94560", height=2)
        separator.pack(fill="x", padx=50, pady=15)

        # 一般設定區域
        self.create_general_settings(form_container.interior)

        # 連接設定區域
        self.create_connection_settings(form_container.interior)

        # 數據設定區域
        self.create_data_settings(form_container.interior)

        # 按鈕區域
        self.create_action_buttons(form_container.interior)

    def create_general_settings(self, parent):
        """創建一般設定區域"""
        # 標題
        title_label = tk.Label(
            parent,
            text="一般設定",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 18, "bold")
        )
        title_label.pack(anchor="w", padx=50, pady=(30, 10))

        # 語言設定
        language_label = tk.Label(
            parent,
            text="語言 / Language",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 14)
        )
        language_label.pack(anchor="w", padx=50, pady=(10, 5))

        language_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        language_frame.pack(fill="x", padx=50, pady=5)

        # 中文選項
        cn_radio = tk.Radiobutton(
            language_frame.interior,
            text="中文",
            variable=self.language,
            value="中文",
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.language_changed
        )
        cn_radio.pack(side="left", padx=20, pady=10)

        # 英文選項
        en_radio = tk.Radiobutton(
            language_frame.interior,
            text="English",
            variable=self.language,
            value="English",
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.language_changed
        )
        en_radio.pack(side="left", padx=20, pady=10)

        # 主題設定
        theme_label = tk.Label(
            parent,
            text="主題",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 14)
        )
        theme_label.pack(anchor="w", padx=50, pady=(10, 5))

        theme_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        theme_frame.pack(fill="x", padx=50, pady=5)

        # 暗色主題選項
        dark_radio = tk.Radiobutton(
            theme_frame.interior,
            text="暗色主題",
            variable=self.theme,
            value="暗色主題",
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.theme_changed
        )
        dark_radio.pack(side="left", padx=20, pady=10)

        # 亮色主題選項
        light_radio = tk.Radiobutton(
            theme_frame.interior,
            text="亮色主題",
            variable=self.theme,
            value="亮色主題",
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.theme_changed
        )
        light_radio.pack(side="left", padx=20, pady=10)

    def create_connection_settings(self, parent):
        """創建連接設定區域"""
        # 標題
        title_label = tk.Label(
            parent,
            text="連接設定",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 18, "bold")
        )
        title_label.pack(anchor="w", padx=50, pady=(30, 10))

        # Lockfile 路徑
        path_label = tk.Label(
            parent,
            text="Lockfile 路徑",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 14)
        )
        path_label.pack(anchor="w", padx=50, pady=(10, 5))

        path_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        path_frame.pack(fill="x", padx=50, pady=5)

        path_entry = tk.Entry(
            path_frame.interior,
            textvariable=self.lockfile_path,
            bg="#0f172a",
            fg="#8b8b8b",
            insertbackground="white",
            relief="flat",
            font=("Noto Sans TC", 12),
            width=50
        )
        path_entry.pack(side="left", fill="x", expand=True, pady=5)

        browse_button = RoundedButton(
            path_frame.interior,
            text="瀏覽...",
            command=self.browse_lockfile,
            font=("Noto Sans TC", 12),
            padx=15,
            pady=5,
            radius=8,
            bg="#e94560",
            fg="white",
            highlight_color="#e94560"
        )
        browse_button.pack(side="right", padx=(10, 0), pady=5)

        # 自動檢測選項
        auto_detect_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        auto_detect_frame.pack(fill="x", padx=50, pady=(10, 5))

        auto_detect_check = tk.Checkbutton(
            auto_detect_frame.interior,
            text="自動檢測遊戲客戶端位置",
            variable=self.auto_detect,
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.toggle_auto_detect
        )
        auto_detect_check.pack(anchor="w", padx=10, pady=10)

    def create_data_settings(self, parent):
        """創建數據設定區域"""
        # 標題
        title_label = tk.Label(
            parent,
            text="數據設定",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 18, "bold")
        )
        title_label.pack(anchor="w", padx=50, pady=(30, 10))

        # 數據刷新頻率
        refresh_label = tk.Label(
            parent,
            text="數據刷新頻率",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 14)
        )
        refresh_label.pack(anchor="w", padx=50, pady=(10, 5))

        refresh_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        refresh_frame.pack(fill="x", padx=50, pady=5)

        refresh_options = ["高 (5秒)", "中 (10秒)", "低 (30秒)"]
        for option in refresh_options:
            radio = tk.Radiobutton(
                refresh_frame.interior,
                text=option,
                variable=self.refresh_rate,
                value=option,
                bg="#0f172a",
                fg="white",
                selectcolor="#0f172a",
                activebackground="#0f172a",
                font=("Noto Sans TC", 12),
                command=self.refresh_rate_changed
            )
            radio.pack(side="left", padx=20, pady=10)

        # 數據緩存
        cache_label = tk.Label(
            parent,
            text="數據緩存",
            bg="#1e293b",
            fg="white",
            font=("Noto Sans TC", 14)
        )
        cache_label.pack(anchor="w", padx=50, pady=(10, 5))

        cache_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        cache_frame.pack(fill="x", padx=50, pady=5)

        cache_check = tk.Checkbutton(
            cache_frame.interior,
            text="啟用本地數據緩存 (推薦)",
            variable=self.enable_cache,
            bg="#0f172a",
            fg="white",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            font=("Noto Sans TC", 12),
            command=self.toggle_cache
        )
        cache_check.pack(side="left", padx=10, pady=10)

        cache_size_label = tk.Label(
            cache_frame.interior,
            text="緩存大小: 256 MB",
            bg="#0f172a",
            fg="#8b8b8b",
            font=("Noto Sans TC", 12)
        )
        cache_size_label.pack(side="right", padx=20, pady=10)

    def create_action_buttons(self, parent):
        """創建操作按鈕區域"""
        button_frame = RoundedFrame(
            parent,
            bg_color="#0f172a",
            corner_radius=8,
            border_width=0
        )
        button_frame.pack(fill="x", padx=50, pady=(30, 40))

        # 重置按鈕
        reset_button = RoundedButton(
            button_frame.interior,
            text="重置為預設",
            command=self.reset_settings,
            font=("Noto Sans TC", 14),
            padx=20,
            pady=10,
            radius=8,
            bg="#0f172a",
            fg="white",
            highlight_color="#e94560"
        )
        reset_button.pack(side="left", padx=5)

        # 保存按鈕
        save_button = RoundedButton(
            button_frame.interior,
            text="保存設定",
            command=self.save_settings,
            font=("Noto Sans TC", 14, "bold"),
            padx=20,
            pady=10,
            radius=8,
            bg="#e94560",
            fg="white",
            highlight_color="#e94560"
        )
        save_button.pack(side="right", padx=5)

        # 取消按鈕
        cancel_button = RoundedButton(
            button_frame.interior,
            text="取消",
            command=self.cancel_settings,
            font=("Noto Sans TC", 14),
            padx=20,
            pady=10,
            radius=8,
            bg="#0f172a",
            fg="white",
            highlight_color="#e94560"
        )
        cancel_button.pack(side="right", padx=5)

    def language_changed(self):
        """語言設定變更時的處理"""
        selected_language = self.language.get()
        print(f"語言設定已變更為: {selected_language}")
        # TODO: 實現語言變更邏輯

    def theme_changed(self):
        """主題設定變更時的處理"""
        selected_theme = self.theme.get()
        print(f"主題設定已變更為: {selected_theme}")
        # TODO: 實現主題變更邏輯

    def browse_lockfile(self):
        """瀏覽 Lockfile 路徑"""
        file_path = filedialog.askopenfilename(
            title="選擇 Lockfile 檔案",
            initialdir="C:/Riot Games/League of Legends",
            filetypes=[("所有檔案", "*.*")]
        )

        if file_path:
            self.lockfile_path.set(file_path)

    def toggle_auto_detect(self):
        """切換自動檢測選項"""
        is_auto_detect = self.auto_detect.get()
        print(f"自動檢測已{'啟用' if is_auto_detect else '停用'}")
        # TODO: 實現自動檢測邏輯

    def refresh_rate_changed(self):
        """刷新頻率設定變更時的處理"""
        selected_rate = self.refresh_rate.get()
        print(f"數據刷新頻率已變更為: {selected_rate}")
        # TODO: 實現刷新頻率變更邏輯

    def toggle_cache(self):
        """切換緩存選項"""
        is_cache_enabled = self.enable_cache.get()
        print(f"本地數據緩存已{'啟用' if is_cache_enabled else '停用'}")
        # TODO: 實現緩存選項邏輯

    def reset_settings(self):
        """重置設定為預設值"""
        print("重置設定為預設值")

        # 重置所有設定
        self.lockfile_path.set("C:\\Riot Games\\League of Legends\\lockfile")
        self.language.set("中文")
        self.theme.set("暗色主題")
        self.auto_detect.set(True)
        self.refresh_rate.set("高 (5秒)")
        self.enable_cache.set(True)

        # TODO: 實現重置設定邏輯

    def save_settings(self):
        """保存設定"""
        print("保存設定")
        # TODO: 實現保存設定邏輯

        # 回到上一頁
        self.controller.show_champion_list()

    def cancel_settings(self):
        """取消設定變更"""
        print("取消設定變更")

        # 回到上一頁
        self.controller.show_champion_list()