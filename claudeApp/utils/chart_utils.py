import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
from matplotlib.font_manager import FontProperties

class ChartGenerator:
    def __init__(self):
        # 確保temp目錄存在
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        # 設置matplotlib的樣式
        plt.style.use('dark_background')
        
        # 設置中文字體
        self.font = FontProperties(fname=r"C:\Windows\Fonts\msjh.ttc", size=14)
        
    def create_trend_chart(self, data, versions, champion_name):
        """
        創建勝率趨勢圖
        
        Args:
            data (list): 勝率數據列表
            versions (list): 版本號列表
            champion_name (str): 英雄名稱
            
        Returns:
            str: 生成的圖片路徑
        """
        # 創建圖形 - 增加圖表尺寸
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 設置背景顏色
        fig.patch.set_facecolor('#0f3460')
        ax.set_facecolor('#0f3460')
        
        # 動態設置y軸範圍
        min_val = min(data)
        max_val = max(data)
        
        # 預設範圍40-60
        y_min, y_max = 40, 60
        
        # 如果數據超出預設範圍，逐步擴大範圍
        while min_val < y_min or max_val > y_max:
            y_min -= 5
            y_max += 5
            
        # 添加一些邊距
        margin = (y_max - y_min) * 0.15  # 增加邊距
        y_min = max(0, y_min - margin)
        y_max = min(100, y_max + margin)
        
        ax.set_ylim(y_min, y_max)
        
        # 繪製數據
        x = np.arange(len(data))
        line = ax.plot(x, data, 'o-', color='#4ecca3', linewidth=3, markersize=10)[0]
        
        # 在每個數據點上添加勝率標籤和版本號
        for i, (value, version) in enumerate(zip(data, versions)):
            # 添加勝率標籤
            ax.annotate(f'{value:.1f}%', 
                       (x[i], value),
                       xytext=(0, 15),  # 向上移動一點
                       textcoords='offset points',
                       ha='center',
                       va='bottom',
                       color='white',
                       fontproperties=self.font,
                       fontsize=14,
                       weight='bold')
            
            # 添加版本號標籤（在數據點下方）
            ax.annotate(version, 
                       (x[i], value),
                       xytext=(0, -25),  # 向下偏移
                       textcoords='offset points',
                       ha='center',
                       va='top',
                       color='white',
                       fontproperties=self.font,
                       fontsize=14,
                       weight='bold')
        
        # 隱藏所有軸線和刻度
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # 移除所有標題和標籤
        ax.set_ylabel('')
        ax.set_title('')
        
        # 調整布局
        plt.tight_layout()
        
        # 生成文件名
        filename = f"trend_{champion_name.lower().replace(' ', '_')}.png"
        filepath = self.temp_dir / filename
        
        # 保存圖片，增加DPI以提高清晰度
        plt.savefig(filepath, dpi=200, bbox_inches='tight', facecolor='#0f3460')
        plt.close()
        
        return str(filepath) 