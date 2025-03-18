import requests
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import time

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AramAPIClient:
    """處理與ARAM API的通訊的客戶端"""

    def __init__(self, base_url: str = "https://api.pinkyjelly.work"):
        """
        初始化API客戶端

        Args:
            base_url: API的基礎URL，預設為"https://api.pinkyjelly.work"
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.cache = {}  # 簡單的記憶體快取
        self.cache_expiry = {}  # 快取的過期時間
        self.cache_duration = 300  # 預設快取持續時間為5分鐘（300秒）

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        從快取中獲取資料，如果快取已過期或不存在則返回None

        Args:
            cache_key: 快取的鍵值

        Returns:
            快取的資料，或者None如果快取不存在或已過期
        """
        if cache_key in self.cache and cache_key in self.cache_expiry:
            if time.time() < self.cache_expiry[cache_key]:
                return self.cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Any, duration: int = None) -> None:
        """
        設置快取資料

        Args:
            cache_key: 快取的鍵值
            data: 要快取的資料
            duration: 快取持續時間（秒），如果為None則使用預設值
        """
        if duration is None:
            duration = self.cache_duration

        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = time.time() + duration

    def _make_request(self,
                      endpoint: str,
                      method: str = "GET",
                      params: Dict = None,
                      data: Dict = None,
                      use_cache: bool = True,
                      cache_duration: int = None) -> Any:
        """
        發送API請求並處理回應

        Args:
            endpoint: API端點
            method: HTTP方法，預設為GET
            params: URL參數
            data: 請求主體資料（用於POST請求）
            use_cache: 是否使用快取，預設為True
            cache_duration: 快取持續時間（秒），如果為None則使用預設值

        Returns:
            API回應的JSON資料

        Raises:
            Exception: 如果API請求失敗或回應無效
        """
        url = f"{self.base_url}{endpoint}"

        # 為GET請求建立快取鍵
        cache_key = None
        if use_cache and method == "GET":
            cache_key = f"{url}_{json.dumps(params) if params else ''}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.debug(f"從快取獲取資料: {url}")
                return cached_data

        try:
            logger.debug(f"{method} 請求到 {url}")
            response = None

            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"不支援的HTTP方法: {method}")

            response.raise_for_status()
            result = response.json()

            # 為GET請求設置快取
            if use_cache and method == "GET" and cache_key:
                self._set_cache(cache_key, result, cache_duration)

            return result

        except requests.RequestException as e:
            logger.error(f"API請求錯誤 ({url}): {str(e)}")
            raise Exception(f"API請求失敗: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"API回應解析錯誤 ({url}): {str(e)}")
            raise Exception(f"無效的API回應: {str(e)}")

    def get_champion_list(self,
                          champion_type: str = None,
                          sort_by: str = "勝率",
                          page: int = 1,
                          limit: int = 12,
                          use_cache: bool = True) -> Dict:
        """
        獲取英雄列表

        Args:
            champion_type: 按英雄類型過濾，如"全部"、"坦克"、"戰士"等，預設為None（不過濾）
            sort_by: 排序方式，可選"勝率"、"選用率"、"KDA"，預設為"勝率"
            page: 頁碼，從1開始，預設為1
            limit: 每頁顯示數量，預設為12
            use_cache: 是否使用快取，預設為True

        Returns:
            包含英雄列表和分頁資訊的字典
        """
        params = {
            'page': page,
            'limit': limit,
            'sort': sort_by
        }

        if champion_type and champion_type != "全部":
            params['type'] = champion_type

        return self._make_request("/api/champions", params=params, use_cache=use_cache)

    def get_champion_detail(self, champion_id: str, use_cache: bool = True) -> Dict:
        """
        獲取英雄詳細資訊

        Args:
            champion_id: 英雄ID
            use_cache: 是否使用快取，預設為True

        Returns:
            英雄詳細資訊
        """
        return self._make_request(f"/api/champions/{champion_id}", use_cache=use_cache)

    def get_champion_by_key(self, key: int, use_cache: bool = True) -> Dict:
        """
        通過Riot key獲取英雄資料

        Args:
            key: Riot定義的英雄key
            use_cache: 是否使用快取，預設為True

        Returns:
            英雄詳細資訊
        """
        return self._make_request(f"/api/champion-stats-by-key/{key}", use_cache=use_cache)

    def search_champions(self, query: str, use_cache: bool = True) -> Dict:
        """
        搜索英雄

        Args:
            query: 搜索關鍵字
            use_cache: 是否使用快取，預設為True

        Returns:
            搜索結果列表
        """
        if not query or len(query) < 1:
            return {"results": []}

        return self._make_request("/api/champion-search", params={"q": query}, use_cache=use_cache)

    def get_tier_list(self, champion_type: str = None, use_cache: bool = True) -> Dict:
        """
        獲取英雄梯隊列表

        Args:
            champion_type: 按英雄類型過濾，如"全部"、"坦克"、"戰士"等，預設為None（不過濾）
            use_cache: 是否使用快取，預設為True

        Returns:
            英雄梯隊列表
        """
        params = {}
        if champion_type and champion_type != "全部":
            params['type'] = champion_type

        return self._make_request("/api/tier-list", params=params, use_cache=use_cache)

    def get_version_info(self, use_cache: bool = True) -> Dict:
        """
        獲取當前資料版本信息

        Returns:
            API當前資料版本、最後更新時間及樣本數量等信息
        """
        return self._make_request("/api/version", use_cache=use_cache)

    def clear_cache(self) -> None:
        """
        清除所有快取
        """
        self.cache = {}
        self.cache_expiry = {}
        logger.info("已清除所有API快取")


# 範例使用方式
if __name__ == "__main__":
    # 建立API客戶端
    api_client = AramAPIClient()

    # 獲取英雄列表
    try:
        champions = api_client.get_champion_list()
        print(f"獲取到 {len(champions['champions'])} 個英雄")

        # 顯示第一個英雄
        if champions['champions']:
            print(f"第一個英雄: {champions['champions'][0]['name']}")
    except Exception as e:
        print(f"獲取英雄列表失敗: {str(e)}")