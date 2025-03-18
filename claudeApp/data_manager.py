import logging
import threading
from typing import Dict, List, Any, Optional, Callable
import json
import os
from datetime import datetime

from api_client import AramAPIClient

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataManager:
    """
    數據管理器，負責管理所有與API和本地數據相關的操作
    """

    def __init__(self, base_url: str = "https://api.pinkyjelly.work"):
        """
        初始化數據管理器

        Args:
            base_url: API的基礎URL，預設為"https://api.pinkyjelly.work"
        """
        self.api_client = AramAPIClient(base_url)
        self.last_update = None
        self.local_data_path = "data"
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """確保數據目錄存在"""
        if not os.path.exists(self.local_data_path):
            os.makedirs(self.local_data_path)
            logger.info(f"已創建數據目錄: {self.local_data_path}")

    def get_champion_list(self,
                          champion_type: str = None,
                          sort_by: str = "勝率",
                          page: int = 1,
                          limit: int = 12,
                          use_cache: bool = True,
                          callback: Callable = None,
                          error_callback: Callable = None):
        """
        獲取英雄列表

        Args:
            champion_type: 按英雄類型過濾，如"全部"、"坦克"、"戰士"等
            sort_by: 排序方式，可選"勝率"、"選用率"、"KDA"
            page: 頁碼，從1開始
            limit: 每頁顯示數量
            use_cache: 是否使用快取
            callback: 成功時的回調函數
            error_callback: 錯誤時的回調函數
        """

        def fetch_data():
            try:
                result = self.api_client.get_champion_list(
                    champion_type=champion_type if champion_type != "全部" else None,
                    sort_by=sort_by,
                    page=page,
                    limit=limit,
                    use_cache=use_cache
                )

                # 保存本地副本
                self.save_local_data("champions", result)

                # 更新最後更新時間
                self.last_update = datetime.now()

                # 執行回調
                if callback:
                    callback(result)

            except Exception as e:
                logger.error(f"獲取英雄列表失敗: {str(e)}")

                # 嘗試從本地加載數據
                local_data = self.load_local_data("champions")

                if local_data and callback:
                    logger.info("使用本地緩存的英雄列表數據")
                    callback(local_data)
                elif error_callback:
                    error_callback(str(e))

        # 在背景執行緒中獲取數據
        threading.Thread(target=fetch_data, daemon=True).start()

    def get_champion_detail(self,
                            champion_id: str,
                            use_cache: bool = True,
                            callback: Callable = None,
                            error_callback: Callable = None):
        """
        獲取英雄詳細資訊

        Args:
            champion_id: 英雄ID
            use_cache: 是否使用快取
            callback: 成功時的回調函數
            error_callback: 錯誤時的回調函數
        """

        def fetch_data():
            try:
                result = self.api_client.get_champion_detail(
                    champion_id=champion_id,
                    use_cache=use_cache
                )

                # 保存本地副本
                self.save_local_data(f"champion_{champion_id}", result)

                # 執行回調
                if callback:
                    callback(result)

            except Exception as e:
                logger.error(f"獲取英雄詳細資訊失敗: {str(e)}")

                # 嘗試從本地加載數據
                local_data = self.load_local_data(f"champion_{champion_id}")

                if local_data and callback:
                    logger.info(f"使用本地緩存的英雄詳細資訊: {champion_id}")
                    callback(local_data)
                elif error_callback:
                    error_callback(str(e))

        # 在背景執行緒中獲取數據
        threading.Thread(target=fetch_data, daemon=True).start()

    def search_champions(self,
                         query: str,
                         use_cache: bool = True,
                         callback: Callable = None,
                         error_callback: Callable = None):
        """
        搜索英雄

        Args:
            query: 搜索關鍵字
            use_cache: 是否使用快取
            callback: 成功時的回調函數
            error_callback: 錯誤時的回調函數
        """

        def fetch_data():
            try:
                result = self.api_client.search_champions(
                    query=query,
                    use_cache=use_cache
                )

                # 執行回調
                if callback:
                    callback(result)

            except Exception as e:
                logger.error(f"搜索英雄失敗: {str(e)}")

                if error_callback:
                    error_callback(str(e))

        # 在背景執行緒中獲取數據
        threading.Thread(target=fetch_data, daemon=True).start()

    def get_version_info(self,
                         use_cache: bool = True,
                         callback: Callable = None,
                         error_callback: Callable = None):
        """
        獲取版本信息

        Args:
            use_cache: 是否使用快取
            callback: 成功時的回調函數
            error_callback: 錯誤時的回調函數
        """

        def fetch_data():
            try:
                result = self.api_client.get_version_info(
                    use_cache=use_cache
                )

                # 保存本地副本
                self.save_local_data("version_info", result)

                # 執行回調
                if callback:
                    callback(result)

            except Exception as e:
                logger.error(f"獲取版本信息失敗: {str(e)}")

                # 嘗試從本地加載數據
                local_data = self.load_local_data("version_info")

                if local_data and callback:
                    logger.info("使用本地緩存的版本信息")
                    callback(local_data)
                elif error_callback:
                    error_callback(str(e))

        # 在背景執行緒中獲取數據
        threading.Thread(target=fetch_data, daemon=True).start()

    def get_tier_list(self,
                      champion_type: str = None,
                      use_cache: bool = True,
                      callback: Callable = None,
                      error_callback: Callable = None):
        """
        獲取英雄梯隊列表

        Args:
            champion_type: 按英雄類型過濾，如"全部"、"坦克"、"戰士"等
            use_cache: 是否使用快取
            callback: 成功時的回調函數
            error_callback: 錯誤時的回調函數
        """

        def fetch_data():
            try:
                result = self.api_client.get_tier_list(
                    champion_type=champion_type if champion_type != "全部" else None,
                    use_cache=use_cache
                )

                # 保存本地副本
                self.save_local_data("tier_list", result)

                # 執行回調
                if callback:
                    callback(result)

            except Exception as e:
                logger.error(f"獲取英雄梯隊列表失敗: {str(e)}")

                # 嘗試從本地加載數據
                local_data = self.load_local_data("tier_list")

                if local_data and callback:
                    logger.info("使用本地緩存的英雄梯隊列表")
                    callback(local_data)
                elif error_callback:
                    error_callback(str(e))

        # 在背景執行緒中獲取數據
        threading.Thread(target=fetch_data, daemon=True).start()

    def refresh_all_data(self, callback: Callable = None):
        """
        刷新所有數據

        Args:
            callback: 成功時的回調函數
        """
        # 清除API快取
        self.api_client.clear_cache()

        # 獲取版本信息
        self.get_version_info(use_cache=False)

        # 獲取英雄列表
        self.get_champion_list(use_cache=False)

        # 獲取英雄梯隊列表
        self.get_tier_list(use_cache=False)

        # 更新最後更新時間
        self.last_update = datetime.now()

        # 執行回調
        if callback:
            callback()

    def save_local_data(self, name: str, data: Any):
        """
        保存數據到本地文件

        Args:
            name: 數據名稱
            data: 要保存的數據
        """
        try:
            file_path = os.path.join(self.local_data_path, f"{name}.json")

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"已保存本地數據: {name}")

        except Exception as e:
            logger.error(f"保存本地數據失敗 ({name}): {str(e)}")

    def load_local_data(self, name: str) -> Optional[Any]:
        """
        從本地文件加載數據

        Args:
            name: 數據名稱

        Returns:
            加載的數據，如果加載失敗則返回None
        """
        try:
            file_path = os.path.join(self.local_data_path, f"{name}.json")

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"已加載本地數據: {name}")
            return data

        except Exception as e:
            logger.error(f"加載本地數據失敗 ({name}): {str(e)}")
            return None