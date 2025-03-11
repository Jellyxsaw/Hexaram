# ------------------ 新的使用方式（批量預測） ------------------
from chatDeep import ARAMPredictor
import itertools
import time
from sqlalchemy import create_engine
import pandas as pd


def recommend_compositions(heroes_list, predictor):
    """
    給定英雄列表（英文），生成所有可能的 5 人陣容（順序無關），
    批量預測每個陣容的勝率，並依據勝率排序後回傳結果。
    回傳格式： [(陣容, win_prob), ...]
    """
    candidate_compositions = list(itertools.combinations(heroes_list, 5))
    comps_list = [list(comp) for comp in candidate_compositions]
    batch_results = predictor.batch_predict(comps_list)
    scored_compositions = list(zip(candidate_compositions, batch_results))
    sorted_scored = sorted(scored_compositions, key=lambda x: x[1])
    return sorted_scored


def get_random_heroes():
    """
    從資料庫隨機選出 15 位英雄，
    回傳英雄英文名稱列表以及英文對應繁體中文的字典 mapping。
    """
    try:
        engine = create_engine('postgresql+psycopg2://postgres:aa030566@localhost:5432/aram')
        query = "SELECT hero_name, hero_tw_name FROM champion_list ORDER BY RANDOM() LIMIT 15"
        df = pd.read_sql(query, engine)
        mapping = dict(zip(df["hero_name"], df["hero_tw_name"]))
        return df["hero_name"].tolist(), mapping
    except Exception as e:
        print(f"取得英雄資料發生錯誤: {e}")
        return [], {}


def get_full_chinese_mapping():
    """
    從資料庫讀取完整的英雄中英文對照，回傳一個 dict {英雄英文: 英雄繁體中文}。
    """
    try:
        engine = create_engine('postgresql+psycopg2://postgres:aa030566@localhost:5432/aram')
        query = "SELECT hero_name, hero_tw_name FROM champion_list"
        df = pd.read_sql(query, engine)
        mapping = dict(zip(df["hero_name"], df["hero_tw_name"]))
        return mapping
    except Exception as e:
        print(f"取得完整英雄對照資料發生錯誤: {e}")
        return {}


def test_specific_combination(combination, predictor):
    """
    測試特定組合功能：輸入一組包含 5 位英雄（英文）的列表，
    回傳該組合的勝率（預測值）。
    """
    if len(combination) != 5:
        raise ValueError("請輸入五位英雄的名稱")
    win_rate = predictor.predict_team_strength(combination)
    return win_rate


def random_test(predictor):
    """
    使用從資料庫隨機取得的候選英雄池進行測試：
      1. 印出候選英雄列表（繁體及英文）
      2. 生成所有可能陣容後批量預測，並印出 Top 10 與 Bottom 10（以繁體中文呈現）
    """
    heroes_list_en, en_to_tw = get_random_heroes()
    if not heroes_list_en:
        predictor_temp = ARAMPredictor()
        heroes_list_en = list(predictor_temp.champion_to_idx.keys())
        en_to_tw = {hero: hero for hero in heroes_list_en}

    print("隨機英雄列表（繁體）:", [en_to_tw.get(hero, hero) for hero in heroes_list_en])
    print("隨機英雄列表（英文）:", heroes_list_en)

    start = time.time()
    sorted_compositions = recommend_compositions(heroes_list_en, predictor)
    total_time = time.time() - start
    print(f"總耗時: {total_time:.2f} 秒")

    top_compositions = sorted_compositions[-10:][::-1]  # 勝率最高前 10
    bottom_compositions = sorted_compositions[:10]       # 勝率最低前 10

    print("\nTop 10 推薦陣容:")
    for comp, win_prob in top_compositions:
        # 利用對照字典轉換為繁體中文
        comp_tw = [en_to_tw.get(hero, hero) for hero in comp]
        print(f"勝率: {win_prob:.2%} | 陣容 (繁體): {comp_tw}")

    print("\nBottom 10 推薦陣容:")
    for comp, win_prob in bottom_compositions:
        comp_tw = [en_to_tw.get(hero, hero) for hero in comp]
        print(f"勝率: {win_prob:.2%} | 陣容 (繁體): {comp_tw}")


if __name__ == "__main__":
    predictor = ARAMPredictor()

    # ------------------ 隨機測試 ------------------
    # random_test(predictor)

    # ------------------ 特定組合測試 ------------------
    # 定義一個候選池（15 位英雄），以英文表示
    test_list = ['Sejuani', 'Gwen', 'Evelynn', 'Warwick', 'Naafiri',
                 'Ziggs', 'Nunu & Willump', 'Nocturne', 'Ivern', 'Ahri',
                 'Jax', 'Viego', 'Qiyana', 'Karma', 'Caitlyn']
    # 取得完整對照字典（英文 -> 繁體中文）
    full_mapping = get_full_chinese_mapping()

    print("\n=== 特定候選池測試 ===")
    print("測試候選池（英文）:", test_list)
    # 使用 test_list 作為候選池，產生所有可能的 5 人陣容，並批量預測
    start = time.time()
    sorted_compositions_test = recommend_compositions(test_list, predictor)
    total_time = time.time() - start
    print(f"總耗時: {total_time:.2f} 秒")

    # 取推薦結果中的前 10 與後 10，並用中文呈現
    top_compositions_test = sorted_compositions_test[-10:][::-1]
    bottom_compositions_test = sorted_compositions_test[:10]

    print("\nTop 10 推薦陣容 (Test List):")
    for comp, win_prob in top_compositions_test:
        comp_tw = [full_mapping.get(hero, hero) for hero in comp]
        print(f"勝率: {win_prob:.2%} | 陣容 (繁體): {comp_tw}")

    print("\nBottom 10 推薦陣容 (Test List):")
    for comp, win_prob in bottom_compositions_test:
        comp_tw = [full_mapping.get(hero, hero) for hero in comp]
        print(f"勝率: {win_prob:.2%} | 陣容 (繁體): {comp_tw}")
