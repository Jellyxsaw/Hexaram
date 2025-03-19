import os
import requests
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiotAssetsDownloader:
    def __init__(self):
        # Riot Data Dragon 的基礎URL
        self.ddragon_base_url = "https://ddragon.leagueoflegends.com"
        self.version = self._get_latest_version()
        
        # 設置資源目錄
        self.assets_dir = Path("assets")
        self.runes_dir = self.assets_dir / "runes"
        self.items_dir = self.assets_dir / "items"
        
        # 創建必要的目錄
        self._create_directories()

    def _get_latest_version(self) -> str:
        """獲取最新的遊戲版本"""
        try:
            versions_url = f"{self.ddragon_base_url}/api/versions.json"
            response = requests.get(versions_url)
            response.raise_for_status()
            versions = response.json()
            return versions[0]  # 返回最新版本
        except Exception as e:
            logger.error(f"獲取版本信息失敗: {e}")
            return "13.24.1"  # 如果失敗則返回一個固定版本

    def _create_directories(self):
        """創建必要的目錄結構"""
        self.runes_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)

    def download_image(self, url: str, save_path: Path) -> bool:
        """
        下載圖片並保存到指定路徑
        
        Args:
            url: 圖片URL
            save_path: 保存路徑
            
        Returns:
            bool: 下載是否成功
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"成功下載圖片: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下載圖片失敗 {url}: {e}")
            return False

    def download_rune_images(self):
        """下載所有符文圖片"""
        try:
            # 獲取符文數據
            runes_url = f"{self.ddragon_base_url}/cdn/{self.version}/data/en_US/runesReforged.json"
            response = requests.get(runes_url)
            response.raise_for_status()
            runes_data = response.json()

            # 下載每個符文系的圖片
            for rune_style in runes_data:
                # 下載主系圖標
                icon_path = rune_style['icon']
                icon_url = f"{self.ddragon_base_url}/cdn/img/{icon_path}"
                save_path = self.runes_dir / f"{rune_style['id']}.png"
                self.download_image(icon_url, save_path)

                # 下載具體符文圖標
                for slot in rune_style['slots']:
                    for rune in slot['runes']:
                        icon_path = rune['icon']
                        icon_url = f"{self.ddragon_base_url}/cdn/img/{icon_path}"
                        save_path = self.runes_dir / f"{rune['id']}.png"
                        self.download_image(icon_url, save_path)

            logger.info("符文圖片下載完成")

        except Exception as e:
            logger.error(f"下載符文圖片時發生錯誤: {e}")

    def download_item_images(self):
        """下載所有裝備圖片"""
        try:
            # 獲取裝備數據
            items_url = f"{self.ddragon_base_url}/cdn/{self.version}/data/en_US/item.json"
            response = requests.get(items_url)
            response.raise_for_status()
            items_data = response.json()

            # 下載每個裝備的圖片
            for item_id, item_info in items_data['data'].items():
                image_name = item_info['image']['full']
                image_url = f"{self.ddragon_base_url}/cdn/{self.version}/img/item/{image_name}"
                save_path = self.items_dir / f"{item_id}.png"
                self.download_image(image_url, save_path)

            logger.info("裝備圖片下載完成")

        except Exception as e:
            logger.error(f"下載裝備圖片時發生錯誤: {e}")

def main():
    """主函數"""
    downloader = RiotAssetsDownloader()
    
    # 下載所有資源
    logger.info("開始下載符文圖片...")
    downloader.download_rune_images()
    
    logger.info("開始下載裝備圖片...")
    downloader.download_item_images()
    
    logger.info("所有資源下載完成!")

if __name__ == "__main__":
    main() 