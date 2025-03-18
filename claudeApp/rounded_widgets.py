# 將此代碼保存為 rounded_widgets.py
import tkinter as tk
from tkinter import font


class RoundedFrame(tk.Frame):
    """圓角框架小部件"""

    def __init__(self, parent, bg_color="#FFFFFF", corner_radius=10, border_color=None, border_width=0, **kwargs):
        tk.Frame.__init__(self, parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self._corner_radius = corner_radius
        self._border_color = border_color
        self._border_width = border_width
        self._bg_color = bg_color

        self.canvas = tk.Canvas(
            self,
            bg=parent["bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # 設置內部框架，用於放置子元素
        self.interior = tk.Frame(self.canvas, bg=bg_color, highlightthickness=0)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor="nw")

        # 綁定事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.interior.bind("<Configure>", self._on_interior_configure)

        # 初始化渲染
        self._draw_rounded_rectangle()

    def _on_canvas_configure(self, event):
        # 更新畫布大小時重繪圓角矩形
        self.canvas.delete("rounded_rectangle")
        self._draw_rounded_rectangle()
        # 更新內部框架大小
        self.canvas.config(width=event.width, height=event.height)
        self.canvas.itemconfig(self.interior_id, width=event.width, height=event.height)

    def _on_interior_configure(self, event):
        # 更新內部框架大小
        size = (max(event.width, self.winfo_width()), max(event.height, self.winfo_height()))
        self.canvas.config(width=size[0], height=size[1])
        self.canvas.itemconfig(self.interior_id, width=size[0], height=size[1])
        # 重繪圓角矩形
        self.canvas.delete("rounded_rectangle")
        self._draw_rounded_rectangle()

    def _draw_rounded_rectangle(self):
        # 繪製圓角矩形
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return  # 避免在初始化時繪製過小的矩形

        # 創建圓角矩形路徑
        self.canvas.delete("rounded_rectangle")
        radius = self._corner_radius

        # 定義圓角矩形座標點
        points = [
            radius, 0,  # 頂部左邊開始點
            width - radius, 0,  # 頂部右邊結束點
            width, 0, width, radius,  # 右上角
            width, height - radius,  # 右側底部結束點
            width, height, width - radius, height,  # 右下角
            radius, height,  # 底部左邊結束點
            0, height, 0, height - radius,  # 左下角
            0, radius,  # 左側頂部結束點
            0, 0, radius, 0  # 左上角和回到起點
        ]

        # 如果有邊框，先繪製邊框底層
        if self._border_color and self._border_width > 0:
            # 繪製邊框底層
            border_points = points.copy()
            self.canvas.create_polygon(border_points, fill=self._border_color, smooth=True, tags="rounded_rectangle")

            # 繪製縮小的內部填充
            inset = self._border_width
            inner_width, inner_height = width - 2 * inset, height - 2 * inset
            inner_radius = max(0, radius - inset)

            inner_points = [
                inset + inner_radius, inset,  # 頂部左邊開始點
                inset + inner_width - inner_radius, inset,  # 頂部右邊結束點
                inset + inner_width, inset, inset + inner_width, inset + inner_radius,  # 右上角
                inset + inner_width, inset + inner_height - inner_radius,  # 右側底部結束點
                inset + inner_width, inset + inner_height,
                inset + inner_width - inner_radius, inset + inner_height,  # 右下角
                inset + inner_radius, inset + inner_height,  # 底部左邊結束點
                inset, inset + inner_height, inset, inset + inner_height - inner_radius,  # 左下角
                inset, inset + inner_radius,  # 左側頂部結束點
                inset, inset, inset + inner_radius, inset  # 左上角和回到起點
            ]

            self.canvas.create_polygon(inner_points, fill=self._bg_color, smooth=True, tags="rounded_rectangle")
        else:
            # 沒有邊框，直接繪製填充區域
            self.canvas.create_polygon(points, fill=self._bg_color, smooth=True, tags="rounded_rectangle")

    def configure(self, **kwargs):
        if "bg" in kwargs:
            self._bg_color = kwargs.pop("bg")
            self.interior.configure(bg=self._bg_color)
            self._draw_rounded_rectangle()
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._draw_rounded_rectangle()
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            self._draw_rounded_rectangle()
        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._draw_rounded_rectangle()
        super().configure(**kwargs)


class RoundedButton(tk.Canvas):
    """圓角按鈕小部件"""

    def __init__(self, parent, text="Button", command=None, radius=10, bg="#1a1a2e", fg="#FFFFFF",
                 highlight_color="#e94560", padx=15, pady=8, font=None, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.config(bg=parent["bg"])

        self.radius = radius
        self.bg_color = bg
        self.fg_color = fg
        self.highlight_color = highlight_color
        self.command = command
        self.padx = padx
        self.pady = pady
        self.text = text
        self.font = font or ("Arial", 10)

        # 標記按鈕狀態
        self.active = False
        self.selected = False  # 新增：選中狀態

        # 初始化繪製
        self._draw_button()

        # 繫結事件
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_configure)

    def _draw_button(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width <= 1 or height <= 1:
            # 如果尺寸還沒有確定，使用預設尺寸
            text_font = font.Font(family=self.font[0], size=self.font[1])
            width = text_font.measure(self.text) + self.padx * 2
            height = text_font.metrics()['linespace'] + self.pady * 2
            self.config(width=width, height=height)

        # 繪製背景
        if self.selected:
            bg_color = self.highlight_color  # 選中狀態使用高亮色
        else:
            bg_color = self.highlight_color if self.active else self.bg_color

        radius = min(self.radius, height // 2, width // 2)  # 確保圓角半徑不超過尺寸的一半

        # 創建圓角矩形
        self.create_rectangle(
            radius, 0, width - radius, height,
            fill=bg_color, outline="", tags="bg")
        self.create_rectangle(
            0, radius, width, height - radius,
            fill=bg_color, outline="", tags="bg")
        self.create_oval(
            0, 0, radius * 2, radius * 2,
            fill=bg_color, outline="", tags="bg")
        self.create_oval(
            width - radius * 2, 0, width, radius * 2,
            fill=bg_color, outline="", tags="bg")
        self.create_oval(
            0, height - radius * 2, radius * 2, height,
            fill=bg_color, outline="", tags="bg")
        self.create_oval(
            width - radius * 2, height - radius * 2, width, height,
            fill=bg_color, outline="", tags="bg")

        # 繪製文字
        self.create_text(
            width // 2, height // 2,
            text=self.text, fill=self.fg_color, font=self.font, tags="text")

    def _on_enter(self, event):
        if not self.selected:  # 只有在非選中狀態下才改變懸停效果
            self.active = True
            self._draw_button()

    def _on_leave(self, event):
        if not self.selected:  # 只有在非選中狀態下才改變懸停效果
            self.active = False
            self._draw_button()

    def _on_press(self, event):
        # 點擊效果 - 可以添加更多視覺效果
        pass

    def _on_release(self, event):
        if self.command is not None:
            self.command()

    def _on_configure(self, event):
        self._draw_button()

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "bg" in kwargs:
            self.bg_color = kwargs.pop("bg")
        if "fg" in kwargs:
            self.fg_color = kwargs.pop("fg")
        if "highlight_color" in kwargs:
            self.highlight_color = kwargs.pop("highlight_color")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "font" in kwargs:
            self.font = kwargs.pop("font")
        if "radius" in kwargs:
            self.radius = kwargs.pop("radius")
        if "padx" in kwargs:
            self.padx = kwargs.pop("padx")
        if "pady" in kwargs:
            self.pady = kwargs.pop("pady")
        if "selected" in kwargs:  # 新增：支持設置選中狀態
            self.selected = kwargs.pop("selected")
            if not self.selected:  # 當按鈕被取消選中時，重置 active 狀態
                self.active = False

        super().configure(**kwargs)
        self._draw_button()

    def cget(self, key):
        if key == "text":
            return self.text
        elif key == "bg":
            return self.bg_color
        elif key == "fg":
            return self.fg_color
        elif key == "selected":  # 新增：支持獲取選中狀態
            return self.selected
        else:
            return super().cget(key)