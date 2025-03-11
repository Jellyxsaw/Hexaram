import json


def extract_features(match_data):
    features = {}
    # 取得遊戲時長（秒）
    game_duration = match_data["info"].get("gameDuration", 0)
    features["game_duration"] = game_duration

    # 初始化隊伍統計（假設隊伍 ID 為 100 與 200）
    team_features = {
        100: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0},
        200: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0}
    }

    # 參賽者層級的特徵列表
    participant_features = []
    # 設定控場時間的縮放因子，因為控場時間（秒）與傷害數值量級不同
    cc_scale = 100.0

    for participant in match_data["info"]["participants"]:
        p_feats = {}
        p_feats["puuid"] = participant.get("puuid", "")
        p_feats["championName"] = participant.get("championName", "")
        p_feats["teamId"] = participant.get("teamId", 0)

        # 傷害數據
        challenges = participant.get("challenges", {})
        if "damagePerMinute" in challenges:
            p_feats["damage_per_minute"] = challenges["damagePerMinute"]
        else:
            total_damage = participant.get("totalDamageDealtToChampions", 0)
            p_feats["damage_per_minute"] = total_damage / (game_duration / 60.0) if game_duration > 0 else 0

        p_feats["total_damage_dealt_to_champions"] = participant.get("totalDamageDealtToChampions", 0)
        p_feats["total_damage_taken"] = participant.get("totalDamageTaken", 0)
        p_feats["physical_damage_dealt_to_champions"] = participant.get("physicalDamageDealtToChampions", 0)
        p_feats["magic_damage_dealt_to_champions"] = participant.get("magicDamageDealtToChampions", 0)

        # 自我減傷
        p_feats["damage_self_mitigated"] = participant.get("damageSelfMitigated", 0)

        # 治療與護盾（對自己與隊友）
        p_feats["total_heal"] = participant.get("totalHeal", 0)
        p_feats["total_heals_on_teammates"] = participant.get("totalHealsOnTeammates", 0)
        p_feats["total_damage_shielded_on_teammates"] = participant.get("totalDamageShieldedOnTeammates", 0)

        # 控場數值：以「timeCCingOthers」作為代表
        p_feats["time_ccing_others"] = participant.get("timeCCingOthers", 0)

        # 金錢數據
        p_feats["gold_earned"] = participant.get("goldEarned", 0)
        p_feats["gold_spent"] = participant.get("goldSpent", 0)

        # 指標1：每點傷害所獲金錢
        total_damage_output = p_feats["total_damage_dealt_to_champions"]
        if total_damage_output > 0:
            p_feats["gold_per_damage_dealt"] = p_feats["gold_earned"] / total_damage_output
        else:
            p_feats["gold_per_damage_dealt"] = 0

        # 綜合效率：結合輸出、承受傷害、控場、治療／護盾和自我減傷
        total_effort = (
                p_feats["total_damage_dealt_to_champions"] +
                p_feats["total_damage_taken"] +
                (p_feats["time_ccing_others"] * cc_scale) +
                (p_feats["total_heal"] + p_feats["total_heals_on_teammates"] + p_feats[
                    "total_damage_shielded_on_teammates"]) +
                p_feats["damage_self_mitigated"]
        )
        if total_effort > 0:
            p_feats["gold_conversion_efficiency"] = p_feats["gold_earned"] / total_effort
        else:
            p_feats["gold_conversion_efficiency"] = 0

        # KDA 指標
        p_feats["kills"] = participant.get("kills", 0)
        p_feats["deaths"] = participant.get("deaths", 0)
        p_feats["assists"] = participant.get("assists", 0)
        if p_feats["deaths"] > 0:
            p_feats["kda"] = (p_feats["kills"] + p_feats["assists"]) / p_feats["deaths"]
        else:
            p_feats["kda"] = p_feats["kills"] + p_feats["assists"]

        participant_features.append(p_feats)

        # 累加到隊伍統計
        team_id = participant.get("teamId", 0)
        if team_id in team_features:
            team_features[team_id]["total_gold"] += p_feats["gold_earned"]
            team_features[team_id]["total_damage_dealt"] += p_feats["total_damage_dealt_to_champions"]
            team_features[team_id]["total_kills"] += p_feats["kills"]
            team_features[team_id]["total_assists"] += p_feats["assists"]
            team_features[team_id]["total_deaths"] += p_feats["deaths"]

    features["participants"] = participant_features

    # 讀取隊伍勝負資訊，並加入隊伍統計中
    for team in match_data["info"].get("teams", []):
        team_id = team.get("teamId")
        if team_id in team_features:
            team_features[team_id]["win"] = team.get("win", False)
    features["teams"] = team_features

    # 可計算雙方隊伍的金錢與傷害差距
    if 100 in team_features and 200 in team_features:
        features["team_gold_diff"] = team_features[100]["total_gold"] - team_features[200]["total_gold"]
        features["team_damage_diff"] = team_features[100]["total_damage_dealt"] - team_features[200][
            "total_damage_dealt"]

    return features
def extract_features(match_data):
    """
    從原始對局資料中擷取精細的特徵數據
    """
    features = {}
    game_duration = match_data["info"].get("gameDuration", 0)
    features["game_duration"] = game_duration

    # 初始化隊伍統計（假設隊伍 ID 為 100 與 200）
    team_features = {
        100: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0},
        200: {"total_gold": 0, "total_damage_dealt": 0, "total_kills": 0, "total_assists": 0, "total_deaths": 0}
    }

    participant_features = []
    cc_scale = 100.0

    for participant in match_data["info"]["participants"]:
        p_feats = {}
        p_feats["puuid"] = participant.get("puuid", "")
        p_feats["championName"] = participant.get("championName", "")
        p_feats["teamId"] = participant.get("teamId", 0)

        challenges = participant.get("challenges", {})
        if "damagePerMinute" in challenges:
            p_feats["damage_per_minute"] = challenges["damagePerMinute"]
        else:
            total_damage = participant.get("totalDamageDealtToChampions", 0)
            p_feats["damage_per_minute"] = total_damage / (game_duration / 60.0) if game_duration > 0 else 0

        p_feats["total_damage_dealt_to_champions"] = participant.get("totalDamageDealtToChampions", 0)
        p_feats["total_damage_taken"] = participant.get("totalDamageTaken", 0)
        p_feats["physical_damage_dealt_to_champions"] = participant.get("physicalDamageDealtToChampions", 0)
        p_feats["magic_damage_dealt_to_champions"] = participant.get("magicDamageDealtToChampions", 0)
        p_feats["damage_self_mitigated"] = participant.get("damageSelfMitigated", 0)
        p_feats["total_heal"] = participant.get("totalHeal", 0)
        p_feats["total_heals_on_teammates"] = participant.get("totalHealsOnTeammates", 0)
        p_feats["total_damage_shielded_on_teammates"] = participant.get("totalDamageShieldedOnTeammates", 0)
        p_feats["time_ccing_others"] = participant.get("timeCCingOthers", 0)
        p_feats["gold_earned"] = participant.get("goldEarned", 0)
        p_feats["gold_spent"] = participant.get("goldSpent", 0)

        total_damage_output = p_feats["total_damage_dealt_to_champions"]
        if total_damage_output > 0:
            p_feats["gold_per_damage_dealt"] = p_feats["gold_earned"] / total_damage_output
        else:
            p_feats["gold_per_damage_dealt"] = 0

        total_effort = (
            p_feats["total_damage_dealt_to_champions"] +
            p_feats["total_damage_taken"] +
            (p_feats["time_ccing_others"] * cc_scale) +
            (p_feats["total_heal"] + p_feats["total_heals_on_teammates"] + p_feats["total_damage_shielded_on_teammates"]) +
            p_feats["damage_self_mitigated"]
        )
        if total_effort > 0:
            p_feats["gold_conversion_efficiency"] = p_feats["gold_earned"] / total_effort
        else:
            p_feats["gold_conversion_efficiency"] = 0

        p_feats["kills"] = participant.get("kills", 0)
        p_feats["deaths"] = participant.get("deaths", 0)
        p_feats["assists"] = participant.get("assists", 0)
        if p_feats["deaths"] > 0:
            p_feats["kda"] = (p_feats["kills"] + p_feats["assists"]) / p_feats["deaths"]
        else:
            p_feats["kda"] = p_feats["kills"] + p_feats["assists"]

        participant_features.append(p_feats)

        team_id = participant.get("teamId", 0)
        if team_id in team_features:
            team_features[team_id]["total_gold"] += p_feats["gold_earned"]
            team_features[team_id]["total_damage_dealt"] += p_feats["total_damage_dealt_to_champions"]
            team_features[team_id]["total_kills"] += p_feats["kills"]
            team_features[team_id]["total_assists"] += p_feats["assists"]
            team_features[team_id]["total_deaths"] += p_feats["deaths"]

    features["participants"] = participant_features

    for team in match_data["info"].get("teams", []):
        team_id = team.get("teamId")
        if team_id in team_features:
            team_features[team_id]["win"] = team.get("win", False)
    features["teams"] = team_features

    if 100 in team_features and 200 in team_features:
        features["team_gold_diff"] = team_features[100]["total_gold"] - team_features[200]["total_gold"]
        features["team_damage_diff"] = team_features[100]["total_damage_dealt"] - team_features[200]["total_damage_dealt"]

    return features

# 主程式：假設 JSON 資料儲存在 match_data.json 檔案中
if __name__ == "__main__":
    with open("match_data.json", "r", encoding="utf-8") as f:
        match_data = json.load(f)
    extracted_features = extract_features(match_data)
    # 輸出轉換後的結構，可進一步轉為 pandas DataFrame 等格式供模型使用
    print(json.dumps(extracted_features, indent=2, ensure_ascii=False))
