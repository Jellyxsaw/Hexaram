import base64
import json
import os
import sys
import time
import tkinter as tk
from functools import lru_cache
from threading import Thread
from tkinter import ttk, messagebox, filedialog

import requests
import urllib3
import yaml  # 使用 PyYAML 處理 YAML 格式
from PIL import Image, ImageTk

from apiWorker import recommend_compositions_api


# ------------------ 共用工具函數 ------------------
def get_resource_path(relative_path):
    # 如果被打包，sys._MEIPASS 會指向臨時目錄
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 載入 YAML 設定檔
config_path = get_resource_path("config.yml")
try:
    with open(config_path, "r", encoding="utf-8") as f:
        YAML_CONFIG = yaml.safe_load(f)
except Exception as e:
    raise FileNotFoundError(f"無法讀取設定檔：{config_path}, 錯誤：{e}")

LOCKFILE_PATH = YAML_CONFIG.get("lockfile_path", "")
DEFAULT_LANGUAGE = YAML_CONFIG.get("language", "zh")


# ------------------ 工具函數 ------------------
@lru_cache(maxsize=1)
def get_champion_mappings():
    # 優先檢查本地 JSON 文件
    json_files_exist = os.path.exists('champion_mapping.json') and os.path.exists('chinese_mapping.json')
    if json_files_exist:
        try:
            with open('champion_mapping.json', 'r', encoding='utf-8') as f:
                champ_data = json.load(f)
                id_to_en = {str(v['key']): k for k, v in champ_data.items()}

            with open('chinese_mapping.json', 'r', encoding='utf-8') as f:
                en_to_tw = json.load(f)

            return id_to_en, en_to_tw
        except Exception as e:
            print(f"本地JSON文件讀取失敗: {e}")


def id_to_name(champion_id, id_mapping):
    return id_mapping.get(str(champion_id), "未知英雄")


# ------------------ 核心邏輯類 ------------------
class DataFetcher:
    def __init__(self, lockfile_path=LOCKFILE_PATH):
        self.lockfile_path = lockfile_path
        self.id_mapping, self.tw_mapping = get_champion_mappings()
        # 建立從英文名稱到 key 的反向映射，用於取得圖片
        self.name_to_key = {v: k for k, v in self.id_mapping.items()}

    def fetch_live_data(self):
        try:
            lock_info = self.read_lockfile()
            session = self.get_champ_select_session(lock_info)
            return self.parse_session_data(session) if session else None
        except Exception as e:
            print(f"即時數據獲取失敗: {e}")
            return None

    def read_lockfile(self):
        try:
            with open(self.lockfile_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            parts = content.split(':')
            return {
                'port': parts[2],
                'password': parts[3],
                'protocol': parts[4]
            }
        except Exception as e:
            raise Exception(f"Lockfile讀取失敗: {e}")

    def get_champ_select_session(self, lock_info):
        urllib3.disable_warnings()
        url = f"{lock_info['protocol']}://127.0.0.1:{lock_info['port']}/lol-champ-select/v1/session"
        auth_str = f"riot:{lock_info['password']}"
        headers = {"Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"}
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=3)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            raise Exception(f"API請求失敗: {e}")

    def parse_session_data(self, session):
        # 解析已選英雄
        selected_ids = [
            player['championId']
            for player in session.get('myTeam', [])
            if player.get('championId', 0) > 0
        ]
        # 解析候選池
        bench_ids = [
            champ['championId']
            for champ in session.get('benchChampions', [])
            if champ.get('championId', 0) > 0
        ]
        selected_heroes = [id_to_name(cid, self.id_mapping) for cid in selected_ids]
        candidate_pool = [id_to_name(cid, self.id_mapping) for cid in bench_ids]
        all_pool = selected_heroes + candidate_pool
        return {
            'selected': selected_heroes,
            'candidates': candidate_pool,
            'all_pool': all_pool
        }

    def load_local_data(self):
        LOCAL_TEST_DATA = 'local_session.json'
        try:
            with open(LOCAL_TEST_DATA, 'r', encoding='utf-8') as f:
                return self.parse_session_data(json.load(f))
        except Exception as e:
            print(f"本地數據加載失敗: {e}")
            return None


# ------------------ 樣式配置 ------------------
STYLE_CONFIG = {
    "bg": "#2d2d2d",
    "fg": "#ffffff",
    "accent": "#1abc9c",
    "secondary": "#34495e",
    "font": ("Microsoft JhengHei", 10),
    "title_font": ("Microsoft JhengHei", 12, "bold"),
    "padding": 10,
    "border_radius": 8,
    "button": {"bg": "#3498db", "active_bg": "#2980b9"},
    "card": {"bg": "#34495e", "relief": "flat", "borderwidth": 0}
}


# ------------------ 主應用程式 ------------------
class ModernARAMApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x800")
        self.root.title("ARAM 勝率助手 - 深色版")
        self.root.configure(bg=STYLE_CONFIG["bg"])

        # 新增設定：lockfile 路徑與語言設定（預設從 YAML 載入）
        self.lockfile_path = LOCKFILE_PATH
        self.language = DEFAULT_LANGUAGE  # "zh" 表示中文，"en" 表示英文

        # 初始化圖片緩存
        self.champ_images = {}
        self.load_champion_images()

        self.setup_ui()
        self.apply_styles()
        self.fetcher = DataFetcher(self.lockfile_path)

    def load_champion_images(self):
        img_dir = "champion_images"
        if not os.path.exists(img_dir):
            print("圖片資料夾不存在")
            return
        for filename in os.listdir(img_dir):
            if filename.endswith(".png"):
                key = filename.split(".")[0]
                try:
                    img = Image.open(os.path.join(img_dir, filename))
                    img = img.resize((40, 40), Image.LANCZOS)
                    self.champ_images[key] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"加載圖片失敗: {filename} - {e}")

    def apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=STYLE_CONFIG["bg"], foreground=STYLE_CONFIG["fg"])
        style.configure("TFrame", background=STYLE_CONFIG["bg"])
        style.configure("TLabel", background=STYLE_CONFIG["bg"], foreground=STYLE_CONFIG["fg"])
        style.configure("TButton",
                        background=STYLE_CONFIG["button"]["bg"],
                        foreground="white",
                        font=STYLE_CONFIG["font"],
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", STYLE_CONFIG["button"]["active_bg"])])

        style.configure("Card.TFrame",
                        background=STYLE_CONFIG["card"]["bg"],
                        relief=STYLE_CONFIG["card"]["relief"],
                        borderwidth=STYLE_CONFIG["card"]["borderwidth"])

        style.configure("Treeview",
                        background=STYLE_CONFIG["card"]["bg"],
                        fieldbackground=STYLE_CONFIG["card"]["bg"],
                        foreground=STYLE_CONFIG["fg"],
                        rowheight=40)
        style.configure("Treeview.Heading",
                        background=STYLE_CONFIG["secondary"],
                        foreground=STYLE_CONFIG["fg"],
                        font=STYLE_CONFIG["title_font"])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def setup_ui(self):
        # 頂部控制欄
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)

        self.mode_var = tk.BooleanVar(value=True)
        self.mode_switch = ttk.Checkbutton(
            control_frame,
            text="即時模式",
            variable=self.mode_var,
            style="Switch.TCheckbutton"
        )
        self.mode_switch.pack(side=tk.LEFT, padx=5)

        # 新增設定按鈕
        self.settings_btn = ttk.Button(
            control_frame,
            text="設定/setting",
            command=self.open_settings
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = ttk.Button(
            control_frame,
            text="🔄 立即刷新",
            command=self.refresh_data
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=5)

        # 主內容區域
        main_panel = ttk.Frame(self.root)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左側面板
        left_panel = ttk.Frame(main_panel, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 已選英雄卡片 (改為使用 Frame 與 Label 顯示圖片與文字)
        self.selected_card = self.create_card(left_panel, "已選英雄")
        self.selected_card.pack(fill=tk.X, padx=5, pady=5)
        self.selected_frame = ttk.Frame(self.selected_card)
        self.selected_frame.pack(fill=tk.BOTH, expand=True)

        # 候選池卡片
        self.candidate_card = self.create_card(left_panel, "可用英雄池")
        self.candidate_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.candidate_canvas = tk.Canvas(
            self.candidate_card,
            bg=STYLE_CONFIG["card"]["bg"],
            highlightthickness=0
        )
        self.candidate_scroll = ttk.Scrollbar(
            self.candidate_card,
            orient="vertical",
            command=self.candidate_canvas.yview
        )
        self.candidate_frame = ttk.Frame(self.candidate_canvas)

        self.candidate_canvas.configure(yscrollcommand=self.candidate_scroll.set)
        self.candidate_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.candidate_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.candidate_canvas.create_window((0, 0), window=self.candidate_frame, anchor="nw")
        self.candidate_frame.bind("<Configure>", lambda e: self.candidate_canvas.configure(
            scrollregion=self.candidate_canvas.bbox("all"))
                                  )

        # 右側結果面板
        self.result_card = self.create_card(main_panel, "推薦陣容", width=700)
        self.result_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 在 result_card 內建立一個容器，讓 grid 佈局只作用於該容器
        result_container = ttk.Frame(self.result_card)
        result_container.pack(fill=tk.BOTH, expand=True)

        self.result_tree = ttk.Treeview(
            result_container,
            columns=("win_rate", "composition"),
            show="headings",
            height=15
        )
        self.result_tree.heading("win_rate", text="勝率", anchor=tk.W)
        self.result_tree.heading("composition", text="陣容組合", anchor=tk.W)
        self.result_tree.column("win_rate", width=100, anchor=tk.W)
        self.result_tree.column("composition", width=500, anchor=tk.W)

        vsb = ttk.Scrollbar(result_container, orient="vertical", command=self.result_tree.yview)
        hsb = ttk.Scrollbar(result_container, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.result_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        result_container.grid_rowconfigure(0, weight=1)
        result_container.grid_columnconfigure(0, weight=1)

    def create_card(self, parent, title, width=None):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=STYLE_CONFIG["padding"])
        if width:
            frame.config(width=width)
        ttk.Label(frame, text=title, style="TLabel", font=STYLE_CONFIG["title_font"]).pack(anchor=tk.W)
        return frame

    def get_champ_key(self, en_name):
        return self.fetcher.name_to_key.get(en_name, "default")

    def get_tw_name(self, en_name):
        return self.fetcher.tw_mapping.get(en_name, "未知")

    def refresh_data(self):
        Thread(target=self._refresh_data, daemon=True).start()

    def _refresh_data(self):
        try:
            data = None
            if self.mode_var.get():
                data = self.fetcher.fetch_live_data()

            if not data:
                data = self.fetcher.load_local_data()
                messagebox.showwarning("警告", "無法取得即時數據，已使用本地測試資料")

            if data:
                self.update_ui(data)
                self.calculate_recommendations(data['all_pool'])

        except Exception as e:
            messagebox.showerror("錯誤", f"資料刷新失敗: {str(e)}")

    def update_ui(self, data):
        # 更新已選英雄：先清空選單，再依序加入圖片與文字
        for widget in self.selected_frame.winfo_children():
            widget.destroy()

        for hero in data['selected']:
            key = self.get_champ_key(hero)
            img = self.champ_images.get(key)
            if self.language == "zh":
                display_name = self.get_tw_name(hero)
            else:
                display_name = hero
            hero_frame = ttk.Frame(self.selected_frame, padding=5)
            hero_frame.pack(side=tk.LEFT, padx=5, pady=5)
            if img:
                lbl_img = ttk.Label(hero_frame, image=img)
                lbl_img.image = img  # 保存參考，避免被垃圾回收
                lbl_img.pack()
            ttk.Label(hero_frame, text=display_name, font=STYLE_CONFIG["font"], foreground=STYLE_CONFIG["fg"]).pack()

        # 更新候選池（圖片網格）
        for widget in self.candidate_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        for hero in data['candidates']:
            key = self.get_champ_key(hero)
            frame = ttk.Frame(self.candidate_frame, padding=5)
            if key in self.champ_images:
                label = ttk.Label(frame, image=self.champ_images[key])
                label.image = self.champ_images[key]
                label.pack(side=tk.TOP)
            if self.language == "zh":
                display_name = self.get_tw_name(hero)
            else:
                display_name = hero
            ttk.Label(frame, text=display_name,
                      font=STYLE_CONFIG["font"],
                      foreground=STYLE_CONFIG["fg"]).pack(side=tk.BOTTOM)
            frame.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col > 5:
                col = 0
                row += 1

    def calculate_recommendations(self, candidate_pool):
        start_time = time.time()
        sorted_compositions = recommend_compositions_api(candidate_pool)
        elapsed = time.time() - start_time

        self.result_tree.delete(*self.result_tree.get_children())

        if not sorted_compositions:
            messagebox.showinfo("提示", "可用英雄不足5個，無法計算組合")
            return

        # 顯示推薦的前10個最佳陣容（勝率最高）
        for comp, prob in sorted_compositions[-10:][::-1]:
            if self.language == "zh":
                names = [self.get_tw_name(h) for h in comp]
            else:
                names = list(comp)
            self.result_tree.insert('', tk.END, values=(
                f"{prob:.2%}",
                "、".join(names)
            ))

        print(f"計算完成，耗時: {elapsed:.2f}秒")

    def open_settings(self):
        # 建立設定視窗並調整背景顏色讓文字易讀
        settings_win = tk.Toplevel(self.root)
        settings_win.title("設定")
        settings_win.grab_set()
        settings_win.configure(bg="#f0f0f0")  # 使用淺色背景

        # 針對設定視窗建立專屬樣式
        s = ttk.Style()
        s.configure("Settings.TLabel", background="#f0f0f0", foreground="black", font=STYLE_CONFIG["font"])
        s.configure("Settings.TEntry", fieldbackground="white", foreground="black", font=STYLE_CONFIG["font"])

        # Lockfile 路徑設定
        lockfile_label = ttk.Label(settings_win, text="Lockfile 位置:", style="Settings.TLabel")
        lockfile_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        lockfile_entry = ttk.Entry(settings_win, width=50, style="Settings.TEntry")
        lockfile_entry.grid(row=0, column=1, padx=5, pady=5)
        lockfile_entry.insert(0, self.lockfile_path)
        browse_btn = ttk.Button(settings_win, text="瀏覽", command=lambda: self.browse_lockfile(lockfile_entry))
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # 語言設定
        lang_label = ttk.Label(settings_win, text="語言:", style="Settings.TLabel")
        lang_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        lang_var = tk.StringVar(value=self.language)
        rb_zh = ttk.Radiobutton(settings_win, text="中文", variable=lang_var, value="zh")
        rb_en = ttk.Radiobutton(settings_win, text="english", variable=lang_var, value="en")
        rb_zh.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        rb_en.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # 儲存與取消按鈕
        save_btn = ttk.Button(settings_win, text="保存",
                              command=lambda: self.save_settings(lockfile_entry.get(), lang_var.get(), settings_win))
        save_btn.grid(row=2, column=1, padx=5, pady=10)
        cancel_btn = ttk.Button(settings_win, text="取消", command=settings_win.destroy)
        cancel_btn.grid(row=2, column=2, padx=5, pady=10)

    def browse_lockfile(self, entry):
        file_path = filedialog.askopenfilename(title="選擇 Lockfile",
                                               filetypes=[("All Files", "*.*")])
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def save_settings(self, new_lockfile_path, new_lang, win):
        self.lockfile_path = new_lockfile_path
        self.language = new_lang
        # 更新 fetcher 使用新的 lockfile 路徑
        self.fetcher = DataFetcher(self.lockfile_path)
        messagebox.showinfo("提示", "設定已保存")
        win.destroy()

        # 將新的設定同步寫入 YAML 檔案
        YAML_CONFIG["lockfile_path"] = self.lockfile_path
        YAML_CONFIG["language"] = self.language
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(YAML_CONFIG, f, allow_unicode=True)
        except Exception as e:
            print(f"寫入設定檔失敗: {e}")


if __name__ == "__main__":
    urllib3.disable_warnings()
    root = tk.Tk()
    app = ModernARAMApp(root)
    root.mainloop()
