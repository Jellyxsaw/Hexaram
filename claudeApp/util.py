import os

from PIL import Image, ImageTk


def load_champion_images(self):
    """載入並處理英雄圖片"""
    self.champ_images = {}

    # 圖片目錄路徑
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "champion_images")
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
        print(f"已創建圖片目錄: {img_dir}")

    # 檢查目錄中的圖片
    if os.path.exists(img_dir):
        for filename in os.listdir(img_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # 從檔名獲取英雄 key (移除副檔名)
                key = os.path.splitext(filename)[0]

                try:
                    # 載入圖片
                    img_path = os.path.join(img_dir, filename)
                    img = Image.open(img_path)

                    # 調整大小，確保所有圖片統一尺寸
                    img = img.resize((40, 40), Image.LANCZOS)

                    # 轉換為 PhotoImage
                    photo_img = ImageTk.PhotoImage(img)

                    # 存儲圖片，使用英雄 key 作為鍵值
                    self.champ_images[key] = photo_img

                    # 如果有 fetcher，建立反向映射
                    if hasattr(self, 'fetcher') and hasattr(self.fetcher, 'id_mapping'):
                        # 將 key 映射到英雄名稱
                        for en_name, k in self.fetcher.name_to_key.items():
                            if k == key:
                                self.champ_images[en_name] = photo_img
                                break
                except Exception as e:
                    print(f"載入圖片失敗: {filename} - {e}")

        print(f"成功載入 {len(self.champ_images)} 張英雄圖片")
    else:
        print("找不到圖片目錄")