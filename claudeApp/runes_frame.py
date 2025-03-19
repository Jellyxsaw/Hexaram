import tkinter as tk
from pathlib import Path
import os
from PIL import Image, ImageTk
import logging
from rounded_widgets import RoundedFrame

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RunesFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#0A1428", **kwargs)
        self.parent = parent
        
        # 初始化符文图片缓存
        self.rune_images = {}
        
        # 创建主容器
        self.main_container = RoundedFrame(
            self,
            bg_color="#0A1428",
            corner_radius=10,
            border_width=0
        )
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建符文展示区域
        self.create_runes_display()
        
    def create_runes_display(self):
        """创建符文展示区域"""
        # 符文配置标题
        self.title_label = tk.Label(
            self.main_container.interior,
            text="符文配置 (勝率: 71.4%)",
            bg="#0A1428",
            fg="white",
            font=("Microsoft JhengHei", 14, "bold")
        )
        self.title_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        # 创建符文框架
        self.runes_frame = RoundedFrame(
            self.main_container.interior,
            bg_color="#091428",
            corner_radius=5,
            border_width=0
        )
        self.runes_frame.pack(fill="x", padx=20, pady=10)
        self.runes_frame.interior.configure(height=80)
        self.runes_frame.interior.pack_propagate(False)
        
        # 创建符文区域
        self.create_rune_slots()
        
    def create_rune_slots(self):
        """创建符文槽位"""
        # 主系符文框架
        self.primary_rune_frame = RoundedFrame(
            self.runes_frame.interior,
            bg_color="#0A1428",
            corner_radius=5,
            border_width=1,
            border_color="#17313f"
        )
        self.primary_rune_frame.place(x=30, y=15)
        self.primary_rune_frame.interior.configure(width=50, height=50)
        self.primary_rune_frame.interior.pack_propagate(False)
        
        # 主系符文ID标签
        self.primary_id_label = tk.Label(
            self.runes_frame.interior,
            text="8128",
            bg="#091428",
            fg="#666666",
            font=("Microsoft JhengHei", 8)
        )
        self.primary_id_label.place(x=30, y=65)
        
        # 副系符文框架
        self.secondary_rune_frame = RoundedFrame(
            self.runes_frame.interior,
            bg_color="#0A1428",
            corner_radius=5,
            border_width=1,
            border_color="#17313f"
        )
        self.secondary_rune_frame.place(x=100, y=15)
        self.secondary_rune_frame.interior.configure(width=50, height=50)
        self.secondary_rune_frame.interior.pack_propagate(False)
        
        # 副系符文ID标签
        self.secondary_id_label = tk.Label(
            self.runes_frame.interior,
            text="8400",
            bg="#091428",
            fg="#666666",
            font=("Microsoft JhengHei", 8)
        )
        self.secondary_id_label.place(x=100, y=65)
            
    def load_rune_image(self, rune_id):
        """加载符文图片
        
        Args:
            rune_id: 符文ID
            
        Returns:
            ImageTk.PhotoImage 对象或 None
        """
        try:
            # 检查缓存
            if rune_id in self.rune_images:
                return self.rune_images[rune_id]
                
            # 获取图片路径
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "runes", f"{rune_id}.png")
            if os.path.exists(image_path):
                image = Image.open(image_path)
                # 调整图片大小
                image = image.resize((40, 40), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.rune_images[rune_id] = photo
                return photo
        except Exception as e:
            logger.error(f"加载符文图片失败 {rune_id}: {e}")
        return None
        
    def update_runes(self, rune_data):
        """更新符文显示
        
        Args:
            rune_data: 包含符文信息的字典
        """
        if not rune_data:
            return
            
        # 更新主系符文
        if 'primary_rune_id' in rune_data:
            primary_photo = self.load_rune_image(rune_data['primary_rune_id'])
            if primary_photo:
                primary_label = tk.Label(
                    self.primary_rune_frame.interior,
                    image=primary_photo,
                    bg="#0A1428"
                )
                primary_label.image = primary_photo
                primary_label.place(relx=0.5, rely=0.5, anchor="center")
                self.primary_id_label.config(text=rune_data['primary_rune_id'])
                
        # 更新副系符文
        if 'secondary_path_id' in rune_data:
            secondary_photo = self.load_rune_image(rune_data['secondary_path_id'])
            if secondary_photo:
                secondary_label = tk.Label(
                    self.secondary_rune_frame.interior,
                    image=secondary_photo,
                    bg="#0A1428"
                )
                secondary_label.image = secondary_photo
                secondary_label.place(relx=0.5, rely=0.5, anchor="center")
                self.secondary_id_label.config(text=rune_data['secondary_path_id']) 