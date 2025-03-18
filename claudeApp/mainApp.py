import os
import tkinter as tk
import atexit
import signal
import sys
from tkinter import ttk, font
from data_manager import DataManager

import dataFetcher
# 導入各界面模組
from champion_list import ChampionListFrame
from util import load_champion_images
# 導入圓角小部件
from rounded_widgets import RoundedFrame, RoundedButton
from settings import SettingsFrame
from stats_analysis import StatsAnalysisFrame
from team_comp import TeamCompFrame
from teammate_stats import TeammateStatsFrame

# 全局變量用於控制程序退出
is_shutting_down = False

def cleanup_resources():
    """清理所有資源的函數"""
    global is_shutting_down
    is_shutting_down = True

# 註冊清理函數
atexit.register(cleanup_resources)

# 註冊信號處理
def signal_handler(signum, frame):
    cleanup_resources()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ARAMAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hexaram")
        self.root.geometry("1200x800")
        
        # 綁定窗口關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.fetcher = dataFetcher.DataFetcher()
        self.data_manager = DataManager()
        
        # 初始化圖片資源
        self.champ_images = {}
        self.load_champion_images()
        
        # 設置深色主題背景 - 調整為更接近設計圖的顏色
        self.bg_color = "#0f172a"  # 主背景色 - 更深的蓝色
        self.accent_color = "#e94560"  # 強調色 - 保持红色
        self.text_color = "#FFFFFF"  # 文字顏色
        self.highlight_color = "#e94560"  # 高亮色 - 与强调色一致
        self.secondary_bg = "#1e293b"  # 次要背景色 - 更深的蓝灰色
        self.nav_bg = "#1e293b"  # 导航栏背景色
        self.content_area_bg = "#0f172a"  # 内容区域背景色
        self.button_bg = "#1e293b"  # 按钮背景色
        self.alternate_row_bg = "#0f172a"  # 表格交替行背景色
        self.hover_color = "#334155"  # 悬停颜色

        # 設定圓角半徑
        self.corner_radius = 10  # 全局圓角半徑設定

        self.root.configure(bg=self.bg_color)
        self.root.resizable(True, True)

        # 設置最小視窗大小
        self.root.minsize(1656, 1024)

        # 載入自訂字體
        self.load_custom_fonts()

        # 設定應用程式風格
        self.setup_style()

        # 創建主要框架
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill="both", expand=True)

        # 創建頂部導航欄
        self.create_nav_bar()

        # 初始化內容框架 (使用圓角框架)
        self.content_frame = RoundedFrame(
            self.main_frame,
            bg_color=self.secondary_bg,
            corner_radius=self.corner_radius,
            border_color=self.accent_color,
            border_width=1
        )
        # 增加內容區域的間距和內邊距
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(15, 20))

        # 顯示默認頁面 (推薦)
        self.show_team_comp()

    def load_custom_fonts(self):
        """載入自訂字體到應用程式"""
        # 建立字體目錄 (如果不存在)
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)

        # 定義字體檔案路徑
        self.font_paths = {
            "regular": os.path.join(fonts_dir, "NotoSansTC-Regular.ttf"),
            "medium": os.path.join(fonts_dir, "NotoSansTC-Medium.ttf"),
            "bold": os.path.join(fonts_dir, "NotoSansTC-Bold.ttf"),
        }

        # 註冊字體 (如果存在)
        all_fonts_exist = all(os.path.exists(font_path) for font_path in self.font_paths.values())

        if all_fonts_exist:
            try:
                # 在 Tkinter 中註冊字體
                font_loaded = False

                # 方式一: 使用 tkinter 原生方法
                try:
                    font_id_regular = font.families()  # 檢查當前可用字體

                    # 加載字體
                    font_id_regular = font.Font(family="Noto Sans TC", size=10, weight="normal")
                    font_id_bold = font.Font(family="Noto Sans TC", size=10, weight="bold")

                    # 使用字體名稱
                    self.font_family = "Noto Sans TC"
                    self.font_family_bold = "Noto Sans TC"
                    self.font_family_medium = "Noto Sans TC"

                    font_loaded = True
                    print("已使用 tkinter 原生方法載入字體")
                except Exception as e1:
                    print(f"使用 tkinter 原生方法載入字體失敗: {str(e1)}")

                # 方式二: 嘗試使用 tkFont 加載 (適用於某些平台)
                if not font_loaded:
                    try:
                        self.custom_font_regular = font.Font(file=self.font_paths["regular"], family="NotoSansTC",
                                                             size=10)
                        self.custom_font_bold = font.Font(file=self.font_paths["bold"], family="NotoSansTCBold",
                                                          size=10)
                        self.custom_font_medium = font.Font(file=self.font_paths["medium"], family="NotoSansTCMedium",
                                                            size=10)

                        self.font_family = "NotoSansTC"
                        self.font_family_bold = "NotoSansTCBold"
                        self.font_family_medium = "NotoSansTCMedium"

                        font_loaded = True
                        print("已使用 tkFont 載入字體")
                    except Exception as e2:
                        print(f"使用 tkFont 載入字體失敗: {str(e2)}")

                if font_loaded:
                    print("成功載入自訂字體")
                else:
                    # 如果無法載入字體，使用系統字體後備方案
                    self._use_system_fonts()

            except Exception as e:
                print(f"載入字體時發生錯誤: {str(e)}")
                self._use_system_fonts()
        else:
            missing_fonts = [os.path.basename(path) for path, exists in
                             {path: os.path.exists(path) for path in self.font_paths.values()}.items()
                             if not exists]
            print(f"缺少以下字體檔案: {', '.join(missing_fonts)}")
            self._use_system_fonts()

    def _use_system_fonts(self):
        """當自訂字體無法載入時使用系統字體"""
        # 優先選擇微軟正黑體，然後是其他備選字體
        font_options = [
            "Microsoft JhengHei UI", "Microsoft JhengHei",
            "Noto Sans TC", "Microsoft YaHei UI",
            "PingFang TC", "Heiti TC", "SimHei", "Arial Unicode MS", "Arial"
        ]

        # 嘗試使用微軟正黑體
        self.font_family = font_options[0]  # 微軟正黑體 UI
        self.font_family_bold = self.font_family
        self.font_family_medium = self.font_family

        print(f"使用系統字體: {self.font_family} 作為後備方案")

        # 嘗試設定全局默認字體
        try:
            default_font = font.nametofont("TkDefaultFont")
            default_font.configure(family=self.font_family, size=10)

            # 設定其他系統字體
            for font_name in ["TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"]:
                try:
                    system_font = font.nametofont(font_name)
                    system_font.configure(family=self.font_family, size=10)
                except:
                    pass  # 忽略不存在的字體

            print("已設定全局系統字體")
        except Exception as e:
            print(f"設定全局字體時發生錯誤: {str(e)}")

    def setup_style(self):
        """設置應用程式風格"""
        style = ttk.Style()

        # 基本設置
        style.theme_use('clam')  # 使用clam主題作為基礎

        # 設置字體大小
        title_size = 18  # 增加標題字體大小
        nav_size = 14
        label_size = 12
        button_size = 12
        entry_size = 12

        # === 全局設定默認字體 ===
        # 設定所有可能使用的控件類型的默認字體
        standard_widgets = [
            "TLabel", "TButton", "TEntry", "TCombobox", "TCheckbutton",
            "TRadiobutton", "Treeview", "TNotebook", "TFrame", "TScrollbar",
            "Horizontal.TScrollbar", "Vertical.TScrollbar", "TSpinbox", "TProgressbar",
            "TMenubutton", "TLabelframe", "TScale", "Horizontal.TScale", "Vertical.TScale"
        ]

        # 為所有標準控件設定默認字體
        for widget in standard_widgets:
            style.configure(widget, font=(self.font_family, label_size))

        # 為樹狀視圖標題設定字體
        style.configure("Treeview.Heading", 
                       background=self.secondary_bg,
                       foreground=self.text_color,
                       font=(self.font_family_bold, label_size))

        # 為文本標籤設定默認樣式
        style.configure(
            "TLabel",
            background=self.secondary_bg,
            foreground=self.text_color,
            font=(self.font_family, label_size)
        )

        # 為按鈕設定默認樣式
        style.configure(
            "TButton",
            font=(self.font_family, button_size),
            padding=(12, 6),
            background=self.button_bg,
            foreground=self.text_color
        )

        # 為輸入框設定默認樣式
        style.configure(
            "TEntry",
            font=(self.font_family, entry_size),
            fieldbackground=self.secondary_bg,
            foreground=self.text_color
        )

        # 為下拉菜單設定默認樣式
        style.configure(
            "TCombobox",
            font=(self.font_family, entry_size),
            background=self.secondary_bg,
            foreground=self.text_color,
            fieldbackground=self.secondary_bg
        )

        # ===== 特定樣式設定 =====
        # 創建導航按鈕樣式 (普通狀態) - 圓角設計
        style.configure(
            "Nav.TButton",
            background=self.nav_bg,
            foreground=self.text_color,
            borderwidth=0,
            focuscolor=self.highlight_color,
            padding=(12, 8),
            font=(self.font_family, nav_size),
            relief="flat"
        )

        # 創建導航按鈕樣式 (活動狀態)
        style.map(
            "Nav.TButton",
            background=[("active", self.button_bg), ("selected", self.button_bg)],
            foreground=[("active", self.text_color)],
            relief=[("active", "flat"), ("selected", "flat")]
        )

        # 創建活動導航按鈕樣式
        style.configure(
            "Active.Nav.TButton",
            background=self.button_bg,
            foreground=self.text_color,
            borderwidth=0,
            focuscolor="none",
            padding=(12, 8),
            font=(self.font_family_bold, nav_size)
        )

        # 創建標題標籤樣式
        style.configure(
            "Title.TLabel",
            background=self.nav_bg,
            foreground=self.highlight_color,
            font=(self.font_family_bold, title_size),
            padding=(0, 8)
        )

        # 設置一般標籤樣式 (再次設定以覆蓋前面的設定)
        style.configure(
            "TLabel",
            background=self.secondary_bg,
            foreground=self.text_color,
            font=(self.font_family, label_size)
        )

        # 創建刷新按鈕樣式 - 更符合設計圖的紅色調
        style.configure(
            "Refresh.TButton",
            background=self.button_bg,
            foreground=self.text_color,
            borderwidth=0,
            padding=(10, 6),
            font=(self.font_family, nav_size),
            relief="flat"
        )

        style.map(
            "Refresh.TButton",
            background=[("active", self.highlight_color)],
            relief=[("active", "flat")]
        )

        # === 滾動條樣式 ===
        # 自定義滾動條樣式
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=self.secondary_bg,
            troughcolor=self.bg_color,
            borderwidth=0,
            arrowsize=0,
            width=10
        )

        style.map(
            "Custom.Vertical.TScrollbar",
            background=[("active", self.accent_color), ("pressed", self.highlight_color)]
        )

        # === 圓角按鈕樣式 ===
        # 自定義圓角按鈕風格
        style.configure(
            "Rounded.TButton",
            background=self.button_bg,
            foreground=self.text_color,
            borderwidth=0,
            focuscolor=self.highlight_color,
            padding=(12, 8),
            font=(self.font_family, button_size),
            relief="flat"
        )

        style.map(
            "Rounded.TButton",
            background=[("active", self.highlight_color)],
            foreground=[("active", self.text_color)],
            relief=[("active", "flat"), ("selected", "flat")]
        )

        # === 原始風格控件樣式 ===
        # 設置 tk 原始按鈕的默認參數值
        # 這對於在 TeamCompFrame 等保留原始設計的頁面中很重要
        self.root.option_add("*Button.background", self.button_bg)
        self.root.option_add("*Button.foreground", "white")
        self.root.option_add("*Button.relief", "flat")
        self.root.option_add("*Button.borderWidth", 0)

        # 突出顯示按鈕的默認值 (如"選擇陣容"按鈕)
        self.root.option_add("*Highlight.Button.background", self.accent_color)
        self.root.option_add("*Highlight.Button.foreground", "white")

        # === 嘗試設定全局默認字體 ===
        try:
            # 設定標準 Tkinter 字體
            default_font = font.nametofont("TkDefaultFont")
            default_font.configure(family=self.font_family, size=10)

            text_font = font.nametofont("TkTextFont")
            text_font.configure(family=self.font_family, size=10)

            fixed_font = font.nametofont("TkFixedFont")
            fixed_font.configure(family=self.font_family, size=10)

            # 設定選項默認值
            self.root.option_add("*Font", default_font)

            print("已設定全局默認字體")
        except Exception as e:
            print(f"設定全局默認字體時發生錯誤: {str(e)}")

    def create_nav_bar(self):
        """創建頂部導航欄"""
        # 定義導航欄字體大小
        nav_size = 14  # 导航栏字体大小

        # 導航欄框架 - 增加高度以符合設計
        nav_bar = RoundedFrame(
            self.main_frame,
            bg_color=self.nav_bg,
            corner_radius=0,  # 只圓角底部
            border_width=0
        )
        nav_bar.interior.configure(height=70)  # 增加导航栏高度
        nav_bar.pack(fill="x", side="top", padx=0, pady=0)

        # 添加一個細線作為分隔
        separator = ttk.Separator(self.main_frame, orient="horizontal")
        separator.pack(fill="x", side="top", padx=0, pady=0)

        # 應用程式標題 (使用圖標和標題組合)
        title_frame = tk.Frame(nav_bar.interior, bg=self.nav_bg)
        title_frame.pack(side="left", padx=(30, 40), pady=15)  # 调整左右间距

        title_label = tk.Label(
            title_frame,
            text="Hexaram",
            bg=self.nav_bg,
            fg=self.highlight_color,
            font=(self.font_family_bold, 24)  # 增加字体大小
        )
        title_label.pack(side="left")

        # 導航按鈕
        self.nav_buttons = {}
        nav_frame = tk.Frame(nav_bar.interior, bg=self.nav_bg)
        nav_frame.pack(side="left", fill="y")

        # 定義導航按鈕樣式
        nav_button_style = {
            "font": (self.font_family, nav_size),
            "padx": 20,
            "pady": 8,
            "radius": 8,
            "bg": self.nav_bg,
            "fg": self.text_color,
            "highlight_color": self.highlight_color
        }

        # 創建導航按鈕
        nav_items = [
            ("陣容推薦", self.show_team_comp),
            ("英雄列表", self.show_champion_list),
            ("隊友數據", self.show_teammate_stats),
            ("數據分析", self.show_stats_analysis),
            ("設定", self.show_settings)
        ]

        for text, command in nav_items:
            btn = RoundedButton(
                nav_frame,
                text=text,
                command=command,
                **nav_button_style
            )
            btn.pack(side="left", padx=5)
            self.nav_buttons[text] = btn

        # 添加右側工具欄
        tools_frame = tk.Frame(nav_bar.interior, bg=self.nav_bg)
        tools_frame.pack(side="right", padx=20, pady=10)

        # 刷新按鈕
        refresh_btn = RoundedButton(
            tools_frame,
            text="刷新",
            command=self.refresh_data,
            font=(self.font_family, nav_size),
            padx=15,
            pady=5,
            radius=8,
            bg=self.button_bg,
            fg=self.text_color,
            highlight_color=self.highlight_color
        )
        refresh_btn.pack(side="right", padx=5)

    def toggle_real_time(self):
        """切換實時模式"""
        # TODO: 實現實時模式的切換邏輯
        print(f"實時模式: {'開啟' if self.real_time_switch_var.get() else '關閉'}")

    def refresh_data(self):
        """刷新数据"""
        try:
            # 获取实时数据
            data = self.fetcher.fetch_live_data()
            
            # 如果无法获取实时数据，使用本地数据
            if not data:
                data = self.fetcher.load_local_data()
                print("无法获取实时数据，已使用本地测试数据")
            
            if data:
                # 更新当前页面
                self.refresh_current_page()
        except Exception as e:
            print(f"数据刷新失败: {str(e)}")

    def refresh_current_page(self):
        """刷新當前頁面"""
        # 獲取當前頁面並刷新
        for name, button in self.nav_buttons.items():
            if button.bg_color == self.button_bg:  # 注意: 用 bg_color 而不是 cget("bg")
                if name == "team_comp":
                    self.show_team_comp(refresh=True)
                elif name == "stats":
                    self.show_stats_analysis(refresh=True)
                elif name == "teammates":
                    self.show_teammate_stats(refresh=True)
                elif name == "settings":
                    self.show_settings(refresh=True)
                elif name == "champ_list":
                    self.show_champion_list(refresh=True)
                return

        # 如果沒有選中的導航按鈕，則刷新陣容推薦頁面
        self.show_team_comp(refresh=True)

    def update_nav_buttons(self, active_button):
        """更新導航按鈕樣式"""
        for button_name, button in self.nav_buttons.items():
            if button_name == active_button:
                button.configure(selected=True)  # 設置選中狀態
            else:
                button.configure(selected=False)  # 取消選中狀態

    def clear_content(self):
        """清除內容區域"""
        for widget in self.content_frame.interior.winfo_children():
            widget.destroy()

    def update_child_frame_fonts(self, frame):
        """遞迴更新子框架中的所有控件字體"""
        for child in frame.winfo_children():
            try:
                # 更新 tkinter 標籤字體
                if isinstance(child, tk.Label) or isinstance(child, tk.Button) or \
                        isinstance(child, tk.Checkbutton) or isinstance(child, tk.Radiobutton):
                    child.configure(font=(self.font_family, 10))

                # 更新 tkinter 文字控件字體
                elif isinstance(child, tk.Entry) or isinstance(child, tk.Text) or \
                        isinstance(child, tk.Listbox):
                    child.configure(font=(self.font_family, 10))

                # 特殊處理標題或強調文字
                if isinstance(child, tk.Label):
                    # 檢查標籤是否可能是標題或強調文字
                    current_font = child.cget("font")
                    if isinstance(current_font, tuple) and len(current_font) > 1:
                        size = current_font[1]
                        if size > 10:  # 如果字體大小大於標準大小，視為標題或強調
                            child.configure(font=(self.font_family_bold, size))

                # 如果是框架，則遞迴更新其子控件
                if hasattr(child, 'winfo_children'):
                    self.update_child_frame_fonts(child)
            except Exception as e:
                # 忽略更新特定控件時可能發生的錯誤
                print(f"更新控件字體時發生錯誤: {str(e)}")
                continue

    def show_champion_list(self, refresh=False):
        """顯示英雄列表"""
        self.update_nav_buttons("英雄列表")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置原始的 ChampionListFrame
        champion_list_frame = ChampionListFrame(container.interior, self)
        champion_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(champion_list_frame)

    def show_team_comp(self, refresh=False):
        """顯示陣容推薦頁面"""
        self.update_nav_buttons("陣容推薦")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置原始的 TeamCompFrame
        team_comp_frame = TeamCompFrame(container.interior, self)
        team_comp_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(team_comp_frame)

    def _prepare_champion_data(self):
        """準備英雄數據，包括圖片"""
        # 這個方法將創建英雄數據列表，每個英雄包含 id, name 和 image
        champion_data = []

        # 假設我們有一個 fetcher 對象，可以獲取英雄數據
        if hasattr(self, 'fetcher') and self.fetcher:
            # 如果你的 fetcher 有相應方法，請使用它們
            # 這裡使用模擬數據作為示例

            # 获取可用的英雄池
            champions = []

            try:
                # 嘗試從 fetcher 獲取數據
                if hasattr(self.fetcher, 'fetch_live_data'):
                    data = self.fetcher.fetch_live_data()
                    if data and 'all_pool' in data:
                        champions = data['all_pool']

                # 如果沒有數據，使用本地測試數據
                if not champions and hasattr(self.fetcher, 'load_local_data'):
                    data = self.fetcher.load_local_data()
                    if data and 'all_pool' in data:
                        champions = data['all_pool']

                # 如果仍然沒有數據，使用模擬數據
                if not champions:
                    # 模擬英雄數據
                    champions = [
                        'Ahri', 'Ashe', 'Blitzcrank', 'Caitlyn', 'Darius',
                        'Ezreal', 'Garen', 'Jinx', 'Lux', 'Morgana',
                        'Varus', 'Veigar', 'Yasuo', 'Zed', 'Ziggs',
                        'Viktor', 'Taliyah', 'Leblanc', 'Braum', 'Sona'
                    ]

                # 構建英雄數據對象
                for i, champion_name in enumerate(champions):
                    champion = {
                        "id": i + 1,  # 使用索引作為臨時 ID
                        "name": champion_name,
                        "image": None  # 預設沒有圖片
                    }

                    # 如果有 champ_images 屬性，嘗試獲取英雄圖片
                    if hasattr(self, 'champ_images'):
                        if champion_name in self.champ_images:
                            champion["image"] = self.champ_images[champion_name]
                        elif hasattr(self.fetcher, 'get_champ_key'):
                            # 嘗試使用 fetcher 的方法獲取圖片鍵
                            key = self.fetcher.get_champ_key(champion_name)
                            if key in self.champ_images:
                                champion["image"] = self.champ_images[key]

                    champion_data.append(champion)
            except Exception as e:
                print(f"準備英雄數據時發生錯誤: {e}")
                # 出錯時使用簡單的模擬數據
                for i in range(10):
                    champion_data.append({
                        "id": i + 1,
                        "name": f"英雄{i + 1}",
                        "image": None
                    })

        return champion_data

    def show_stats_analysis(self, refresh=False):
        """顯示數據分析頁面"""
        self.update_nav_buttons("數據分析")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置原始的 StatsAnalysisFrame
        stats_analysis_frame = StatsAnalysisFrame(container.interior, self)
        stats_analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(stats_analysis_frame)

    def show_teammate_stats(self, refresh=False):
        """顯示隊友戰績頁面"""
        self.update_nav_buttons("隊友數據")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置原始的 TeammateStatsFrame
        teammate_stats_frame = TeammateStatsFrame(container.interior, self)
        teammate_stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(teammate_stats_frame)

    def show_settings(self, refresh=False):
        """顯示設定頁面"""
        self.update_nav_buttons("設定")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置原始的 SettingsFrame
        settings_frame = SettingsFrame(container.interior, self)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(settings_frame)

    def show_champion_detail(self, champion_name):
        """顯示英雄詳細資訊"""
        print(f"顯示英雄詳細資訊: {champion_name}")
        self.clear_content()

        # 建立圓角容器
        container = RoundedFrame(
            self.content_frame.interior,
            bg_color=self.content_area_bg,
            corner_radius=self.corner_radius,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 在圓角容器內放置英雄詳細資訊
        from champion_detail import ChampionDetailFrame
        champion_detail_frame = ChampionDetailFrame(container.interior, self, champion_name)
        champion_detail_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 更新子頁面的字體
        self.update_child_frame_fonts(champion_detail_frame)

    def load_champion_images(self):
        load_champion_images(self)

    def on_closing(self):
        """處理窗口關閉事件"""
        try:
            # 設置關閉標誌
            global is_shutting_down
            is_shutting_down = True
            
            # 清理圖片資源
            for img in self.champ_images.values():
                if hasattr(img, 'close'):
                    try:
                        img.close()
                    except:
                        pass
            
            # 清理其他資源
            if hasattr(self, 'fetcher'):
                if hasattr(self.fetcher, 'close'):
                    self.fetcher.close()
            
            if hasattr(self, 'data_manager'):
                if hasattr(self.data_manager, 'close'):
                    self.data_manager.close()
            
            # 銷毀所有子窗口
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    widget.destroy()
            
            # 關閉主窗口
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            print(f"關閉程序時發生錯誤: {str(e)}")
        finally:
            sys.exit(0)


# 主程式入口
if __name__ == "__main__":
    # 檢查字體目錄
    fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
        print(f"已創建字體目錄: {fonts_dir}")
        print("請從以下網址手動下載 Noto Sans TC 字體:")
        print("https://fonts.google.com/noto/specimen/Noto+Sans+TC")
        print("下載後，請將以下字體檔案放入上述字體目錄:")
        print("- NotoSansTC-Regular.ttf")
        print("- NotoSansTC-Medium.ttf")
        print("- NotoSansTC-Bold.ttf")

    # 檢查字體檔案
    required_fonts = ["NotoSansTC-Regular.ttf", "NotoSansTC-Medium.ttf", "NotoSansTC-Bold.ttf"]
    missing_fonts = [f for f in required_fonts if not os.path.exists(os.path.join(fonts_dir, f))]

    if missing_fonts:
        print(f"缺少以下字體檔案: {', '.join(missing_fonts)}")
        print("程式將使用系統字體作為後備方案。")
        print("您可以手動下載所需字體並放入字體目錄以改進顯示效果。")

    root = tk.Tk()
    app = ARAMAnalyzerApp(root)
    root.mainloop()
