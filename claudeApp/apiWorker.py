import requests

PREDICT_API_URL = "https://api.pinkyjelly.work/predict/predict_team"
PREDICT_WORST_API_URL = "https://api.pinkyjelly.work/predict/predict_worst_team"


def recommend_compositions_api(candidate_pool):
    """
    傳入 candidate_pool 後，透過 API 取得排序後的結果 sorted_scored。

    參數:
        candidate_pool: list，候選英雄列表（API 可處理 5~15 位英雄）
        api_url: str，API 的完整 URL，例如 "https://your-app-engine-url/predict_team"

    回傳:
        sorted_scored: list，每個元素為 tuple，格式 (team, win_rate)
    """
    # 將 candidate_pool 作為 heroes 傳送給 API
    payload = {"heroes": candidate_pool}
    try:
        response = requests.post(PREDICT_API_URL, json=payload, timeout=25)
    except Exception as e:
        raise Exception(f"API 請求失敗：{e}")

    if response.status_code != 200:
        raise Exception(f"API 請求失敗，狀態碼：{response.status_code}，回應：{response.text}")

    data = response.json()
    top_teams = data.get("top_teams")
    if not top_teams:
        raise Exception("API 回傳格式錯誤，缺少 top_teams 資料")

    # 假設 API 回傳的 top_teams 已經是排序好的，轉換成 (team, win_rate) tuple 的列表
    sorted_scored = sorted(
        [(team_info["team"], team_info["win_rate"]) for team_info in top_teams],
        key=lambda x: x[1]
    )

    return sorted_scored


def recommend_worst_compositions_api(candidate_pool):
    """
    傳入 candidate_pool 後，透過 API 取得最不推薦的陣容組合。

    參數:
        candidate_pool: list，候選英雄列表（API 可處理 5~15 位英雄）

    回傳:
        sorted_scored: list，每個元素為 tuple，格式 (team, win_rate)，按勝率從低到高排序
    """
    # 將 candidate_pool 作為 heroes 傳送給 API
    payload = {"heroes": candidate_pool}
    try:
        response = requests.post(PREDICT_WORST_API_URL, json=payload, timeout=25)
    except Exception as e:
        raise Exception(f"API 請求失敗：{e}")

    if response.status_code != 200:
        raise Exception(f"API 請求失敗，狀態碼：{response.status_code}，回應：{response.text}")

    data = response.json()
    worst_teams = data.get("worst_teams")
    if not worst_teams:
        raise Exception("API 回傳格式錯誤，缺少 worst_teams 資料")

    # 轉換成 (team, win_rate) tuple 的列表，並按勝率從低到高排序
    sorted_scored = sorted(
        [(team_info["team"], team_info["win_rate"]) for team_info in worst_teams],
        key=lambda x: x[1]
    )

    return sorted_scored
